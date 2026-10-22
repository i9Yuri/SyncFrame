"""SyncFrame entry point (GUI and CLI diagnostics)."""

import argparse
import logging
import sys

from src.ui.app import create_application
from src.ui.main_window import SyncFrameMainWindow
from src.utils.system_check import check_system_dependencies

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] (%(name)s) %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("syncframe")


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
        version="SyncFrame 0.1.0"
    )

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

    if not diag.is_operational:
        logger.warning("Ferramentas essenciais ausentes no host: %s", ", ".join(diag.missing_required))
        print(diag.install_instructions(), file=sys.stderr)

    # Launch desktop GUI
    app = create_application()
    window = SyncFrameMainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
