"""SyncFrame entry point (GUI and CLI diagnostics)."""

import argparse
import logging
import os
import sys

# Resource Throttling: Enforce thread limits before native math runtimes load
os.environ.setdefault("OMP_NUM_THREADS", "2")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "2")
os.environ.setdefault("MKL_NUM_THREADS", "2")
os.environ.setdefault("VECLIB_MAXIMUM_THREADS", "2")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "2")

# FlexiBLAS runtime resolution (required for standalone Linux ELF binaries)
if "FLEXIBLAS_LIBRARY_PATH" not in os.environ:
    _meipass = getattr(sys, "_MEIPASS", "")
    _bundled_flexiblas = os.path.join(_meipass, "flexiblas") if _meipass else ""
    if _bundled_flexiblas and os.path.isdir(_bundled_flexiblas):
        os.environ["FLEXIBLAS_LIBRARY_PATH"] = _bundled_flexiblas
    elif os.path.isdir("/usr/lib64/flexiblas"):
        os.environ["FLEXIBLAS_LIBRARY_PATH"] = "/usr/lib64/flexiblas"
    elif os.path.isdir("/usr/lib/x86_64-linux-gnu/flexiblas"):
        os.environ["FLEXIBLAS_LIBRARY_PATH"] = "/usr/lib/x86_64-linux-gnu/flexiblas"
    elif os.path.isdir("/usr/lib/flexiblas"):
        os.environ["FLEXIBLAS_LIBRARY_PATH"] = "/usr/lib/flexiblas"

_repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)

from PySide6.QtWidgets import QDialog
from src.ui.app import create_application
from src.ui.main_window import SyncFrameMainWindow
from src.ui.components.preflight_dialog import PreFlightDialog
from src.utils.system_check import check_system_dependencies, PreFlightChecker, PreFlightReport

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] (%(name)s) %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("syncframe")


