"""Main application window with responsive layout and unified ingestion."""

import logging
import os
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget
)

from .components.collapsible_section import CollapsibleSection
from .components.completion_dialog import show_completion_modal
from .components.correlation_view import CorrelationView
from .components.log_drawer import LogDrawer
from .components.preview_player import PreviewPlayer
from .components.sync_controls import SyncControls
from .components.stream_selector_modal import StreamSelectorModal
from .components.unified_drop_zone import UnifiedDropZone
from .style import apply_theme, get_theme_qss
from .workers.analyze_worker import AnalyzeWorker
from .workers.remux_worker import RemuxWorker
from .workers.unified_pipeline_worker import UnifiedPipelineWorker
from ..core.disk_utils import check_disk_space, format_bytes
from ..core.inspector import inspect_media, evaluate_media_streams
from ..core.models import RemuxJob, SyncMetrics, AutoMatchVerdict, StreamCandidate, format_channel_layout_label

logger = logging.getLogger(__name__)


class SyncFrameMainWindow(QWidget):
    """
    Main application window implementing neutral monochrome aesthetics,
    responsive scrollable layout, unified drop ingestion, and autonomous execution.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("SyncFrame — Lossless Audio/Video Synchronizer")
        self.resize(1180, 840)
        self.setMinimumSize(800, 540)

        self.current_theme: str = "dark"
        self.video_path: Optional[str] = None
        self.audio_path: Optional[str] = None
        self.total_duration_sec: float = 0.0
        self.selected_video_track_id: int = 0
        self.selected_ref_audio_id: int = 1
        self.selected_target_audio_id: int = 0

        self.latest_metrics: Optional[SyncMetrics] = None
        self.pipeline_worker: Optional[UnifiedPipelineWorker] = None
        self.analyze_worker: Optional[AnalyzeWorker] = None
        self.remux_worker: Optional[RemuxWorker] = None
        self.auto_chain_remux: bool = False
        self.manual_offset_override: Optional[float] = None

        self.setAcceptDrops(True)
        self.init_ui()

    @property
    def check_keep_original(self):
        """Forwarding property for backwards-compatibility with existing tests."""
        return self.drop_zone.check_keep_original

    @property
    def btn_remux(self):
        """Forwarding property pointing to the unified primary action button."""
        return self.drop_zone.btn_confirm

    def init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setSpacing(0)
        root_layout.setContentsMargins(0, 0, 0, 0)

        # 1. Fixed Clean Header Bar
        header_widget = QWidget()
        header_widget.setObjectName("headerBar")
        header = QHBoxLayout(header_widget)
        header.setContentsMargins(20, 14, 20, 14)

        header_text_box = QVBoxLayout()
        header_text_box.setSpacing(2)

        title = QLabel("SyncFrame")
        title.setStyleSheet("font-size: 20px; font-weight: 800; letter-spacing: -0.5px;")
        header_text_box.addWidget(title)

        subtitle = QLabel("Automação de Sincronia Acústica por FFT & Lossless Remux de Alta Fidelidade")
        subtitle.setProperty("class", "subText")
        header_text_box.addWidget(subtitle)
        header.addLayout(header_text_box)

        header.addStretch()

        self.btn_theme = QPushButton("Modo Claro")
        self.btn_theme.setProperty("class", "btnSecondary")
        self.btn_theme.setToolTip("Alternar entre modo Escuro e Claro Neutro")
        self.btn_theme.clicked.connect(self._toggle_theme)
        header.addWidget(self.btn_theme)

        badge_v = QLabel("v1.0.0")
        badge_v.setProperty("class", "badgeNeutral")
        header.addWidget(badge_v)

        root_layout.addWidget(header_widget)

        # 2. Scroll Area for Responsive Windowed Operation
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        body_container = QWidget()
        body_layout = QVBoxLayout(body_container)
        body_layout.setSpacing(14)
        body_layout.setContentsMargins(20, 8, 20, 20)

        # 3. Unified Drop Zone & Review Gate
        self.drop_zone = UnifiedDropZone()
        self.drop_zone.files_ready.connect(self._on_files_ready)
        self.drop_zone.confirmation_confirmed.connect(self._on_confirmation_confirmed)
        self.drop_zone.reset_requested.connect(self._on_reset_requested)
        body_layout.addWidget(self.drop_zone)

        # 4. Retractable Drawer: Advanced Controls & Lip-Sync Inspection (CollapsibleSection)
        self.advanced_drawer = CollapsibleSection("Ajustes Avançados e Inspeção Labial", self)

        # Drawer Content: Waveform + Controls + Miniplayer
        drawer_content_layout = QVBoxLayout()
        drawer_content_layout.setSpacing(10)

        mid_layout = QHBoxLayout()
        mid_layout.setSpacing(12)

        # Left: Correlation Canvas
        self.correlation_view = CorrelationView()
        mid_layout.addWidget(self.correlation_view, 1)

        # Right: Sync Controls & Fine-Tuning Steps
        self.sync_controls = SyncControls()
        self.sync_controls.offset_changed.connect(self._on_manual_offset_changed)
        mid_layout.addWidget(self.sync_controls, 1)

        drawer_content_layout.addLayout(mid_layout)

        # Miniplayer for spot-check preview
        self.preview_player = PreviewPlayer()
        drawer_content_layout.addWidget(self.preview_player)

        self.advanced_drawer.add_layout(drawer_content_layout)
        body_layout.addWidget(self.advanced_drawer)

        # 5. Destination & Execution Status Card
        dest_card = QFrame()
        dest_card.setObjectName("bentoCard")
        dest_card.setProperty("class", "bentoCard")
        dest_layout = QVBoxLayout(dest_card)
        dest_layout.setSpacing(10)
        dest_layout.setContentsMargins(16, 14, 16, 14)

        dest_header = QHBoxLayout()
        dest_title = QLabel("Destino & Conclusão do Processamento")
        dest_title.setProperty("class", "cardTitle")
        dest_header.addWidget(dest_title)
        dest_header.addStretch()
        dest_layout.addLayout(dest_header)

        # Output Path selector
        path_row = QHBoxLayout()
        path_lbl = QLabel("Arquivo de Saída:")
        path_lbl.setStyleSheet("color: #b0b0b0; font-weight: 600;")
        path_row.addWidget(path_lbl)

        self.txt_output_path = QLineEdit()
        self.txt_output_path.setPlaceholderText("Defina o caminho de destino do arquivo MKV sincronizado...")
        path_row.addWidget(self.txt_output_path, 1)

        btn_browse_dest = QPushButton("Procurar...")
        btn_browse_dest.setProperty("class", "btnSecondary")
        btn_browse_dest.clicked.connect(self._browse_destination)
        path_row.addWidget(btn_browse_dest)

        dest_layout.addLayout(path_row)

        # Progress Bar and Contextual Cancel Button
        action_row = QHBoxLayout()
        action_row.setSpacing(12)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        action_row.addWidget(self.progress_bar, 1)

        self.btn_cancel = QPushButton("Cancelar Operação")
        self.btn_cancel.setProperty("class", "btnDanger")
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.clicked.connect(self.cancel_active_operation)
        action_row.addWidget(self.btn_cancel)

        dest_layout.addLayout(action_row)

        self.lbl_progress_status = QLabel("Pronto para operação.")
        self.lbl_progress_status.setProperty("class", "subText")
        dest_layout.addWidget(self.lbl_progress_status)

        body_layout.addWidget(dest_card)

        # 6. Retractable Terminal Logs Drawer
        self.log_drawer = LogDrawer()
        body_layout.addWidget(self.log_drawer)

        self.scroll_area.setWidget(body_container)
        root_layout.addWidget(self.scroll_area)

    def _toggle_theme(self):
        """Toggles between neutral dark and neutral light theme."""
        if self.current_theme == "dark":
            self.current_theme = "light"
            self.btn_theme.setText("Modo Escuro")
        else:
            self.current_theme = "dark"
            self.btn_theme.setText("Modo Claro")

        app = QApplication.instance()
        target = app if app else self
        apply_theme(target, self.current_theme)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        valid = [u.toLocalFile() for u in urls if os.path.isfile(u.toLocalFile())]
        if valid:
            self.drop_zone.ingest_files(valid)

    def _on_files_ready(self, file_a: str, file_b: str):
        """Triggers heuristic evaluation when two files are loaded in UnifiedDropZone."""
        self.log_drawer.append_log(
            f"[AUTO-MATCH] Inspecionando fontes e avaliando heurística determinística:\n"
            f"  Fonte A: {os.path.basename(file_a)}\n  Fonte B: {os.path.basename(file_b)}"
        )
        try:
            verdict = evaluate_media_streams(file_a, file_b)
            self.drop_zone.set_verdict(verdict)
            tgt_name = os.path.basename(verdict.recommended_target_audio.file_path) if verdict.recommended_target_audio else "N/A"
            self.log_drawer.append_log(
                f"[AUTO-MATCH] Heurística concluída:\n"
                f"  Vídeo recomendado: '{os.path.basename(verdict.recommended_video.file_path)}'\n"
                f"  Dublagem alvo: '{tgt_name}'"
            )
        except Exception as exc:
            logger.error("Auto match evaluation failed: %s", exc)
            QMessageBox.critical(
                self,
                "Falha na Avaliação Heurística",
                f"Ocorreu um erro ao inspecionar as fontes:\n\n{exc}"
            )
            self.drop_zone.reset()

    def _on_confirmation_confirmed(
        self,
        chosen_video: StreamCandidate,
        chosen_target: StreamCandidate,
        chosen_ref: Optional[StreamCandidate],
        keep_orig: bool
    ):
        """Handles 1-click confirmation from UnifiedDropZone's Review Gate."""
        if not chosen_video or not chosen_target:
            QMessageBox.warning(self, "Seleção Incompleta", "É necessário selecionar tanto o vídeo quanto o áudio dublado.")
            return

        self.video_path = chosen_video.file_path
        self.audio_path = chosen_target.file_path
        self.selected_video_track_id = chosen_video.stream.id
        self.selected_ref_audio_id = chosen_ref.stream.id if chosen_ref else 0
        self.selected_target_audio_id = chosen_target.stream.id
        self.total_duration_sec = (chosen_video.stream.duration_ms / 1000.0) if chosen_video.stream.duration_ms > 0 else 7200.0

        self.check_keep_original.setChecked(keep_orig)

        # Auto suggest output path
        base, _ = os.path.splitext(self.video_path)
        self.txt_output_path.setText(f"{base}_synced.mkv")

        self._update_preview_sources()

        fmt_v = chosen_video.stream.container_format.upper() if chosen_video.stream.container_format else "MKV"
        fmt_a = chosen_target.stream.container_format.upper() if chosen_target.stream.container_format else "MKV"
        layout_name = format_channel_layout_label(chosen_target.stream.channels, chosen_target.stream.channel_layout)

        self.log_drawer.append_log(
            f"[CONFIRMADO] Vídeo #{self.selected_video_track_id} ({os.path.basename(self.video_path)} [{fmt_v}]) | "
            f"Dublagem #{self.selected_target_audio_id} ({os.path.basename(self.audio_path)} [{fmt_a}]: {layout_name}, {chosen_target.stream.codec.upper()}) | "
            f"Ref #{self.selected_ref_audio_id}"
        )

        # Deflagra sequencialmente e sem novas intervenções a extração, FFT e remux
        self.auto_chain_remux = True
        self.start_analysis()

    def _on_reset_requested(self):
        """Resets all media and analysis state when files are cleared."""
        self.video_path = None
        self.audio_path = None
        self.selected_video_track_id = 0
        self.selected_ref_audio_id = 1
        self.selected_target_audio_id = 0
        self.total_duration_sec = 0.0
        self.latest_metrics = None
        self.manual_offset_override = None
        self.txt_output_path.clear()
        self.correlation_view.clear()
        self.sync_controls.reset()
        self.preview_player.reset()
        self.lbl_progress_status.setText("Pronto para operação.")
        self.progress_bar.setValue(0)
        self.log_drawer.append_log("[RESET] Fontes e parâmetros resetados.")

    def _on_manual_offset_changed(self, offset_ms: float):
        self.manual_offset_override = offset_ms
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
        """Starts the unified execution pipeline (backwards-compatible with tests)."""
        self.start_unified_pipeline()

    def start_remux(self):
        """Starts the unified execution pipeline (backwards-compatible with tests)."""
        self.start_unified_pipeline()

    def start_unified_pipeline(self):
        """Orchestrates single-action extraction, FFT cross-correlation, and lossless remuxing."""
        if not self.video_path or not self.audio_path:
            QMessageBox.warning(self, "Fontes Incompletas", "Carregue os arquivos de vídeo e áudio dublado antes de sincronizar.")
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
        self.btn_cancel.setEnabled(True)
        self.progress_bar.setValue(0)
        self.lbl_progress_status.setText("Iniciando esteira unificada de sincronização e remux...")
        self.log_drawer.append_log("[PIPELINE] Esteira unificada deflagrada: extração, correlação acústica e lossless remux...")

        self.pipeline_worker = UnifiedPipelineWorker(job, manual_offset_override=self.manual_offset_override)
        self.pipeline_worker.progress.connect(self._on_worker_progress)
        self.pipeline_worker.metrics_ready.connect(self._on_metrics_ready)
        self.pipeline_worker.completed.connect(self._on_pipeline_completed)
        self.pipeline_worker.error.connect(self._on_worker_error)
        self.pipeline_worker.start()

    def _on_metrics_ready(self, metrics: SyncMetrics):
        self.latest_metrics = metrics
        self.sync_controls.set_metrics(metrics)
        self.correlation_view.set_data(
            metrics.correlation_curve,
            metrics.static_offset_ms,
            metrics.confidence_score
        )
        self.preview_player.update_offset(metrics.static_offset_ms)
        self.log_drawer.append_log(
            f"[ACÚSTICA] FFT concluída: Offset {metrics.static_offset_ms:+.1f} ms | "
            f"Drift: {metrics.drift_ratio:.6f}x | Confiança: {metrics.confidence_score*100:.1f}%"
        )

    def _on_worker_progress(self, pct: float, log_line: str):
        if pct >= 0:
            self.progress_bar.setValue(int(pct))
        self.lbl_progress_status.setText(log_line)
        self.log_drawer.append_log(log_line)

    def _on_pipeline_completed(self, success: bool, msg: str):
        self.btn_remux.setEnabled(True)
        self.btn_cancel.setEnabled(False)

        if success:
            self.progress_bar.setValue(100)
            self.lbl_progress_status.setText("Sincronização e remux finalizados com sucesso!")
            self.log_drawer.append_log(f"[SUCESSO] {msg}")
            out_file = self.txt_output_path.text().strip()
            show_completion_modal(self, out_file)
        else:
            self.lbl_progress_status.setText(msg)
            self.log_drawer.append_log(f"[INTERROMPIDO] {msg}")

    def _on_worker_error(self, err_msg: str):
        self.btn_remux.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self.lbl_progress_status.setText(f"Erro: {err_msg}")
        self.log_drawer.append_log(f"[ERRO CRÍTICO] {err_msg}")
        QMessageBox.critical(self, "Falha na Operação", f"Ocorreu um erro no pipeline:\n\n{err_msg}")

    def cancel_active_operation(self):
        if self.pipeline_worker and self.pipeline_worker.isRunning():
            self.pipeline_worker.cancel()
            self.lbl_progress_status.setText("Cancelando operação e finalizando subprocessos...")
        if self.analyze_worker and self.analyze_worker.isRunning():
            self.analyze_worker.cancel()
            self.lbl_progress_status.setText("Cancelando análise...")
        if self.remux_worker and self.remux_worker.isRunning():
            self.remux_worker.cancel()
            self.lbl_progress_status.setText("Cancelando remux e finalizando subprocessos...")
        self.btn_cancel.setEnabled(False)
