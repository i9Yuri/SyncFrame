"""Main application window implementing the Precision Bench Media Alignment Workbench."""

import logging
import os
from typing import Optional, List, Literal

from PySide6.QtCore import Qt, QSize
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
    QSizePolicy,
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
from .style import apply_workbench_theme, get_theme_stylesheet
from .workers.analyze_worker import AnalyzeWorker
from .workers.remux_worker import RemuxWorker
from .workers.unified_pipeline_worker import UnifiedPipelineWorker
from ..core.disk_utils import check_disk_space, format_bytes
from ..core.inspector import inspect_media, evaluate_media_streams
from ..core.models import RemuxJob, SyncMetrics, AutoMatchVerdict, StreamCandidate, format_channel_layout_label, MediaSourceInfo

logger = logging.getLogger(__name__)


class SyncFrameMainWindow(QWidget):
    """
    Main application window implementing the Media Alignment Workbench (Precision Bench):
    - Topbar técnica compacta (~56px) com indicador LOCAL WORKSPACE e alternador de tema
    - Stepper de pipeline segmentado (01 Ingestão -> 02 Auditoria -> 03 Sincronização -> 04 Remux)
    - Grid assimétrico de 2 colunas em QScrollArea fluida:
      * Coluna Esquerda (Operacional & Decisório): Ingestão, Review Gate, Saída & Execução Remux
      * Coluna Direita (Auditoria & Instrumentação): Auditoria acústica, Correlação FFT, Alinhamento temporal, Miniplayer
    - Gaveta retrátil inferior de Event Logs
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("SyncFrame — Media Alignment Workbench")
        self.resize(1280, 840)
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

    def minimumSizeHint(self) -> QSize:
        return QSize(800, 540)

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

        # ======================================================================
        # 1. Fixed Technical Topbar
        # ======================================================================
        self.topbar = QWidget()
        self.topbar.setObjectName("workbenchTopbar")
        tb_layout = QHBoxLayout(self.topbar)
        tb_layout.setContentsMargins(20, 10, 20, 10)
        tb_layout.setSpacing(14)

        # Brand mark & Title in integrated transparent block
        brand_box = QHBoxLayout()
        brand_box.setSpacing(12)
        brand_box.setContentsMargins(0, 0, 0, 0)

        brand_texts = QVBoxLayout()
        brand_texts.setSpacing(1)
        brand_texts.setContentsMargins(0, 0, 0, 0)
        self.lbl_brand_title = QLabel("SyncFrame")
        self.lbl_brand_title.setObjectName("brandTitle")
        brand_texts.addWidget(self.lbl_brand_title)

        self.lbl_brand_sub = QLabel("MEDIA ALIGNMENT WORKBENCH")
        self.lbl_brand_sub.setObjectName("brandSubtitle")
        brand_texts.addWidget(self.lbl_brand_sub)
        brand_box.addLayout(brand_texts)

        # Subtle vertical separator
        crumb_sep = QFrame()
        crumb_sep.setObjectName("crumbSep")
        crumb_sep.setFrameShape(QFrame.VLine)
        crumb_sep.setProperty("class", "verticalDivider")
        brand_box.addWidget(crumb_sep)

        self.lbl_crumb = QLabel("Workspace / <strong>Session 01</strong>")
        self.lbl_crumb.setObjectName("topCrumb")
        brand_box.addWidget(self.lbl_crumb)
        tb_layout.addLayout(brand_box)

        tb_layout.addStretch()

        # Right actions: Local workspace chip, theme switcher
        self.chip_workspace = QLabel("● LOCAL WORKSPACE")
        self.chip_workspace.setProperty("class", "systemChip")
        tb_layout.addWidget(self.chip_workspace)

        self.btn_theme = QPushButton("Modo Claro")
        self.btn_theme.setProperty("class", "btnSecondary")
        self.btn_theme.setToolTip("Alternar entre Dark e Light Mode")
        self.btn_theme.clicked.connect(self.toggle_theme_mode)
        tb_layout.addWidget(self.btn_theme)

        badge_v = QLabel("v1.0.0")
        badge_v.setProperty("class", "badgeNeutral")
        tb_layout.addWidget(badge_v)

        root_layout.addWidget(self.topbar)

        # Passive progress / stepper references retained for backwards compatibility
        self.pipeline_ruler = QProgressBar()
        self.pipeline_ruler.setVisible(False)
        self.btn_step_01 = QPushButton("01 Ingestão")
        self.btn_step_02 = QPushButton("02 Auditoria")
        self.btn_step_03 = QPushButton("03 Sincronização")
        self.btn_step_04 = QPushButton("04 Remux")
        self.lbl_stepper_info = QLabel("Atalho de aprovação: ENTER")

        # ======================================================================
        # 2. Responsive Scroll Area for Central Workbench Layout
        # ======================================================================
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        body_container = QWidget()
        body_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        body_layout = QHBoxLayout(body_container)
        body_layout.setSpacing(14)
        body_layout.setContentsMargins(18, 6, 18, 14)

        # ----------------------------------------------------------------------
        # LEFT COLUMN (Stack 1: Operational & Decision Gate)
        # ----------------------------------------------------------------------
        col_left = QVBoxLayout()
        col_left.setSpacing(16)

        # Card 01 & 02: Unified Drop Zone & Review Gate
        self.drop_zone = UnifiedDropZone()
        self.drop_zone.files_ready.connect(self._on_files_ready)
        self.drop_zone.confirmation_confirmed.connect(self._on_confirmation_confirmed)
        self.drop_zone.target_audio_changed.connect(self._on_target_audio_changed)
        self.drop_zone.ref_audio_changed.connect(self._on_ref_audio_changed)
        self.drop_zone.reset_requested.connect(self._on_reset_requested)
        col_left.addWidget(self.drop_zone)

        # Card 04: Lossless Remux (Saída e Execução)
        self.card_remux_exec = QFrame()
        self.card_remux_exec.setObjectName("panelCardRemux")
        self.card_remux_exec.setProperty("class", "panelCard")
        cre_layout = QVBoxLayout(self.card_remux_exec)
        cre_layout.setContentsMargins(18, 16, 18, 16)
        cre_layout.setSpacing(12)

        cre_head = QHBoxLayout()
        cre_head.setSpacing(8)
        idx_c04 = QLabel("04")
        idx_c04.setProperty("class", "sectionIndex")
        cre_head.addWidget(idx_c04)
        cre_title = QLabel("Lossless Remux (Saída & Execução)")
        cre_title.setProperty("class", "cardTitle")
        cre_head.addWidget(cre_title)
        cre_head.addStretch()
        badge_passthrough = QLabel("ZERO RE-ENCODE")
        badge_passthrough.setProperty("class", "badgeGreen")
        cre_head.addWidget(badge_passthrough)
        cre_layout.addLayout(cre_head)

        # Destination Path selector
        path_box = QVBoxLayout()
        path_box.setSpacing(6)
        lbl_dest_desc = QLabel("ARQUIVO DE SAIDA (DESTINO)")
        lbl_dest_desc.setProperty("class", "eyebrowText")
        path_box.addWidget(lbl_dest_desc)

        path_row = QHBoxLayout()
        path_row.setSpacing(8)
        self.txt_output_path = QLineEdit()
        self.txt_output_path.setPlaceholderText("Defina o caminho de destino do arquivo MKV sincronizado...")
        path_row.addWidget(self.txt_output_path, 1)

        btn_browse_dest = QPushButton("Procurar...")
        btn_browse_dest.setProperty("class", "btnSecondary")
        btn_browse_dest.clicked.connect(self._browse_destination)
        path_row.addWidget(btn_browse_dest)
        path_box.addLayout(path_row)
        cre_layout.addLayout(path_box)

        # Progress bar & Cancel action
        prog_box = QVBoxLayout()
        prog_box.setSpacing(6)
        action_row = QHBoxLayout()
        action_row.setSpacing(10)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        action_row.addWidget(self.progress_bar, 1)

        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.setProperty("class", "btnDanger")
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.clicked.connect(self.cancel_active_operation)
        action_row.addWidget(self.btn_cancel)
        prog_box.addLayout(action_row)

        self.lbl_progress_status = QLabel("Pronto para operação.")
        self.lbl_progress_status.setProperty("class", "subText")
        prog_box.addWidget(self.lbl_progress_status)
        cre_layout.addLayout(prog_box)

        col_left.addWidget(self.card_remux_exec)
        body_layout.addLayout(col_left, 6)

        # ----------------------------------------------------------------------
        # RIGHT COLUMN (Stack 2: Acoustic Audit & Instrumentation)
        # ----------------------------------------------------------------------
        col_right = QVBoxLayout()
        col_right.setSpacing(16)

        # Card 03: Acoustic Audit (FFT & Drift Diagnosis)
        card_acoustic = QFrame()
        card_acoustic.setProperty("class", "panelCard")
        ca_layout = QVBoxLayout(card_acoustic)
        ca_layout.setContentsMargins(18, 16, 18, 16)
        ca_layout.setSpacing(12)

        ca_head = QHBoxLayout()
        ca_head.setSpacing(8)
        idx_c03 = QLabel("03")
        idx_c03.setProperty("class", "sectionIndex")
        ca_head.addWidget(idx_c03)
        ca_title = QLabel("Acoustic Audit & Correlação FFT")
        ca_title.setProperty("class", "cardTitle")
        ca_head.addWidget(ca_title)
        ca_head.addStretch()
        chip_fft = QLabel("FFT READY")
        chip_fft.setProperty("class", "badgeSignal")
        ca_head.addWidget(chip_fft)
        ca_layout.addLayout(ca_head)

        # Correlation view canvas (Hardware-accelerated QPainter)
        self.correlation_view = CorrelationView()
        ca_layout.addWidget(self.correlation_view)

        col_right.addWidget(card_acoustic)

        # Card 03A: Temporal Alignment (Micro-ajuste & métricas)
        self.sync_controls = SyncControls()
        self.sync_controls.offset_changed.connect(self._on_manual_offset_changed)
        col_right.addWidget(self.sync_controls)

        # Card 03B: Lip-sync Spot Check (Preview Player)
        self.preview_player = PreviewPlayer()
        col_right.addWidget(self.preview_player)

        # Retractable wrapper for secondary inspection if needed
        self.advanced_drawer = CollapsibleSection("Gaveta de Instrumentação Avançada", self)
        self.advanced_drawer.setVisible(False)  # Hidden since widgets are now organized in 2-column workbench
        col_right.addWidget(self.advanced_drawer)

        body_layout.addLayout(col_right, 5)

        self.scroll_area.setWidget(body_container)
        root_layout.addWidget(self.scroll_area, 1)

        # ======================================================================
        # 4. Fixed Base Event Log Drawer
        # ======================================================================
        self.log_drawer = LogDrawer()
        root_layout.addWidget(self.log_drawer)

        # Set default dark theme on app and window
        app = QApplication.instance()
        if app:
            apply_workbench_theme(app, "dark")
        apply_workbench_theme(self, "dark")

    def _set_stepper_active(self, step_idx: int):
        btns = [self.btn_step_01, self.btn_step_02, self.btn_step_03, self.btn_step_04]
        for i, b in enumerate(btns):
            if i < step_idx:
                b.setProperty("done", "true")
                b.setProperty("active", "false")
            elif i == step_idx:
                b.setProperty("active", "true")
                b.setProperty("done", "false")
            else:
                b.setProperty("active", "false")
                b.setProperty("done", "false")
            b.setStyle(b.style())

    def apply_application_theme(self, theme_mode: Literal["dark", "light"]) -> None:
        """Applies the application theme atomically across the window and all child widgets."""
        self.current_theme = theme_mode
        if self.current_theme == "light":
            self.btn_theme.setText("Modo Escuro")
        else:
            self.btn_theme.setText("Modo Claro")

        theme_qss = get_theme_stylesheet(self.current_theme)
        app = QApplication.instance()
        if app:
            app.setStyleSheet(theme_qss)
        self.setStyleSheet(theme_qss)

        # Notify subcomponents
        if hasattr(self, "correlation_view") and hasattr(self.correlation_view, "set_theme_mode"):
            self.correlation_view.set_theme_mode(self.current_theme)

        # Recursively unpolish and polish all child widgets to refresh CSS properties
        for child in self.findChildren(QWidget):
            st = child.style()
            if st:
                st.unpolish(child)
                st.polish(child)

        st = self.style()
        if st:
            st.unpolish(self)
            st.polish(self)
        self.update()

    def toggle_theme_mode(self) -> None:
        """Toggles between strictly monochrome neutral dark and neutral light workbench theme."""
        new_mode: Literal["dark", "light"] = "light" if self.current_theme == "dark" else "dark"
        self.apply_application_theme(new_mode)

    def _toggle_theme(self):
        """Backwards-compatible alias for toggle_theme_mode."""
        self.toggle_theme_mode()

    def resizeEvent(self, event):
        """Ensures responsive adaptation and geometry recalculation on window resize."""
        super().resizeEvent(event)
        if hasattr(self, "scroll_area"):
            self.scroll_area.updateGeometry()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        valid = [u.toLocalFile() for u in urls if os.path.isfile(u.toLocalFile())]
        if valid:
            self.handle_files_ingested(valid)

    def handle_files_ingested(self, file_paths: List[str]) -> None:
        """Validates incoming files and delegates ingestion to the unified drop zone."""
        if not file_paths:
            return
        self.drop_zone.handle_files_ingested(file_paths)

    def update_sources_view(self, media_sources: List[MediaSourceInfo]) -> None:
        """Updates the media source cards and drop zone view with structured source information."""
        self.drop_zone.update_sources_view(media_sources)

    def _on_files_ready(self, file_a: str, file_b: str):
        self.log_drawer.append_log(f"Fontes recebidas: {os.path.basename(file_a)}, {os.path.basename(file_b)}")
        self._set_stepper_active(1)

        try:
            verdict = evaluate_media_streams(file_a, file_b)
        except Exception as exc:
            logger.error("Falha ao avaliar streams de mídia: %s", exc, exc_info=True)
            self.log_drawer.append_log(f"Erro na inspeção: {exc}")
            QMessageBox.warning(self, "Falha na Inspeção", f"Não foi possível inspecionar os arquivos selecionados:\n{exc}")
            self.drop_zone.reset()
            return

        file_v = verdict.recommended_video.file_path
        file_a_path = verdict.recommended_target_audio.file_path if verdict.recommended_target_audio else ""

        sz_v = format_bytes(os.path.getsize(file_v)) if os.path.isfile(file_v) else "0 B"
        sz_a = format_bytes(os.path.getsize(file_a_path)) if file_a_path and os.path.isfile(file_a_path) else "0 B"

        ext_v = os.path.splitext(file_v)[1].replace(".", "").upper()
        ext_a = os.path.splitext(file_a_path)[1].replace(".", "").upper() if file_a_path else ""

        v_summary = f"{sz_v}  •  {verdict.recommended_video.stream.fps:.3f} fps" if verdict.recommended_video.stream.fps > 0 else sz_v

        media_sources = [
            MediaSourceInfo(
                file_path=file_v,
                file_size_formatted=sz_v,
                extension=ext_v,
                role_label="REFERENCIA DE VIDEO",
                summary=v_summary,
                is_video_source=True
            )
        ]

        if file_a_path and verdict.recommended_target_audio:
            a_stream = verdict.recommended_target_audio.stream
            sr = a_stream.sample_rate or 48000
            layout_lbl = format_channel_layout_label(a_stream.channels, a_stream.channel_layout) if a_stream.channels else ""
            a_summary = f"{sz_a}  •  {layout_lbl} • {sr} Hz" if layout_lbl else f"{sz_a}  •  {sr} Hz"
            media_sources.append(
                MediaSourceInfo(
                    file_path=file_a_path,
                    file_size_formatted=sz_a,
                    extension=ext_a,
                    role_label="AUDIO DUBLADO",
                    summary=a_summary,
                    is_video_source=False
                )
            )

        self.update_sources_view(media_sources)
        self.drop_zone.set_verdict(verdict)

        default_out = os.path.join(
            os.path.dirname(verdict.recommended_video.file_path),
            f"{os.path.splitext(os.path.basename(verdict.recommended_video.file_path))[0]}.SYNCED.mkv"
        )
        self.txt_output_path.setText(default_out)
        self.log_drawer.append_log(
            f"Auto-matching concluído: Vídeo={os.path.basename(verdict.recommended_video.file_path)}, "
            f"Áudio={os.path.basename(verdict.recommended_target_audio.file_path)}"
        )

    def _on_confirmation_confirmed(
        self,
        chosen_video: StreamCandidate,
        chosen_target_audio: StreamCandidate,
        chosen_ref_audio: Optional[StreamCandidate],
        keep_original_audio: bool
    ):
        self._set_stepper_active(2)
        self.video_path = chosen_video.file_path
        self.audio_path = chosen_target_audio.file_path
        self.selected_video_track_id = chosen_video.stream.id
        self.selected_target_audio_id = chosen_target_audio.stream.id

        if chosen_ref_audio:
            self.selected_ref_audio_id = chosen_ref_audio.stream.id
        else:
            self.selected_ref_audio_id = 1

        self.total_duration_sec = (chosen_video.stream.duration_ms or 60000.0) / 1000.0
        self.preview_player.set_media_sources(
            self.video_path,
            self.audio_path,
            self.total_duration_sec,
            0.0
        )

        # Set default output path if not yet populated
        if not self.txt_output_path.text().strip():
            base_dir = os.path.dirname(self.video_path) or "."
            base_name = os.path.splitext(os.path.basename(self.video_path))[0]
            self.txt_output_path.setText(os.path.join(base_dir, f"{base_name}_synced.mkv"))

        self.auto_chain_remux = True
        self.start_analysis()

    def _on_target_audio_changed(self, track_id: int):
        self.selected_target_audio_id = track_id
        target_cand = self.drop_zone.combo_target_audio.currentData()
        if target_cand:
            self.audio_path = target_cand.file_path

    def _on_ref_audio_changed(self, track_id: int):
        self.selected_ref_audio_id = track_id

    def _on_reset_requested(self):
        self._set_stepper_active(0)
        self.video_path = None
        self.audio_path = None
        self.latest_metrics = None
        self.correlation_view.clear()
        self.sync_controls.reset()
        self.preview_player.set_media_sources(None, None, 0.0, 0.0)
        self.txt_output_path.clear()
        self.progress_bar.setValue(0)
        self.lbl_progress_status.setText("Pronto para operação.")
        self.btn_cancel.setEnabled(False)

    def _browse_destination(self):
        f, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar Vídeo Sincronizado",
            self.txt_output_path.text() or "output_synced.mkv",
            "Matroska Video (*.mkv)"
        )
        if f:
            self.txt_output_path.setText(f)

    def start_analysis(self):
        if not self.video_path or not self.audio_path:
            return

        out_path = self.txt_output_path.text().strip()
        if not out_path:
            QMessageBox.warning(self, "Aviso", "Por favor, defina o arquivo de saída.")
            return

        ok, msg = check_disk_space(os.path.dirname(out_path) or ".", 2 * 1024 * 1024 * 1024)
        if not ok:
            QMessageBox.critical(self, "Espaço Insuficiente", msg)
            return

        keep_orig = self.drop_zone.check_keep_original.isChecked()
        pal_pitch = getattr(self.drop_zone, "check_pal_pitch", None) and self.drop_zone.check_pal_pitch.isChecked()
        codec = self.drop_zone.combo_audio_codec.currentData() if hasattr(self.drop_zone, "combo_audio_codec") else "flac"
        discarded_ids = self.drop_zone.get_discarded_audio_ids() if hasattr(self.drop_zone, "get_discarded_audio_ids") else []

        job = RemuxJob(
            output_path=out_path,
            video_file=self.video_path,
            target_audio_file=self.audio_path,
            offset_ms=0.0,
            stretch_ratio=1.0,
            video_track_id=self.selected_video_track_id,
            target_audio_track_id=self.selected_target_audio_id,
            ref_audio_track_id=self.selected_ref_audio_id,
            keep_original_audio=keep_orig,
            pal_pitch_restore=bool(pal_pitch),
            audio_codec=str(codec),
            discarded_audio_ids=discarded_ids
        )

        self.job = job

        if hasattr(self, "drop_zone") and hasattr(self.drop_zone, "btn_confirm"):
            self.drop_zone.btn_confirm.setEnabled(False)
            self.drop_zone.btn_confirm.setText("Processando sincronização...")
        QApplication.setOverrideCursor(Qt.WaitCursor)

        self.btn_cancel.setEnabled(True)
        self.lbl_progress_status.setText("Iniciando esteira unificada de processamento...")
        self.progress_bar.setValue(5)
        self.log_drawer.append_log("Disparando UnifiedPipelineWorker...")
        self.correlation_view.set_status("Extraindo amostras acústicas e calculando FFT...")

        self.pipeline_worker = UnifiedPipelineWorker(
            job,
            manual_offset_override=self.manual_offset_override,
            parent=self
        )
        self.pipeline_worker.analysis_started.connect(self._on_analysis_started)
        self.pipeline_worker.step_progress.connect(self._on_step_progress)
        self.pipeline_worker.correlation_ready.connect(self._on_correlation_ready)
        self.pipeline_worker.correlation_completed.connect(self._on_correlation_completed)
        self.pipeline_worker.preview_ready.connect(self._on_preview_ready)
        self.pipeline_worker.finished_success.connect(self._on_finished_success)
        self.pipeline_worker.execution_failed.connect(self._on_execution_failed)

        self.pipeline_worker.progress.connect(self._on_worker_progress)
        self.pipeline_worker.log_message.connect(self.log_drawer.append_log)
        self.pipeline_worker.metrics_ready.connect(self._on_metrics_ready)
        self.pipeline_worker.completed.connect(self._on_pipeline_completed)
        self.pipeline_worker.start()

    def _restore_action_button(self):
        """Restores the primary action button and normal mouse cursor."""
        while QApplication.overrideCursor() is not None:
            QApplication.restoreOverrideCursor()
        if hasattr(self, "drop_zone") and hasattr(self.drop_zone, "btn_confirm"):
            self.drop_zone.btn_confirm.setEnabled(True)
            self.drop_zone.btn_confirm.setText("Sincronizar e Concluir")

    def _on_analysis_started(self):
        self.correlation_view.set_status("Extraindo amostras acústicas e calculando FFT...")
        self.lbl_progress_status.setText("Extraindo amostras acústicas e calculando FFT...")

    def _on_step_progress(self, msg: str, pct: float):
        self.progress_bar.setValue(int(pct))
        self.lbl_progress_status.setText(msg)

    def _on_correlation_ready(self, telemetry: dict):
        offset = telemetry.get("offset_ms", 0.0)
        self.log_drawer.append_log(f"Telemetria espectral pronta: offset={offset:+.1f} ms")

    def _on_correlation_completed(self, offset_ms: float, confidence: float, drift: float, curve: list):
        self.correlation_view.set_data(curve, offset_ms, confidence)
        self.preview_player.update_offset(offset_ms)
        self.preview_player.set_preview_ready(f"Offset acústico determinado: {offset_ms:+.1f} ms")

    def _on_preview_ready(self, preview_data: object):
        self.preview_player.set_markers_enabled(True)

    def _on_finished_success(self, output_path: str):
        self.log_drawer.append_log(f"Esteira unificada finalizada com sucesso: {output_path}")

    def _on_execution_failed(self, error_msg: str):
        self._restore_action_button()
        self.log_drawer.append_log(f"Falha na esteira: {error_msg}")

    def _on_manual_offset_changed(self, offset_ms: float):
        self.manual_offset_override = offset_ms
        self.preview_player.update_offset(offset_ms)

    def _on_worker_progress(self, pct: int, status_str: str):
        self.progress_bar.setValue(int(pct))
        self.lbl_progress_status.setText(status_str)

    def _on_metrics_ready(self, metrics: SyncMetrics):
        self.latest_metrics = metrics
        self.sync_controls.set_metrics(metrics)
        self.preview_player.update_offset(metrics.static_offset_ms)
        self.correlation_view.set_data(
            metrics.correlation_curve,
            metrics.static_offset_ms,
            metrics.confidence_score
        )

    def _on_pipeline_completed(self, success: bool, msg: str):
        self._restore_action_button()
        self.btn_cancel.setEnabled(False)
        self.progress_bar.setValue(100 if success else 0)
        self.lbl_progress_status.setText(msg)

        if success:
            self._set_stepper_active(3)
            self.log_drawer.append_log(f"Concluído com êxito: {self.txt_output_path.text()}")
            show_completion_modal(self, self.txt_output_path.text().strip())
        else:
            self.log_drawer.append_log(f"Falha na operação: {msg}")
            QMessageBox.critical(self, "Erro no Remux", msg)

    def cancel_active_operation(self):
        self._restore_action_button()
        if self.pipeline_worker and self.pipeline_worker.isRunning():
            self.lbl_progress_status.setText("Cancelando esteira...")
            self.pipeline_worker.cancel()
        if self.analyze_worker and self.analyze_worker.isRunning():
            self.analyze_worker.cancel()
        if self.remux_worker and self.remux_worker.isRunning():
            self.remux_worker.cancel()
        self.btn_cancel.setEnabled(False)
