"""Unified drag-and-drop ingestion zone with hierarchical confirmation table and acoustic auditing."""

import os
from typing import List, Optional, Tuple, Any, Dict

from PySide6.QtCore import Qt, Signal, QObject, QEvent
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget
)

from ...core.disk_utils import format_bytes
from ...core.models import (
    AutoMatchVerdict,
    AudioStreamDetail,
    StreamCandidate,
    format_channel_layout_label,
    format_immersive_profile_label,
    MediaSourceInfo,
    StreamReviewState,
    SmartDefaultsConfig,
    MediaInspectionReport,
    ConsolidatedStreamSelection,
    AudioQualityBadge,
    StreamAuditSummary
)
from ...core.inspector import (
    PORTUGUESE_TAGS,
    PORTUGUESE_KEYWORDS,
    format_audiophile_recommendation_badge,
    format_audiophile_discard_notice,
    determine_smart_defaults,
    rank_secondary_audio_streams,
    build_audio_quality_badge,
    build_stream_audit_summary,
    Inspector
)
from ..style import get_role_badge_style, get_action_chip_style
from ..workers.single_file_inspection_worker import SingleFileInspectionWorker
from .audio_preserve_checkbox import AudioPreserveCheckbox
from .media_inspector_view import MediaInspectorView
from .custom_combobox import (
    HighlightComboBox,
    DropdownHighlightDelegate,
    configure_translucent_combobox_popup,
)

SUPPORTED_EXTENSIONS = (
    ".mkv", ".mp4", ".m4v", ".mov",
    ".ac3", ".eac3", ".aac", ".dts",
    ".flac", ".m4a", ".mp3", ".wav", ".opus"
)


class WheelBlockerFilter(QObject):
    """Filters wheel events on comboboxes to prevent accidental track changes during scrolling."""
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Wheel:
            event.ignore()
            return True
        return super().eventFilter(watched, event)


_global_wheel_blocker = WheelBlockerFilter()


def install_wheel_blocker(combobox: QComboBox) -> None:
    """Disables mouse wheel scrolling on a QComboBox, forwarding the scroll to its parent."""
    combobox.installEventFilter(_global_wheel_blocker)
    combobox.wheelEvent = lambda event: event.ignore()
    configure_translucent_combobox_popup(combobox)


class NoWheelComboBox(QComboBox):
    """QComboBox subclass that ignores wheel scroll events unless popup is open and supports smooth rounded popups."""
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        install_wheel_blocker(self)
        configure_translucent_combobox_popup(self)

    def showPopup(self):
        configure_translucent_combobox_popup(self)
        super().showPopup()
        configure_translucent_combobox_popup(self)

    def wheelEvent(self, event):
        event.ignore()


def elide_filename(filename: str, max_chars: int = 36) -> str:
    """
    Applies middle elision to a filename (e.g. 'The.Avengers...1-DTOne.mkv'),
    preserving the stem prefix, '...', and stem suffix with file extension.
    """
    if not filename or len(filename) <= max_chars:
        return filename

    stem, ext = os.path.splitext(filename)
    if len(ext) >= max_chars - 5:
        return filename[: max(0, max_chars - 3)] + "..."

    available = max_chars - len(ext) - 3  # 3 for '...'
    if available < 6:
        return filename[: max(0, max_chars - 3)] + "..."

    left = (available + 1) // 2
    right = available // 2
    return f"{stem[:left]}...{stem[-right:]}{ext}"


def format_audio_dropdown_item(cand: StreamCandidate, max_filename_len: int = 24) -> str:
    """
    Formats audio dropdown item specification:
    [Arquivo Origem] • Trilha #ID • Idioma • Codec • Canais (ex.: 5.1 / 7.1) • Bitrate Real
    """
    base = elide_filename(os.path.basename(cand.file_path), max_chars=max_filename_len)
    track_id = f"Trilha #{cand.stream.id}"
    lang = (cand.stream.language or "und").upper()
    codec = (cand.stream.codec or "audio").upper()
    channels = cand.stream.spatial_label or format_channel_layout_label(cand.stream.channels, cand.stream.channel_layout)
    if cand.stream.bitrate and cand.stream.bitrate > 0:
        bitrate_kbps = int(round(cand.stream.bitrate / 1000.0))
        bitrate_str = f"{bitrate_kbps} kbps"
    else:
        bitrate_str = "Bitrate N/D"
    return f"[{base}] • {track_id} • {lang} • {codec} • {channels} • {bitrate_str}"


def format_stream_item_text(cand: StreamCandidate, max_filename_len: int = 36) -> str:
    """Formats technical specifications with middle elision on the filename for compact workbench readability."""
    if cand.stream.track_type == "audio":
        return format_audio_dropdown_item(cand, max_filename_len=24)

    basename = elide_filename(os.path.basename(cand.file_path), max_chars=max_filename_len)
    fmt = cand.stream.container_format.upper() if cand.stream.container_format else "MKV"
    if cand.stream.track_type == "video":
        res = f"{cand.stream.width}x{cand.stream.height}" if cand.stream.width and cand.stream.height else "Vídeo"
        fps_str = f" @ {cand.stream.fps:.3f}fps" if cand.stream.fps > 0 else ""
        return f"[{res}{fps_str}] {cand.stream.codec.upper()} [{fmt}] — {basename} (Trilha #{cand.stream.id})"
    else:
        lang = cand.stream.language.upper() if cand.stream.language else "UND"
        layout_tag = cand.stream.spatial_label or (format_channel_layout_label(cand.stream.channels, cand.stream.channel_layout) if cand.stream.channels else "")
        title = f" ({cand.stream.title})" if cand.stream.title else ""
        specs = " • ".join(filter(None, [cand.stream.codec.upper(), layout_tag]))
        return f"[{lang}] {specs}{title} [{fmt}] — {basename} (Trilha #{cand.stream.id})"


def decompose_channel_topology(
    channels: int,
    channel_layout: str = "",
    is_immersive: bool = False,
    spatial_label: str = ""
) -> Tuple[str, bool]:
    """
    Decomposes audio channel topology into explicit components:
    - Surround (e.g. 5.1, 7.1)
    - Superior / Height (e.g. 7.1.4, 5.1.2, Atmos)
    - LFE / Subwoofer presence
    Returns (topology_str, has_lfe).
    """
    layout_str = (channel_layout or "").lower().strip()
    spatial_str = (spatial_label or "").lower().strip()

    # Check LFE presence
    if ".1" in layout_str or ".2" in layout_str or "lfe" in layout_str or "sub" in layout_str:
        has_lfe = True
    elif ".0" in layout_str:
        has_lfe = False
    elif channels >= 6:
        has_lfe = True
    else:
        has_lfe = False

    # Check Height / Overheads (3 components: X.Y.Z, e.g. 7.1.4, 5.1.2) or Immersive
    has_height = False
    height_base = ""
    for candidate in (layout_str, spatial_str):
        parts = candidate.split(".")
        if len(parts) == 3 and parts[0].isdigit() and parts[1].isdigit() and parts[2].isdigit():
            has_height = True
            height_base = candidate
            break

    if has_height:
        return f"{height_base} Atmos (Surround + Height + Sub)", True

    if is_immersive or "atmos" in layout_str or "atmos" in spatial_str:
        if channels >= 8:
            return "7.1 Atmos (Surround + Height + Sub)", True
        elif channels >= 6:
            return "5.1 Atmos (Surround + Height + Sub)", True
        else:
            return f"{channels}.0 Atmos (Imersivo)", has_lfe

    if channels >= 8 or "7.1" in layout_str:
        if has_lfe:
            return "7.1 Surround (+Subwoofer)", True
        return "7.0 Surround (Sem LFE)", False

    if channels >= 6 or "5.1" in layout_str:
        if has_lfe:
            return "5.1 Surround (+Subwoofer)", True
        return "5.0 Surround (Sem LFE)", False

    if channels == 2 or "stereo" in layout_str or "estéreo" in spatial_str:
        if has_lfe or "2.1" in layout_str:
            return "2.1 Estéreo (+Subwoofer)", True
        return "2.0 Estéreo (Sem LFE)", False

    if channels == 1 or "mono" in layout_str:
        return "1.0 Mono (Sem LFE)", False

    if channels > 2:
        if has_lfe:
            return f"{channels-1}.1 Surround (+Subwoofer)", True
        return f"{channels}.0 Multi-canal (Sem LFE)", False

    return "Sem áudio", False


def format_commercial_branding(
    codec: str,
    channels: int,
    channel_layout: str = "",
    is_immersive: bool = False,
    title: str = "",
    spatial_label: str = ""
) -> str:
    """Formats standardized commercial branding label (Dolby Atmos, Dolby Audio 5.1, DTS-HD MA, etc.)."""
    c = (codec or "").lower().replace("-", "").replace("_", "")
    layout_lower = (channel_layout or "").lower()
    title_lower = (title or "").lower()
    spatial_lower = (spatial_label or "").lower()

    if is_immersive or "atmos" in title_lower or "atmos" in layout_lower or "atmos" in spatial_lower or "joc" in layout_lower:
        return "DOLBY ATMOS"

    if "dts" in c or "dts" in title_lower:
        if channels >= 8 or "7.1" in layout_lower or "dts-hd ma" in title_lower or "dtshd" in c:
            return "DTS-HD MA 7.1"
        elif "dts:x" in title_lower or "dtsx" in c:
            return "DTS:X"
        elif "dts-hd" in title_lower or "dtshd" in c:
            return f"DTS-HD MA {channels}.1" if channels >= 6 else "DTS-HD MA"
        return "DTS SURROUND"

    if any(k in c for k in ("ac3", "eac3", "truehd", "dolby")) or "dolby" in title_lower:
        if channels >= 8 or "7.1" in layout_lower:
            return "DOLBY AUDIO 7.1"
        elif channels >= 6 or "5.1" in layout_lower:
            return "DOLBY AUDIO 5.1"
        elif channels == 2 and ("surround" in layout_lower or "surround" in title_lower):
            return "DOLBY SURROUND"
        elif channels <= 2:
            return "ESTÉREO CONVENCIONAL"
        return f"DOLBY AUDIO {channels}ch"

    if "flac" in c:
        return "FLAC LOSSLESS"
    if "opus" in c:
        return "OPUS"
    if "aac" in c:
        return "AAC" if channels <= 2 else f"AAC {channels}.1"

    if channels <= 2:
        return "ESTÉREO CONVENCIONAL"
    elif channels >= 8 or "7.1" in layout_lower:
        return "SURROUND 7.1"
    elif channels >= 6 or "5.1" in layout_lower:
        return "SURROUND 5.1"

    return format_channel_layout_label(channels, channel_layout).upper()