def run_headless_cli(args: argparse.Namespace) -> int:
    """
    Executes headless automated synchronization and lossless remuxing from the terminal.
    
    Exit codes:
    - 0: Success (remux completed and verified in closed-loop)
    - 1: Host dependency error, invalid file path, or fatal system error
    - 2: Montage cut or temporal step discontinuity detected
    - 3: Low acoustic correlation confidence or noise floor rejection
    """
    from src.core.extractor import extract_reference_channel
    from src.core.correlator import (
        calculate_offset_from_signals,
        detect_temporal_discontinuities,
        diagnose_drift_and_framerate,
        load_wav_mono
    )
    from src.core.inspector import probe_media_file, extract_container_time_offsets
    from src.core.models import RemuxJob
    from src.core.remuxer import execute_lossless_remux
    from src.core.temp_manager import TempWorkspace

    video_path = os.path.abspath(args.video)
    dub_path = os.path.abspath(args.dub)
    out_path = os.path.abspath(args.output) if args.output else os.path.splitext(video_path)[0] + ".synced.mkv"

    if not os.path.isfile(video_path):
        print(f"Erro: Arquivo de vídeo de referência não encontrado: {video_path}", file=sys.stderr)
        return 1
    if not os.path.isfile(dub_path):
        print(f"Erro: Arquivo de áudio dublado não encontrado: {dub_path}", file=sys.stderr)
        return 1

    print("=== SyncFrame Headless CLI Engine (v1.1.0) ===")
    print(f"Vídeo Referência: {video_path}")
    print(f"Áudio Dublado:    {dub_path}")
    print(f"Destino Remux:    {out_path}")

    # Inspect media containers
    try:
        vid_info = probe_media_file(video_path)
        dub_info = probe_media_file(dub_path)
    except Exception as exc:
        print(f"Erro na inspeção dos contêineres: {exc}", file=sys.stderr)
        return 1

    ref_audio_id = vid_info.audio_streams[0].id if vid_info.audio_streams else 0
    target_audio_id = dub_info.audio_streams[0].id if dub_info.audio_streams else 0
    duration_sec = vid_info.duration_ms / 1000.0 if vid_info.duration_ms > 0 else 1800.0

    print(f"Trilha Referência: #{ref_audio_id} | Trilha Dublada: #{target_audio_id} | Duração: {duration_sec:.1f}s")

    with TempWorkspace(session_name="cli_headless") as ws:
        # Multi-window extraction for cut and drift analysis (5%, 50%, 85%)
        window_pcts = [0.05, 0.50, 0.85]
        window_duration = min(120.0, max(20.0, duration_sec * 0.05))
        window_results = []

        print("Extraindo amostras acústicas e calculando correlação cruzada FFT...")
        for i, pct in enumerate(window_pcts):
            start_sec = max(0.0, (duration_sec * pct) - (window_duration / 2.0))
            ref_w = ws.get_path(f"ref_w{i}.wav")
            tgt_w = ws.get_path(f"tgt_w{i}.wav")

            extract_reference_channel(
                video_path, stream_id=ref_audio_id, duration_sec=window_duration,
                start_sec=start_sec, output_path=ref_w, apply_bandpass=True
            )
            extract_reference_channel(
                dub_path, stream_id=target_audio_id, duration_sec=window_duration,
                start_sec=start_sec, output_path=tgt_w, apply_bandpass=True
            )

            ref_sig, sr_r = load_wav_mono(ref_w)
            tgt_sig, sr_t = load_wav_mono(tgt_w)

            off_ms, conf, _, pslr = calculate_offset_from_signals(ref_sig, tgt_sig, sr_r, max_lag_sec=60.0)
            window_results.append((start_sec, off_ms, conf))
            print(f"  Janela {int(pct*100)}% ({start_sec:.0f}s): offset = {off_ms:+.1f} ms, conf = {conf:.2f}, pslr = {pslr:.1f}")

        # Check for non-linear step discontinuity / cuts
        discont = detect_temporal_discontinuities(window_results, duration_sec=duration_sec)
        if discont.has_cuts and not getattr(args, "ignore_cuts", False):
            print(f"ERRO: Descontinuidade temporal em degrau detectada!\nDetalhes: {discont.diagnosis}", file=sys.stderr)
            print("Cortes de montagem, introduções ou logos ausentes impedem sincronização linear contínua.", file=sys.stderr)
            return 2

        # Check for framerate drift
        drift_ratio, detected_mismatch, diag_txt, stretch_ratio = diagnose_drift_and_framerate(window_results)
        print(f"Diagnóstico de Deriva: {diag_txt}")

        # Static offset selection
        valid_windows = [w for w in window_results if w[2] >= 0.25]
        if not valid_windows or valid_windows[0][2] < 0.35:
            print(f"ERRO: Confiança acústica insuficiente no pico de correlação (< 0.35). Piso de ruído excessivo.", file=sys.stderr)
            return 3

        static_offset_ms = valid_windows[0][1]
        print(f"Offset Estático Base: {static_offset_ms:+.1f} ms")

        job = RemuxJob(
            output_path=out_path,
            video_file=video_path,
            target_audio_file=dub_path,
            offset_ms=static_offset_ms,
            stretch_ratio=stretch_ratio,
            keep_original_audio=args.keep_original,
            target_track_id=target_audio_id,
            ref_audio_track_id=ref_audio_id,
            video_track_id=0,
            pal_pitch_restore=args.pal_pitch_restore,
            audio_codec=args.audio_codec or "flac",
            run_post_audit=not getattr(args, "no_audit", False)
        )

        def _cli_progress(pct: float, msg: str):
            if pct >= 0:
                print(f"  [{pct:5.1f}%] {msg}")

        print("Executando multiplexação lossless com mkvmerge...")
        try:
            success = execute_lossless_remux(job, on_progress=_cli_progress)
            if success:
                print(f"SUCESSO: Arquivo remuxado e auditado com êxito: {out_path}")
                return 0
            else:
                print("ERRO: Falha na execução da multiplexação.", file=sys.stderr)
                return 1
        except Exception as exc:
            print(f"ERRO FATAL: {exc}", file=sys.stderr)
            return 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description="SyncFrame — High-Fidelity Audio/Video Lossless Remux & Sincronizador Acústico"
    )
    parser.add_argument(
        "--cli-check",
        action="store_true",
        help="Executa diagnóstico de dependências do sistema e sai sem abrir a interface gráfica."
    )
    parser.add_argument(
        "--version",
        action="version",
        version="SyncFrame 1.1.0"
    )

    # Headless CLI arguments
    parser.add_argument("--video", type=str, help="Caminho do arquivo de vídeo de referência (MKV/MP4/MOV).")
    parser.add_argument("--dub", type=str, help="Caminho do arquivo de áudio ou vídeo dublado (MKV/MP4/MOV).")
    parser.add_argument("--output", "-o", type=str, default="", help="Caminho do arquivo MKV sincronizado de saída.")
    parser.add_argument("--keep-original", action="store_true", default=False, help="Preserva o áudio original em inglês como faixa secundária.")
    parser.add_argument("--pal-pitch-restore", action="store_true", default=False, help="Aplica desaceleração PAL (25fps -> 24fps) com restauração tonal (pitch drop).")
    parser.add_argument("--audio-codec", type=str, default="flac", choices=["flac", "opus", "eac3", "ac3", "aac"], help="Codec para recompressão caso time-stretch/pitch seja obrigatório (padrão: flac).")
    parser.add_argument("--ignore-cuts", action="store_true", default=False, help="Ignora detecção de cortes/descontinuidades em degrau.")
    parser.add_argument("--no-audit", action="store_true", default=False, help="Desativa verificação pós-remux em malha fechada.")

    args = parser.parse_args()

    # Perform host system dependencies validation
    diag = check_system_dependencies()

    if args.cli_check:
        print("=== Diagnóstico de Ferramentas do Sistema — SyncFrame ===")
        print(f"FFmpeg:    {'[OK] ' + diag.binary_paths.get('ffmpeg', '') if diag.ffmpeg_available else '[FALHA]'}")
        print(f"FFprobe:   {'[OK] ' + diag.binary_paths.get('ffprobe', '') if diag.ffprobe_available else '[FALHA]'}")
        print(f"mkvmerge:  {'[OK] ' + diag.binary_paths.get('mkvmerge', '') if diag.mkvmerge_available else '[FALHA]'}")
        print(f"mkvextract:{'[OK] ' + diag.binary_paths.get('mkvextract', '') if diag.mkvextract_available else '[AUSENTE (Opcional)]'}")
        print(f"mpv player:{'[OK] ' + diag.binary_paths.get('mpv', '') if diag.mpv_available else '[AUSENTE (Fallback ffplay)]'}")
        print(f"Status Operacional: {'APROVADO' if diag.is_operational else 'INCOMPLETO'}")
        if not diag.is_operational:
            print("\n" + diag.install_instructions())
            return 1
        return 0

    # If headless arguments provided, execute CLI pipeline
    if args.video and args.dub:
        if not diag.is_operational:
            logger.error("Ferramentas essenciais ausentes no host: %s", ", ".join(diag.missing_required))
            print(diag.install_instructions(), file=sys.stderr)
            return 1
        return run_headless_cli(args)

    # Guard against headless terminal executions without active display
    if not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
        print(
            "Erro: Nenhum servidor gráfico ativo detectado ($DISPLAY ou $WAYLAND_DISPLAY ausente).\n"
            "O SyncFrame requer uma sessão gráfica (X11 ou Wayland) para execução da interface desktop.\n"
            "Para operações headless no terminal, informe os parâmetros: --video <arquivo> --dub <arquivo> [opções]\n"
            "Para diagnósticos no terminal sem interface, utilize a flag: --cli-check",
            file=sys.stderr
        )
        return 1

    # Pre-Flight Gate: Verify mandatory system binaries before main window initialization
    preflight_report = PreFlightChecker.verify_system_binaries()
    app = create_application()

    if not preflight_report.is_ready:
        logger.warning(
            "Dependências obrigatórias ausentes no pré-voo: %s. Abrindo diálogo de provisionamento...",
            ", ".join(preflight_report.missing_tools)
        )
        preflight_dlg = PreFlightDialog(preflight_report)
        if preflight_dlg.exec() != QDialog.Accepted:
            logger.info("Inicialização cancelada pelo usuário no diálogo de dependências.")
            return 0
        # Re-verify post installation
        preflight_report = PreFlightChecker.verify_system_binaries()
        if not preflight_report.is_ready:
            logger.error("Dependências continuam ausentes após tentativa de provisionamento.")
            return 1

    # Launch desktop GUI
    window = SyncFrameMainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
