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
        root_layout.setContentsMargins(14, 14, 14, 14)
        root_layout.setSpacing(10)

        self.stack = QStackedWidget()

        # ======================================================================
        # Page 0: Standby / Empty Drop Zone
        # ======================================================================
        self.page_empty = QFrame()
        self.page_empty.setObjectName("dropFrameEmpty")
        self.page_empty.setProperty("class", "dropFrame")
        empty_layout = QVBoxLayout(self.page_empty)
        empty_layout.setAlignment(Qt.AlignCenter)
        empty_layout.setSpacing(10)

        self.lbl_empty_title = QLabel("Arraste e solte os 2 arquivos aqui\nou clique para navegar e selecionar ambos")
        self.lbl_empty_title.setAlignment(Qt.AlignCenter)
        self.lbl_empty_title.setStyleSheet("font-size: 14px; font-weight: 700;")
        empty_layout.addWidget(self.lbl_empty_title)

        lbl_hint = QLabel("Suporte agnóstico a contêineres: MKV, MP4, M4V, MOV (alta fidelidade visual + dublagem)")
        lbl_hint.setAlignment(Qt.AlignCenter)
        lbl_hint.setProperty("class", "subText")
        empty_layout.addWidget(lbl_hint)

        btn_browse = QPushButton("Selecionar Arquivos (MKV / MP4)...")
        btn_browse.setProperty("class", "btnPrimary")
        btn_browse.setFixedWidth(240)
        btn_browse.clicked.connect(self._open_file_dialog)
        empty_layout.addWidget(btn_browse, alignment=Qt.AlignCenter)

        self.stack.addWidget(self.page_empty)

        # ======================================================================
        # Page 1: 1 File Ingested (Awaiting Second File)
        # ======================================================================
        self.page_single = QFrame()
        self.page_single.setObjectName("dropFrameSingle")
        self.page_single.setProperty("class", "dropFrame")
        single_layout = QVBoxLayout(self.page_single)
        single_layout.setAlignment(Qt.AlignCenter)
        single_layout.setSpacing(8)

        self.badge_waiting = QLabel("1 de 2 arquivos carregados — Aguardando segundo arquivo")
        self.badge_waiting.setProperty("class", "badgeAmber")
        single_layout.addWidget(self.badge_waiting, alignment=Qt.AlignCenter)

        self.lbl_single_filename = QLabel("")
        self.lbl_single_filename.setStyleSheet("font-weight: 700; font-size: 13px;")
        self.lbl_single_filename.setAlignment(Qt.AlignCenter)
        single_layout.addWidget(self.lbl_single_filename)

        lbl_single_instruction = QLabel("Arraste o segundo arquivo de mídia aqui ou selecione manualmente:")
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
        # Page 2: 2 Files Ingested (Tabular Review Gate & Confirmation Panel)
        # ======================================================================
        self.page_confirm = QWidget()
        confirm_layout = QVBoxLayout(self.page_confirm)
        confirm_layout.setContentsMargins(0, 0, 0, 0)
        confirm_layout.setSpacing(10)

        # Header with status & reset
        conf_header = QHBoxLayout()
        conf_title = QLabel("Confirmação de Trilhas & Mapeamento Assistido")
        conf_title.setProperty("class", "cardTitle")
        conf_header.addWidget(conf_title)
        conf_header.addStretch()

        btn_change_files = QPushButton("Trocar Arquivos")
        btn_change_files.setProperty("class", "btnSecondary")
        btn_change_files.clicked.connect(self.reset)
        conf_header.addWidget(btn_change_files)
        confirm_layout.addLayout(conf_header)

        # Files summary strip
        self.lbl_files_summary = QLabel("")
        self.lbl_files_summary.setProperty("class", "summaryStrip")
        self.lbl_files_summary.setStyleSheet("font-size: 11px;")
        confirm_layout.addWidget(self.lbl_files_summary)

        # Ambiguity Banner
        self.frame_ambiguity = QFrame()
        self.frame_ambiguity.setStyleSheet(
            "background-color: rgba(245, 158, 11, 0.1); border: 1px solid rgba(245, 158, 11, 0.35); border-radius: 6px; padding: 6px 10px;"
        )
        amb_layout = QHBoxLayout(self.frame_ambiguity)
        amb_layout.setContentsMargins(0, 0, 0, 0)
        self.lbl_ambiguity = QLabel("")
        self.lbl_ambiguity.setStyleSheet("color: #fbbf24; font-size: 11px; font-weight: 600;")
        amb_layout.addWidget(self.lbl_ambiguity)
        self.frame_ambiguity.setVisible(False)
        confirm_layout.addWidget(self.frame_ambiguity)

        # Table Grid for Selections
        table_grid = QGridLayout()
        table_grid.setSpacing(10)

        # Row 1: Primary Video
        lbl_v_tag = QLabel("Vídeo:")
        lbl_v_tag.setStyleSheet("font-weight: 700; font-size: 12px;")
        table_grid.addWidget(lbl_v_tag, 0, 0)

        self.badge_v_status = QLabel("Melhor Imagem")
        self.badge_v_status.setProperty("class", "badgeGreen")
        self.badge_v_status.setFixedWidth(130)
        table_grid.addWidget(self.badge_v_status, 0, 1)

        self.combo_video = QComboBox()
        self.combo_video.currentIndexChanged.connect(self._update_audio_audit)
        table_grid.addWidget(self.combo_video, 0, 2)

        # Row 2: Target Dubbed Audio
        lbl_a_tag = QLabel("Áudio Dublado:")
        lbl_a_tag.setStyleSheet("font-weight: 700; font-size: 12px;")
        table_grid.addWidget(lbl_a_tag, 1, 0)

        self.badge_a_status = QLabel("Português")
        self.badge_a_status.setProperty("class", "badgeGreen")
        self.badge_a_status.setFixedWidth(130)
        table_grid.addWidget(self.badge_a_status, 1, 1)

        self.combo_target_audio = QComboBox()
        self.combo_target_audio.currentIndexChanged.connect(self._update_audio_audit)
        table_grid.addWidget(self.combo_target_audio, 1, 2)

        # Row 3: Reference Audio
        lbl_ref_tag = QLabel("Áudio Referência:")
        lbl_ref_tag.setStyleSheet("font-weight: 700; font-size: 12px;")
        table_grid.addWidget(lbl_ref_tag, 2, 0)

        self.badge_ref_status = QLabel("Referência FFT")
        self.badge_ref_status.setProperty("class", "badgeNeutral")
        self.badge_ref_status.setFixedWidth(130)
        table_grid.addWidget(self.badge_ref_status, 2, 1)

        self.combo_ref_audio = QComboBox()
        self.combo_ref_audio.currentIndexChanged.connect(self._update_audio_audit)
        table_grid.addWidget(self.combo_ref_audio, 2, 2)

        confirm_layout.addLayout(table_grid)

        # ======================================================================
        # Acoustic Audit Card & Channel Configuration Badges
        # ======================================================================
        self.frame_audio_audit = QFrame()
        self.frame_audio_audit.setProperty("class", "auditCard")
        audit_layout = QHBoxLayout(self.frame_audio_audit)
        audit_layout.setContentsMargins(0, 0, 0, 0)
        audit_layout.setSpacing(10)

        lbl_audit_title = QLabel("Auditoria da Dublagem:")
        lbl_audit_title.setStyleSheet("font-weight: 700; font-size: 11px;")
        audit_layout.addWidget(lbl_audit_title)

        self.lbl_audit_origin = QLabel("")
        self.lbl_audit_origin.setProperty("class", "badgeNeutral")
        audit_layout.addWidget(self.lbl_audit_origin)

        self.badge_audit_layout = QLabel("Estéreo 2.0")
        self.badge_audit_layout.setProperty("class", "badgeNeutral")
        audit_layout.addWidget(self.badge_audit_layout)

        self.lbl_audit_specs = QLabel("")
        self.lbl_audit_specs.setStyleSheet(
            "font-family: 'JetBrains Mono', monospace; font-size: 11px; font-weight: 600;"
        )
        audit_layout.addWidget(self.lbl_audit_specs)

        audit_layout.addStretch()
        confirm_layout.addWidget(self.frame_audio_audit)

        # Contextual Channel Difference Alert
        self.frame_channel_alert = QFrame()
        self.frame_channel_alert.setStyleSheet(
            "background-color: rgba(59, 130, 246, 0.08); border: 1px solid rgba(59, 130, 246, 0.25); border-radius: 6px; padding: 6px 10px;"
        )
        alert_layout = QHBoxLayout(self.frame_channel_alert)
        alert_layout.setContentsMargins(0, 0, 0, 0)
        self.lbl_channel_alert = QLabel("")
        self.lbl_channel_alert.setStyleSheet("color: #93c5fd; font-size: 11px; font-weight: 600;")
        alert_layout.addWidget(self.lbl_channel_alert)
        self.frame_channel_alert.setVisible(False)
        confirm_layout.addWidget(self.frame_channel_alert)

        # High-Contrast Dynamic Checkbox for Composition
        check_row = QHBoxLayout()
        check_row.setSpacing(16)

        self.check_keep_original = AudioPreserveCheckbox(self.page_confirm, language_name="inglês")
        check_row.addWidget(self.check_keep_original)

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
                QFrame {
                    border: 2px dashed #666666;
                    border-radius: 8px;
                    background-color: #1f1f1f;
                }
            """)

    def dragLeaveEvent(self, event):
        self.page_empty.setStyleSheet("""
            QFrame {
                border: 2px dashed #383838;
                border-radius: 8px;
                background-color: #141414;
            }
        """)

    def dropEvent(self, event: QDropEvent):
        self.dragLeaveEvent(event)
        urls = event.mimeData().urls()
        valid_paths = [u.toLocalFile() for u in urls if os.path.isfile(u.toLocalFile())]
        if valid_paths:
            self.ingest_files(valid_paths)

    def _open_file_dialog(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Selecionar os 2 Arquivos de Mídia (Vídeo de Alta Resolução + Dublado)",
            os.path.expanduser("~"),
            "Arquivos de Mídia (*.mkv *.mp4 *.m4v *.mov);;Todos os Arquivos (*.*)"
        )
        if files:
            self.ingest_files(files)

    def _open_single_file_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar o Segundo Arquivo de Mídia",
            os.path.expanduser("~"),
            "Arquivos de Mídia (*.mkv *.mp4 *.m4v *.mov);;Todos os Arquivos (*.*)"
        )
        if file_path:
            self.ingest_files([file_path])

    def ingest_files(self, paths: List[str]):
        """Processes newly ingested file paths."""
        for p in paths:
            abs_p = os.path.abspath(p)
            if abs_p not in self.loaded_files:
                self.loaded_files.append(abs_p)

        if len(self.loaded_files) == 1:
            self.stack.setCurrentIndex(1)
            file_0 = self.loaded_files[0]
            bname = os.path.basename(file_0)
            sz = format_bytes(os.path.getsize(file_0)) if os.path.exists(file_0) else "0 B"
            self.lbl_single_filename.setText(f"{bname} ({sz})")
        elif len(self.loaded_files) >= 2:
            file_a, file_b = self.loaded_files[0], self.loaded_files[1]
            self.files_ready.emit(file_a, file_b)

    def set_verdict(self, verdict: AutoMatchVerdict):
        """Populates the confirmation table with heuristic verdict choices."""
        self.current_verdict = verdict
        self.stack.setCurrentIndex(2)

        file_v = verdict.recommended_video.file_path
        file_a = verdict.recommended_target_audio.file_path if verdict.recommended_target_audio else ""

        sz_v = format_bytes(os.path.getsize(file_v)) if os.path.isfile(file_v) else ""
        sz_a = format_bytes(os.path.getsize(file_a)) if os.path.isfile(file_a) else ""

        ext_v = os.path.splitext(file_v)[1].upper().lstrip(".")
        ext_a = os.path.splitext(file_a)[1].upper().lstrip(".")

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
            self.badge_a_status.setProperty("class", "badgeGreen")
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
        # Emits neutral alert if dubbed audio is stereo 2.0 while reference English audio is 5.1/7.1
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
