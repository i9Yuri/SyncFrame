"""Main application window implementing the Precision Bench Media Alignment Workbench."""

import logging
import os
from typing import Optional, List, Literal

from PySide6.QtCore import Qt, QSize, QTimer, QThread
from PySide6.QtGui import QColor, QFontMetrics, QPainter, QPen
from PySide6.QtWidgets import (
    QApplication,
    QBoxLayout,
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
from .components.log_drawer import FloatingDockWidget, LogDrawer
from .components.preview_player import PreviewPlayer
from .components.sync_controls import SyncControls
from .components.stream_selector_modal import StreamSelectorModal
from .components.unified_drop_zone import UnifiedDropZone
from .style import apply_workbench_theme, get_theme_stylesheet, apply_one_ui_monochrome_theme, get_theme_tokens, get_theme_icon
from .workspace_layout import WorkspaceLayoutManager
from .workers.analyze_worker import AnalyzeWorker
from .workers.dependency_update_worker import DependencyUpdateWorker
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
        self.active_pipeline_worker: Optional[UnifiedPipelineWorker] = None
        self.active_update_worker: Optional[DependencyUpdateWorker] = None
        self.pipeline_worker: Optional[UnifiedPipelineWorker] = None
        self.active_worker: Optional[UnifiedPipelineWorker] = None
        self.current_worker: Optional[UnifiedPipelineWorker] = None
        self.analyze_worker: Optional[AnalyzeWorker] = None
        self.remux_worker: Optional[RemuxWorker] = None
        self.ref_audio_file: Optional[str] = None
        self.auto_chain_remux: bool = False
        self.manual_offset_override: Optional[float] = None
        self._completion_modal_shown: bool = False

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

    @property
    def btn_run(self):
        """Forwarding property pointing to the unified primary action button."""
        return self.drop_zone.btn_confirm

    def init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setSpacing(0)
        root_layout.setContentsMargins(0, 0, 0, 0)

        # ======================================================================
        # 1. Spacious One UI Header
        # ======================================================================
        self.topbar = QWidget()
        self.topbar.setObjectName("topHeader")
        tb_layout = QHBoxLayout(self.topbar)
        tb_layout.setContentsMargins(28, 14, 28, 6)
        tb_layout.setSpacing(16)

        # Brand mark & Title in integrated transparent block
        brand_texts = QVBoxLayout()
        brand_texts.setSpacing(3)
        brand_texts.setContentsMargins(0, 0, 0, 0)
        self.lbl_brand_title = QLabel("SyncFrame")
        self.lbl_brand_title.setObjectName("appTitle")
        brand_texts.addWidget(self.lbl_brand_title)

        self.lbl_brand_sub = QLabel("Bancada de alinhamento de mídia · Sessão 01")
        self.lbl_brand_sub.setObjectName("appSubtitle")
        brand_texts.addWidget(self.lbl_brand_sub)
        tb_layout.addLayout(brand_texts)

        # Retain crumb label for compatibility
        self.lbl_crumb = QLabel("")
        self.lbl_crumb.setVisible(False)

        tb_layout.addStretch()
        self.setup_topbar_actions()
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
        self.body_layout = QHBoxLayout(body_container)
        self.body_layout.setSpacing(12)
        self.body_layout.setContentsMargins(18, 0, 18, 10)

        # ----------------------------------------------------------------------
        # LEFT COLUMN (Stack 1: Operational & Decision Gate)
        # ----------------------------------------------------------------------
        col_left = QVBoxLayout()
        col_left.setSpacing(12)

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
        cre_layout.setSpacing(10)

        cre_head = QHBoxLayout()
        cre_head.setSpacing(10)
        cre_title = QLabel("Saída do remux")
        cre_title.setProperty("class", "cardTitle")
        cre_head.addWidget(cre_title)
        cre_head.addStretch()
        badge_passthrough = QLabel("Zero re-encode")
        badge_passthrough.setObjectName("badgePassthrough")
        badge_passthrough.setProperty("class", "tagGreen")
        badge_passthrough.setFixedHeight(28)
        badge_passthrough.setAlignment(Qt.AlignCenter)
        cre_head.addWidget(badge_passthrough, alignment=Qt.AlignVCenter)
        cre_layout.addLayout(cre_head)

        # Destination Path selector (.out container)
        self.frame_out_path = QFrame()
        self.frame_out_path.setObjectName("frameOutPath")
        self.frame_out_path.setProperty("class", "outPill")
        self.frame_out_path.setFixedHeight(44)
        path_row = QHBoxLayout(self.frame_out_path)
        path_row.setContentsMargins(16, 4, 6, 4)
        path_row.setSpacing(8)

        self.txt_output_path = QLineEdit()
        self.txt_output_path.setObjectName("txtOutputPath")
        self.txt_output_path.setProperty("class", "outPath")
        self.txt_output_path.setPlaceholderText("Defina o caminho de destino do arquivo MKV sincronizado...")
        path_row.addWidget(self.txt_output_path, 1)

        btn_browse_dest = QPushButton("Procurar…")
        btn_browse_dest.setObjectName("btnBrowseDest")
        btn_browse_dest.setProperty("class", "btnSm")
        btn_browse_dest.setFixedHeight(34)
        btn_browse_dest.setCursor(Qt.PointingHandCursor)
        btn_browse_dest.clicked.connect(self._browse_destination)
        self.btn_browse_dest = btn_browse_dest
        path_row.addWidget(btn_browse_dest)
        cre_layout.addWidget(self.frame_out_path)

        # Progress bar (.prog container), percentage, & Cancel action
        prog_row = QHBoxLayout()
        prog_row.setSpacing(12)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(14)
        prog_row.addWidget(self.progress_bar, 1)

        self.lbl_progress_pct = QLabel("0%")
        self.lbl_progress_pct.setStyleSheet("font-weight: 700; font-size: 14px; min-width: 38px;")
        prog_row.addWidget(self.lbl_progress_pct)

        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.setObjectName("btnCancel")
        self.btn_cancel.setProperty("class", "btnSm")
        self.btn_cancel.setFixedHeight(34)
        self.btn_cancel.setCursor(Qt.PointingHandCursor)
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.clicked.connect(self.cancel_active_operation)
        prog_row.addWidget(self.btn_cancel)
        cre_layout.addLayout(prog_row)

        self.lbl_progress_status = QLabel("Pronto para operação.")
        self.lbl_progress_status.setProperty("class", "hint")
        cre_layout.addWidget(self.lbl_progress_status)
        cre_layout.addStretch()

        col_left.addWidget(self.card_remux_exec)
        self.body_layout.addLayout(col_left, 6)

        # ----------------------------------------------------------------------
        # RIGHT COLUMN (Stack 2: Acoustic Audit & Instrumentation)
        # ----------------------------------------------------------------------
        col_right = QVBoxLayout()
        col_right.setSpacing(12)

        # Card 03: Acoustic Audit (FFT & Drift Diagnosis)
        self.card_acoustic = QFrame()
        self.card_acoustic.setObjectName("cardAcoustic")
        self.card_acoustic.setProperty("class", "panelCard")
        ca_layout = QVBoxLayout(self.card_acoustic)
        ca_layout.setContentsMargins(18, 16, 18, 16)
        ca_layout.setSpacing(10)

        ca_head = QHBoxLayout()
        ca_head.setSpacing(10)
        ca_title = QLabel("Auditoria acústica e correlação FFT")
        ca_title.setProperty("class", "cardTitle")
        ca_head.addWidget(ca_title)
        ca_head.addStretch()
        chip_fft = QLabel("FFT pronta")
        chip_fft.setObjectName("chipFFT")
        chip_fft.setProperty("class", "statusPill")
        ca_head.addWidget(chip_fft)
        ca_layout.addLayout(ca_head)

        # Correlation view canvas (Hardware-accelerated QPainter)
        self.correlation_view = CorrelationView()
        ca_layout.addWidget(self.correlation_view)

        col_right.addWidget(self.card_acoustic)

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

        self.body_layout.addLayout(col_right, 5)

        self.scroll_area.setWidget(body_container)
        root_layout.addWidget(self.scroll_area, 1)

        # ======================================================================
        # 4. Floating Bottom Dock Container
        # ======================================================================
        self.dock_container = QWidget()
        self.dock_container.setObjectName("dockContainer")
        dock_bar = QHBoxLayout(self.dock_container)
        dock_bar.setContentsMargins(24, 0, 24, 14)
        dock_bar.setAlignment(Qt.AlignCenter)

        self.log_drawer = FloatingDockWidget()
        self.floating_dock = self.log_drawer
        dock_bar.addWidget(self.log_drawer)
        root_layout.addWidget(self.dock_container)

        # Register manageable cards in WorkspaceLayoutManager
        self.widgets_map = {
            "drop_zone": self.drop_zone,
            "card_remux_exec": self.card_remux_exec,
            "card_acoustic": self.card_acoustic,
            "sync_controls": self.sync_controls,
            "preview_player": self.preview_player,
        }
        self.layout_manager = WorkspaceLayoutManager(
            widgets_map=self.widgets_map
        )

        self._update_topbar_pill_sizes()

        # Set default dark theme on app and window
        app = QApplication.instance()
        if app:
            apply_one_ui_monochrome_theme(app, "dark")
        apply_one_ui_monochrome_theme(self, "dark")

        # Silent background audit of tools and versions
        QTimer.singleShot(1500, lambda: self.check_for_updates(silent=True))

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
        if hasattr(self, "btn_theme") and self.btn_theme:
            self.btn_theme.setText("")
            self.btn_theme.setIcon(get_theme_icon(self.current_theme))
            self.btn_theme.setIconSize(QSize(18, 18))
            if self.current_theme == "light":
                self.btn_theme.setToolTip("Modo Escuro")
            else:
                self.btn_theme.setToolTip("Modo Claro")
            self.btn_theme.setFixedSize(34, 34)

        theme_qss = get_theme_stylesheet(self.current_theme)
        app = QApplication.instance()
        if app:
            apply_one_ui_monochrome_theme(app, self.current_theme)
        self.setStyleSheet(theme_qss)

        # Notify subcomponents
        if hasattr(self, "correlation_view") and hasattr(self.correlation_view, "set_theme_mode"):
            self.correlation_view.set_theme_mode(self.current_theme)
        if hasattr(self, "preview_player") and hasattr(self.preview_player, "set_theme_mode"):
            self.preview_player.set_theme_mode(self.current_theme)

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

    def apply_theme(self, theme_name: Literal["dark", "light"]) -> None:
        """Public API method to apply the theme to the main window."""
        self.apply_application_theme(theme_name)

    def update_dropzone_state(self, has_files: bool) -> None:
        """Updates dropzone geometry and height dynamically based on file ingestion state."""
        self.drop_zone.update_dropzone_state(has_files)

    def set_manual_offset(self, offset_ms: float) -> None:
        """Forwards manual offset override to sync controls and preview player."""
        self.manual_offset_override = offset_ms
        self.sync_controls.set_manual_offset(offset_ms)
        self.preview_player.update_offset(offset_ms)

    def check_for_updates(self, silent: bool = False) -> None:
        """
        Dispatches background low-priority DependencyUpdateWorker auditing local and remote versions.
        """
        if not silent and hasattr(self, "btn_check_updates"):
            self.btn_check_updates.setText("Verificando...")
            self.btn_check_updates.setEnabled(False)
            self._update_topbar_pill_sizes()

        worker = DependencyUpdateWorker(self)
        worker.status_message.connect(self.log_drawer.append_log)
        worker.update_available.connect(self._on_update_available)
        worker.audit_finished.connect(lambda res: self._on_update_audit_finished(res, silent))
        self.active_update_worker = worker
        worker.start(QThread.LowPriority)

    def _on_update_available(self, tool_name: str, new_version: str) -> None:
        """Receives notice of available update and records telemetry."""
        msg = f"Atualização disponível: {tool_name} ({new_version})"
        self.log_drawer.append_log(msg)
        if hasattr(self, "btn_check_updates"):
            self.btn_check_updates.setToolTip(msg)

    def _on_update_audit_finished(self, audit_result: dict, silent: bool) -> None:
        """Handles audit completion without disturbing active user workflows."""
        has_any_update = (
            audit_result.get("syncframe", {}).get("has_update", False)
            or any(t.get("has_update") for t in audit_result.get("tools", {}).values())
        )
        if not silent and hasattr(self, "btn_check_updates"):
            if has_any_update:
                self.btn_check_updates.setText("Atualização disponível")
            else:
                self.btn_check_updates.setText("Todas as ferramentas atualizadas")
            self._update_topbar_pill_sizes()
            QTimer.singleShot(3500, self._reset_update_button_state)

    def _reset_update_button_state(self) -> None:
        """Restores default label and enabled state on update button."""
        if hasattr(self, "btn_check_updates"):
            self.btn_check_updates.setText("Verificar Atualizações")
            self.btn_check_updates.setEnabled(True)
            self._update_topbar_pill_sizes()

    def setup_topbar_actions(self) -> None:
        """
        Constructs and configures topbar pill actions deterministically:
        - Espaço de trabalho local (pill with green dot)
        - Modo Claro / Modo Escuro (theme switcher pill)
        - v1.2.0 (version pill)
        - Fully expunges inoperant Edit Mode and rogue '+' crosses
        - Standardizes compact height to 34px with 8px horizontal gap
        - Auto-fits pill widths via QFontMetrics + 28px symmetric padding
        """
        tb_layout = self.topbar.layout() if hasattr(self, "topbar") and self.topbar else None
        if tb_layout is None:
            return

        tb_layout.setSpacing(8)

        # 1. Local workspace pill
        if not hasattr(self, "pill_workspace") or self.pill_workspace is None:
            self.pill_workspace = QFrame()
            pw_layout = QHBoxLayout(self.pill_workspace)
            pw_layout.setContentsMargins(14, 0, 14, 0)
            pw_layout.setSpacing(8)
            dot_ws = QLabel()
            dot_ws.setProperty("class", "greenDot")
            pw_layout.addWidget(dot_ws)
            self.chip_workspace = QLabel("Espaço de trabalho")
            self.chip_workspace.setStyleSheet("font-weight: 600; font-size: 13px; border: none; background: transparent;")
            pw_layout.addWidget(self.chip_workspace)
            tb_layout.addWidget(self.pill_workspace)

        self.pill_workspace.setObjectName("pillWorkspace")
        self.pill_workspace.setProperty("class", "pill")
        self.pill_workspace.setFixedHeight(34)

        # 2. Backward-compatible edit mode button: strictly expunged from visible topbar
        if not hasattr(self, "btn_edit_mode") or self.btn_edit_mode is None:
            self.btn_edit_mode = QPushButton("Modo Edição")
            self.btn_edit_mode.setObjectName("btnEditMode")
            self.btn_edit_mode.setProperty("class", "pill")
            self.btn_edit_mode.clicked.connect(self.toggle_workspace_edit_mode)

        self.btn_edit_mode.setVisible(False)
        tb_layout.removeWidget(self.btn_edit_mode)

        # 3. Theme toggle button
        if not hasattr(self, "btn_theme") or self.btn_theme is None:
            self.btn_theme = QPushButton()
            self.btn_theme.setToolTip("Modo Claro" if self.current_theme == "dark" else "Modo Escuro")
            self.btn_theme.setIcon(get_theme_icon(self.current_theme))
            self.btn_theme.setIconSize(QSize(18, 18))
            self.btn_theme.clicked.connect(self.toggle_theme_mode)
            tb_layout.addWidget(self.btn_theme)

        self.btn_theme.setObjectName("btnTheme")
        self.btn_theme.setProperty("class", "pill")
        self.btn_theme.setFixedSize(34, 34)
        self.btn_theme.setIconSize(QSize(18, 18))
        self.btn_theme.setCursor(Qt.PointingHandCursor)

        # 4. Check updates button (silent/interactive updater)
        if not hasattr(self, "btn_check_updates") or self.btn_check_updates is None:
            self.btn_check_updates = QPushButton("Verificar Atualizações")
            self.btn_check_updates.setToolTip("Auditar versões locais e checar releases do sistema")
            self.btn_check_updates.clicked.connect(lambda: self.check_for_updates(silent=False))
            tb_layout.addWidget(self.btn_check_updates)

        self.btn_check_updates.setObjectName("btnCheckUpdates")
        self.btn_check_updates.setProperty("class", "pill")
        self.btn_check_updates.setFixedHeight(34)
        self.btn_check_updates.setCursor(Qt.PointingHandCursor)

        # 5. Version badge
        if not hasattr(self, "badge_v") or self.badge_v is None:
            self.badge_v = QLabel("v1.2.0")
            self.badge_v.setAlignment(Qt.AlignCenter)
            tb_layout.addWidget(self.badge_v)

        self.badge_v.setObjectName("badgeVersion")
        self.badge_v.setProperty("class", "pillSoft")
        self.badge_v.setFixedHeight(34)
        self.badge_v.setAlignment(Qt.AlignCenter)

        self._update_topbar_pill_sizes()

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
        if hasattr(self, "body_layout") and self.body_layout is not None:
            if event.size().width() < 960:
                self.body_layout.setDirection(QBoxLayout.TopToBottom)
            else:
                self.body_layout.setDirection(QBoxLayout.LeftToRight)
        if hasattr(self, "scroll_area"):
            self.scroll_area.updateGeometry()
        self._update_topbar_pill_sizes()

    def _update_topbar_pill_sizes(self) -> None:
        """Dynamically sizes topbar pill tags and buttons based on QFontMetrics with generous margins."""
        if hasattr(self, "pill_workspace") and hasattr(self, "chip_workspace") and self.pill_workspace:
            fm_ws = self.chip_workspace.fontMetrics()
            text_w = fm_ws.horizontalAdvance(self.chip_workspace.text())
            self.pill_workspace.setFixedWidth(max(text_w + 52, 160))
            self.pill_workspace.setFixedHeight(34)

        if hasattr(self, "btn_theme") and self.btn_theme:
            self.btn_theme.setFixedSize(34, 34)

        if hasattr(self, "btn_check_updates") and self.btn_check_updates and self.btn_check_updates.text():
            fm_up = self.btn_check_updates.fontMetrics()
            self.btn_check_updates.setFixedWidth(fm_up.horizontalAdvance(self.btn_check_updates.text()) + 34)
            self.btn_check_updates.setFixedHeight(34)

        if hasattr(self, "badge_v") and self.badge_v and self.badge_v.text():
            fm_v = self.badge_v.fontMetrics()
            self.badge_v.setFixedWidth(max(76, fm_v.horizontalAdvance(self.badge_v.text()) + 38))
            self.badge_v.setFixedHeight(34)

        if hasattr(self, "btn_edit_mode") and self.btn_edit_mode and self.btn_edit_mode.text():
            fm_edit = self.btn_edit_mode.fontMetrics()
            self.btn_edit_mode.setFixedWidth(fm_edit.horizontalAdvance(self.btn_edit_mode.text()) + 28)
            self.btn_edit_mode.setFixedHeight(34)

    def paintEvent(self, event):
        """Draws orthogonal modular grid (48px spacing) with symmetric crosses (+), strictly below topbar."""
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, False)
        cross_color = QColor("#1f2329") if getattr(self, "current_theme", "dark") == "dark" else QColor("#e2e5eb")
        pen = QPen(cross_color, 1)
        painter.setPen(pen)

        step = 48
        arm = 4
        w = self.width()
        h = self.height()

        topbar_h = self.topbar.geometry().bottom() if hasattr(self, "topbar") and self.topbar else 70
        start_y = ((max(topbar_h, 60) + step) // step) * step

        for x in range(step, w, step):
            for y in range(start_y, h, step):
                painter.drawLine(x - arm, y, x + arm, y)
                painter.drawLine(x, y - arm, x, y + arm)
        painter.end()

    def toggle_workspace_edit_mode(self) -> None:
        """Toggles workspace customization edit mode and persists layout on completion."""
        new_mode = not self.layout_manager.is_edit_mode
        self.layout_manager.toggle_edit_mode(new_mode)
        if new_mode:
            self.btn_edit_mode.setText("Concluir Layout")
            self.log_drawer.append_log("Modo de personalização de layout ativado. Ajuste os cartões.")
        else:
            self.btn_edit_mode.setText("Modo Edição")
            self.layout_manager.save_layout(self.widgets_map)
            self.log_drawer.append_log("Layout do espaço de trabalho salvo com sucesso.")
        self._update_topbar_pill_sizes()

    def execute_end_to_end_pipeline(self) -> None:
        """
        Public programmatic interface to execute the full end-to-end sync and remux pipeline.
        Contract: MainWindow.execute_end_to_end_pipeline() -> None
        """
        self.on_run_clicked()

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

        # Arm preview player immediately with nominal duration and sources
        if verdict.recommended_video:
            v_path = verdict.recommended_video.file_path
            a_path = verdict.recommended_target_audio.file_path if verdict.recommended_target_audio else None
            dur_sec = (verdict.recommended_video.stream.duration_ms or 60000.0) / 1000.0
            self.preview_player.set_media_sources(v_path, a_path, dur_sec, 0.0)
            self.preview_player.set_preview_ready("Fontes carregadas: marcadores habilitados para inspeção")

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
        self.ref_audio_file = chosen_ref_audio.file_path if chosen_ref_audio else self.video_path
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
            base, _ = os.path.splitext(self.video_path)
            self.txt_output_path.setText(f"{base}_synced.mkv")

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
        self.lbl_progress_pct.setText("0%")
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

    def on_run_clicked(self) -> None:
        """
        Validates pre-flight conditions with explicit logging, updates UI to processing state,
        and dispatches the unified asynchronous pipeline worker.
        """
        # Guard against concurrent dispatches
        if (self.active_worker and self.active_worker.isRunning()) or (self.pipeline_worker and self.pipeline_worker.isRunning()):
            return

        # Ensure video_path and audio_path are populated
        if not self.video_path or not self.audio_path:
            v_cand = self.drop_zone.combo_video.currentData() if hasattr(self.drop_zone, "combo_video") else None
            t_cand = self.drop_zone.combo_target_audio.currentData() if hasattr(self.drop_zone, "combo_target_audio") else None
            r_cand = self.drop_zone.combo_ref_audio.currentData() if hasattr(self.drop_zone, "combo_ref_audio") else None
            if not v_cand and getattr(self.drop_zone, "current_verdict", None):
                v_cand = self.drop_zone.current_verdict.recommended_video
            if not t_cand and getattr(self.drop_zone, "current_verdict", None):
                t_cand = self.drop_zone.current_verdict.recommended_target_audio
            if not r_cand and getattr(self.drop_zone, "current_verdict", None):
                r_cand = self.drop_zone.current_verdict.reference_audio

            if v_cand and t_cand:
                self.video_path = v_cand.file_path
                self.audio_path = t_cand.file_path
                self.selected_video_track_id = v_cand.stream.id
                self.selected_target_audio_id = t_cand.stream.id
                self.ref_audio_file = r_cand.file_path if r_cand else self.video_path
                self.selected_ref_audio_id = r_cand.stream.id if r_cand else 1
            else:
                msg = "Fontes de vídeo e áudio não selecionadas para sincronização."
                self.log_drawer.append_log(f"[AVISO] {msg}")
                QMessageBox.warning(self, "Aviso", msg)
                self._restore_action_button()
                return

        out_path = self.txt_output_path.text().strip()
        if not out_path:
            base, _ = os.path.splitext(self.video_path)
            out_path = f"{base}_synced.mkv"
            self.txt_output_path.setText(out_path)

        # Pre-flight disk space validation with correct signature: (out_path, video_path, audio_path)
        is_sufficient, free_bytes, required_bytes = check_disk_space(
            destination_path=out_path,
            video_source_path=self.video_path,
            audio_source_path=self.audio_path
        )
        if not is_sufficient:
            err_msg = (
                f"Espaço insuficiente no disco de destino. "
                f"Disponível: {format_bytes(free_bytes)} | Necessário estimado: {format_bytes(required_bytes)}"
            )
            self.log_drawer.append_log(f"[ERRO CRÍTICO] {err_msg}")
            QMessageBox.critical(self, "Espaço Insuficiente", err_msg)
            self._restore_action_button()
            return

        keep_orig = self.drop_zone.check_keep_original.isChecked() if hasattr(self.drop_zone, "check_keep_original") else True
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
            discarded_audio_ids=discarded_ids,
            ref_audio_file=getattr(self, "ref_audio_file", None) or self.video_path
        )

        self.job = job

        # Visual update: disable button, set label, set wait cursor
        if hasattr(self, "drop_zone") and hasattr(self.drop_zone, "btn_confirm"):
            self.drop_zone.btn_confirm.setEnabled(False)
            self.drop_zone.btn_confirm.setText("Processando...")
        QApplication.setOverrideCursor(Qt.WaitCursor)

        self._completion_modal_shown = False
        self.btn_cancel.setEnabled(True)
        self.lbl_progress_status.setText("Iniciando esteira unificada de processamento...")
        self.progress_bar.setValue(5)
        if hasattr(self, "lbl_progress_pct"):
            self.lbl_progress_pct.setText("5%")
        self.log_drawer.append_log("Disparando UnifiedPipelineWorker...")
        self.correlation_view.set_status("Calculando correlação espectral...")

        # Worker instantiation and explicit instance binding
        worker = UnifiedPipelineWorker(
            job,
            manual_offset_override=self.manual_offset_override,
            parent=self
        )
        self.active_pipeline_worker = worker
        self.pipeline_worker = worker
        self.active_worker = worker
        self.current_worker = worker

        self.wire_pipeline_signals(worker)
        worker.start()

    def start_sync_pipeline(self) -> None:
        """Public deterministic method to launch the end-to-end sync and remux pipeline."""
        self.on_run_clicked()

    def wire_pipeline_signals(self, worker: PipelineWorker) -> None:
        """Explicitly connects all telemetry and progress signals from the worker to GUI components."""
        worker.started.connect(self._on_worker_started)
        if hasattr(worker, "analysis_started"):
            worker.analysis_started.connect(self._on_analysis_started)
        if hasattr(worker, "correlation_started"):
            worker.correlation_started.connect(self._on_analysis_started)
        worker.step_progress.connect(self._on_step_progress)
        worker.correlation_ready.connect(self._on_correlation_ready)
        worker.correlation_completed.connect(self._on_correlation_completed)
        if hasattr(worker, "correlation_finished"):
            worker.correlation_finished.connect(self._on_correlation_completed)
        worker.preview_segments_ready.connect(self._on_preview_segments_ready)
        worker.preview_ready.connect(self._on_preview_ready)
        worker.remux_progress.connect(self._on_remux_progress)
        worker.remux_completed.connect(self._on_remux_completed)
        if hasattr(worker, "remux_finished"):
            worker.remux_finished.connect(self._on_remux_completed)
        worker.finished_success.connect(self._on_finished_success)
        worker.execution_failed.connect(self._on_execution_failed)

        worker.progress.connect(self._on_worker_progress)
        worker.log_message.connect(self.log_drawer.append_log)
        worker.metrics_ready.connect(self._on_metrics_ready)
        worker.completed.connect(self._on_pipeline_completed)

    def _on_worker_started(self):
        self.correlation_view.set_status("Calculando correlação espectral...")
        self.lbl_progress_status.setText("Calculando correlação espectral...")

    def start_analysis(self):
        """Backwards-compatible alias for start_sync_pipeline."""
        self.start_sync_pipeline()

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
        if hasattr(self, "lbl_progress_pct"):
            self.lbl_progress_pct.setText(f"{int(pct)}%")
        self.lbl_progress_status.setText(msg)

    def _on_correlation_ready(self, telemetry: dict):
        offset = telemetry.get("offset_ms", 0.0)
        self.log_drawer.append_log(f"Telemetria espectral pronta: offset={offset:+.1f} ms")

    def _on_correlation_completed(self, offset_ms: float, confidence: float, drift: float, curve: list):
        self.correlation_view.set_data(curve, offset_ms, confidence)
        self.sync_controls.set_offset(offset_ms, is_calculated=True)
        if hasattr(self.sync_controls, "lbl_drift_val"):
            self.sync_controls.lbl_drift_val.setText(f"{drift:.6f}x".replace(".", ","))
        if hasattr(self.sync_controls, "lbl_confidence"):
            if confidence < 0.40:
                self.sync_controls.lbl_confidence.setText(f"Baixa ({confidence:.2f}) - Inspecione marcadores")
            else:
                self.sync_controls.lbl_confidence.setText(f"{confidence:.2f}")
        self.preview_player.update_offset(offset_ms)
        self.preview_player.set_preview_ready(f"Offset acústico determinado: {offset_ms:+.1f} ms")
        self.preview_player.set_markers_enabled(True)

    def _on_preview_segments_ready(self, segment_paths: list):
        self.preview_player.set_markers_enabled(True)

    def _on_preview_ready(self, preview_data: object):
        self.preview_player.set_markers_enabled(True)

    def _on_remux_progress(self, pct: float):
        self.progress_bar.setValue(int(pct))
        if hasattr(self, "lbl_progress_pct"):
            self.lbl_progress_pct.setText(f"{int(pct)}%")

    def _on_remux_completed(self, output_path: str):
        self._restore_action_button()
        self.btn_cancel.setEnabled(False)
        self.progress_bar.setValue(100)
        if hasattr(self, "lbl_progress_pct"):
            self.lbl_progress_pct.setText("100%")
        self.lbl_progress_status.setText("Remux finalizado com sucesso.")
        self._set_stepper_active(3)
        self.log_drawer.append_log(f"Remux concluído: {output_path}")
        if not getattr(self, "_completion_modal_shown", False):
            self._completion_modal_shown = True
            show_completion_modal(self, output_path)

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
        if hasattr(self, "lbl_progress_pct"):
            self.lbl_progress_pct.setText(f"{int(pct)}%")
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
        if hasattr(self, "lbl_progress_pct"):
            self.lbl_progress_pct.setText("100%" if success else "0%")
        self.lbl_progress_status.setText(msg)

        if success:
            self._set_stepper_active(3)
            self.log_drawer.append_log(f"Concluído com êxito: {self.txt_output_path.text()}")
            if not getattr(self, "_completion_modal_shown", False):
                self._completion_modal_shown = True
                show_completion_modal(self, self.txt_output_path.text().strip())
        else:
            self.log_drawer.append_log(f"Falha na operação: {msg}")
            QMessageBox.critical(self, "Erro no Remux", msg)

    def reset_to_recommended_state(self) -> None:
        """Resets the review gate state back to the initial deterministic recommendation."""
        if hasattr(self, "drop_zone"):
            self.drop_zone.reset_to_recommended_state()

    def cancel_active_operation(self):
        self._restore_action_button()
        if self.active_worker and self.active_worker.isRunning():
            self.lbl_progress_status.setText("Cancelando esteira...")
            self.active_worker.cancel()
        elif self.pipeline_worker and self.pipeline_worker.isRunning():
            self.lbl_progress_status.setText("Cancelando esteira...")
            self.pipeline_worker.cancel()
        if self.analyze_worker and self.analyze_worker.isRunning():
            self.analyze_worker.cancel()
        if self.remux_worker and self.remux_worker.isRunning():
            self.remux_worker.cancel()
        self.btn_cancel.setEnabled(False)


# Backwards compatibility alias
MainWindow = SyncFrameMainWindow

