"""Main application window with asymmetric Bento Grid layout."""

import logging
import os
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget
)

from .components.correlation_view import CorrelationView
from .components.file_drop_card import FileDropCard
from .components.log_drawer import LogDrawer
from .components.preview_player import PreviewPlayer
from .components.sync_controls import SyncControls
from .components.stream_selector_modal import StreamSelectorModal
from .workers.analyze_worker import AnalyzeWorker
from .workers.remux_worker import RemuxWorker
from ..core.disk_utils import check_disk_space, format_bytes
from ..core.inspector import inspect_media, evaluate_media_streams
from ..core.models import RemuxJob, SyncMetrics, AutoMatchVerdict, StreamCandidate

logger = logging.getLogger(__name__)


class SyncFrameMainWindow(QWidget):
    """
    Main application window implementing Pro Max v4 Bento Grid aesthetics
    and asynchronous correlation & remux pipelines.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("SyncFrame — Lossless Audio/Video Synchronizer")
        self.resize(1180, 880)
        self.setMinimumSize(960, 720)

        self.video_path: Optional[str] = None
        self.audio_path: Optional[str] = None
        self.total_duration_sec: float = 0.0
        self.selected_video_track_id: int = 0
        self.selected_ref_audio_id: int = 1
        self.selected_target_audio_id: int = 0

        self.latest_metrics: Optional[SyncMetrics] = None
        self.analyze_worker: Optional[AnalyzeWorker] = None
        self.remux_worker: Optional[RemuxWorker] = None
        self.auto_chain_remux: bool = False

        self.setAcceptDrops(True)
        self.init_ui()

    def init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setSpacing(14)
        root_layout.setContentsMargins(20, 18, 20, 18)

        # 1. Header Banner
        header = QHBoxLayout()
        header_text_box = QVBoxLayout()
        header_text_box.setSpacing(2)

        title = QLabel("SyncFrame")
        title.setStyleSheet("font-size: 22px; font-weight: 800; color: #f8fafc; letter-spacing: -0.5px;")
        header_text_box.addWidget(title)

        subtitle = QLabel("Automação de Sincronia Acústica por FFT & Lossless Remux de Alta Fidelidade")
        subtitle.setProperty("class", "subText")
        header_text_box.addWidget(subtitle)
        header.addLayout(header_text_box)

        header.addStretch()

        self.btn_auto_match = QPushButton("⚡ Auto-Mapear")
        self.btn_auto_match.setProperty("class", "btnPrimary")
        self.btn_auto_match.setToolTip("Executa análise heurística comparativa das duas fontes carregadas")
        self.btn_auto_match.clicked.connect(self._on_click_auto_match)
        header.addWidget(self.btn_auto_match)

        badge_v = QLabel("v0.1.0 • Anti-Slop Engine")
        badge_v.setProperty("class", "badgeBlue")
        header.addWidget(badge_v)

        root_layout.addLayout(header)

        # 2. Bento Grid: Source Files (Top Row)
        sources_layout = QHBoxLayout()
        sources_layout.setSpacing(14)

        self.card_video = FileDropCard(
            title="Fonte de Vídeo (Alta Fidelidade)",
            subtitle="MKV ou MP4 de referência visual com áudio original"
        )
        self.card_video.file_selected.connect(self._on_video_selected)
        self.card_video.stream_changed.connect(self._on_ref_audio_track_changed)
        self.card_video.multiple_files_dropped.connect(self._on_multiple_files_dropped)
        sources_layout.addWidget(self.card_video, 1)

        self.card_audio = FileDropCard(
            title="Fonte de Áudio Dublado (Alvo)",
            subtitle="MKV ou arquivo de áudio com dublagem em Português"
        )
        self.card_audio.file_selected.connect(self._on_audio_selected)
        self.card_audio.stream_changed.connect(self._on_target_audio_track_changed)
        self.card_audio.multiple_files_dropped.connect(self._on_multiple_files_dropped)
        sources_layout.addWidget(self.card_audio, 1)

        root_layout.addLayout(sources_layout)

        # 3. Bento Grid: Metrics & Correlation Visualization (Middle Row)
        mid_layout = QHBoxLayout()
        mid_layout.setSpacing(14)

        # Left: Correlation Canvas
        self.correlation_view = CorrelationView()
        mid_layout.addWidget(self.correlation_view, 1)

        # Right: Sync Controls & Metrics
        self.sync_controls = SyncControls()
        self.sync_controls.analyze_requested.connect(self.start_analysis)
        self.sync_controls.offset_changed.connect(self._on_manual_offset_changed)
        mid_layout.addWidget(self.sync_controls, 1)

        root_layout.addLayout(mid_layout)

        # 4. Preview Player Panel
        self.preview_player = PreviewPlayer()
        root_layout.addWidget(self.preview_player)

        # 5. Destination & Output Remux Card (Bottom Row)
        dest_card = QFrame()
        dest_card.setObjectName("bentoCard")
        dest_card.setProperty("class", "bentoCard")
        dest_layout = QVBoxLayout(dest_card)
        dest_layout.setSpacing(10)
        dest_layout.setContentsMargins(16, 14, 16, 14)

        dest_header = QHBoxLayout()
        dest_title = QLabel("Destino & Multiplexação Lossless (mkvmerge)")
        dest_title.setProperty("class", "cardTitle")
        dest_header.addWidget(dest_title)
        dest_header.addStretch()

        self.check_keep_original = QCheckBox("Preservar áudio original (Inglês) como faixa secundária")
        self.check_keep_original.setChecked(True)
        dest_header.addWidget(self.check_keep_original)

        dest_layout.addLayout(dest_header)

        # Output Path selector
        path_row = QHBoxLayout()
        path_lbl = QLabel("Arquivo de Saída:")
        path_lbl.setStyleSheet("color: #cbd5e1; font-weight: 600;")
        path_row.addWidget(path_lbl)

        self.txt_output_path = QLineEdit()
        self.txt_output_path.setPlaceholderText("Defina o caminho de destino do arquivo MKV sincronizado...")
        path_row.addWidget(self.txt_output_path, 1)

        btn_browse_dest = QPushButton("Procurar...")
        btn_browse_dest.setProperty("class", "btnSecondary")
        btn_browse_dest.clicked.connect(self._browse_destination)
        path_row.addWidget(btn_browse_dest)

        dest_layout.addLayout(path_row)

        # Action Buttons & Linear Progress
        action_row = QHBoxLayout()
        action_row.setSpacing(12)

        self.btn_remux = QPushButton("Executar Lossless Remux")
        self.btn_remux.setProperty("class", "btnSuccess")
        self.btn_remux.clicked.connect(self.start_remux)
        action_row.addWidget(self.btn_remux)

        self.btn_cancel = QPushButton("Cancelar Operação")
        self.btn_cancel.setProperty("class", "btnDanger")
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.clicked.connect(self.cancel_active_operation)
        action_row.addWidget(self.btn_cancel)

        action_row.addSpacing(10)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        action_row.addWidget(self.progress_bar, 1)

        dest_layout.addLayout(action_row)

        self.lbl_progress_status = QLabel("Pronto para operação.")
        self.lbl_progress_status.setStyleSheet("color: #64748b; font-size: 11px;")
        dest_layout.addWidget(self.lbl_progress_status)

        root_layout.addWidget(dest_card)

        # 6. Retractable Terminal Logs Drawer
        self.log_drawer = LogDrawer()
        root_layout.addWidget(self.log_drawer)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        valid = [u.toLocalFile() for u in urls if os.path.isfile(u.toLocalFile())]
        if len(valid) >= 2:
            self._on_multiple_files_dropped(valid)
        elif len(valid) == 1:
            if not self.video_path:
                self.card_video.set_file_path(valid[0])
            else:
                self.card_audio.set_file_path(valid[0])

    def _on_multiple_files_dropped(self, files: list):
        if len(files) < 2:
            return
        self.process_dual_files(files[0], files[1])

    def _on_click_auto_match(self):
        if not self.video_path or not self.audio_path:
            QMessageBox.information(
                self,
                "Fontes Incompletas",
                "Carregue ou arraste dois arquivos de vídeo/áudio para executar o mapeamento heurístico automático."
            )
            return
        self.process_dual_files(self.video_path, self.audio_path)

    def process_dual_files(self, file_a: str, file_b: str):
        self.log_drawer.append_log(
            f"[AUTO-MATCH] Executando heurística comparativa determinística entre:\n  Fonte A: {os.path.basename(file_a)}\n  Fonte B: {os.path.basename(file_b)}"
        )
        try:
            verdict = evaluate_media_streams(file_a, file_b)
        except Exception as exc:
            logger.error("Auto match evaluation failed: %s", exc)
            QMessageBox.critical(
                self,
                "Falha na Avaliação Heurística",
                f"Ocorreu um erro ao inspecionar as fontes:\n\n{exc}"
            )
            return

        modal = StreamSelectorModal(verdict, self)
        if modal.exec() == QDialog.Accepted:
            chosen_video, chosen_target, chosen_ref, keep_orig = modal.get_selection()
            if not chosen_video or not chosen_target:
                QMessageBox.warning(self, "Seleção Incompleta", "É necessário selecionar tanto o vídeo quanto o áudio dublado.")
                return

            self.video_path = chosen_video.file_path
            self.audio_path = chosen_target.file_path
            self.selected_video_track_id = chosen_video.stream.id
            self.selected_ref_audio_id = chosen_ref.stream.id if chosen_ref else 0
            self.selected_target_audio_id = chosen_target.stream.id
            self.total_duration_sec = (chosen_video.stream.duration_ms / 1000.0) if chosen_video.stream.duration_ms > 0 else 7200.0

            # Update UI cards
            self.card_video.set_file_path(self.video_path)
            v_streams = inspect_media(self.video_path)
            self.card_video.update_streams(
                [s for s in v_streams if s.track_type == "audio"],
                default_stream_id=self.selected_ref_audio_id
            )

            self.card_audio.set_file_path(self.audio_path)
            a_streams = inspect_media(self.audio_path)
            self.card_audio.update_streams(
                [s for s in a_streams if s.track_type == "audio"],
                default_stream_id=self.selected_target_audio_id
            )

            self.check_keep_original.setChecked(keep_orig)

            # Auto suggest output path
            base, _ = os.path.splitext(self.video_path)
            self.txt_output_path.setText(f"{base}_synced.mkv")

            self._update_preview_sources()

            self.log_drawer.append_log(
                f"[CONFIRMADO] Vídeo #{self.selected_video_track_id} ({os.path.basename(self.video_path)}) | "
                f"Dublagem #{self.selected_target_audio_id} ({os.path.basename(self.audio_path)}) | "
                f"Ref #{self.selected_ref_audio_id}"
            )

            # Deflagra sequencialmente e sem novas intervenções a extração, FFT e remux
            self.auto_chain_remux = True
            self.start_analysis()

    def _on_video_selected(self, path: str):
        self.video_path = path
        try:
            streams = inspect_media(path)
            video_streams = [s for s in streams if s.track_type == "video"]
            audio_streams = [s for s in streams if s.track_type == "audio"]

            if video_streams:
                self.selected_video_track_id = video_streams[0].id
                self.total_duration_sec = video_streams[0].duration_ms / 1000.0

            # Default reference audio track
            default_ref_id = None
            if audio_streams:
                eng = [s for s in audio_streams if s.language.lower() in ("eng", "en")]
                default_ref_id = eng[0].id if eng else audio_streams[0].id
                self.selected_ref_audio_id = default_ref_id

            self.card_video.update_streams(audio_streams, default_ref_id)

            # Auto suggest output path
            if not self.txt_output_path.text():
                base, _ = os.path.splitext(path)
                suggested = f"{base}_synced.mkv"
                self.txt_output_path.setText(suggested)

            self._update_preview_sources()
            self.log_drawer.append_log(f"[INFO] Vídeo de referência carregado: {path} ({len(audio_streams)} faixas de áudio)")
        except Exception as exc:
            logger.error("Error inspecting video: %s", exc)
            QMessageBox.critical(self, "Erro de Leitura", f"Não foi possível inspecionar o vídeo:\n{exc}")

    def _on_audio_selected(self, path: str):
        self.audio_path = path
        try:
            streams = inspect_media(path)
            audio_streams = [s for s in streams if s.track_type == "audio"]

            # Prefer Portuguese track
            default_tgt_id = None
            if audio_streams:
                pt = [s for s in audio_streams if s.language.lower() in ("por", "pt", "pob", "pt-br", "bra")]
                default_tgt_id = pt[0].id if pt else audio_streams[0].id
                self.selected_target_audio_id = default_tgt_id

            self.card_audio.update_streams(audio_streams, default_tgt_id)
            self._update_preview_sources()
            self.log_drawer.append_log(f"[INFO] Fonte de áudio dublado carregada: {path} ({len(audio_streams)} faixas de áudio)")
        except Exception as exc:
            logger.error("Error inspecting audio: %s", exc)
            QMessageBox.critical(self, "Erro de Leitura", f"Não foi possível inspecionar o áudio:\n{exc}")

    def _on_ref_audio_track_changed(self, track_id: int):
        self.selected_ref_audio_id = track_id
        self.log_drawer.append_log(f"[CONFIG] Faixa de áudio de referência alterada para #{track_id}")

    def _on_target_audio_track_changed(self, track_id: int):
        self.selected_target_audio_id = track_id
        self.log_drawer.append_log(f"[CONFIG] Faixa de áudio dublado alvo alterada para #{track_id}")

    def _on_manual_offset_changed(self, offset_ms: float):
        self.preview_player.update_offset(offset_ms)
        if self.latest_metrics:
            self.correlation_view.set_data(
                self.latest_metrics.correlation_curve,
                offset_ms,
                self.latest_metrics.confidence_score,
                f"Offset Ajustado: {offset_ms:+.1f} ms"
            )

    def _update_preview_sources(self):
        offset = self.sync_controls.get_offset_ms()
        self.preview_player.set_media_sources(
            video_path=self.video_path,
            audio_path=self.audio_path,
            duration_sec=self.total_duration_sec,
            offset_ms=offset
        )

    def _browse_destination(self):
        current = self.txt_output_path.text() or os.path.expanduser("~")
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Definir Arquivo de Saída MKV",
            current,
            "Matroska Video (*.mkv)"
        )
        if path:
            if not path.endswith(".mkv"):
                path += ".mkv"
            self.txt_output_path.setText(path)

    def start_analysis(self):
        if not self.video_path or not self.audio_path:
            QMessageBox.warning(self, "Fontes Incompletas", "Carregue o arquivo de vídeo e o arquivo de áudio dublado antes de calcular a sincronia.")
            return

        self.btn_remux.setEnabled(False)
        self.sync_controls.btn_analyze.setEnabled(False)
        self.btn_cancel.setEnabled(True)
        self.progress_bar.setValue(0)

        self.analyze_worker = AnalyzeWorker(
            video_path=self.video_path,
            video_audio_track_id=self.selected_ref_audio_id,
            audio_path=self.audio_path,
            target_audio_track_id=self.selected_target_audio_id,
            duration_sec=self.total_duration_sec
        )
        self.analyze_worker.progress.connect(self._on_worker_progress)
        self.analyze_worker.finished.connect(self._on_analysis_finished)
        self.analyze_worker.error.connect(self._on_worker_error)
        self.analyze_worker.start()

    def _on_analysis_finished(self, metrics: SyncMetrics):
        self.latest_metrics = metrics
        self.sync_controls.set_metrics(metrics)
        self.correlation_view.set_data(
            metrics.correlation_curve,
            metrics.static_offset_ms,
            metrics.confidence_score
        )
        self.preview_player.update_offset(metrics.static_offset_ms)

        self.btn_remux.setEnabled(True)
        self.sync_controls.btn_analyze.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self.progress_bar.setValue(100)
        self.lbl_progress_status.setText("Cálculo espectral concluído com sucesso!")
        self.log_drawer.append_log(
            f"[SUCESSO] Offset: {metrics.static_offset_ms:+.1f} ms | Drift: {metrics.drift_ratio:.6f}x | Confiança: {metrics.confidence_score*100:.1f}%"
        )

        if getattr(self, "auto_chain_remux", False):
            self.auto_chain_remux = False
            self.log_drawer.append_log("[AUTO-CHAIN] Review Gate confirmado: Iniciando multiplexação lossless autônoma...")
            self.start_remux()

    def start_remux(self):
        if not self.video_path or not self.audio_path:
            QMessageBox.warning(self, "Fontes Incompletas", "Selecione o vídeo e o áudio antes de iniciar o remux.")
            return

        output_path = self.txt_output_path.text().strip()
        if not output_path:
            QMessageBox.warning(self, "Destino Ausente", "Defina o caminho do arquivo MKV de saída.")
            return

        # Pre-flight disk space check
        has_space, free_b, req_b = check_disk_space(output_path, self.video_path, self.audio_path)
        if not has_space:
            QMessageBox.critical(
                self,
                "Espaço em Disco Insuficiente",
                f"Espaço livre insuficiente na partição de destino!\n\n"
                f"Disponível: {format_bytes(free_b)}\n"
                f"Estimado necessário: {format_bytes(req_b)}\n\n"
                f"Libere espaço ou selecione outra partição."
            )
            return

        offset_ms = self.sync_controls.get_offset_ms()
        stretch_ratio = self.latest_metrics.time_stretch_ratio if self.latest_metrics else 1.0

        job = RemuxJob(
            output_path=output_path,
            video_file=self.video_path,
            target_audio_file=self.audio_path,
            offset_ms=offset_ms,
            stretch_ratio=stretch_ratio,
            keep_original_audio=self.check_keep_original.isChecked(),
            target_track_id=self.selected_target_audio_id,
            ref_audio_track_id=self.selected_ref_audio_id,
            video_track_id=self.selected_video_track_id
        )

        self.btn_remux.setEnabled(False)
        self.sync_controls.btn_analyze.setEnabled(False)
        self.btn_cancel.setEnabled(True)
        self.progress_bar.setValue(0)

        self.remux_worker = RemuxWorker(job)
        self.remux_worker.progress.connect(self._on_worker_progress)
        self.remux_worker.completed.connect(self._on_remux_completed)
        self.remux_worker.error.connect(self._on_worker_error)
        self.remux_worker.start()

    def _on_worker_progress(self, pct: float, log_line: str):
        if pct >= 0:
            self.progress_bar.setValue(int(pct))
        self.lbl_progress_status.setText(log_line)
        self.log_drawer.append_log(log_line)

    def _on_remux_completed(self, success: bool, msg: str):
        self.btn_remux.setEnabled(True)
        self.sync_controls.btn_analyze.setEnabled(True)
        self.btn_cancel.setEnabled(False)

        if success:
            self.progress_bar.setValue(100)
            self.lbl_progress_status.setText("Multiplexação finalizada com sucesso!")
            QMessageBox.information(self, "Sucesso", msg)
        else:
            self.lbl_progress_status.setText(msg)

    def _on_worker_error(self, err_msg: str):
        self.btn_remux.setEnabled(True)
        self.sync_controls.btn_analyze.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self.lbl_progress_status.setText(f"Erro: {err_msg}")
        self.log_drawer.append_log(f"[ERRO CRÍTICO] {err_msg}")
        QMessageBox.critical(self, "Falha na Operação", f"Ocorreu um erro no pipeline:\n\n{err_msg}")

    def cancel_active_operation(self):
        if self.analyze_worker and self.analyze_worker.isRunning():
            self.analyze_worker.cancel()
            self.lbl_progress_status.setText("Cancelando análise...")
        if self.remux_worker and self.remux_worker.isRunning():
            self.remux_worker.cancel()
            self.lbl_progress_status.setText("Cancelando remux e finalizando subprocessos...")
        self.btn_cancel.setEnabled(False)
