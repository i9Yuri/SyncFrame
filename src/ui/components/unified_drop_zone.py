"""Unified drag-and-drop ingestion zone with hierarchical confirmation table and acoustic auditing."""

import os
from typing import List, Optional, Tuple

from PySide6.QtCore import Qt, Signal
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
from ...core.models import AutoMatchVerdict, StreamCandidate, format_channel_layout_label, MediaSourceInfo
from ...core.inspector import (
    PORTUGUESE_TAGS,
    PORTUGUESE_KEYWORDS,
    format_audiophile_recommendation_badge,
    format_audiophile_discard_notice
)
from ..style import get_role_badge_style, get_action_chip_style
from .audio_preserve_checkbox import AudioPreserveCheckbox


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


class UnifiedDropZone(QFrame):
    """
    Unified ingestion zone supporting:
    - Drag & drop of 1 or 2 files simultaneously (.mkv, .mp4, .m4v, .mov).
    - Single system file picker for selecting both media files.
    - Paired horizontal subcards for video and dubbed audio sources.
    - Clean tabular Review Gate with pre-selected streams, acoustic channel audit, and composition options.
    """
    files_ready = Signal(str, str)
    confirmation_confirmed = Signal(object, object, object, bool)  # (video_cand, target_cand, ref_cand, keep_orig)
    target_audio_changed = Signal(int)
    ref_audio_changed = Signal(int)
    reset_requested = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("bentoCard")
        self.setProperty("class", "bentoCard")
        self.setAcceptDrops(True)

        self.loaded_files: List[str] = []
        self.current_verdict: Optional[AutoMatchVerdict] = None

        self.init_ui()

    def init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(18, 16, 18, 16)
        root_layout.setSpacing(12)

        self.stack = QStackedWidget()

        # ======================================================================
        # Page 0: Standby / Empty Drop Zone (Card 01 - Unified Drop Zone)
        # ======================================================================
        self.page_empty = QFrame()
        self.page_empty.setObjectName("dropFrameEmpty")
        empty_layout = QVBoxLayout(self.page_empty)
        empty_layout.setAlignment(Qt.AlignCenter)
        empty_layout.setSpacing(10)
        empty_layout.setContentsMargins(20, 24, 20, 24)

        tag_row = QHBoxLayout()
        tag_row.setAlignment(Qt.AlignCenter)
        tag_ingest = QLabel("01  INGESTÃO DE FONTES")
        tag_ingest.setProperty("class", "systemChip")
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
        btn_browse.setProperty("class", "btnPrimary")
        btn_browse.setMinimumWidth(160)
        btn_browse.setMaximumWidth(220)
        btn_browse.clicked.connect(self._open_file_dialog)
        empty_layout.addWidget(btn_browse, alignment=Qt.AlignCenter)

        self.stack.addWidget(self.page_empty)

        # ======================================================================
        # Page 1: 1 File Ingested (Awaiting Second File)
        # ======================================================================
        self.page_single = QFrame()
        self.page_single.setObjectName("dropFrameSingle")
        single_layout = QVBoxLayout(self.page_single)
        single_layout.setAlignment(Qt.AlignCenter)
        single_layout.setSpacing(10)
        single_layout.setContentsMargins(20, 20, 20, 20)

        self.badge_waiting = QLabel("1 de 2 arquivos carregados — Aguardando segundo arquivo")
        self.badge_waiting.setProperty("class", "badgeAmber")
        single_layout.addWidget(self.badge_waiting, alignment=Qt.AlignCenter)

        self.lbl_single_filename = QLabel("")
        self.lbl_single_filename.setProperty("class", "monoValue")
        self.lbl_single_filename.setAlignment(Qt.AlignCenter)
        single_layout.addWidget(self.lbl_single_filename)

        lbl_single_instruction = QLabel("Arraste a segunda fonte aqui ou selecione manualmente:")
        lbl_single_instruction.setProperty("class", "subText")
        lbl_single_instruction.setAlignment(Qt.AlignCenter)
        single_layout.addWidget(lbl_single_instruction)

        btn_row = QHBoxLayout()
        btn_row.setAlignment(Qt.AlignCenter)
        btn_row.setSpacing(10)

        btn_browse_second = QPushButton("Adicionar Segundo Arquivo...")
        btn_browse_second.setProperty("class", "btnPrimary")
        btn_browse_second.clicked.connect(self._open_single_file_dialog)
        btn_row.addWidget(btn_browse_second)

        btn_reset_single = QPushButton("Limpar")
        btn_reset_single.setProperty("class", "btnSecondary")
        btn_reset_single.clicked.connect(self.reset)
        btn_row.addWidget(btn_reset_single)

        single_layout.addLayout(btn_row)
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
        bs_layout.setContentsMargins(22, 22, 22, 22)
        bs_layout.setSpacing(14)

        # Header with Card title, sources count tag and Change button
        conf_header = QHBoxLayout()
        conf_header.setSpacing(10)

        conf_title = QLabel("Fontes ingeridas")
        conf_title.setProperty("class", "cardTitle")
        conf_header.addWidget(conf_title)
        conf_header.addStretch()

        self.chip_sources_count = QLabel("2 / 2 fontes")
        self.chip_sources_count.setProperty("class", "tagNeutral")
        conf_header.addWidget(self.chip_sources_count)

        btn_change_files = QPushButton("Trocar arquivos")
        btn_change_files.setProperty("class", "btnSm")
        btn_change_files.clicked.connect(self.reset)
        conf_header.addWidget(btn_change_files)
        bs_layout.addLayout(conf_header)

        # Paired Horizontal File Cards (.pair)
        pair_row = QHBoxLayout()
        pair_row.setSpacing(10)

        # File Card: Video Reference (.file)
        self.card_file_v = QFrame()
        self.card_file_v.setProperty("class", "fileBox")
        cf_v_layout = QVBoxLayout(self.card_file_v)
        cf_v_layout.setContentsMargins(16, 16, 16, 16)
        cf_v_layout.setSpacing(6)

        head_v = QHBoxLayout()
        lbl_v_role = QLabel("Referência de vídeo")
        lbl_v_role.setProperty("class", "fileRole")
        head_v.addWidget(lbl_v_role)
        head_v.addStretch()
        self.badge_v_fmt = QLabel("MKV")
        self.badge_v_fmt.setProperty("class", "tag")
        head_v.addWidget(self.badge_v_fmt)
        cf_v_layout.addLayout(head_v)

        self.lbl_v_filename = QLabel("video_ref.mkv")
        self.lbl_v_filename.setProperty("class", "fileName")
        self.lbl_v_filename.setWordWrap(True)
        cf_v_layout.addWidget(self.lbl_v_filename)

        self.lbl_v_meta = QLabel("0.0 GB · 00:00:00")
        self.lbl_v_meta.setProperty("class", "fileMeta")
        cf_v_layout.addWidget(self.lbl_v_meta)
        pair_row.addWidget(self.card_file_v, 1)

        # File Card: Dubbed Audio Source (.file)
        self.card_file_a = QFrame()
        self.card_file_a.setProperty("class", "fileBox")
        cf_a_layout = QVBoxLayout(self.card_file_a)
        cf_a_layout.setContentsMargins(16, 16, 16, 16)
        cf_a_layout.setSpacing(6)

        head_a = QHBoxLayout()
        lbl_a_role = QLabel("Áudio dublado")
        lbl_a_role.setProperty("class", "fileRole")
        head_a.addWidget(lbl_a_role)
        head_a.addStretch()
        self.badge_a_fmt = QLabel("MP4")
        self.badge_a_fmt.setProperty("class", "tag")
        head_a.addWidget(self.badge_a_fmt)
        cf_a_layout.addLayout(head_a)

        self.lbl_a_filename = QLabel("audio_dub.mp4")
        self.lbl_a_filename.setProperty("class", "fileName")
        self.lbl_a_filename.setWordWrap(True)
        cf_a_layout.addWidget(self.lbl_a_filename)

        self.lbl_a_meta = QLabel("0.0 MB · 00:00:00")
        self.lbl_a_meta.setProperty("class", "fileMeta")
        cf_a_layout.addWidget(self.lbl_a_meta)
        pair_row.addWidget(self.card_file_a, 1)

        bs_layout.addLayout(pair_row)

        # Dubbing Container (.dub)
        self.frame_arbitration = QFrame()
        self.frame_arbitration.setObjectName("frameArbitration")
        self.frame_arbitration.setProperty("class", "arbitrationCard")
        arb_layout = QHBoxLayout(self.frame_arbitration)
        arb_layout.setContentsMargins(16, 14, 16, 14)
        arb_layout.setSpacing(12)

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
        br_layout.setContentsMargins(22, 22, 22, 22)
        br_layout.setSpacing(12)

        rf_head = QHBoxLayout()
        rf_head.setSpacing(10)
        rf_title = QLabel("Revisão de faixas")
        rf_title.setProperty("class", "cardTitle")
        rf_head.addWidget(rf_title)
        rf_head.addStretch()
        lbl_no_rec = QLabel("Sem reencode de vídeo")
        lbl_no_rec.setProperty("class", "tagGreen")
        rf_head.addWidget(lbl_no_rec)
        br_layout.addLayout(rf_head)

        # Comboboxes instantiated
        self.combo_video = QComboBox()
        self.combo_video.currentIndexChanged.connect(self._update_audio_audit)

        self.combo_target_audio = QComboBox()
        self.combo_target_audio.currentIndexChanged.connect(self._on_combo_target_changed)

        self.combo_ref_audio = QComboBox()
        self.combo_ref_audio.currentIndexChanged.connect(self._on_combo_ref_changed)

        # Structured Two-Level Stream Rows via configure_stream_row contract
        self.row_video = self.configure_stream_row(
            "V01", "Melhor Imagem", "", "Copy", self.combo_video
        )
        self.badge_v_status = self.row_video.badge
        self.chip_v_act = self.row_video.chip
        br_layout.addWidget(self.row_video)

        self.row_target = self.configure_stream_row(
            "A02", "Português Oficial", "", "Align", self.combo_target_audio
        )
        self.badge_a_status = self.row_target.badge
        self.chip_a_act = self.row_target.chip
        br_layout.addWidget(self.row_target)

        self.row_ref = self.configure_stream_row(
            "A01", "Referência Fixa", "", "Copy", self.combo_ref_audio
        )
        self.badge_ref_status = self.row_ref.badge
        self.chip_ref_act = self.row_ref.chip
        br_layout.addWidget(self.row_ref)

        # Acoustic Audit Card & Channel Configuration Badges (.audit)
        self.frame_audio_audit = QFrame()
        self.frame_audio_audit.setObjectName("frameAudioAudit")
        self.frame_audio_audit.setProperty("class", "auditPill")
        audit_layout = QHBoxLayout(self.frame_audio_audit)
        audit_layout.setContentsMargins(18, 8, 18, 8)
        audit_layout.setSpacing(10)

        lbl_audit_title = QLabel("Auditoria de canais")
        lbl_audit_title.setProperty("class", "hint")
        audit_layout.addWidget(lbl_audit_title)

        self.lbl_audit_origin = QLabel("MKV → MKV remux")
        self.lbl_audit_origin.setProperty("class", "tagNeutral")
        audit_layout.addWidget(self.lbl_audit_origin)

        self.badge_audit_layout = QLabel("Estéreo 2.0")
        self.badge_audit_layout.setProperty("class", "tag")
        audit_layout.addWidget(self.badge_audit_layout)

        self.lbl_audit_specs = QLabel("")
        self.lbl_audit_specs.setStyleSheet("font-weight: 700; font-size: 13px; color: #f2f3f7;")
        audit_layout.addWidget(self.lbl_audit_specs)

        audit_layout.addStretch()
        br_layout.addWidget(self.frame_audio_audit)

        # Contextual Channel Difference Alert
        self.frame_channel_alert = QFrame()
        self.frame_channel_alert.setProperty("class", "subCard")
        alert_layout = QHBoxLayout(self.frame_channel_alert)
        alert_layout.setContentsMargins(8, 8, 8, 8)
        self.lbl_channel_alert = QLabel("")
        self.lbl_channel_alert.setProperty("class", "diagnosisBanner")
        alert_layout.addWidget(self.lbl_channel_alert)
        self.frame_channel_alert.setVisible(False)
        br_layout.addWidget(self.frame_channel_alert)

        # Vertical Options Stack (.opts): Audio preservation + PAL pitch restore + Re-encode codec
        self.frame_options = QFrame()
        self.frame_options.setObjectName("frameOptions")
        self.frame_options.setProperty("class", "optionsContainer")
        options_col = QVBoxLayout(self.frame_options)
        options_col.setContentsMargins(0, 4, 0, 4)
        options_col.setSpacing(6)

        # Option 1: Audio preservation
        opt_1 = QFrame()
        opt_1.setProperty("class", "optRow")
        l1 = QHBoxLayout(opt_1)
        l1.setContentsMargins(18, 4, 14, 4)
        self.check_keep_original = AudioPreserveCheckbox(self.page_confirm, language_name="inglês")
        self.check_keep_original.setLayoutDirection(Qt.RightToLeft)
        self.check_keep_original.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        l1.addWidget(self.check_keep_original)
        options_col.addWidget(opt_1)

        # Option 2: PAL Pitch restore
        opt_2 = QFrame()
        opt_2.setProperty("class", "optRow")
        l2 = QHBoxLayout(opt_2)
        l2.setContentsMargins(18, 4, 14, 4)
        self.check_pal_pitch = QCheckBox("Restauração PAL (25 fps → 24 fps)")
        self.check_pal_pitch.setLayoutDirection(Qt.RightToLeft)
        self.check_pal_pitch.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.check_pal_pitch.setToolTip(
            "Aplica desaceleração natural com correção de tom (asetrate+aresample soxr) para dublagens originadas de masters PAL (25 fps)."
        )
        l2.addWidget(self.check_pal_pitch)
        options_col.addWidget(opt_2)

        # Option 3: Re-encode codec
        opt_3 = QFrame()
        opt_3.setProperty("class", "optRow")
        l3 = QHBoxLayout(opt_3)
        l3.setContentsMargins(18, 4, 14, 4)
        lbl_codec = QLabel("Codec de re-encode")
        lbl_codec.setProperty("class", "optLabel")
        l3.addWidget(lbl_codec)
        l3.addStretch()

        self.combo_audio_codec = QComboBox()
        self.combo_audio_codec.addItem("FLAC (lossless)", "flac")
        self.combo_audio_codec.addItem("Opus", "opus")
        self.combo_audio_codec.addItem("E-AC3 / AC3", "eac3")
        self.combo_audio_codec.addItem("AAC", "aac")
        self.combo_audio_codec.setToolTip(
            "Codec de saída caso time-stretch contínuo ou restauração PAL seja obrigatório."
        )
        l3.addWidget(self.combo_audio_codec)
        options_col.addWidget(opt_3)

        br_layout.addWidget(self.frame_options)

        # Primary Action Row: Single button ("Sincronizar e concluir") anchored cleanly
        action_row = QHBoxLayout()
        action_row.setSpacing(14)
        action_row.setContentsMargins(0, 6, 0, 0)

        self.btn_confirm = QPushButton("Sincronizar e concluir")
        self.btn_confirm.setProperty("class", "btnPrimary")
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
            "Selecionar Arquivos (Vídeo + Áudio)",
            "",
            "Vídeos (*.mkv *.mp4 *.m4v *.mov)"
        )
        if files:
            self.handle_files_ingested(files)

    def _open_single_file_dialog(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Selecionar Segundo Arquivo de Mídia",
            "",
            "Vídeos (*.mkv *.mp4 *.m4v *.mov)"
        )
        if files:
            self.handle_files_ingested(files)

    def handle_files_ingested(self, file_paths: List[str]) -> None:
        """
        Validates incoming files, updates drop zone state machine:
        - 1 file: displays single file slot on page 1 awaiting second file.
        - 2 files: emits files_ready signal for inspection and review gate progression.
        """
        supported_exts = (".mkv", ".mp4", ".m4v", ".mov")
        valid_files = [f for f in file_paths if f.lower().endswith(supported_exts) and not os.path.isdir(f)]

        if not valid_files:
            return

        for f in valid_files:
            if f not in self.loaded_files and len(self.loaded_files) < 2:
                self.loaded_files.append(f)

        if len(self.loaded_files) == 1:
            self.lbl_single_filename.setText(os.path.basename(self.loaded_files[0]))
            self.badge_waiting.setText("1 / 2 fontes carregadas — Aguardando segundo arquivo")
            self.stack.setCurrentIndex(1)
        elif len(self.loaded_files) >= 2:
            self.files_ready.emit(self.loaded_files[0], self.loaded_files[1])

    def ingest_files(self, file_paths: List[str]) -> None:
        """Backwards-compatible alias for handle_files_ingested."""
        self.handle_files_ingested(file_paths)

    def update_sources_view(self, media_sources: List[MediaSourceInfo]) -> None:
        """Renders paired media source cards and transitions visual state to the Review Gate (Page 2)."""
        if not media_sources:
            return

        for src in media_sources:
            if src.is_video_source or (src == media_sources[0] and not any(s.is_video_source for s in media_sources)):
                self.lbl_v_filename.setText(os.path.basename(src.file_path))
                self.lbl_v_meta.setText(src.summary)
                self.badge_v_fmt.setText(src.extension or os.path.splitext(src.file_path)[1].replace(".", "").upper())
            else:
                self.lbl_a_filename.setText(os.path.basename(src.file_path))
                self.lbl_a_meta.setText(src.summary)
                self.badge_a_fmt.setText(src.extension or os.path.splitext(src.file_path)[1].replace(".", "").upper())

        self.chip_sources_count.setText(f"{len(media_sources)} / 2 SOURCES")
        self.stack.setCurrentIndex(2)

    def set_verdict(self, verdict: AutoMatchVerdict):
        self.current_verdict = verdict

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
                role_label="REFERENCIA DE VIDEO",
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
                    role_label="AUDIO DUBLADO",
                    summary=a_summary,
                    is_video_source=False
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

        self.update_role_badge(self.badge_v_status, "Melhor Imagem")

        # Collect all audio candidates from both sources
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

        self.update_role_badge(self.badge_ref_status, "Referência Fixa")

        if verdict.reference_audio and verdict.reference_audio.stream.language:
            lang = verdict.reference_audio.stream.language.lower()
            lang_name = "inglês" if lang in ("eng", "en") else lang.upper()
            self.check_keep_original.set_language_name(lang_name)

        # Update acoustic audit card
        self._update_audio_audit()

        # Set focus to confirm button for instant Enter activation
        self.btn_confirm.setFocus()

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

    def _update_audio_audit(self):
        """Updates acoustic audit badges and contextual channel warnings based on combo selection."""
        target_cand: Optional[StreamCandidate] = self.combo_target_audio.currentData()
        ref_cand: Optional[StreamCandidate] = self.combo_ref_audio.currentData()
        video_cand: Optional[StreamCandidate] = self.combo_video.currentData()

        if not target_cand:
            self.frame_audio_audit.setVisible(False)
            self.frame_channel_alert.setVisible(False)
            return

        self.frame_audio_audit.setVisible(True)
        tgt_stream = target_cand.stream
        tgt_fmt = tgt_stream.container_format.upper() if tgt_stream.container_format else "MKV"

        # Origin indicator
        is_hybrid = (tgt_fmt != "MKV") or (video_cand and target_cand.file_path != video_cand.file_path)
        if is_hybrid:
            self.lbl_audit_origin.setText(f"{tgt_fmt} -> MKV Remux")
            self.lbl_audit_origin.setProperty("class", "badgeAmber" if tgt_fmt != "MKV" else "badgeNeutral")
        else:
            self.lbl_audit_origin.setText(f"{tgt_fmt} Nativo")
            self.lbl_audit_origin.setProperty("class", "badgeNeutral")
        self.lbl_audit_origin.setStyle(self.lbl_audit_origin.style())

        # Channel layout badge & Immersive Atmos detection
        layout_text = tgt_stream.spatial_label or format_channel_layout_label(tgt_stream.channels, tgt_stream.channel_layout)
        self.badge_audit_layout.setText(layout_text)
        if tgt_stream.is_immersive or "atmos" in layout_text.lower():
            self.badge_audit_layout.setProperty("class", "badgeSignal")
        elif tgt_stream.channels >= 6:
            self.badge_audit_layout.setProperty("class", "badgeGreen")
        else:
            self.badge_audit_layout.setProperty("class", "badgeNeutral")
        self.badge_audit_layout.setStyle(self.badge_audit_layout.style())

        # Acoustic specs label
        if tgt_stream.audio_profile:
            spec_str = tgt_stream.audio_profile.spec_label()
        else:
            sr_str = f"{tgt_stream.sample_rate:,} Hz".replace(",", ".") if tgt_stream.sample_rate else ""
            spec_str = f"{tgt_stream.codec.upper()} • {sr_str}"
        self.lbl_audit_specs.setText(spec_str)

        # Contextual Channel Difference Alert
        if target_cand and ref_cand and target_cand.file_path == ref_cand.file_path and target_cand.stream.id == ref_cand.stream.id:
            return

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
        - Upper line: 44x44px rounded identifier (.tid), dynamic auto-fit role badge, and action chip (.tag / .tag.n).
        - Lower line: Technical description or embedded stream combo selector.
        """
        row_frame = QFrame()
        is_rec = action_chip == "Align" or "Recomendado" in role_badge or "RECOMENDADA" in role_badge
        row_frame.setProperty("recommended", "true" if is_rec else "false")
        row_frame.setProperty("class", "trackRow" + (" trackRowRec" if is_rec else ""))
        rf_layout = QVBoxLayout(row_frame)
        rf_layout.setContentsMargins(16, 14, 16, 14)
        rf_layout.setSpacing(8)

        # Upper line
        top_line = QHBoxLayout()
        top_line.setSpacing(12)
        top_line.setContentsMargins(0, 0, 0, 0)

        lbl_id = QLabel(track_id)
        lbl_id.setProperty("class", "trackIdBox")
        lbl_id.setProperty("recommended", "true" if is_rec else "false")
        fm_id = lbl_id.fontMetrics()
        id_w = max(44, fm_id.horizontalAdvance(track_id) + 16)
        lbl_id.setMinimumWidth(id_w)
        lbl_id.setFixedHeight(44)
        lbl_id.setAlignment(Qt.AlignCenter)
        top_line.addWidget(lbl_id)

        badge = QLabel(role_badge)
        badge.setProperty("class", "roleBadge")
        badge.setStyleSheet(self.get_role_badge_style(role_badge))
        badge.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        fm = badge.fontMetrics()
        badge_w = fm.horizontalAdvance(role_badge) + 24
        badge.setMinimumWidth(max(badge_w, 88))
        badge.setAlignment(Qt.AlignCenter)
        top_line.addWidget(badge)

        top_line.addStretch()

        chip = QLabel(action_chip)
        chip.setProperty("class", "streamActionChip")
        chip.setStyleSheet(self.get_action_chip_style(action_chip))
        chip.setMinimumWidth(68)
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

    def reset(self):
        """Resets the drop zone to initial standby state."""
        self.loaded_files = []
        self.current_verdict = None
        self.lbl_v_filename.setText("video_ref.mkv")
        self.lbl_v_meta.setText("0.0 GB  •  00:00:00")
        self.lbl_a_filename.setText("audio_dub.mp4")
        self.lbl_a_meta.setText("0.0 MB  •  00:00:00")
        self.combo_video.clear()
        self.combo_target_audio.clear()
        self.combo_ref_audio.clear()
        self.update_role_badge(self.badge_v_status, "Melhor Imagem")
        self.update_role_badge(self.badge_a_status, "Português Oficial")
        self.update_role_badge(self.badge_ref_status, "Referência Fixa")
        self.chip_v_act.setText("Copy")
        self.chip_a_act.setText("Align")
        self.chip_ref_act.setText("Copy")
        self.frame_ambiguity.setVisible(False)
        self.frame_arbitration.setVisible(False)
        self.frame_audio_audit.setVisible(False)
        self.frame_channel_alert.setVisible(False)
        self.stack.setCurrentIndex(0)
        self.reset_requested.emit()