class UnifiedDropZone(QFrame):
    """
    Unified ingestion zone supporting:
    - Drag & drop of 1 or 2 files simultaneously (.mkv, .mp4, .m4v, .mov).
    - Single system file picker for selecting both media files.
    - Paired horizontal subcards for video and dubbed audio sources.
    - Clean tabular Review Gate with pre-selected streams, acoustic channel audit, and composition options.
    """
    files_ready = Signal(str, str)
    multiple_files_ready = Signal(list)
    confirmation_confirmed = Signal(object, object, object, bool)  # (video_cand, target_cand, ref_cand, keep_orig)
    target_audio_changed = Signal(int)
    primary_audio_changed = Signal(object)
    ref_audio_changed = Signal(int)
    reset_requested = Signal()
    single_file_inspected = Signal(object)
    single_file_failed = Signal(str)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("unifiedDropZone")
        self.setProperty("class", "unifiedDropZone")
        self.setAcceptDrops(True)

        self.loaded_files: List[str] = []
        self.current_verdict: Optional[AutoMatchVerdict] = None
        self.inspection_worker: Optional[SingleFileInspectionWorker] = None
        self.secondary_checkbox_items: List[Tuple[QCheckBox, str, int]] = []

        self.init_ui()

    def init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.stack = QStackedWidget()

        # ======================================================================
        # Page 0: Standby / Empty Drop Zone (Card 01 - Unified Drop Zone)
        # ======================================================================
        self.page_empty = QFrame()
        self.page_empty.setObjectName("dropFrameEmpty")
        self.page_empty.setMaximumHeight(240)
        self.setMaximumHeight(240)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        empty_layout = QVBoxLayout(self.page_empty)
        empty_layout.setAlignment(Qt.AlignCenter)
        empty_layout.setSpacing(10)
        empty_layout.setContentsMargins(20, 20, 20, 20)

        tag_row = QHBoxLayout()
        tag_row.setAlignment(Qt.AlignCenter)
        tag_ingest = QLabel("01  INGESTÃO DE FONTES")
        tag_ingest.setObjectName("tagIngest")
        tag_ingest.setProperty("class", "systemChip")
        tag_ingest.setFixedHeight(28)
        tag_ingest.setAlignment(Qt.AlignCenter)
        tag_row.addWidget(tag_ingest)
        empty_layout.addLayout(tag_row)

        self.lbl_empty_title = QLabel("Arraste e solte os 2 arquivos de mídia aqui\nou selecione ambos pelo navegador")
        self.lbl_empty_title.setAlignment(Qt.AlignCenter)
        self.lbl_empty_title.setProperty("class", "dropTitle")
        empty_layout.addWidget(self.lbl_empty_title)

        lbl_hint = QLabel("MKV / MP4 / M4V / MOV  •  1 Vídeo de Referência + 1 Faixa de Dublagem")
        lbl_hint.setAlignment(Qt.AlignCenter)
        lbl_hint.setProperty("class", "subText")
        empty_layout.addWidget(lbl_hint)

        btn_browse = QPushButton("Selecionar Arquivos...")
        btn_browse.setObjectName("btnBrowse")
        btn_browse.setProperty("class", "btnPrimary")
        btn_browse.setMinimumWidth(180)
        btn_browse.setMaximumWidth(240)
        btn_browse.setFixedHeight(44)
        btn_browse.setCursor(Qt.PointingHandCursor)
        btn_browse.clicked.connect(self._open_file_dialog)
        empty_layout.addWidget(btn_browse, alignment=Qt.AlignCenter)

        self.stack.addWidget(self.page_empty)

        # ======================================================================
        # Page 1: 1 File Ingested (Single-File Media Inspector Workbench)
        # ======================================================================
        self.page_single = QFrame()
        self.page_single.setObjectName("dropFrameSingle")
        single_layout = QVBoxLayout(self.page_single)
        single_layout.setContentsMargins(0, 0, 0, 0)
        single_layout.setSpacing(0)

        # Legacy widgets preserved for test compatibility
        self.badge_waiting = QLabel("1 de 2 arquivos carregados — Aguardando segundo arquivo", self.page_single)
        self.badge_waiting.setObjectName("badgeWaiting")
        self.badge_waiting.setProperty("class", "badgeAmber")
        self.badge_waiting.setVisible(False)

        self.lbl_single_filename = QLabel("", self.page_single)
        self.lbl_single_filename.setObjectName("lblSingleFilename")
        self.lbl_single_filename.setProperty("class", "monoValue")
        self.lbl_single_filename.setVisible(False)

        self.btn_browse_second = QPushButton("Adicionar Segundo Arquivo...", self.page_single)
        self.btn_browse_second.setObjectName("btnBrowseSecond")
        self.btn_browse_second.clicked.connect(self._open_single_file_dialog)
        self.btn_browse_second.setVisible(False)

        self.btn_reset_single = QPushButton("Limpar", self.page_single)
        self.btn_reset_single.setObjectName("btnResetSingle")
        self.btn_reset_single.clicked.connect(self.reset)
        self.btn_reset_single.setVisible(False)

        self.inspector_view = MediaInspectorView(self.page_single)
        self.inspector_view.add_second_source_clicked.connect(self._open_single_file_dialog)
        self.inspector_view.reset_requested.connect(self.reset)
        single_layout.addWidget(self.inspector_view)

        self.stack.addWidget(self.page_single)

        # ======================================================================
        # Page 2: 2 Files Ingested (Workbench Paired File Cards + Review Gate)
        # ======================================================================
        self.page_confirm = QWidget()
        confirm_layout = QVBoxLayout(self.page_confirm)
        confirm_layout.setContentsMargins(0, 0, 0, 0)
        confirm_layout.setSpacing(14)

        # ----------------------------------------------------------------------
        # Container A: Ingested Sources Block (Pair Cards + Dub Container)
        # ----------------------------------------------------------------------
        self.block_sources = QFrame()
        self.block_sources.setObjectName("blockSourcesIngested")
        self.block_sources.setProperty("class", "subCard")
        bs_layout = QVBoxLayout(self.block_sources)
        bs_layout.setContentsMargins(16, 12, 16, 12)
        bs_layout.setSpacing(8)

        # Header with Card title, sources count tag and Change button
        conf_header = QHBoxLayout()
        conf_header.setSpacing(10)

        conf_title = QLabel("Fontes ingeridas")
        conf_title.setProperty("class", "cardTitle")
        conf_header.addWidget(conf_title)
        conf_header.addStretch()

        self.chip_sources_count = QLabel("0 / 0 FONTES")
        self.chip_sources_count.setObjectName("chipSourcesCount")
        self.chip_sources_count.setProperty("class", "tagNeutral")
        self.chip_sources_count.setFixedHeight(28)
        self.chip_sources_count.setAlignment(Qt.AlignCenter)
        conf_header.addWidget(self.chip_sources_count)

        self.btn_change_files = QPushButton("Trocar arquivos")
        self.btn_change_files.setObjectName("btnChangeFiles")
        self.btn_change_files.setProperty("class", "btnSm")
        self.btn_change_files.setFixedHeight(28)
        self.btn_change_files.setCursor(Qt.PointingHandCursor)
        self.btn_change_files.clicked.connect(self.reset)
        conf_header.addWidget(self.btn_change_files)
        bs_layout.addLayout(conf_header)

        # Dynamic Horizontal File Cards (.pair) - supports N sources
        self.sources_layout = QHBoxLayout()
        self.sources_layout.setSpacing(10)
        self.dynamic_source_cards: List[QFrame] = []

        # File Card: Video Reference (.file)
        self.card_file_v = QFrame()
        self.card_file_v.setObjectName("cardFileV")
        self.card_file_v.setProperty("class", "fileBox")
        cf_v_layout = QVBoxLayout(self.card_file_v)
        cf_v_layout.setContentsMargins(14, 10, 14, 10)
        cf_v_layout.setSpacing(4)

        head_v = QHBoxLayout()
        self.lbl_v_role = QLabel("Referência de vídeo")
        self.lbl_v_role.setProperty("class", "fileRole")
        head_v.addWidget(self.lbl_v_role)
        head_v.addStretch()
        self.badge_v_fmt = QLabel("MKV")
        self.badge_v_fmt.setObjectName("badgeVFmt")
        self.badge_v_fmt.setProperty("class", "formatChip")
        self.badge_v_fmt.setFixedHeight(24)
        self.badge_v_fmt.setAlignment(Qt.AlignCenter)
        head_v.addWidget(self.badge_v_fmt)
        cf_v_layout.addLayout(head_v)

        self.lbl_v_filename = QLabel("video_ref.mkv")
        self.lbl_v_filename.setProperty("class", "fileName")
        self.lbl_v_filename.setWordWrap(True)
        cf_v_layout.addWidget(self.lbl_v_filename)

        self.lbl_v_meta = QLabel("0.0 GB · 00:00:00")
        self.lbl_v_meta.setProperty("class", "fileMeta")
        cf_v_layout.addWidget(self.lbl_v_meta)
        self.sources_layout.addWidget(self.card_file_v, 1)

        # File Card: Dubbed Audio Source (.file)
        self.card_file_a = QFrame()
        self.card_file_a.setObjectName("cardFileA")
        self.card_file_a.setProperty("class", "fileBox")
        cf_a_layout = QVBoxLayout(self.card_file_a)
        cf_a_layout.setContentsMargins(14, 10, 14, 10)
        cf_a_layout.setSpacing(4)

        head_a = QHBoxLayout()
        self.lbl_a_role = QLabel("Áudio dublado")
        self.lbl_a_role.setProperty("class", "fileRole")
        head_a.addWidget(self.lbl_a_role)
        head_a.addStretch()
        self.badge_a_fmt = QLabel("MP4")
        self.badge_a_fmt.setObjectName("badgeAFmt")
        self.badge_a_fmt.setProperty("class", "formatChip")
        self.badge_a_fmt.setFixedHeight(24)
        self.badge_a_fmt.setAlignment(Qt.AlignCenter)
        head_a.addWidget(self.badge_a_fmt)
        cf_a_layout.addLayout(head_a)

        self.lbl_a_filename = QLabel("audio_dub.mp4")
        self.lbl_a_filename.setProperty("class", "fileName")
        self.lbl_a_filename.setWordWrap(True)
        cf_a_layout.addWidget(self.lbl_a_filename)

        self.lbl_a_meta = QLabel("0.0 MB · 00:00:00")
        self.lbl_a_meta.setProperty("class", "fileMeta")
        cf_a_layout.addWidget(self.lbl_a_meta)
        self.sources_layout.addWidget(self.card_file_a, 1)

        bs_layout.addLayout(self.sources_layout)

        # Dubbing Container (.dub)
        self.frame_arbitration = QFrame()
        self.frame_arbitration.setObjectName("frameArbitration")
        self.frame_arbitration.setProperty("class", "arbitrationCard")
        arb_layout = QHBoxLayout(self.frame_arbitration)
        arb_layout.setContentsMargins(14, 8, 14, 8)
        arb_layout.setSpacing(8)

        dub_text_box = QVBoxLayout()
        dub_text_box.setSpacing(2)
        self.lbl_arbitration_title = QLabel("Dublagem externa selecionada")
        self.lbl_arbitration_title.setProperty("class", "dubTitle")
        dub_text_box.addWidget(self.lbl_arbitration_title)

        self.lbl_arbitration = QLabel("")
        self.lbl_arbitration.setProperty("class", "dubDesc")
        self.lbl_arbitration.setWordWrap(True)
        dub_text_box.addWidget(self.lbl_arbitration)
        arb_layout.addLayout(dub_text_box, 1)

        self.check_revert_arbitration = QCheckBox("Manter dublagem local embutida")
        self.check_revert_arbitration.setLayoutDirection(Qt.RightToLeft)
        self.check_revert_arbitration.toggled.connect(self._on_revert_arbitration_toggled)
        arb_layout.addWidget(self.check_revert_arbitration)

        self.frame_arbitration.setVisible(False)
        bs_layout.addWidget(self.frame_arbitration)

        # Files summary strip (preserved for test compatibility)
        self.lbl_files_summary = QLabel("")
        self.lbl_files_summary.setVisible(False)
        bs_layout.addWidget(self.lbl_files_summary)

        # Ambiguity Banner
        self.frame_ambiguity = QFrame()
        self.frame_ambiguity.setProperty("class", "subCard")
        amb_layout = QHBoxLayout(self.frame_ambiguity)
        amb_layout.setContentsMargins(8, 8, 8, 8)
        self.lbl_ambiguity = QLabel("")
        self.lbl_ambiguity.setProperty("class", "diagnosisBanner")
        amb_layout.addWidget(self.lbl_ambiguity)
        self.frame_ambiguity.setVisible(False)
        bs_layout.addWidget(self.frame_ambiguity)

        confirm_layout.addWidget(self.block_sources)

        # ----------------------------------------------------------------------
        # Container C: Stream Review Gate (Mapping, Channels Audit, Action)
        # ----------------------------------------------------------------------
        self.block_review = QFrame()
        self.block_review.setObjectName("blockReviewGate")
        self.block_review.setProperty("class", "subCard")
        br_layout = QVBoxLayout(self.block_review)
        br_layout.setContentsMargins(16, 12, 16, 12)
        br_layout.setSpacing(8)

        rf_head = QHBoxLayout()
        rf_head.setSpacing(10)
        rf_title = QLabel("Revisão de faixas")
        rf_title.setProperty("class", "cardTitle")
        rf_head.addWidget(rf_title)
        rf_head.addStretch()

        self.btn_restore_recommendation = QPushButton("Restaurar Recomendação")
        self.btn_restore_recommendation.setObjectName("btnRestore")
        self.btn_restore_recommendation.setProperty("class", "btnRestore")
        self.btn_restore_recommendation.setToolTip("Restaura a combinação ótima original calculada pelo probing inicial.")
        self.btn_restore_recommendation.clicked.connect(self.reset_to_recommended_state)
        rf_head.addWidget(self.btn_restore_recommendation)

        lbl_no_rec = QLabel("Sem reencode de vídeo")
        lbl_no_rec.setProperty("class", "tagGreen")
        rf_head.addWidget(lbl_no_rec)
        br_layout.addLayout(rf_head)

        # Comboboxes instantiated with HighlightComboBox (delegate + wheel blocker + translucent popup)
        self.combo_video = HighlightComboBox()
        self.combo_video.currentIndexChanged.connect(self._update_audio_audit)

        self.combo_target_audio = HighlightComboBox()
        self.combo_target_audio.currentIndexChanged.connect(self._on_combo_target_changed)

        self.combo_ref_audio = HighlightComboBox()
        self.combo_ref_audio.currentIndexChanged.connect(self._on_combo_ref_changed)

        # Structured Two-Level Stream Rows via configure_stream_row contract
        self.row_video = self.configure_stream_row(
            "V01", "Melhor Imagem", "", "Vídeo Intocado (Cópia Direta)", self.combo_video
        )
        self.badge_v_status = self.row_video.badge
        self.chip_v_act = self.row_video.chip
        br_layout.addWidget(self.row_video)

        self.row_target = self.configure_stream_row(
            "A02", "Português Oficial", "", "Sincronizar e Alinhar", self.combo_target_audio
        )
        self.badge_a_status = self.row_target.badge
        self.chip_a_act = self.row_target.chip
        br_layout.addWidget(self.row_target)

        self.row_ref = self.configure_stream_row(
            "A01", "Referência Fixa", "", "Manter como Secundária", self.combo_ref_audio
        )
        self.badge_ref_status = self.row_ref.badge
        self.chip_ref_act = self.row_ref.chip
        br_layout.addWidget(self.row_ref)

        # Section 3: Secondary Audio Streams Panel (Multi-Select Checkboxes)
        self.frame_secondary_audio = QFrame()
        self.frame_secondary_audio.setObjectName("frameSecondaryAudio")
        fsa_layout = QVBoxLayout(self.frame_secondary_audio)
        fsa_layout.setContentsMargins(0, 4, 0, 4)
        fsa_layout.setSpacing(8)

        fsa_head = QHBoxLayout()
        fsa_head.setSpacing(10)
        lbl_fsa_title = QLabel("Faixas de áudio secundárias (Multi-Select)")
        lbl_fsa_title.setObjectName("lblFsaTitle")
        fsa_head.addWidget(lbl_fsa_title)
        fsa_head.addStretch()

        self.chip_fsa_status = QLabel("Passthrough direto (copy)")
        self.chip_fsa_status.setObjectName("chipFsaStatus")
        self.chip_fsa_status.setFixedHeight(24)
        fsa_head.addWidget(self.chip_fsa_status)
        fsa_layout.addLayout(fsa_head)

        self.secondary_container = QWidget()
        self.secondary_container.setObjectName("secondaryContainer")
        self.secondary_container.setStyleSheet("background: transparent; border: none;")
        self.secondary_layout = QVBoxLayout(self.secondary_container)
        self.secondary_layout.setContentsMargins(0, 2, 0, 2)
        self.secondary_layout.setSpacing(6)
        fsa_layout.addWidget(self.secondary_container)

        br_layout.addWidget(self.frame_secondary_audio)

        # Target Output Summary / Resulting File Specs Bar (.audit, .resultingSpecsBar)
        self.frame_audio_audit = QFrame()
        self.frame_audio_audit.setObjectName("frameAudioAudit")
        self.frame_audio_audit.setProperty("class", "auditPill resultingSpecsBar")
        audit_layout = QHBoxLayout(self.frame_audio_audit)
        audit_layout.setContentsMargins(12, 6, 12, 6)
        audit_layout.setSpacing(6)

        self.lbl_resulting_title = QLabel("Arquivo Resultante:")
        self.lbl_resulting_title.setObjectName("lblResultingTitle")
        self.lbl_resulting_title.setProperty("class", "resultingTitle")
        audit_layout.addWidget(self.lbl_resulting_title)

        self.pill_res_container = QLabel("MKV Matroska")
        self.pill_res_container.setObjectName("pillResContainer")
        self.pill_res_container.setProperty("class", "resultingSpecPill")
        audit_layout.addWidget(self.pill_res_container)

        self.pill_res_mode = QLabel("Cópia Direta (Passthrough)")
        self.pill_res_mode.setObjectName("pillResMode")
        self.pill_res_mode.setProperty("class", "resultingSpecPill resultingPillGreen")
        audit_layout.addWidget(self.pill_res_mode)

        self.pill_res_brand = QLabel("DOLBY AUDIO 5.1")
        self.pill_res_brand.setObjectName("pillResBrand")
        self.pill_res_brand.setProperty("class", "resultingSpecPill resultingPillGreen")
        audit_layout.addWidget(self.pill_res_brand)

        self.pill_res_codec = QLabel("AC-3")
        self.pill_res_codec.setObjectName("pillResCodec")
        self.pill_res_codec.setProperty("class", "resultingSpecPill")
        audit_layout.addWidget(self.pill_res_codec)

        self.pill_res_channels = QLabel("5.1 Surround (+Subwoofer)")
        self.pill_res_channels.setObjectName("pillResChannels")
        self.pill_res_channels.setProperty("class", "resultingSpecPill")
        audit_layout.addWidget(self.pill_res_channels)

        self.pill_res_rate = QLabel("48.000 Hz")
        self.pill_res_rate.setObjectName("pillResRate")
        self.pill_res_rate.setProperty("class", "resultingSpecPill")
        audit_layout.addWidget(self.pill_res_rate)

        self.pill_res_bitrate = QLabel("640 kbps")
        self.pill_res_bitrate.setObjectName("pillResBitrate")
        self.pill_res_bitrate.setProperty("class", "resultingSpecPill")
        audit_layout.addWidget(self.pill_res_bitrate)

        # Backward compatibility labels for test assertions
        self.lbl_audit_origin = QLabel("MKV Nativo", self.frame_audio_audit)
        self.lbl_audit_origin.setObjectName("lblAuditOrigin")
        self.lbl_audit_origin.setProperty("class", "badgeNeutral")
        self.lbl_audit_origin.setVisible(False)

        self.badge_audit_layout = QLabel("DOLBY AUDIO 5.1", self.frame_audio_audit)
        self.badge_audit_layout.setObjectName("badgeAuditLayout")
        self.badge_audit_layout.setProperty("class", "badgeGreen")
        self.badge_audit_layout.setVisible(False)

        self.lbl_audit_specs = QLabel("", self.frame_audio_audit)
        self.lbl_audit_specs.setObjectName("lblAuditSpecs")
        self.lbl_audit_specs.setVisible(False)

        audit_layout.addStretch()
        br_layout.addWidget(self.frame_audio_audit)

        # Contextual Channel Difference Alert
        self.frame_channel_alert = QFrame()
        self.frame_channel_alert.setProperty("class", "subCard")
        alert_layout = QHBoxLayout(self.frame_channel_alert)
        alert_layout.setContentsMargins(8, 6, 8, 6)
        self.lbl_channel_alert = QLabel("")
        self.lbl_channel_alert.setProperty("class", "diagnosisBanner")
        alert_layout.addWidget(self.lbl_channel_alert)
        self.frame_channel_alert.setVisible(False)
        br_layout.addWidget(self.frame_channel_alert)

        # Compact Horizontal Options Row (.opts): Audio preservation + PAL pitch restore + Re-encode codec
        self.frame_options = QFrame()
        self.frame_options.setObjectName("frameOptions")
        self.frame_options.setProperty("class", "optionsContainer")
        options_row = QHBoxLayout(self.frame_options)
        options_row.setContentsMargins(0, 2, 0, 2)
        options_row.setSpacing(8)

        # Option 1: Audio preservation
        opt_1 = QFrame()
        opt_1.setProperty("class", "optRow")
        l1 = QHBoxLayout(opt_1)
        l1.setContentsMargins(12, 4, 12, 4)
        self.check_keep_original = AudioPreserveCheckbox(self.page_confirm, language_name="inglês")
        self.check_keep_original.setLayoutDirection(Qt.RightToLeft)
        self.check_keep_original.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        l1.addWidget(self.check_keep_original)
        options_row.addWidget(opt_1, 1)

        # Option 2: PAL Pitch restore
        opt_2 = QFrame()
        opt_2.setProperty("class", "optRow")
        l2 = QHBoxLayout(opt_2)
        l2.setContentsMargins(12, 4, 12, 4)
        self.check_pal_pitch = QCheckBox("Restauração PAL (25 fps → 24 fps)")
        self.check_pal_pitch.setLayoutDirection(Qt.RightToLeft)
        self.check_pal_pitch.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.check_pal_pitch.setToolTip(
            "Aplica desaceleração natural com correção de tom (asetrate+aresample soxr) para dublagens originadas de masters PAL (25 fps)."
        )
        self.check_pal_pitch.toggled.connect(lambda _: self._update_audio_audit())
        l2.addWidget(self.check_pal_pitch)
        options_row.addWidget(opt_2, 1)

        # Option 3: Re-encode codec
        opt_3 = QFrame()
        opt_3.setProperty("class", "optRow")
        l3 = QHBoxLayout(opt_3)
        l3.setContentsMargins(12, 4, 12, 4)
        lbl_codec = QLabel("Codec de re-encode")
        lbl_codec.setProperty("class", "optLabel")
        l3.addWidget(lbl_codec)
        l3.addStretch()

        self.combo_audio_codec = HighlightComboBox(self)
        self.combo_audio_codec.addItem("FLAC (lossless)", "flac")
        self.combo_audio_codec.addItem("Opus", "opus")
        self.combo_audio_codec.addItem("E-AC3 / AC3", "eac3")
        self.combo_audio_codec.addItem("AAC", "aac")
        self.combo_audio_codec.setToolTip(
            "Codec de saída caso time-stretch contínuo ou restauração PAL seja obrigatório."
        )
        install_wheel_blocker(self.combo_audio_codec)
        self.combo_audio_codec.currentIndexChanged.connect(lambda _: self._update_audio_audit())
        l3.addWidget(self.combo_audio_codec)
        options_row.addWidget(opt_3, 1)

        br_layout.addWidget(self.frame_options)

        # Primary Action Row: Single button ("Sincronizar e concluir") anchored cleanly
        action_row = QHBoxLayout()
        action_row.setSpacing(12)
        action_row.setContentsMargins(0, 4, 0, 0)

        self.btn_confirm = QPushButton("Sincronizar e concluir")
        self.btn_confirm.setObjectName("btnConfirm")
        self.btn_confirm.setProperty("class", "btnPrimary")
        self.btn_confirm.setFixedHeight(44)
        self.btn_confirm.setCursor(Qt.PointingHandCursor)
        self.btn_confirm.clicked.connect(self._on_confirm_clicked)
        action_row.addWidget(self.btn_confirm)

        self.lbl_confirm_hint = QLabel("Pressione Enter para aprovação imediata da seleção.")
        self.lbl_confirm_hint.setProperty("class", "hint")
        action_row.addWidget(self.lbl_confirm_hint)
        action_row.addStretch()

        br_layout.addLayout(action_row)

        confirm_layout.addWidget(self.block_review)

        self.stack.addWidget(self.page_confirm)
        root_layout.addWidget(self.stack)

    # ==========================================================================
    # Drag and Drop Events
    # ==========================================================================
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.page_empty.setProperty("dragOver", True)
            self.page_empty.style().unpolish(self.page_empty)
            self.page_empty.style().polish(self.page_empty)

    def dragLeaveEvent(self, event):
        self.page_empty.setProperty("dragOver", False)
        self.page_empty.style().unpolish(self.page_empty)
        self.page_empty.style().polish(self.page_empty)

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        files = [u.toLocalFile() for u in urls if os.path.isfile(u.toLocalFile())]
        self.dragLeaveEvent(None)
        if files:
            self.handle_files_ingested(files)

    def _open_file_dialog(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Selecionar Arquivos (Vídeo / Áudio)",
            "",
            "Mídias Suportadas (*.mkv *.mp4 *.m4v *.mov *.ac3 *.eac3 *.aac *.dts *.flac *.m4a *.mp3 *.wav *.opus);;Vídeos (*.mkv *.mp4 *.m4v *.mov);;Áudios (*.ac3 *.eac3 *.aac *.dts *.flac *.m4a *.mp3 *.wav *.opus);;Todos os Arquivos (*)"
        )
        if files:
            self.handle_files_ingested(files)

    def _open_single_file_dialog(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Selecionar Segundo Arquivo de Mídia",
            "",
            "Mídias Suportadas (*.mkv *.mp4 *.m4v *.mov *.ac3 *.eac3 *.aac *.dts *.flac *.m4a *.mp3 *.wav *.opus);;Vídeos (*.mkv *.mp4 *.m4v *.mov);;Áudios (*.ac3 *.eac3 *.aac *.dts *.flac *.m4a *.mp3 *.wav *.opus);;Todos os Arquivos (*)"
        )
        if files:
            self.handle_files_ingested(files)

    def handle_files_ingested(self, file_paths: List[str]) -> None:
        """
        Validates incoming files, updates drop zone state machine:
        - 1 file: displays single file slot on page 1 and runs async MediaInspectorView.
        - 2 files: cancels single inspector and emits files_ready signal for multi-file review gate.
        """
        valid_files = [f for f in file_paths if f.lower().endswith(SUPPORTED_EXTENSIONS) and not os.path.isdir(f)]

        if not valid_files:
            return

        for f in valid_files:
            if f not in self.loaded_files:
                self.loaded_files.append(f)

        if len(self.loaded_files) == 1:
            self.lbl_single_filename.setText(os.path.basename(self.loaded_files[0]))
            self.badge_waiting.setText("1 / 2 fontes carregadas — Aguardando segundo arquivo")
            self.update_dropzone_state(True)
            self.stack.setCurrentIndex(1)
            self.start_single_file_inspection(self.loaded_files[0])
        elif len(self.loaded_files) == 2:
            if self.inspection_worker and self.inspection_worker.isRunning():
                self.inspection_worker.cancel()
            self.files_ready.emit(self.loaded_files[0], self.loaded_files[1])
        elif len(self.loaded_files) > 2:
            if self.inspection_worker and self.inspection_worker.isRunning():
                self.inspection_worker.cancel()
            self.multiple_files_ready.emit(list(self.loaded_files))

    def start_single_file_inspection(self, file_path: str) -> None:
        """Dispatches SingleFileInspectionWorker to inspect single media without blocking GUI."""
        self.inspector_view.set_loading(file_path)
        if self.inspection_worker and self.inspection_worker.isRunning():
            self.inspection_worker.cancel()
            self.inspection_worker.wait()

        self.inspection_worker = SingleFileInspectionWorker(file_path, self)
        self.inspection_worker.inspection_completed.connect(self._on_single_inspection_completed)
        self.inspection_worker.inspection_failed.connect(self._on_single_inspection_failed)
        self.inspection_worker.start()

    def _on_single_inspection_completed(self, report: MediaInspectionReport) -> None:
        self.inspector_view.set_report(report)
        self.single_file_inspected.emit(report)

    def _on_single_inspection_failed(self, err_msg: str) -> None:
        self.inspector_view.set_error(err_msg)
        self.single_file_failed.emit(err_msg)

    def ingest_files(self, file_paths: List[str]) -> None:
        """Backwards-compatible alias for handle_files_ingested."""
        self.handle_files_ingested(file_paths)

    def _create_source_card(self, src: MediaSourceInfo, idx: int) -> QFrame:
        """Dynamically creates a styled card for the i-th ingested source (i >= 2)."""
        card = QFrame()
        card.setObjectName(f"cardFileExtra_{idx}")
        card.setProperty("class", "fileBox")
        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(14, 10, 14, 10)
        c_layout.setSpacing(4)

        head = QHBoxLayout()
        lbl_role = QLabel(src.role_label or f"Fonte adicional #{idx + 1}")
        lbl_role.setProperty("class", "fileRole")
        head.addWidget(lbl_role)
        head.addStretch()

        fmt_str = src.extension or os.path.splitext(src.file_path)[1].replace(".", "").upper() or "MÍDIA"
        badge_fmt = QLabel(fmt_str)
        badge_fmt.setProperty("class", "formatChip")
        badge_fmt.setFixedHeight(24)
        badge_fmt.setAlignment(Qt.AlignCenter)
        head.addWidget(badge_fmt)
        c_layout.addLayout(head)

        lbl_filename = QLabel(os.path.basename(src.file_path))
        lbl_filename.setProperty("class", "fileName")
        lbl_filename.setWordWrap(True)
        c_layout.addWidget(lbl_filename)

        lbl_meta = QLabel(src.summary or "")
        lbl_meta.setProperty("class", "fileMeta")
        c_layout.addWidget(lbl_meta)

        return card

    def update_sources_view(self, media_sources: List[MediaSourceInfo]) -> None:
        """Renders dynamic media source cards and transitions visual state to the Review Gate (Page 2)."""
        if not media_sources:
            return

        # 1. Clean previous dynamic cards (idx >= 2)
        if hasattr(self, "dynamic_source_cards"):
            for card in self.dynamic_source_cards:
                if hasattr(self, "sources_layout"):
                    self.sources_layout.removeWidget(card)
                card.setParent(None)
                card.deleteLater()
            self.dynamic_source_cards = []
        else:
            self.dynamic_source_cards = []

        # 2. Populate card 0 (card_file_v)
        src_0 = media_sources[0]
        self.lbl_v_filename.setText(os.path.basename(src_0.file_path))
        self.lbl_v_meta.setText(src_0.summary)
        self.badge_v_fmt.setText(src_0.extension or os.path.splitext(src_0.file_path)[1].replace(".", "").upper())
        if hasattr(self, "lbl_v_role") and src_0.role_label:
            self.lbl_v_role.setText(src_0.role_label)

        # 3. Populate card 1 (card_file_a) if len >= 2
        if len(media_sources) > 1:
            self.card_file_a.setVisible(True)
            src_1 = media_sources[1]
            self.lbl_a_filename.setText(os.path.basename(src_1.file_path))
            self.lbl_a_meta.setText(src_1.summary)
            self.badge_a_fmt.setText(src_1.extension or os.path.splitext(src_1.file_path)[1].replace(".", "").upper())
            if hasattr(self, "lbl_a_role") and src_1.role_label:
                self.lbl_a_role.setText(src_1.role_label)
        else:
            self.card_file_a.setVisible(False)

        # 4. Dynamically create and add cards for sources 2..N-1
        for i in range(2, len(media_sources)):
            extra_card = self._create_source_card(media_sources[i], i)
            if hasattr(self, "sources_layout"):
                self.sources_layout.addWidget(extra_card, 1)
            self.dynamic_source_cards.append(extra_card)

        self.update_source_count_badge(len(media_sources))
        self.update_dropzone_state(True)
        self.stack.setCurrentIndex(2)

    def update_source_count_badge(self, count: int) -> None:
        """Dynamically updates the ingested sources count badge for N sources."""
        if hasattr(self, "chip_sources_count"):
            self.chip_sources_count.setText(f"{count} / {count} FONTES")

    def set_verdict(self, verdict: AutoMatchVerdict):
        self.current_verdict = verdict
        self.update_dropzone_state(True)

        file_v = verdict.recommended_video.file_path
        file_a = verdict.recommended_target_audio.file_path if verdict.recommended_target_audio else ""

        sz_v = format_bytes(os.path.getsize(file_v)) if os.path.exists(file_v) else ""
        sz_a = format_bytes(os.path.getsize(file_a)) if file_a and os.path.exists(file_a) else ""

        ext_v = os.path.splitext(file_v)[1].replace(".", "").upper()
        ext_a = os.path.splitext(file_a)[1].replace(".", "").upper() if file_a else ""

        v_summary = f"{sz_v}  •  {verdict.recommended_video.stream.fps:.3f} fps" if verdict.recommended_video.stream.fps > 0 else sz_v

        sources = [
            MediaSourceInfo(
                file_path=file_v,
                file_size_formatted=sz_v,
                extension=ext_v,
                role_label="REFERÊNCIA DE VÍDEO",
                summary=v_summary,
                is_video_source=True
            )
        ]

        if file_a and verdict.recommended_target_audio:
            a_stream = verdict.recommended_target_audio.stream
            sr = a_stream.sample_rate or 48000
            layout_lbl = format_channel_layout_label(a_stream.channels, a_stream.channel_layout) if a_stream.channels else ""
            a_summary = f"{sz_a}  •  {layout_lbl} • {sr} Hz" if layout_lbl else f"{sz_a}  •  {sr} Hz"
            sources.append(
                MediaSourceInfo(
                    file_path=file_a,
                    file_size_formatted=sz_a,
                    extension=ext_a,
                    role_label="ÁUDIO DUBLADO",
                    summary=a_summary,
                    is_video_source=False
                )
            )

        existing_paths = {file_v}
        if file_a:
            existing_paths.add(file_a)

        extra_files = []
        for f in getattr(self, "loaded_files", []):
            if f not in existing_paths and f not in extra_files:
                extra_files.append(f)
        for cand in verdict.alternative_videos + verdict.alternative_audios + ([verdict.reference_audio] if verdict.reference_audio else []):
            if cand and cand.file_path and cand.file_path not in existing_paths and cand.file_path not in extra_files:
                extra_files.append(cand.file_path)

        for extra_f in extra_files:
            extra_sz = format_bytes(os.path.getsize(extra_f)) if os.path.exists(extra_f) else ""
            extra_ext = os.path.splitext(extra_f)[1].replace(".", "").upper()

            is_extra_vid = any(v.file_path == extra_f for v in verdict.alternative_videos)
            vid_cand = next((v for v in verdict.alternative_videos if v.file_path == extra_f), None)
            aud_cand = next((a for a in verdict.alternative_audios if a.file_path == extra_f), None)

            if is_extra_vid and vid_cand:
                role_lbl = "VÍDEO ALTERNATIVO"
                fps_txt = f"  •  {vid_cand.stream.fps:.3f} fps" if vid_cand.stream.fps > 0 else ""
                summary_txt = f"{extra_sz}{fps_txt}"
            elif aud_cand:
                role_lbl = "ÁUDIO ADICIONAL"
                ch_lbl = format_channel_layout_label(aud_cand.stream.channels, aud_cand.stream.channel_layout) if aud_cand.stream.channels else ""
                summary_txt = f"{extra_sz}  •  {ch_lbl}" if ch_lbl else f"{extra_sz} [{extra_ext}]"
            else:
                role_lbl = "FONTE ADICIONAL"
                summary_txt = f"{extra_sz} [{extra_ext}]"

            sources.append(
                MediaSourceInfo(
                    file_path=extra_f,
                    file_size_formatted=extra_sz,
                    extension=extra_ext,
                    role_label=role_lbl,
                    summary=summary_txt,
                    is_video_source=is_extra_vid
                )
            )

        self.update_sources_view(sources)

        self.lbl_files_summary.setText(
            f"Fonte Vídeo: {os.path.basename(file_v)} ({sz_v}) [{ext_v}]  |  "
            f"Fonte Áudio: {os.path.basename(file_a)} ({sz_a}) [{ext_a}]"
        )

        # Ambiguity banner
        if verdict.is_ambiguous:
            self.lbl_ambiguity.setText(f"[ATENCAO] {verdict.ambiguity_reason}")
            self.frame_ambiguity.setVisible(True)
        else:
            self.frame_ambiguity.setVisible(False)

        # Stream arbitration decision & audiophile recommendation
        if verdict.arbitration_result and (verdict.arbitration_result.is_replacement or "já possui fidelidade técnica superior" in verdict.arbitration_result.reason or "ÁUDIO DE MAIOR FIDELIDADE" in verdict.arbitration_result.reason):
            self.lbl_arbitration.setText(verdict.arbitration_result.reason)
            self.check_revert_arbitration.blockSignals(True)
            self.check_revert_arbitration.setChecked(False)
            self.check_revert_arbitration.setVisible(verdict.arbitration_result.is_replacement)
            self.check_revert_arbitration.blockSignals(False)
            self.frame_arbitration.setVisible(True)
        elif verdict.recommended_target_audio and verdict.alternative_audios:
            rec_badge, rec_reason = format_audiophile_recommendation_badge(verdict.recommended_target_audio.stream)
            discard_note = f"\n{format_audiophile_discard_notice(verdict.alternative_audios[0].stream)}"
            self.lbl_arbitration.setText(f"[{rec_badge}] {rec_reason}{discard_note}")
            self.check_revert_arbitration.setVisible(False)
            self.frame_arbitration.setVisible(True)
        else:
            self.frame_arbitration.setVisible(False)

        # Populate stream comboboxes
        self.populate_stream_dropdowns(sources)

        self.update_role_badge(self.badge_v_status, "Melhor Imagem")

        if verdict.recommended_target_audio:
            rec_badge, _ = format_audiophile_recommendation_badge(verdict.recommended_target_audio.stream)
            if verdict.is_ambiguous:
                self.update_role_badge(self.badge_a_status, "Ajuste Manual", is_amber=True)
            else:
                self.update_role_badge(self.badge_a_status, rec_badge)
        else:
            if verdict.is_ambiguous:
                self.update_role_badge(self.badge_a_status, "Ajuste Manual", is_amber=True)
            else:
                self.update_role_badge(self.badge_a_status, "Português Oficial")

        self.update_role_badge(self.badge_ref_status, "Referência Fixa")

        if verdict.reference_audio and verdict.reference_audio.stream.language:
            lang = verdict.reference_audio.stream.language.lower()
            lang_name = "inglês" if lang in ("eng", "en") else lang.upper()
            self.check_keep_original.set_language_name(lang_name)

        # Smart defaults for PAL pitch restoration and output codec
        if verdict.recommended_video and verdict.recommended_target_audio:
            smart = determine_smart_defaults(
                verdict.recommended_video.stream,
                verdict.recommended_target_audio.stream
            )
            self.check_pal_pitch.setChecked(smart.pal_pitch_restore)
            if smart.pal_badge_text:
                self.check_pal_pitch.setToolTip(smart.pal_badge_text)
            idx_c = self.combo_audio_codec.findData(smart.target_codec)
            if idx_c >= 0:
                self.combo_audio_codec.setCurrentIndex(idx_c)

        # Collect all audio candidates from all sources for secondary checkboxes
        all_audio_cands: List[StreamCandidate] = []
        if verdict.recommended_target_audio:
            all_audio_cands.append(verdict.recommended_target_audio)
        for alt in verdict.alternative_audios:
            if alt not in all_audio_cands:
                all_audio_cands.append(alt)
        if verdict.reference_audio and verdict.reference_audio not in all_audio_cands:
            all_audio_cands.append(verdict.reference_audio)

        # Populate Section 3 secondary audio checkboxes
        self._populate_secondary_checkboxes(all_audio_cands, verdict.recommended_target_audio)

        # Update acoustic audit card
        self._update_audio_audit()
        self.primary_audio_changed.emit(verdict.recommended_target_audio)

        # Set focus to confirm button for instant Enter activation
        self.btn_confirm.setFocus()

    def populate_stream_dropdowns(self, sources: List[MediaSourceInfo]) -> None:
        """
        Populates combo_video, combo_target_audio, and combo_ref_audio from media sources,
        attaching DropdownHighlightDelegate and ensuring origin containers are indicated.
        """
        if not self.current_verdict:
            return

        verdict = self.current_verdict

        # Video combo
        self.combo_video.blockSignals(True)
        self.combo_video.clear()
        v_cand = verdict.recommended_video
        self.combo_video.addItem(format_stream_item_text(v_cand), userData=v_cand)
        self.combo_video.setItemData(0, v_cand.summary_title(), Qt.ToolTipRole)
        for alt in verdict.alternative_videos:
            idx = self.combo_video.count()
            self.combo_video.addItem(format_stream_item_text(alt), userData=alt)
            self.combo_video.setItemData(idx, alt.summary_title(), Qt.ToolTipRole)
        self.combo_video.blockSignals(False)

        # Collect all audio candidates
        all_audio_cands: List[StreamCandidate] = []
        if verdict.recommended_target_audio:
            all_audio_cands.append(verdict.recommended_target_audio)
        for alt in verdict.alternative_audios:
            if alt not in all_audio_cands:
                all_audio_cands.append(alt)
        if verdict.reference_audio and verdict.reference_audio not in all_audio_cands:
            all_audio_cands.append(verdict.reference_audio)

        # Target audio combo
        self.combo_target_audio.blockSignals(True)
        self.combo_target_audio.clear()
        target_idx = 0
        for i, cand in enumerate(all_audio_cands):
            self.combo_target_audio.addItem(format_stream_item_text(cand), userData=cand)
            self.combo_target_audio.setItemData(i, cand.summary_title(), Qt.ToolTipRole)
            if verdict.recommended_target_audio and cand == verdict.recommended_target_audio:
                target_idx = i
        if self.combo_target_audio.count() > 0:
            self.combo_target_audio.setCurrentIndex(target_idx)
        self.combo_target_audio.blockSignals(False)

        # Reference audio combo
        self.combo_ref_audio.blockSignals(True)
        self.combo_ref_audio.clear()
        ref_idx = 0
        for i, cand in enumerate(all_audio_cands):
            self.combo_ref_audio.addItem(format_stream_item_text(cand), userData=cand)
            self.combo_ref_audio.setItemData(i, cand.summary_title(), Qt.ToolTipRole)
            if verdict.reference_audio and cand == verdict.reference_audio:
                ref_idx = i
        if self.combo_ref_audio.count() > 0:
            self.combo_ref_audio.setCurrentIndex(ref_idx)
        self.combo_ref_audio.blockSignals(False)

    def render_secondary_audio_item(self, badge_data: AudioQualityBadge) -> QWidget:
        """
        Renders a secondary audio stream item as a modular card composed of
        atomic micro-chips with continuous rounded geometry (border-radius: 999px).
        """
        card = QFrame()
        card.setObjectName(f"secondaryCard_{badge_data.track_id}")
        card.setProperty("class", "secondaryTrackCard")
        card.setStyleSheet("background: transparent; border: none;")
        card.setFixedHeight(34)
        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(10, 4, 12, 4)
        card_layout.setSpacing(6)

        chk = QCheckBox()
        chk.setObjectName(f"chkSecondary_{badge_data.track_id}")
        chk.setProperty("class", "chkSecondaryAudio")
        chk.setCursor(Qt.PointingHandCursor)
        chk.setChecked(badge_data.is_best_option)
        chk.toggled.connect(self._on_secondary_checkbox_toggled)
        card_layout.addWidget(chk)
        card.checkbox = chk

        for text in [
            badge_data.language,
            badge_data.brand_format,
            badge_data.channels_desc,
            badge_data.codec_name,
        ]:
            chip = QLabel(text)
            chip.setProperty("class", "atomicChip")
            chip.setFixedHeight(20)
            chip.setAlignment(Qt.AlignCenter)
            card_layout.addWidget(chip)

        sr_txt = f"{badge_data.sample_rate_hz:,} Hz".replace(",", ".") if badge_data.sample_rate_hz > 0 else "48.000 Hz"
        br_txt = f"{badge_data.bit_rate_kbps} kbps" if badge_data.bit_rate_kbps > 0 else "VBR"
        chip_specs = QLabel(f"{sr_txt} • {br_txt}")
        chip_specs.setProperty("class", "atomicChip")
        chip_specs.setFixedHeight(20)
        chip_specs.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(chip_specs)

        fname = elide_filename(badge_data.source_filename, max_chars=24)
        title_s = f" ({badge_data.title})" if badge_data.title else ""
        lbl_file = QLabel(f"{fname}{title_s} (Trilha #{badge_data.track_id})")
        lbl_file.setProperty("class", "hint")
        card_layout.addWidget(lbl_file)

        card_layout.addStretch()

        if badge_data.is_best_option:
            chip_best = QLabel("RECOMENDADO")
            chip_best.setProperty("class", "atomicChipBest")
            chip_best.setFixedHeight(20)
            chip_best.setAlignment(Qt.AlignCenter)
            card_layout.addWidget(chip_best)

        return card

    def _populate_secondary_checkboxes(
        self,
        all_audio_cands: List[StreamCandidate],
        target_cand: Optional[StreamCandidate]
    ) -> None:
        """Populates Section 3 of Review Gate with independent micro-chip cards for secondary audio tracks."""
        while self.secondary_layout.count():
            item = self.secondary_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        self.secondary_checkbox_items = []

        ref_cand = self.current_verdict.reference_audio if self.current_verdict else None

        eligible_cands = [
            cand for cand in all_audio_cands
            if not (target_cand and cand.file_path == target_cand.file_path and cand.stream.id == target_cand.stream.id)
        ]

        ranked = rank_secondary_audio_streams(eligible_cands)
        if ref_cand and not any(is_rec for _, is_rec in ranked):
            ranked = [
                (c, True if (c.file_path == ref_cand.file_path and c.stream.id == ref_cand.stream.id) else is_rec)
                for c, is_rec in ranked
            ]

        for cand, is_recommended in ranked:
            badge_data = build_audio_quality_badge(cand, is_recommended)
            item_widget = self.render_secondary_audio_item(badge_data)
            self.secondary_layout.addWidget(item_widget)
            chk = getattr(item_widget, "checkbox", None) or item_widget.findChild(QCheckBox)
            if chk:
                self.secondary_checkbox_items.append((chk, cand.file_path, cand.stream.id))

        if not self.secondary_checkbox_items:
            lbl_none = QLabel("Nenhuma faixa de áudio secundária detectada nas fontes.")
            lbl_none.setProperty("class", "hint")
            self.secondary_layout.addWidget(lbl_none)

    def _on_secondary_checkbox_toggled(self) -> None:
        """Syncs check_keep_original when secondary audio checkboxes are toggled."""
        ref_cand = self.current_verdict.reference_audio if self.current_verdict else None
        if ref_cand:
            for chk, f_path, track_id in self.secondary_checkbox_items:
                if f_path == ref_cand.file_path and track_id == ref_cand.stream.id:
                    self.check_keep_original.blockSignals(True)
                    self.check_keep_original.setChecked(chk.isChecked())
                    self.check_keep_original.blockSignals(False)
                    break

    def get_consolidated_selection(self) -> ConsolidatedStreamSelection:
        """Constructs ConsolidatedStreamSelection contract representing the user choices in the Review Gate."""
        v_cand = self.combo_video.currentData()
        t_cand = self.combo_target_audio.currentData()
        r_cand = self.combo_ref_audio.currentData()

        v_file = v_cand.file_path if v_cand else (self.loaded_files[0] if self.loaded_files else "")
        v_id = v_cand.stream.id if v_cand else 0

        t_file = t_cand.file_path if t_cand else (self.loaded_files[1] if len(self.loaded_files) > 1 else v_file)
        t_id = t_cand.stream.id if t_cand else 0

        r_file = r_cand.file_path if r_cand else None
        r_id = r_cand.stream.id if r_cand else None

        secondary_selections: List[Tuple[str, int, bool]] = []
        for chk, f_path, track_id in self.secondary_checkbox_items:
            secondary_selections.append((f_path, track_id, chk.isChecked()))

        if not secondary_selections and r_file:
            secondary_selections.append((r_file, r_id or 1, self.check_keep_original.isChecked()))

        return ConsolidatedStreamSelection(
            primary_video_file=v_file,
            primary_video_track_id=v_id,
            target_audio_file=t_file,
            target_audio_track_id=t_id,
            secondary_audio_selections=secondary_selections,
            ref_audio_file=r_file,
            ref_audio_track_id=r_id
        )

    def set_theme_mode(self, mode: str) -> None:
        """Passes theme mode update to internal components."""
        if hasattr(self, "inspector_view"):
            self.inspector_view.set_theme_mode(mode)

    def _on_combo_target_changed(self, index: int):
        cand = self.combo_target_audio.currentData()
        track_id = cand.stream.id if cand else index
        self.on_user_target_audio_changed(track_id)

    def _on_combo_ref_changed(self, index: int):
        cand = self.combo_ref_audio.currentData()
        track_id = cand.stream.id if cand else index
        self.on_user_ref_audio_changed(track_id)

    def on_user_target_audio_changed(self, selected_track_id: int) -> None:
        """Handles manual user selection of the target dubbing track."""
        curr_cand = self.combo_target_audio.currentData()
        if not curr_cand or curr_cand.stream.id != selected_track_id:
            for i in range(self.combo_target_audio.count()):
                c = self.combo_target_audio.itemData(i)
                if c and c.stream.id == selected_track_id:
                    self.combo_target_audio.blockSignals(True)
                    self.combo_target_audio.setCurrentIndex(i)
                    self.combo_target_audio.blockSignals(False)
                    break

        target_cand: Optional[StreamCandidate] = self.combo_target_audio.currentData()
        ref_cand: Optional[StreamCandidate] = self.combo_ref_audio.currentData()
        video_cand: Optional[StreamCandidate] = self.combo_video.currentData()

        if target_cand and video_cand:
            smart = determine_smart_defaults(video_cand.stream, target_cand.stream)
            self.check_pal_pitch.setChecked(smart.pal_pitch_restore)
            if smart.pal_badge_text:
                self.check_pal_pitch.setToolTip(smart.pal_badge_text)
            idx_c = self.combo_audio_codec.findData(smart.target_codec)
            if idx_c >= 0:
                self.combo_audio_codec.setCurrentIndex(idx_c)

        # Refresh secondary checkboxes to exclude the new target and include previous
        all_cands: List[StreamCandidate] = []
        for i in range(self.combo_target_audio.count()):
            c = self.combo_target_audio.itemData(i)
            if c and c not in all_cands:
                all_cands.append(c)
        if hasattr(self, "combo_ref_audio"):
            for i in range(self.combo_ref_audio.count()):
                c = self.combo_ref_audio.itemData(i)
                if c and c not in all_cands:
                    all_cands.append(c)
        self._populate_secondary_checkboxes(all_cands, target_cand)
        if target_cand and ref_cand and target_cand.file_path == ref_cand.file_path and target_cand.stream.id == ref_cand.stream.id:
            self.lbl_channel_alert.setText("[AVISO] Seleção conflitante: A faixa alvo de dublagem não pode ser idêntica à faixa de referência.")
            self.frame_channel_alert.setVisible(True)
            self.btn_confirm.setEnabled(False)
            self.update_role_badge(self.badge_a_status, "Conflito", is_amber=True)
            return

        self.btn_confirm.setEnabled(True)
        self.frame_channel_alert.setVisible(False)
        if self.current_verdict and self.current_verdict.recommended_target_audio and target_cand == self.current_verdict.recommended_target_audio:
            rec_badge, _ = format_audiophile_recommendation_badge(self.current_verdict.recommended_target_audio.stream)
            self.update_role_badge(self.badge_a_status, "Ajuste Manual" if self.current_verdict.is_ambiguous else rec_badge)
        else:
            self.update_role_badge(self.badge_a_status, "Seleção Manual")
        self._update_audio_audit()
        self.target_audio_changed.emit(selected_track_id)
        self.primary_audio_changed.emit(target_cand)

    def on_user_ref_audio_changed(self, selected_track_id: int) -> None:
        """Handles manual user selection of the reference audio track."""
        curr_cand = self.combo_ref_audio.currentData()
        if not curr_cand or curr_cand.stream.id != selected_track_id:
            for i in range(self.combo_ref_audio.count()):
                c = self.combo_ref_audio.itemData(i)
                if c and c.stream.id == selected_track_id:
                    self.combo_ref_audio.blockSignals(True)
                    self.combo_ref_audio.setCurrentIndex(i)
                    self.combo_ref_audio.blockSignals(False)
                    break

        target_cand: Optional[StreamCandidate] = self.combo_target_audio.currentData()
        ref_cand: Optional[StreamCandidate] = self.combo_ref_audio.currentData()
        if target_cand and ref_cand and target_cand.file_path == ref_cand.file_path and target_cand.stream.id == ref_cand.stream.id:
            self.lbl_channel_alert.setText("[AVISO] Seleção conflitante: A faixa de referência não pode ser idêntica à faixa alvo de dublagem.")
            self.frame_channel_alert.setVisible(True)
            self.btn_confirm.setEnabled(False)
            self.update_role_badge(self.badge_ref_status, "Conflito", is_amber=True)
            return

        self.btn_confirm.setEnabled(True)
        self.frame_channel_alert.setVisible(False)
        if self.current_verdict and self.current_verdict.reference_audio and ref_cand == self.current_verdict.reference_audio:
            self.update_role_badge(self.badge_ref_status, "Referência Fixa")
        else:
            self.update_role_badge(self.badge_ref_status, "Ref. Manual")
        self._update_audio_audit()
        self.ref_audio_changed.emit(selected_track_id)

    def update_channel_audit_tags(self, summary: StreamAuditSummary) -> None:
        """
        Updates the channel audit section with structured deduplicated atomic tags:
        - Container tag: summary.container
        - Immersive profile tag: summary.audio_profile
        - Channels tag: summary.channels
        - Codec tag: summary.codec
        - Frequency tag: summary.sample_rate
        - Bitrate tag: summary.bit_rate
        """
        if not summary:
            self.update_resulting_specs(None)
            return

        self.frame_audio_audit.setVisible(True)
        self.lbl_audit_origin.setText(summary.container)
        self.badge_audit_layout.setText(summary.audio_profile)
        if "ATMOS" in summary.audio_profile or "DTS:X" in summary.audio_profile:
            self.badge_audit_layout.setProperty("class", "badgeSignal")
        elif "5.1" in summary.channels or "7.1" in summary.channels or "SURROUND" in summary.audio_profile:
            self.badge_audit_layout.setProperty("class", "badgeGreen")
        else:
            self.badge_audit_layout.setProperty("class", "badgeNeutral")
        self.badge_audit_layout.setStyle(self.badge_audit_layout.style())

        spec_str = f"Codec: {summary.codec} • Canais: {summary.channels} • Frequência: {summary.sample_rate} • Taxa de Bits: {summary.bit_rate}"
        self.lbl_audit_specs.setText(spec_str)

        # Synchronize pills
        self.lbl_resulting_title.setText("Arquivo Resultante:")
        is_remux = "remux" in summary.container.lower() or "->" in summary.container
        self.pill_res_container.setText("MKV Remux" if is_remux else "MKV Matroska")
        self.pill_res_container.setProperty("class", "resultingSpecPill")
        self.pill_res_container.setStyle(self.pill_res_container.style())
        self.pill_res_container.setVisible(True)

        self.pill_res_mode.setText("Cópia Direta (Passthrough)")
        self.pill_res_mode.setProperty("class", "resultingSpecPill resultingPillGreen")
        self.pill_res_mode.setStyle(self.pill_res_mode.style())
        self.pill_res_mode.setVisible(True)

        self.pill_res_brand.setText(summary.audio_profile)
        brand_class = "resultingPillSignal" if ("ATMOS" in summary.audio_profile or "DTS:X" in summary.audio_profile) else "resultingPillGreen"
        self.pill_res_brand.setProperty("class", f"resultingSpecPill {brand_class}")
        self.pill_res_brand.setStyle(self.pill_res_brand.style())
        self.pill_res_brand.setVisible(True)

        self.pill_res_codec.setText(summary.codec.upper())
        self.pill_res_codec.setProperty("class", "resultingSpecPill")
        self.pill_res_codec.setStyle(self.pill_res_codec.style())
        self.pill_res_codec.setVisible(True)

        channels_num = 8 if "7.1" in summary.channels else (6 if "5.1" in summary.channels else 2)
        top, has_lfe = decompose_channel_topology(channels_num, summary.channels)
        self.pill_res_channels.setText(top)
        self.pill_res_channels.setProperty("class", "resultingSpecPill")
        self.pill_res_channels.setStyle(self.pill_res_channels.style())
        self.pill_res_channels.setVisible(True)

        self.pill_res_rate.setText(summary.sample_rate)
        self.pill_res_rate.setProperty("class", "resultingSpecPill")
        self.pill_res_rate.setStyle(self.pill_res_rate.style())
        self.pill_res_rate.setVisible(True)

        self.pill_res_bitrate.setText(summary.bit_rate)
        self.pill_res_bitrate.setProperty("class", "resultingSpecPill")
        self.pill_res_bitrate.setStyle(self.pill_res_bitrate.style())
        self.pill_res_bitrate.setVisible(True)

        self.resulting_audio_specs = {
            "container": self.pill_res_container.text(),
            "mode": self.pill_res_mode.text(),
            "branding": summary.audio_profile,
            "codec": summary.codec.upper(),
            "channel_layout": top,
            "sample_rate": summary.sample_rate,
            "bitrate": summary.bit_rate,
            "is_passthrough": True,
            "has_lfe": has_lfe,
        }

    def update_channel_audit_summary(self, primary_audio: Any, container_format: str = "mkv") -> None:
        """
        Updates the structured technical audit block in real time:
        - Container badge: 'MKV Nativo' or '<FMT> -> MKV Remux'
        - Immersive profile badge: 'DOLBY ATMOS', 'DOLBY AUDIO 5.1', etc.
        - Unified specification label: 'Codec: <CODEC> • Canais: <LAYOUT> • Frequência: <HZ> Hz • Taxa de Bits: <KBPS> kbps'
        """
        if not primary_audio:
            self.update_resulting_specs(None)
            return
        self.update_resulting_specs(primary_audio, {"container": container_format})

    def update_resulting_specs(self, track_info: Any = None, remux_options: Optional[dict] = None) -> dict:
        """
        Public contract consolidating and displaying technical specifications of the resulting output file:
        - Container format badge (e.g. 'MKV Matroska' or 'MKV Remux')
        - Processing mode badge ('Cópia Direta (Passthrough)' or 'Re-encode [CODEC] (PAL 24fps)')
        - Commercial branding badge ('DOLBY ATMOS', 'DOLBY AUDIO 5.1', 'DTS-HD MA 7.1', etc.)
        - Exact Codec in uppercase ('AC-3', 'E-AC-3', 'TRUEHD', 'DTS-HD MA', 'FLAC', etc.)
        - Decomposed channel topology ('5.1 Surround (+Subwoofer)', '7.1 Atmos (Surround + Height + Sub)', etc.)
        - Sample rate formatted ('48.000 Hz')
        - Bitrate formatted ('640 kbps', '3500 kbps', or 'Bitrate Variável (VBR)')

        Returns the resulting specification dictionary and updates all UI pill badges synchronously.
        """
        if remux_options is None:
            remux_options = {}

        if "pal_pitch" not in remux_options and hasattr(self, "check_pal_pitch"):
            remux_options["pal_pitch"] = self.check_pal_pitch.isChecked()
        if "audio_codec" not in remux_options and hasattr(self, "combo_audio_codec"):
            remux_options["audio_codec"] = self.combo_audio_codec.currentData()
        if "video_file_path" not in remux_options and hasattr(self, "combo_video"):
            video_cand = self.combo_video.currentData()
            if video_cand:
                remux_options["video_file_path"] = getattr(video_cand, "file_path", "")

        # Fallback to combo_target_audio if track_info is None
        cand_file_path = ""
        if track_info is None:
            if hasattr(self, "combo_target_audio") and self.combo_target_audio.currentData():
                cand = self.combo_target_audio.currentData()
                cand_file_path = getattr(cand, "file_path", "")
                stream = getattr(cand, "stream", cand)
            else:
                stream = None
        elif isinstance(track_info, dict):
            cand_file_path = track_info.get("file_path", "")
            stream = track_info
        elif hasattr(track_info, "stream"):
            cand_file_path = getattr(track_info, "file_path", "")
            stream = track_info.stream
        else:
            stream = track_info
            cand_file_path = getattr(track_info, "file_path", "")

        if not stream:
            self.frame_audio_audit.setVisible(True)
            self.lbl_resulting_title.setText("Arquivo Resultante:")
            self.pill_res_container.setText("Nenhum áudio selecionado")
            self.pill_res_container.setProperty("class", "resultingSpecPill resultingPillNeutral")
            self.pill_res_container.setStyle(self.pill_res_container.style())
            self.pill_res_container.setVisible(True)
            self.pill_res_mode.setVisible(False)
            self.pill_res_brand.setVisible(False)
            self.pill_res_codec.setVisible(False)
            self.pill_res_channels.setVisible(False)
            self.pill_res_rate.setVisible(False)
            self.pill_res_bitrate.setVisible(False)
            self.lbl_audit_origin.setText("Nenhum áudio selecionado")
            self.badge_audit_layout.setText("")
            self.lbl_audit_specs.setText("")
            fallback_dict = {
                "container": "Nenhum áudio selecionado",
                "mode": "N/D",
                "branding": "N/D",
                "codec": "N/D",
                "channel_layout": "N/D",
                "sample_rate": "N/D",
                "bitrate": "N/D",
                "is_passthrough": True,
                "has_lfe": False,
            }
            self.resulting_audio_specs = fallback_dict
            return fallback_dict

        # Extract audio stream properties
        if isinstance(stream, dict):
            raw_codec = stream.get("codec", "audio")
            channels = int(stream.get("channels", 2) or 2)
            channel_layout = stream.get("channel_layout", "")
            sample_rate = stream.get("sample_rate", 48000)
            bitrate = stream.get("bitrate", stream.get("bit_rate"))
            is_immersive = stream.get("is_immersive", False)
            spatial_label = stream.get("spatial_label", "")
            title = stream.get("title", "")
            container_fmt = stream.get("container", stream.get("container_format", "mkv"))
        else:
            raw_codec = getattr(stream, "codec", "audio") or "audio"
            channels = int(getattr(stream, "channels", 2) or 2)
            channel_layout = getattr(stream, "channel_layout", "") or ""
            sample_rate = getattr(stream, "sample_rate", 48000) or 48000
            bitrate = getattr(stream, "bitrate", getattr(stream, "bit_rate", None))
            is_immersive = getattr(stream, "is_immersive", False) or False
            spatial_label = getattr(stream, "spatial_label", "") or ""
            title = getattr(stream, "title", "") or ""
            container_fmt = getattr(stream, "container_format", getattr(stream, "container", "mkv")) or "mkv"

        # Container & remux origin
        container_opt = remux_options.get("container", container_fmt)
        fmt = (container_opt or "mkv").upper().lstrip(".")
        video_path = remux_options.get("video_file_path", "")
        if not video_path and hasattr(self, "combo_video"):
            vc = self.combo_video.currentData()
            if vc:
                video_path = getattr(vc, "file_path", "")

        is_hybrid = (fmt != "MKV") or (bool(video_path) and bool(cand_file_path) and cand_file_path != video_path)

        if fmt == "MKV" and not is_hybrid:
            container_pill_text = "MKV Matroska"
            origin_compat_text = f"{fmt} Nativo"
            origin_compat_class = "badgeNeutral"
        else:
            container_pill_text = "MKV Remux"
            origin_compat_text = f"{fmt} -> MKV Remux"
            origin_compat_class = "badgeAmber" if fmt != "MKV" else "badgeNeutral"

        # Processing Mode & PAL Pitch Restore
        pal_pitch = bool(remux_options.get("pal_pitch", False))
        target_codec_opt = str(remux_options.get("audio_codec", "flac") or "flac").lower()

        if pal_pitch:
            reencode_badge = target_codec_opt.upper()
            mode_pill_text = f"Re-encode {reencode_badge} (PAL 24fps)"
            mode_class = "resultingPillAmber"
            is_passthrough = False
            resulting_codec = reencode_badge
        else:
            mode_pill_text = "Cópia Direta (Passthrough)"
            mode_class = "resultingPillGreen"
            is_passthrough = True
            c_up = str(raw_codec).upper()
            if "EAC3" in c_up or "EC3" in c_up:
                resulting_codec = "E-AC-3"
            elif "AC3" in c_up:
                resulting_codec = "AC-3"
            elif "TRUEHD" in c_up:
                resulting_codec = "TRUEHD"
            elif "DTS" in c_up:
                t_low = str(title).lower()
                if "dts-hd ma" in t_low or "dtshd" in c_up.lower():
                    resulting_codec = "DTS-HD MA"
                elif "dts:x" in t_low or "dtsx" in c_up.lower():
                    resulting_codec = "DTS:X"
                else:
                    resulting_codec = "DTS"
            elif "FLAC" in c_up:
                resulting_codec = "FLAC"
            elif "OPUS" in c_up:
                resulting_codec = "OPUS"
            elif "AAC" in c_up:
                resulting_codec = "AAC"
            else:
                resulting_codec = c_up

        # Commercial Branding
        if hasattr(stream, "get_immersive_profile_label"):
            branding = stream.get_immersive_profile_label()
        else:
            branding = format_commercial_branding(
                codec=raw_codec,
                channels=channels,
                channel_layout=channel_layout,
                is_immersive=is_immersive,
                title=title,
                spatial_label=spatial_label,
            )

        if pal_pitch and target_codec_opt == "flac":
            branding_pill = "FLAC LOSSLESS"
        elif pal_pitch and target_codec_opt == "opus":
            branding_pill = "OPUS"
        else:
            branding_pill = branding

        if "ATMOS" in branding_pill or "DTS:X" in branding_pill:
            branding_class = "resultingPillSignal"
        elif any(k in branding_pill for k in ("5.1", "7.1", "SURROUND", "DOLBY AUDIO", "DTS")):
            branding_class = "resultingPillGreen"
        else:
            branding_class = "resultingPillNeutral"

        # Channel topology decomposed
        channel_topology, has_lfe = decompose_channel_topology(
            channels=channels,
            channel_layout=channel_layout,
            is_immersive=is_immersive,
            spatial_label=spatial_label
        )

        # Sample rate
        if isinstance(sample_rate, str) and "hz" in sample_rate.lower():
            sr_formatted = sample_rate
        else:
            try:
                sr_num = int(sample_rate) if sample_rate else 48000
                sr_formatted = f"{sr_num:,} Hz".replace(",", ".")
            except (ValueError, TypeError):
                sr_formatted = "48.000 Hz"

        # Bitrate
        if isinstance(bitrate, str) and ("kbps" in bitrate.lower() or "vbr" in bitrate.lower() or "n/a" in bitrate.lower()):
            bitrate_str = bitrate
        elif pal_pitch and target_codec_opt == "flac":
            bitrate_str = "Bitrate Variável (VBR)"
        elif bitrate and int(bitrate) > 0:
            b_val = int(bitrate)
            kbps = int(round(b_val / 1000.0)) if b_val > 5000 else b_val
            bitrate_str = f"{kbps} kbps"
        else:
            bitrate_str = "Bitrate Variável (VBR)" if not is_passthrough else "N/A"

        # Update visual pills
        self.frame_audio_audit.setVisible(True)
        self.lbl_resulting_title.setText("Arquivo Resultante:")

        self.pill_res_container.setVisible(True)
        self.pill_res_container.setText(container_pill_text)
        self.pill_res_container.setProperty("class", "resultingSpecPill")
        self.pill_res_container.setStyle(self.pill_res_container.style())

        self.pill_res_mode.setVisible(True)
        self.pill_res_mode.setText(mode_pill_text)
        self.pill_res_mode.setProperty("class", f"resultingSpecPill {mode_class}")
        self.pill_res_mode.setStyle(self.pill_res_mode.style())

        self.pill_res_brand.setVisible(True)
        self.pill_res_brand.setText(branding_pill)
        self.pill_res_brand.setProperty("class", f"resultingSpecPill {branding_class}")
        self.pill_res_brand.setStyle(self.pill_res_brand.style())

        self.pill_res_codec.setVisible(True)
        self.pill_res_codec.setText(resulting_codec)
        self.pill_res_codec.setProperty("class", "resultingSpecPill")
        self.pill_res_codec.setStyle(self.pill_res_codec.style())

        self.pill_res_channels.setVisible(True)
        self.pill_res_channels.setText(channel_topology)
        self.pill_res_channels.setProperty("class", "resultingSpecPill")
        self.pill_res_channels.setStyle(self.pill_res_channels.style())

        self.pill_res_rate.setVisible(True)
        self.pill_res_rate.setText(sr_formatted)
        self.pill_res_rate.setProperty("class", "resultingSpecPill")
        self.pill_res_rate.setStyle(self.pill_res_rate.style())

        self.pill_res_bitrate.setVisible(True)
        self.pill_res_bitrate.setText(bitrate_str)
        self.pill_res_bitrate.setProperty("class", "resultingSpecPill")
        self.pill_res_bitrate.setStyle(self.pill_res_bitrate.style())

        # Update compatibility labels
        compat_codec = resulting_codec
        if compat_codec == "TRUEHD":
            compat_codec = "TrueHD"

        self.lbl_audit_origin.setText(origin_compat_text)
        self.lbl_audit_origin.setProperty("class", origin_compat_class)
        self.lbl_audit_origin.setStyle(self.lbl_audit_origin.style())

        self.badge_audit_layout.setText(branding)
        if "ATMOS" in branding or "DTS:X" in branding:
            self.badge_audit_layout.setProperty("class", "badgeSignal")
        elif "5.1" in str(channels) or "7.1" in str(channels) or "SURROUND" in branding:
            self.badge_audit_layout.setProperty("class", "badgeGreen")
        else:
            self.badge_audit_layout.setProperty("class", "badgeNeutral")
        self.badge_audit_layout.setStyle(self.badge_audit_layout.style())

        layout_lbl = spatial_label or format_channel_layout_label(channels, channel_layout)
        spec_br = bitrate_str if bitrate_str != "Bitrate Variável (VBR)" else "N/A"
        if bitrate and int(bitrate if not isinstance(bitrate, str) else 1) > 0:
            spec_br = bitrate_str
        self.lbl_audit_specs.setText(
            f"Codec: {compat_codec} • Canais: {layout_lbl} • Frequência: {sr_formatted} • Taxa de Bits: {spec_br}"
        )

        res_dict = {
            "container": container_pill_text,
            "mode": mode_pill_text,
            "branding": branding_pill,
            "codec": resulting_codec,
            "channel_layout": channel_topology,
            "sample_rate": sr_formatted,
            "bitrate": bitrate_str,
            "is_passthrough": is_passthrough,
            "has_lfe": has_lfe,
        }
        self.resulting_audio_specs = res_dict
        return res_dict

    def _update_audio_audit(self):
        """Updates acoustic audit badges and contextual channel warnings based on combo selection."""
        target_cand: Optional[StreamCandidate] = self.combo_target_audio.currentData() if hasattr(self, "combo_target_audio") else None
        ref_cand: Optional[StreamCandidate] = self.combo_ref_audio.currentData() if hasattr(self, "combo_ref_audio") else None

        if not target_cand:
            self.update_resulting_specs(None)
            self.frame_channel_alert.setVisible(False)
            return

        tgt_stream = target_cand.stream
        tgt_fmt = getattr(tgt_stream, "container_format", None) or (
            os.path.splitext(target_cand.file_path)[1].replace(".", "") if target_cand.file_path else "mkv"
        )
        self.update_resulting_specs(target_cand, {"container": tgt_fmt})

        # Contextual Channel Difference Alert
        if target_cand and ref_cand and target_cand.file_path == ref_cand.file_path and target_cand.stream.id == ref_cand.stream.id:
            return

        layout_text = tgt_stream.spatial_label or format_channel_layout_label(tgt_stream.channels, tgt_stream.channel_layout)
        if tgt_stream.channels in (1, 2) and ref_cand and ref_cand.stream.channels >= 6:
            ref_layout = ref_cand.stream.spatial_label or format_channel_layout_label(ref_cand.stream.channels, ref_cand.stream.channel_layout)
            self.lbl_channel_alert.setText(
                f"[INFO] {layout_text} identificado na dublagem; áudio original em inglês possui {ref_layout} ({ref_cand.stream.channels} canais)."
            )
            self.frame_channel_alert.setVisible(True)
        else:
            self.frame_channel_alert.setVisible(False)

    def _on_confirm_clicked(self):
        chosen_video = self.combo_video.currentData()
        chosen_target = self.combo_target_audio.currentData()
        chosen_ref = self.combo_ref_audio.currentData()
        keep_orig = self.check_keep_original.isChecked()

        if not chosen_video and self.current_verdict:
            chosen_video = self.current_verdict.recommended_video
        if not chosen_target and self.current_verdict:
            chosen_target = self.current_verdict.recommended_target_audio
        if not chosen_ref and self.current_verdict:
            chosen_ref = self.current_verdict.reference_audio

        # Fallback: if verdict was not ready but files are loaded, evaluate them
        if (not chosen_video or not chosen_target) and len(self.loaded_files) >= 2:
            try:
                from ...core.inspector import evaluate_media_streams
                verdict = evaluate_media_streams(self.loaded_files[0], self.loaded_files[1], *self.loaded_files[2:])
                self.set_verdict(verdict)
                chosen_video = self.combo_video.currentData() or verdict.recommended_video
                chosen_target = self.combo_target_audio.currentData() or verdict.recommended_target_audio
                chosen_ref = self.combo_ref_audio.currentData() or verdict.reference_audio
            except Exception as err:
                logger.error("Failed to auto-evaluate media streams on confirmation: %s", err)

        if chosen_video and chosen_target:
            self.confirmation_confirmed.emit(chosen_video, chosen_target, chosen_ref, keep_orig)

    def _on_revert_arbitration_toggled(self, checked: bool):
        if not self.current_verdict or not self.current_verdict.arbitration_result:
            return
        if checked:
            # Revert target audio combo to internal base video audio stream if available
            base_file = self.current_verdict.recommended_video.file_path
            target_idx = None
            for i in range(self.combo_target_audio.count()):
                cand = self.combo_target_audio.itemData(i)
                if cand and cand.file_path == base_file and cand.stream.track_type == "audio":
                    lang = (cand.stream.language or "").lower()
                    if lang in PORTUGUESE_TAGS or any(kw in (cand.stream.title or "").lower() for kw in PORTUGUESE_KEYWORDS):
                        target_idx = i
                        break
            if target_idx is not None:
                self.combo_target_audio.setCurrentIndex(target_idx)
        else:
            # Restore recommended external target
            if self.current_verdict.recommended_target_audio:
                idx = self.combo_target_audio.findData(self.current_verdict.recommended_target_audio)
                if idx >= 0:
                    self.combo_target_audio.setCurrentIndex(idx)

    def get_discarded_audio_ids(self) -> List[int]:
        """Returns list of stream IDs from base video file to discard during remuxing."""
        if not self.current_verdict or not self.current_verdict.arbitration_result:
            return []
        if self.check_revert_arbitration.isChecked():
            return []
        return list(self.current_verdict.arbitration_result.discarded_audio_ids)

    def configure_stream_row(
        self,
        track_id: str,
        role_badge: str,
        description: str,
        action_chip: str,
        combo: Optional[QComboBox] = None
    ) -> QWidget:
        """
        Configures a structured two-level stream row (.trk / .trk.rec):
        - Upper line: rounded identifier (.tid), dynamic auto-fit role badge, and action chip (.tag / .tag.n).
        - Lower line: Technical description or embedded stream combo selector.
        """
        row_frame = QFrame()
        is_rec = action_chip in ("Align", "Sincronizar e Alinhar") or "Recomendado" in role_badge or "RECOMENDADA" in role_badge
        row_frame.setProperty("recommended", "true" if is_rec else "false")
        row_frame.setProperty("class", "trackRow" + (" trackRowRec" if is_rec else ""))
        rf_layout = QVBoxLayout(row_frame)
        rf_layout.setContentsMargins(14, 8, 14, 8)
        rf_layout.setSpacing(6)

        # Upper line
        top_line = QHBoxLayout()
        top_line.setSpacing(10)
        top_line.setContentsMargins(0, 0, 0, 0)

        lbl_id = QLabel(track_id)
        lbl_id.setProperty("class", "trackIdBox")
        lbl_id.setProperty("recommended", "true" if is_rec else "false")
        fm_id = lbl_id.fontMetrics()
        id_w = max(38, fm_id.horizontalAdvance(track_id) + 12)
        lbl_id.setMinimumWidth(id_w)
        lbl_id.setFixedHeight(32)
        lbl_id.setAlignment(Qt.AlignCenter)
        top_line.addWidget(lbl_id)

        badge = QLabel(role_badge)
        badge.setProperty("class", "roleBadge")
        badge.setStyleSheet(self.get_role_badge_style(role_badge))
        badge.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        fm = badge.fontMetrics()
        badge_w = fm.horizontalAdvance(role_badge) + 20
        badge.setMinimumWidth(max(badge_w, 80))
        badge.setAlignment(Qt.AlignCenter)
        top_line.addWidget(badge)

        top_line.addStretch()

        chip = QLabel(action_chip)
        chip.setProperty("class", "streamActionChip")
        chip.setStyleSheet(self.get_action_chip_style(action_chip))
        fm_chip = chip.fontMetrics()
        chip_w = max(68, fm_chip.horizontalAdvance(action_chip) + 20)
        chip.setMinimumWidth(chip_w)
        chip.setAlignment(Qt.AlignCenter)
        top_line.addWidget(chip)

        rf_layout.addLayout(top_line)

        # Lower line
        if combo is not None:
            combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            combo.setProperty("class", "streamCombo")
            rf_layout.addWidget(combo)
            row_frame.combo = combo
        else:
            lbl_desc = QLabel(description)
            lbl_desc.setProperty("class", "streamDesc")
            lbl_desc.setWordWrap(True)
            rf_layout.addWidget(lbl_desc)
            row_frame.lbl_desc = lbl_desc

        row_frame.lbl_id = lbl_id
        row_frame.badge = badge
        row_frame.chip = chip
        return row_frame

    def reset_to_recommended_state(self) -> None:
        """
        Resets track selectors, flags and audio codec back to the initial deterministic recommendation.
        """
        if not self.current_verdict:
            return

        target_track_id = -1
        ref_track_id = -1

        if self.current_verdict.recommended_video:
            for i in range(self.combo_video.count()):
                cand = self.combo_video.itemData(i)
                if cand and cand.stream.id == self.current_verdict.recommended_video.stream.id and cand.file_path == self.current_verdict.recommended_video.file_path:
                    self.combo_video.setCurrentIndex(i)
                    break

        if self.current_verdict.recommended_target_audio:
            target_track_id = self.current_verdict.recommended_target_audio.stream.id
            for i in range(self.combo_target_audio.count()):
                cand = self.combo_target_audio.itemData(i)
                if cand and cand.stream.id == target_track_id and cand.file_path == self.current_verdict.recommended_target_audio.file_path:
                    self.combo_target_audio.setCurrentIndex(i)
                    break

        if self.current_verdict.reference_audio:
            ref_track_id = self.current_verdict.reference_audio.stream.id
            for i in range(self.combo_ref_audio.count()):
                cand = self.combo_ref_audio.itemData(i)
                if cand and cand.stream.id == ref_track_id and cand.file_path == self.current_verdict.reference_audio.file_path:
                    self.combo_ref_audio.setCurrentIndex(i)
                    break

        if hasattr(self, "check_revert_arbitration"):
            self.check_revert_arbitration.setChecked(False)
        self.check_keep_original.setChecked(True)

        if self.current_verdict.recommended_video and self.current_verdict.recommended_target_audio:
            smart = determine_smart_defaults(
                self.current_verdict.recommended_video.stream,
                self.current_verdict.recommended_target_audio.stream
            )
            self.check_pal_pitch.setChecked(smart.pal_pitch_restore)
            if smart.pal_badge_text:
                self.check_pal_pitch.setToolTip(smart.pal_badge_text)
            idx_c = self.combo_audio_codec.findData(smart.target_codec)
            if idx_c >= 0:
                self.combo_audio_codec.setCurrentIndex(idx_c)

        self._update_audio_audit()
        self.btn_confirm.setEnabled(True)
        self.btn_confirm.setToolTip("")
        self.lbl_channel_alert.setText("")
        self.frame_channel_alert.setVisible(False)

        if target_track_id >= 0:
            self.target_audio_changed.emit(target_track_id)
            if self.current_verdict:
                self.primary_audio_changed.emit(self.current_verdict.recommended_target_audio)
        if ref_track_id >= 0:
            self.ref_audio_changed.emit(ref_track_id)

    def reset_to_recommended(self) -> None:
        """Alias for reset_to_recommended_state for public contract compliance."""
        self.reset_to_recommended_state()

    @property
    def btn_run(self) -> QPushButton:
        """Primary action trigger alias."""
        return self.btn_confirm

    def get_review_state(self) -> StreamReviewState:
        """Constructs a snapshot contract representing the user-configured stream selection state."""
        v_cand: Optional[StreamCandidate] = self.combo_video.currentData()
        t_cand: Optional[StreamCandidate] = self.combo_target_audio.currentData()
        r_cand: Optional[StreamCandidate] = self.combo_ref_audio.currentData()

        v_id = v_cand.stream.id if v_cand and v_cand.stream else 0
        t_id = t_cand.stream.id if t_cand and t_cand.stream else 0
        r_id = r_cand.stream.id if r_cand and r_cand.stream else 0

        is_customized = False
        if self.current_verdict:
            rec_v = self.current_verdict.recommended_video
            rec_t = self.current_verdict.recommended_target_audio
            rec_r = self.current_verdict.reference_audio
            if (rec_v and rec_v.stream and rec_v.stream.id != v_id) or \
               (rec_t and rec_t.stream and rec_t.stream.id != t_id) or \
               (rec_r and rec_r.stream and rec_r.stream.id != r_id):
                is_customized = True

        return StreamReviewState(
            selected_video_id=v_id,
            selected_target_audio_id=t_id,
            selected_ref_audio_id=r_id,
            pal_restore_enabled=self.check_pal_pitch.isChecked(),
            target_codec=self.combo_audio_codec.currentData() or "aac",
            is_customized=is_customized
        )

    def update_role_badge(self, badge: QLabel, text: str, is_amber: bool = False) -> None:
        """Sets role badge text and recalculates dynamic auto-fit width to prevent truncation."""
        badge.setText(text)
        badge.setProperty("class", "badgeAmber" if is_amber else "roleBadge")
        badge.setStyleSheet(self.get_role_badge_style(text))
        badge.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        fm = badge.fontMetrics()
        w = fm.horizontalAdvance(text) + 24
        badge.setMinimumWidth(max(w, 88))
        badge.setAlignment(Qt.AlignCenter)
        st = badge.style()
        if st:
            st.unpolish(badge)
            st.polish(badge)
        badge.update()

    def get_role_badge_style(self, role_type: str) -> str:
        """Returns CSS/QSS styling string for stream role classification badges."""
        return get_role_badge_style(role_type)

    def get_action_chip_style(self, action_type: str) -> str:
        """Returns CSS/QSS styling string for stream action/state chips (Copy, Align)."""
        return get_action_chip_style(action_type)

    def update_dropzone_state(self, has_files: bool) -> None:
        """Updates dropzone geometry and height dynamically based on file ingestion state."""
        if has_files:
            self.setMaximumHeight(16777215)
            self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
            if hasattr(self, "page_empty"):
                self.page_empty.setMaximumHeight(16777215)
        else:
            self.setMaximumHeight(240)
            self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
            if hasattr(self, "page_empty"):
                self.page_empty.setMaximumHeight(240)

    def reset(self):
        """Resets the drop zone to initial standby state."""
        self.loaded_files = []
        self.current_verdict = None
        self.lbl_v_filename.setText("video_ref.mkv")
        self.lbl_v_meta.setText("0.0 GB  •  00:00:00")
        self.lbl_a_filename.setText("audio_dub.mp4")
        if hasattr(self, "dynamic_source_cards"):
            for card in self.dynamic_source_cards:
                if hasattr(self, "sources_layout"):
                    self.sources_layout.removeWidget(card)
                card.setParent(None)
                card.deleteLater()
            self.dynamic_source_cards = []
        if hasattr(self, "card_file_a"):
            self.card_file_a.setVisible(True)
        if hasattr(self, "lbl_v_role"):
            self.lbl_v_role.setText("Referência de vídeo")
        if hasattr(self, "lbl_a_role"):
            self.lbl_a_role.setText("Áudio dublado")
        self.update_source_count_badge(0)
        self.combo_video.clear()
        self.combo_target_audio.clear()
        self.combo_ref_audio.clear()
        self.update_role_badge(self.badge_v_status, "Melhor Imagem")
        self.update_role_badge(self.badge_a_status, "Português Oficial")
        self.update_role_badge(self.badge_ref_status, "Referência Fixa")
        for ch, txt in [
            (self.chip_v_act, "Vídeo Intocado (Cópia Direta)"),
            (self.chip_a_act, "Sincronizar e Alinhar"),
            (self.chip_ref_act, "Manter como Secundária")
        ]:
            ch.setText(txt)
            ch.setMinimumWidth(max(68, ch.fontMetrics().horizontalAdvance(txt) + 20))
        if self.inspection_worker and self.inspection_worker.isRunning():
            self.inspection_worker.cancel()
        if hasattr(self, "secondary_layout"):
            while self.secondary_layout.count():
                item = self.secondary_layout.takeAt(0)
                w = item.widget()
                if w:
                    w.deleteLater()
        self.secondary_checkbox_items = []
        self.frame_ambiguity.setVisible(False)
        self.frame_arbitration.setVisible(False)
        self.frame_audio_audit.setVisible(False)
        self.frame_channel_alert.setVisible(False)
        self.update_dropzone_state(False)
        self.stack.setCurrentIndex(0)
        self.primary_audio_changed.emit(None)
        self.reset_requested.emit()

