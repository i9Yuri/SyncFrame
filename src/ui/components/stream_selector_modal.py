"""Assisted confirmation Review Gate modal for stream selection."""

import os
from typing import Optional, Tuple

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget
)

from ...core.models import AutoMatchVerdict, StreamCandidate


class StreamSelectorModal(QDialog):
    """
    Review Gate modal presenting deterministic heuristic recommendations for
    Video, Dubbed Target Audio, and Reference Audio with 1-click Enter confirmation.
    """

    def __init__(self, verdict: AutoMatchVerdict, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.verdict = verdict
        self.setWindowTitle("Confirmação Assistida de Trilhas — SyncFrame")
        self.setModal(True)
        self.resize(780, 560)
        self.setMinimumWidth(680)

        # Neutral monochrome dialog styling with universal continuous rounding
        self.setStyleSheet("""
            QDialog {
                background-color: #1b1c20;
                color: #f2f3f7;
                border-radius: 28px;
                border: 1px solid #33343b;
            }
            QFrame.bentoCard {
                background-color: #26272d;
                border-radius: 24px;
                border: none;
            }
            QComboBox {
                border-radius: 17px;
                height: 34px;
                min-height: 34px;
                max-height: 34px;
                /* border-radius: 999px; */
                background-color: #1b1c20;
                color: #f2f3f7;
                padding: 0 14px;
                border: 1px solid #33343b;
            }
            QComboBox QAbstractItemView {
                background-color: #1b1c20;
                color: #f2f3f7;
                border: 1px solid #33343b;
                border-radius: 16px;
                padding: 6px;
            }
            QComboBox QAbstractItemView::item {
                border-radius: 10px;
                padding: 6px 12px;
            }
            QPushButton.btnSecondary {
                border-radius: 17px;
                height: 34px;
                min-height: 34px;
                max-height: 34px;
                padding: 0 16px;
            }
            QPushButton.btnSuccess {
                border-radius: 22px;
                height: 44px;
                min-height: 44px;
                max-height: 44px;
                /* border-radius: 999px; */
            }
        """)

        self.init_ui()

    def init_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(14)
        root.setContentsMargins(22, 20, 22, 20)

        # Header Title
        header_box = QVBoxLayout()
        header_box.setSpacing(3)
        title = QLabel("Revisão de Trilhas & Mapeamento Automático")
        title.setStyleSheet("background: transparent; font-size: 18px; font-weight: 800; color: #f8fafc; border: none;")
        header_box.addWidget(title)

        subtitle = QLabel("O motor analisou os metadados e selecionou as melhores fontes. Valide ou ajuste:")
        subtitle.setProperty("class", "subText")
        header_box.addWidget(subtitle)
        root.addLayout(header_box)

        # Ambiguity alert banner if needed
        if self.verdict.is_ambiguous:
            alert_frame = QFrame()
            alert_frame.setStyleSheet("""
                QFrame {
                    background-color: rgba(245, 158, 11, 0.12);
                    border: 1px solid rgba(245, 158, 11, 0.4);
                    border-radius: 20px;
                    padding: 10px;
                }
            """)
            al_layout = QHBoxLayout(alert_frame)
            al_layout.setContentsMargins(8, 6, 8, 6)
            al_text = QLabel(f"[ATENCAO] {self.verdict.ambiguity_reason}")
            al_text.setStyleSheet("background: transparent; color: #fbbf24; font-size: 12px; font-weight: 600; border: none;")
            al_layout.addWidget(al_text)
            root.addWidget(alert_frame)

        # Card 1: Chosen Video Stream
        card_v = QFrame()
        card_v.setObjectName("bentoCard")
        card_v.setProperty("class", "bentoCard")
        cv_layout = QVBoxLayout(card_v)
        cv_layout.setSpacing(8)

        v_head = QHBoxLayout()
        v_title = QLabel("1. Fonte de Vídeo (Alta Qualidade)")
        v_title.setProperty("class", "cardTitle")
        v_head.addWidget(v_title)
        v_head.addStretch()

        badge_v = QLabel(self.verdict.recommended_video.badge_label or "Recomendado")
        badge_v.setProperty("class", "badgeGreen")
        v_head.addWidget(badge_v)
        cv_layout.addLayout(v_head)

        self.combo_video = QComboBox()
        # Add recommended first
        self.combo_video.addItem(
            self.verdict.recommended_video.summary_title(),
            userData=self.verdict.recommended_video
        )
        for alt in self.verdict.alternative_videos:
            self.combo_video.addItem(alt.summary_title(), userData=alt)
        cv_layout.addWidget(self.combo_video)

        self.lbl_v_details = QLabel(self.verdict.recommended_video.details_str)
        self.lbl_v_details.setProperty("class", "subText")
        cv_layout.addWidget(self.lbl_v_details)
        root.addWidget(card_v)

        # Card 2: Dubbed Target Audio Stream
        card_a = QFrame()
        card_a.setObjectName("bentoCard")
        card_a.setProperty("class", "bentoCard")
        ca_layout = QVBoxLayout(card_a)
        ca_layout.setSpacing(8)

        a_head = QHBoxLayout()
        a_title = QLabel("2. Faixa Alvo (Dublagem em Português)")
        a_title.setProperty("class", "cardTitle")
        a_head.addWidget(a_title)
        a_head.addStretch()

        is_high_conf = not self.verdict.is_ambiguous
        badge_a_text = self.verdict.recommended_target_audio.badge_label if self.verdict.recommended_target_audio else "Seleção Manual"
        badge_a = QLabel(badge_a_text)
        badge_a.setProperty("class", "badgeGreen" if is_high_conf else "badgeAmber")
        a_head.addWidget(badge_a)
        ca_layout.addLayout(a_head)

        self.combo_target_audio = QComboBox()
        if self.verdict.recommended_target_audio:
            self.combo_target_audio.addItem(
                self.verdict.recommended_target_audio.summary_title(),
                userData=self.verdict.recommended_target_audio
            )
        for alt in self.verdict.alternative_audios:
            self.combo_target_audio.addItem(alt.summary_title(), userData=alt)
        ca_layout.addWidget(self.combo_target_audio)

        self.lbl_a_details = QLabel(
            self.verdict.recommended_target_audio.details_str if self.verdict.recommended_target_audio else ""
        )
        self.lbl_a_details.setProperty("class", "subText")
        ca_layout.addWidget(self.lbl_a_details)
        root.addWidget(card_a)

        # Card 3: Reference & Preservation Audio Stream
        card_ref = QFrame()
        card_ref.setObjectName("bentoCard")
        card_ref.setProperty("class", "bentoCard")
        cr_layout = QVBoxLayout(card_ref)
        cr_layout.setSpacing(8)

        r_head = QHBoxLayout()
        r_title = QLabel("3. Faixa de Referência Acústica (Áudio Original)")
        r_title.setProperty("class", "cardTitle")
        r_head.addWidget(r_title)
        r_head.addStretch()

        badge_r = QLabel("Referência FFT")
        badge_r.setProperty("class", "badgeNeutral")
        r_head.addWidget(badge_r)
        cr_layout.addLayout(r_head)

        self.combo_ref_audio = QComboBox()
        if self.verdict.reference_audio:
            self.combo_ref_audio.addItem(
                self.verdict.reference_audio.summary_title(),
                userData=self.verdict.reference_audio
            )
        for alt in self.verdict.alternative_audios:
            if alt != self.verdict.reference_audio:
                self.combo_ref_audio.addItem(alt.summary_title(), userData=alt)
        cr_layout.addWidget(self.combo_ref_audio)

        self.check_keep_original = QCheckBox("Manter também o áudio original em inglês como faixa secundária no MKV")
        self.check_keep_original.setChecked(True)
        cr_layout.addWidget(self.check_keep_original)

        root.addWidget(card_ref)

        # Action Buttons Row
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.setProperty("class", "btnSecondary")
        self.btn_cancel.setFixedHeight(34)
        self.btn_cancel.setCursor(Qt.PointingHandCursor)
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)

        btn_layout.addStretch()

        self.btn_confirm = QPushButton("Confirmar e Sincronizar Tudo")
        self.btn_confirm.setProperty("class", "btnSuccess")
        self.btn_confirm.setFixedHeight(44)
        self.btn_confirm.setCursor(Qt.PointingHandCursor)
        self.btn_confirm.setDefault(True)
        self.btn_confirm.setFocus()
        self.btn_confirm.clicked.connect(self.accept)
        btn_layout.addWidget(self.btn_confirm)

        root.addLayout(btn_layout)

    def keyPressEvent(self, event):
        """Allows instant confirmation via Enter key."""
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.accept()
        elif event.key() == Qt.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)

    def get_selection(self) -> Tuple[StreamCandidate, StreamCandidate, StreamCandidate, bool]:
        """Returns the confirmed stream candidates and original audio preservation flag."""
        chosen_video = self.combo_video.currentData()
        chosen_target = self.combo_target_audio.currentData()
        chosen_ref = self.combo_ref_audio.currentData()
        keep_original = self.check_keep_original.isChecked()

        return chosen_video, chosen_target, chosen_ref, keep_original
