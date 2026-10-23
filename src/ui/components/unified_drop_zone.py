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
    QStackedWidget,
    QVBoxLayout,
    QWidget
)

from ...core.disk_utils import format_bytes
from ...core.models import AutoMatchVerdict, StreamCandidate, format_channel_layout_label
from .audio_preserve_checkbox import AudioPreserveCheckbox


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
        self.lbl_empty_title.setStyleSheet("background: transparent; font-size: 14px; font-weight: 700; color: #eef0f2; border: none;")
        empty_layout.addWidget(self.lbl_empty_title)

        lbl_hint = QLabel("MKV / MP4 / M4V / MOV  •  1 Vídeo de Referência + 1 Faixa de Dublagem")
        lbl_hint.setAlignment(Qt.AlignCenter)
        lbl_hint.setProperty("class", "subText")
        lbl_hint.setStyleSheet("background: transparent; color: #7e8792; font-size: 11px; border: none;")
        empty_layout.addWidget(lbl_hint)

        btn_browse = QPushButton("Selecionar Arquivos...")
        btn_browse.setProperty("class", "btnPrimary")
        btn_browse.setFixedWidth(200)
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
        self.lbl_single_filename.setStyleSheet(
            "background: transparent; font-family: 'SFMono-Regular', monospace; font-weight: 700; font-size: 13px; color: #eef0f2; border: none;"
        )
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
        confirm_layout.setSpacing(12)

        # Header with Card 01 Tag and Change button
        conf_header = QHBoxLayout()
        conf_header.setSpacing(8)

        idx_c01 = QLabel("01")
        idx_c01.setProperty("class", "sectionIndex")
        conf_header.addWidget(idx_c01)

        conf_title = QLabel("Fontes Ingeridas (File Pair)")
        conf_title.setProperty("class", "cardTitle")
        conf_header.addWidget(conf_title)
        conf_header.addStretch()

        self.chip_sources_count = QLabel("2 / 2 SOURCES")
        self.chip_sources_count.setProperty("class", "badgeGreen")
        conf_header.addWidget(self.chip_sources_count)

        btn_change_files = QPushButton("Trocar Arquivos")
        btn_change_files.setProperty("class", "btnSecondary")
        btn_change_files.clicked.connect(self.reset)
        conf_header.addWidget(btn_change_files)
        confirm_layout.addLayout(conf_header)

        # Paired Horizontal File Cards
        pair_row = QHBoxLayout()
        pair_row.setSpacing(10)

        # File Card: Video Reference
        self.card_file_v = QFrame()
        self.card_file_v.setProperty("class", "fileCardWorkbench")
        cf_v_layout = QVBoxLayout(self.card_file_v)
        cf_v_layout.setContentsMargins(10, 8, 10, 8)
        cf_v_layout.setSpacing(4)

        head_v = QHBoxLayout()
        lbl_v_role = QLabel("REFERENCIA DE VIDEO")
        lbl_v_role.setProperty("class", "eyebrowText")
        head_v.addWidget(lbl_v_role)
        head_v.addStretch()
        self.badge_v_fmt = QLabel("MKV")
        self.badge_v_fmt.setProperty("class", "codecChip")
        head_v.addWidget(self.badge_v_fmt)
        cf_v_layout.addLayout(head_v)

        self.lbl_v_filename = QLabel("video_ref.mkv")
        self.lbl_v_filename.setStyleSheet("background: transparent; font-weight: 700; font-size: 12px; color: #eef0f2; border: none;")
        cf_v_layout.addWidget(self.lbl_v_filename)

        self.lbl_v_meta = QLabel("0.0 GB  •  00:00:00")
        self.lbl_v_meta.setStyleSheet("background: transparent; font-family: 'SFMono-Regular', monospace; font-size: 10px; color: #7e8792; border: none;")
        cf_v_layout.addWidget(self.lbl_v_meta)
        pair_row.addWidget(self.card_file_v, 1)

        # File Card: Dubbed Audio Source
        self.card_file_a = QFrame()
        self.card_file_a.setProperty("class", "fileCardWorkbench")
        cf_a_layout = QVBoxLayout(self.card_file_a)
        cf_a_layout.setContentsMargins(10, 8, 10, 8)
        cf_a_layout.setSpacing(4)

        head_a = QHBoxLayout()
        lbl_a_role = QLabel("AUDIO DUBLADO")
        lbl_a_role.setProperty("class", "eyebrowText")
        head_a.addWidget(lbl_a_role)
        head_a.addStretch()
        self.badge_a_fmt = QLabel("MP4")
        self.badge_a_fmt.setProperty("class", "badgeSignal")
        head_a.addWidget(self.badge_a_fmt)
        cf_a_layout.addLayout(head_a)

        self.lbl_a_filename = QLabel("audio_dub.mp4")
        self.lbl_a_filename.setStyleSheet("background: transparent; font-weight: 700; font-size: 12px; color: #eef0f2; border: none;")
        cf_a_layout.addWidget(self.lbl_a_filename)

        self.lbl_a_meta = QLabel("0.0 MB  •  00:00:00")
        self.lbl_a_meta.setStyleSheet("background: transparent; font-family: 'SFMono-Regular', monospace; font-size: 10px; color: #7e8792; border: none;")
        cf_a_layout.addWidget(self.lbl_a_meta)
        pair_row.addWidget(self.card_file_a, 1)

        confirm_layout.addLayout(pair_row)

        # Files summary strip (preserved for test compatibility)
        self.lbl_files_summary = QLabel("")
        self.lbl_files_summary.setVisible(False)
        confirm_layout.addWidget(self.lbl_files_summary)

        # Ambiguity Banner
        self.frame_ambiguity = QFrame()
        self.frame_ambiguity.setStyleSheet(
            "background-color: rgba(231, 199, 131, 0.1); border: 1px solid rgba(231, 199, 131, 0.35); border-radius: 6px; padding: 6px 10px;"
        )
        amb_layout = QHBoxLayout(self.frame_ambiguity)
        amb_layout.setContentsMargins(0, 0, 0, 0)
        self.lbl_ambiguity = QLabel("")
        self.lbl_ambiguity.setStyleSheet("background: transparent; color: #e7c783; font-size: 11px; font-weight: 600; border: none;")
        amb_layout.addWidget(self.lbl_ambiguity)
        self.frame_ambiguity.setVisible(False)
        confirm_layout.addWidget(self.frame_ambiguity)

        # Card 02: Stream Review Gate (Tabela de Auditoria)
        review_frame = QFrame()
        review_frame.setProperty("class", "subCard")
        rf_layout = QVBoxLayout(review_frame)
        rf_layout.setContentsMargins(12, 12, 12, 12)
        rf_layout.setSpacing(10)

        rf_head = QHBoxLayout()
        idx_c02 = QLabel("02")
        idx_c02.setProperty("class", "sectionIndex")
        rf_head.addWidget(idx_c02)
        rf_title = QLabel("Stream Review Gate (Mapeamento de Faixas)")
        rf_title.setProperty("class", "cardTitle")
        rf_head.addWidget(rf_title)
        rf_head.addStretch()
        lbl_no_rec = QLabel("SEM REENCODIFICACAO DE VIDEO")
        lbl_no_rec.setProperty("class", "eyebrowText")
        rf_head.addWidget(lbl_no_rec)
        rf_layout.addLayout(rf_head)

        # Table Grid for Selections
        table_grid = QGridLayout()
        table_grid.setSpacing(8)

        # Row 1: Primary Video
        lbl_v_tag = QLabel("V01 / Vídeo:")
        lbl_v_tag.setStyleSheet("background: transparent; font-family: 'SFMono-Regular', monospace; font-weight: 700; font-size: 11px; color: #c1c6cd; border: none;")
        table_grid.addWidget(lbl_v_tag, 0, 0)

        self.badge_v_status = QLabel("Melhor Imagem")
        self.badge_v_status.setProperty("class", "badgeGreen")
        self.badge_v_status.setFixedWidth(120)
        table_grid.addWidget(self.badge_v_status, 0, 1)

        self.combo_video = QComboBox()
        self.combo_video.currentIndexChanged.connect(self._update_audio_audit)
        table_grid.addWidget(self.combo_video, 0, 2)

        chip_v_act = QLabel("Copy")
        chip_v_act.setProperty("class", "systemChip")
        chip_v_act.setFixedWidth(54)
        table_grid.addWidget(chip_v_act, 0, 3)

        # Row 2: Target Dubbed Audio
        lbl_a_tag = QLabel("A02 / Alvo (PT):")
        lbl_a_tag.setStyleSheet("background: transparent; font-family: 'SFMono-Regular', monospace; font-weight: 700; font-size: 11px; color: #c1c6cd; border: none;")
        table_grid.addWidget(lbl_a_tag, 1, 0)

        self.badge_a_status = QLabel("Português")
        self.badge_a_status.setProperty("class", "badgeSignal")
        self.badge_a_status.setFixedWidth(120)
        table_grid.addWidget(self.badge_a_status, 1, 1)

        self.combo_target_audio = QComboBox()
        self.combo_target_audio.currentIndexChanged.connect(self._update_audio_audit)
        table_grid.addWidget(self.combo_target_audio, 1, 2)

        chip_a_act = QLabel("Align")
        chip_a_act.setProperty("class", "badgeSignal")
        chip_a_act.setFixedWidth(54)
        table_grid.addWidget(chip_a_act, 1, 3)

        # Row 3: Reference Audio
        lbl_ref_tag = QLabel("A01 / Ref. (ENG):")
        lbl_ref_tag.setStyleSheet("background: transparent; font-family: 'SFMono-Regular', monospace; font-weight: 700; font-size: 11px; color: #c1c6cd; border: none;")
        table_grid.addWidget(lbl_ref_tag, 2, 0)

        self.badge_ref_status = QLabel("Referência FFT")
        self.badge_ref_status.setProperty("class", "badgeNeutral")
        self.badge_ref_status.setFixedWidth(120)
        table_grid.addWidget(self.badge_ref_status, 2, 1)

        self.combo_ref_audio = QComboBox()
        self.combo_ref_audio.currentIndexChanged.connect(self._update_audio_audit)
        table_grid.addWidget(self.combo_ref_audio, 2, 2)

        chip_ref_act = QLabel("Copy")
        chip_ref_act.setProperty("class", "systemChip")
        chip_ref_act.setFixedWidth(54)
        table_grid.addWidget(chip_ref_act, 2, 3)

        rf_layout.addLayout(table_grid)
        confirm_layout.addWidget(review_frame)

        # ======================================================================
        # Acoustic Audit Card & Channel Configuration Badges
        # ======================================================================
        self.frame_audio_audit = QFrame()
        self.frame_audio_audit.setProperty("class", "subCard")
        audit_layout = QHBoxLayout(self.frame_audio_audit)
        audit_layout.setContentsMargins(10, 8, 10, 8)
        audit_layout.setSpacing(10)

        lbl_audit_title = QLabel("Auditoria de Canais:")
        lbl_audit_title.setStyleSheet("background: transparent; font-weight: 700; font-size: 11px; color: #c1c6cd; border: none;")
        audit_layout.addWidget(lbl_audit_title)

        self.lbl_audit_origin = QLabel("")
        self.lbl_audit_origin.setProperty("class", "badgeNeutral")
        audit_layout.addWidget(self.lbl_audit_origin)

        self.badge_audit_layout = QLabel("Estéreo 2.0")
        self.badge_audit_layout.setProperty("class", "badgeNeutral")
        audit_layout.addWidget(self.badge_audit_layout)

        self.lbl_audit_specs = QLabel("")
        self.lbl_audit_specs.setStyleSheet(
            "background: transparent; font-family: 'SFMono-Regular', Consolas, monospace; font-size: 11px; font-weight: 600; color: #eef0f2; border: none;"
        )
        audit_layout.addWidget(self.lbl_audit_specs)

        audit_layout.addStretch()
        confirm_layout.addWidget(self.frame_audio_audit)

        # Contextual Channel Difference Alert
        self.frame_channel_alert = QFrame()
        self.frame_channel_alert.setStyleSheet(
            "background-color: rgba(231, 199, 131, 0.08); border: 1px solid rgba(231, 199, 131, 0.3); border-radius: 6px; padding: 6px 10px;"
        )
        alert_layout = QHBoxLayout(self.frame_channel_alert)
        alert_layout.setContentsMargins(0, 0, 0, 0)
        self.lbl_channel_alert = QLabel("")
        self.lbl_channel_alert.setStyleSheet("background: transparent; color: #e7c783; font-size: 11px; font-weight: 600; border: none;")
        alert_layout.addWidget(self.lbl_channel_alert)
        self.frame_channel_alert.setVisible(False)
        confirm_layout.addWidget(self.frame_channel_alert)

        # High-Contrast Dynamic Checkbox for Composition
        check_row = QHBoxLayout()
        check_row.setSpacing(16)

        self.check_keep_original = AudioPreserveCheckbox(self.page_confirm, language_name="inglês")
        check_row.addWidget(self.check_keep_original)

        self.check_pal_pitch = QCheckBox("Restauração Tonal PAL (25fps -> 24fps)")
        self.check_pal_pitch.setStyleSheet("background: transparent; font-size: 11px; font-weight: 600; color: #c1c6cd; border: none;")
        self.check_pal_pitch.setToolTip("Aplica desaceleração natural com correção de tom (asetrate+aresample soxr) para dublagens originadas de masters PAL (25 fps).")
        check_row.addWidget(self.check_pal_pitch)

        lbl_codec = QLabel("Codec Re-encode:")
        lbl_codec.setStyleSheet("background: transparent; font-size: 11px; font-weight: 600; color: #7e8792; border: none;")
        check_row.addWidget(lbl_codec)

        self.combo_audio_codec = QComboBox()
        self.combo_audio_codec.addItem("FLAC (Lossless)", "flac")
        self.combo_audio_codec.addItem("Opus (160k/450k)", "opus")
        self.combo_audio_codec.addItem("E-AC3 / AC3 (640k)", "eac3")
        self.combo_audio_codec.addItem("AAC (256k)", "aac")
        self.combo_audio_codec.setToolTip("Codec de saída caso time-stretch contínuo ou restauração PAL seja obrigatório.")
        check_row.addWidget(self.combo_audio_codec)

        confirm_layout.addLayout(check_row)

        # Primary Action Row: Single button ("Sincronizar e Concluir")
        action_row = QHBoxLayout()
        action_row.setSpacing(12)

        self.btn_confirm = QPushButton("Sincronizar e Concluir")
        self.btn_confirm.setProperty("class", "btnSuccess")
        self.btn_confirm.clicked.connect(self._on_confirm_clicked)
        action_row.addWidget(self.btn_confirm)

        self.lbl_confirm_hint = QLabel("Pressione Enter para aprovação imediata da seleção.")
        self.lbl_confirm_hint.setProperty("class", "subText")
        action_row.addWidget(self.lbl_confirm_hint)
        action_row.addStretch()

        confirm_layout.addLayout(action_row)

        self.stack.addWidget(self.page_confirm)
        root_layout.addWidget(self.stack)

    # ==========================================================================
    # Drag and Drop Events
    # ==========================================================================
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.page_empty.setStyleSheet("""
                QFrame#dropFrameEmpty {
                    border: 2px dashed #d9f56b;
                    border-radius: 11px;
                    background-color: #15181d;
                }
            """)

    def dragLeaveEvent(self, event):
        self.page_empty.setStyleSheet("""
            QFrame#dropFrameEmpty {
                border: 1px dashed #3b424c;
                border-radius: 11px;
                background-color: #0e1013;
            }
        """)

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        files = [u.toLocalFile() for u in urls if os.path.isfile(u.toLocalFile())]
        self.dragLeaveEvent(None)
        if files:
            self.ingest_files(files)

    def _open_file_dialog(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Selecionar Arquivos (Vídeo + Áudio)",
            "",
            "Arquivos de Mídia (*.mkv *.mp4 *.m4v *.mov);;Todos (*.*)"
        )
        if files:
            self.ingest_files(files)

    def _open_single_file_dialog(self):
        f, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar Segundo Arquivo de Mídia",
            "",
            "Arquivos de Mídia (*.mkv *.mp4 *.m4v *.mov);;Todos (*.*)"
        )
        if f:
            self.ingest_files([f])

    def ingest_files(self, file_paths: List[str]):
        supported_exts = (".mkv", ".mp4", ".m4v", ".mov")
        valid_files = [f for f in file_paths if f.lower().endswith(supported_exts)]

        if not valid_files:
            return

        for f in valid_files:
            if f not in self.loaded_files and len(self.loaded_files) < 2:
                self.loaded_files.append(f)

        if len(self.loaded_files) == 1:
            self.lbl_single_filename.setText(os.path.basename(self.loaded_files[0]))
            self.stack.setCurrentIndex(1)
        elif len(self.loaded_files) >= 2:
            self.files_ready.emit(self.loaded_files[0], self.loaded_files[1])

    def set_verdict(self, verdict: AutoMatchVerdict):
        self.current_verdict = verdict
        self.stack.setCurrentIndex(2)

        file_v = verdict.recommended_video.file_path
        file_a = verdict.recommended_target_audio.file_path if verdict.recommended_target_audio else ""

        sz_v = format_bytes(os.path.getsize(file_v)) if os.path.exists(file_v) else ""
        sz_a = format_bytes(os.path.getsize(file_a)) if file_a and os.path.exists(file_a) else ""

        ext_v = os.path.splitext(file_v)[1].replace(".", "").upper()
        ext_a = os.path.splitext(file_a)[1].replace(".", "").upper() if file_a else ""

        self.lbl_v_filename.setText(os.path.basename(file_v))
        self.lbl_v_meta.setText(f"{sz_v}  •  {verdict.recommended_video.stream.fps:.3f} fps")
        self.badge_v_fmt.setText(ext_v)

        if file_a:
            self.lbl_a_filename.setText(os.path.basename(file_a))
            sr = verdict.recommended_target_audio.stream.sample_rate or 48000
            self.lbl_a_meta.setText(f"{sz_a}  •  {sr} Hz")
            self.badge_a_fmt.setText(ext_a)

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

        # Video combo
        self.combo_video.blockSignals(True)
        self.combo_video.clear()
        self.combo_video.addItem(verdict.recommended_video.summary_title(), userData=verdict.recommended_video)
        for alt in verdict.alternative_videos:
            self.combo_video.addItem(alt.summary_title(), userData=alt)
        self.combo_video.blockSignals(False)

        # Target audio combo
        self.combo_target_audio.blockSignals(True)
        self.combo_target_audio.clear()
        if verdict.recommended_target_audio:
            self.combo_target_audio.addItem(
                verdict.recommended_target_audio.summary_title(),
                userData=verdict.recommended_target_audio
            )
        for alt in verdict.alternative_audios:
            self.combo_target_audio.addItem(alt.summary_title(), userData=alt)
        self.combo_target_audio.blockSignals(False)

        if verdict.is_ambiguous:
            self.badge_a_status.setText("Ajuste Manual")
            self.badge_a_status.setProperty("class", "badgeAmber")
        else:
            self.badge_a_status.setText("Português OK")
            self.badge_a_status.setProperty("class", "badgeSignal")
        self.badge_a_status.setStyle(self.badge_a_status.style())

        # Reference audio combo
        self.combo_ref_audio.blockSignals(True)
        self.combo_ref_audio.clear()
        if verdict.reference_audio:
            self.combo_ref_audio.addItem(verdict.reference_audio.summary_title(), userData=verdict.reference_audio)
        for alt in verdict.alternative_audios:
            if alt != verdict.reference_audio:
                self.combo_ref_audio.addItem(alt.summary_title(), userData=alt)
        self.combo_ref_audio.blockSignals(False)

        if verdict.reference_audio and verdict.reference_audio.stream.language:
            lang = verdict.reference_audio.stream.language.lower()
            lang_name = "inglês" if lang in ("eng", "en") else lang.upper()
            self.check_keep_original.set_language_name(lang_name)

        # Update acoustic audit card
        self._update_audio_audit()

        # Set focus to confirm button for instant Enter activation
        self.btn_confirm.setFocus()

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

        # Channel layout badge
        layout_text = format_channel_layout_label(tgt_stream.channels, tgt_stream.channel_layout)
        self.badge_audit_layout.setText(layout_text)
        if tgt_stream.channels >= 6:
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
        if tgt_stream.channels in (1, 2) and ref_cand and ref_cand.stream.channels >= 6:
            ref_layout = format_channel_layout_label(ref_cand.stream.channels, ref_cand.stream.channel_layout)
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

    def reset(self):
        """Resets the drop zone to initial standby state."""
        self.loaded_files = []
        self.current_verdict = None
        self.stack.setCurrentIndex(0)
        self.reset_requested.emit()
