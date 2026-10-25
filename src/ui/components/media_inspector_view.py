"""Media inspector view for deep single-file inspection mode."""

import os
from typing import Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QWidget,
    QSizePolicy
)

from ...core.disk_utils import format_bytes
from ...core.models import (
    MediaInspectionReport,
    VideoStreamDetail,
    AudioStreamDetail,
    SubtitleDetail,
    format_channel_layout_label
)


def format_duration(seconds: float) -> str:
    """Formats duration in seconds to HH:MM:SS format."""
    if seconds <= 0:
        return "00:00:00"
    total_sec = int(round(seconds))
    h = total_sec // 3600
    m = (total_sec % 3600) // 60
    s = total_sec % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


def get_resolution_label(width: int, height: int) -> str:
    """Returns user-friendly resolution classification label."""
    if width >= 3800 or height >= 2100:
        return f"{width}x{height} (4K UHD)"
    elif width >= 2500 or height >= 1400:
        return f"{width}x{height} (2.5K QHD)"
    elif width >= 1900 or height >= 1000:
        return f"{width}x{height} (Full HD 1080p)"
    elif width >= 1200 or height >= 700:
        return f"{width}x{height} (HD 720p)"
    elif width > 0 and height > 0:
        return f"{width}x{height} (SD)"
    return "Resolução Desconhecida"


class MediaInspectorView(QFrame):
    """
    Deep inspection workbench for single ingested media containers or isolated audio files.
    Features:
    - 100% continuous rounded geometry (zero sharp corners).
    - Monochrome neutral palette with functional status colors.
    - Video specification card (resolution, fps, codec, HDR/Dolby Vision, color profile).
    - Audio stream list with channel layout pills, immersive audio badges, sample rates.
    - Subtitle and chapter summary.
    - Isolated audio special panel with reference video advisory notice.
    - Connective action footer to seamlessly ingest a second source.
    """
    add_second_source_clicked = Signal()
    reset_requested = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("mediaInspectorView")
        self.setProperty("class", "mediaInspectorView")
        self.theme_mode = "dark"
        self._report: Optional[MediaInspectionReport] = None

        self.init_ui()

    def init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setObjectName("inspectorScrollArea")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.content_widget = QWidget()
        self.content_widget.setObjectName("inspectorContentWidget")
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(16, 16, 16, 16)
        self.content_layout.setSpacing(14)

        self.scroll_area.setWidget(self.content_widget)
        root_layout.addWidget(self.scroll_area)

        # Loading container
        self.card_loading = QFrame()
        self.card_loading.setObjectName("cardInspectorLoading")
        self.card_loading.setProperty("class", "inspectorCard")
        cl_layout = QVBoxLayout(self.card_loading)
        cl_layout.setContentsMargins(24, 32, 24, 32)
        cl_layout.setAlignment(Qt.AlignCenter)
        cl_layout.setSpacing(12)

        self.lbl_loading_title = QLabel("Inspecionando arquivo com ffprobe...")
        self.lbl_loading_title.setAlignment(Qt.AlignCenter)
        self.lbl_loading_title.setStyleSheet("font-size: 14px; font-weight: 700; color: #f2f3f7;")
        cl_layout.addWidget(self.lbl_loading_title)

        lbl_loading_sub = QLabel("Extraindo topologia de contêiner, trilhas de vídeo, áudio, legendas e capítulos...")
        lbl_loading_sub.setAlignment(Qt.AlignCenter)
        lbl_loading_sub.setStyleSheet("font-size: 12px; color: #9a9eac;")
        cl_layout.addWidget(lbl_loading_sub)

        self.content_layout.addWidget(self.card_loading)
        self.card_loading.setVisible(False)

        # Error container
        self.card_error = QFrame()
        self.card_error.setObjectName("cardInspectorError")
        self.card_error.setProperty("class", "inspectorCard")
        ce_layout = QVBoxLayout(self.card_error)
        ce_layout.setContentsMargins(20, 20, 20, 20)
        ce_layout.setSpacing(10)

        err_badge = QLabel("Contêiner corrompido ou formato não suportado")
        err_badge.setObjectName("badgeInspectorError")
        err_badge.setFixedHeight(28)
        err_badge.setAlignment(Qt.AlignCenter)
        err_badge.setStyleSheet(
            "background-color: rgba(224, 60, 60, 0.15); color: #e03c3c; "
            "border: 1px solid #e03c3c; border-radius: 14px; font-weight: 700; font-size: 11px; padding: 0 14px;"
        )
        ce_layout.addWidget(err_badge, alignment=Qt.AlignLeft)

        self.lbl_error_details = QLabel("")
        self.lbl_error_details.setWordWrap(True)
        self.lbl_error_details.setStyleSheet("font-size: 12px; color: #f2f3f7;")
        ce_layout.addWidget(self.lbl_error_details)

        btn_retry_row = QHBoxLayout()
        btn_reset_err = QPushButton("Limpar e tentar outro arquivo")
        btn_reset_err.setProperty("class", "btnSecondary")
        btn_reset_err.setFixedHeight(36)
        btn_reset_err.setCursor(Qt.PointingHandCursor)
        btn_reset_err.clicked.connect(self.reset_requested.emit)
        btn_retry_row.addWidget(btn_reset_err)
        btn_retry_row.addStretch()
        ce_layout.addLayout(btn_retry_row)

        self.content_layout.addWidget(self.card_error)
        self.card_error.setVisible(False)

        # Dynamic report widgets container
        self.report_container = QWidget()
        self.report_layout = QVBoxLayout(self.report_container)
        self.report_layout.setContentsMargins(0, 0, 0, 0)
        self.report_layout.setSpacing(14)
        self.content_layout.addWidget(self.report_container)

    def set_loading(self, file_path: str):
        """Displays async loading indicator."""
        self.card_error.setVisible(False)
        self.report_container.setVisible(False)
        self.lbl_loading_title.setText(f"Inspecionando {os.path.basename(file_path)}...")
        self.card_loading.setVisible(True)

    def set_error(self, err_message: str):
        """Displays error message card."""
        self.card_loading.setVisible(False)
        self.report_container.setVisible(False)
        self.lbl_error_details.setText(err_message)
        self.card_error.setVisible(True)

    def set_report(self, report: MediaInspectionReport):
        """Populates inspector view with technical report data."""
        self._report = report
        self.card_loading.setVisible(False)
        self.card_error.setVisible(False)
        self.report_container.setVisible(True)

        is_light = getattr(self, "theme_mode", "dark") == "light"
        text_primary = "#16181d" if is_light else "#f2f3f7"
        text_secondary = "#575d6e" if is_light else "#9a9eac"
        card_bg = "#f5f6fa" if is_light else "#222329"
        card_border = "#dcdfe8" if is_light else "#33343b"
        row_bg = "#ffffff" if is_light else "#1b1c20"
        row_border = "#e2e4ec" if is_light else "#2c2d34"
        badge_bg = "#e5e7ef" if is_light else "#222329"
        badge_border = "#dcdfe8" if is_light else "#33343b"
        notice_bg = "#fbf5ee" if is_light else "#1e1f25"
        notice_border = "#e8963a" if is_light else "#33343b"

        # Clear existing dynamic widgets
        while self.report_layout.count():
            item = self.report_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        # ----------------------------------------------------------------------
        # 1. Header Card (File identity and container specs)
        # ----------------------------------------------------------------------
        card_header = QFrame()
        card_header.setObjectName("cardInspectorHeader")
        card_header.setProperty("class", "inspectorCard")
        card_header.setStyleSheet(
            f"QFrame#cardInspectorHeader {{ background-color: {card_bg}; border: 1px solid {card_border}; border-radius: 20px; }} "
            f"QLabel {{ border: none; background: transparent; }}"
        )
        ch_layout = QVBoxLayout(card_header)
        ch_layout.setContentsMargins(18, 14, 18, 14)
        ch_layout.setSpacing(8)

        head_row = QHBoxLayout()
        head_row.setSpacing(10)

        lbl_mode_chip = QLabel("MODO INSPEÇÃO")
        lbl_mode_chip.setObjectName("chipInspectorMode")
        lbl_mode_chip.setFixedHeight(24)
        lbl_mode_chip.setAlignment(Qt.AlignCenter)
        lbl_mode_chip.setStyleSheet(
            f"background-color: {badge_bg}; color: {text_primary}; border: 1px solid {badge_border}; "
            f"border-radius: 12px; font-weight: 700; font-size: 10px; padding: 0 10px;"
        )
        head_row.addWidget(lbl_mode_chip)

        self.badge_format = QLabel(report.container_format)
        self.badge_format.setObjectName("badgeInspectorFormat")
        self.badge_format.setFixedHeight(24)
        self.badge_format.setAlignment(Qt.AlignCenter)
        self.badge_format.setStyleSheet(
            f"background-color: {badge_bg}; color: #2fb16b; border: 1px solid #2fb16b; "
            f"border-radius: 12px; font-weight: 700; font-size: 10px; padding: 0 10px;"
        )
        head_row.addWidget(self.badge_format)
        head_row.addStretch()

        btn_reset = QPushButton("Trocar arquivo")
        btn_reset.setObjectName("btnResetInspector")
        btn_reset.setProperty("class", "btnSm")
        btn_reset.setFixedHeight(28)
        btn_reset.setCursor(Qt.PointingHandCursor)
        btn_reset.clicked.connect(self.reset_requested.emit)
        head_row.addWidget(btn_reset)
        ch_layout.addLayout(head_row)

        lbl_filename = QLabel(report.file_name)
        lbl_filename.setObjectName("lblInspectorFilename")
        lbl_filename.setWordWrap(True)
        lbl_filename.setStyleSheet(f"font-size: 15px; font-weight: 700; color: {text_primary}; border: none; background: transparent;")
        ch_layout.addWidget(lbl_filename)

        sz_str = format_bytes(report.file_size_bytes)
        dur_str = format_duration(report.duration_sec)
        streams_summary = f"{len(report.video_streams)} vídeo · {len(report.audio_streams)} áudio · {len(report.subtitle_streams)} legendas"
        if report.is_audio_only:
            streams_summary = f"{len(report.audio_streams)} faixa(s) de áudio · Áudio isolado"

        meta_parts = [sz_str, dur_str, streams_summary]
        lbl_meta = QLabel("  •  ".join(meta_parts))
        lbl_meta.setStyleSheet(f"font-size: 12px; color: {text_secondary}; border: none; background: transparent;")
        ch_layout.addWidget(lbl_meta)

        self.report_layout.addWidget(card_header)

        # ----------------------------------------------------------------------
        # 2. Isolated Audio Advisory Notice (if audio only)
        # ----------------------------------------------------------------------
        if report.is_audio_only:
            card_notice = QFrame()
            card_notice.setObjectName("cardAudioNotice")
            card_notice.setStyleSheet(
                f"QFrame#cardAudioNotice {{ background-color: {notice_bg}; border: 1px solid {notice_border}; border-radius: 16px; }} "
                f"QLabel {{ border: none; background: transparent; }}"
            )
            cn_layout = QHBoxLayout(card_notice)
            cn_layout.setContentsMargins(12, 10, 12, 10)
            cn_layout.setSpacing(12)

            lbl_notice_icon = QLabel("INFO")
            lbl_notice_icon.setFixedHeight(24)
            lbl_notice_icon.setStyleSheet(
                f"background-color: {badge_bg}; color: #e8963a; border: 1px solid #e8963a; "
                f"border-radius: 12px; font-weight: 700; font-size: 10px; padding: 0 10px;"
            )
            cn_layout.addWidget(lbl_notice_icon)

            lbl_notice_text = QLabel(
                "Arquivo de áudio isolado detectado. Para sincronização e remux de vídeo, "
                "adicione um arquivo de vídeo de referência abaixo."
            )
            lbl_notice_text.setWordWrap(True)
            lbl_notice_text.setStyleSheet(f"font-size: 12px; color: {text_primary};")
            cn_layout.addWidget(lbl_notice_text, 1)

            self.report_layout.addWidget(card_notice)

        # ----------------------------------------------------------------------
        # 3. Video Stream Card (if not audio only and video streams exist)
        # ----------------------------------------------------------------------
        if not report.is_audio_only and report.video_streams:
            card_video = QFrame()
            card_video.setObjectName("cardInspectorVideo")
            card_video.setProperty("class", "inspectorCard")
            card_video.setStyleSheet(
                f"QFrame#cardInspectorVideo {{ background-color: {card_bg}; border: 1px solid {card_border}; border-radius: 20px; }} "
                f"QLabel {{ border: none; background: transparent; }}"
            )
            cv_layout = QVBoxLayout(card_video)
            cv_layout.setContentsMargins(18, 14, 18, 14)
            cv_layout.setSpacing(10)

            v_head = QHBoxLayout()
            v_title = QLabel("Fluxo de Vídeo")
            v_title.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {text_primary}; border: none; background: transparent;")
            v_head.addWidget(v_title)
            v_head.addStretch()

            lbl_v_count = QLabel(f"{len(report.video_streams)} stream(s)")
            lbl_v_count.setStyleSheet(
                f"background-color: {badge_bg}; color: {text_secondary}; border: 1px solid {badge_border}; "
                f"border-radius: 10px; font-size: 10px; font-weight: 600; padding: 2px 8px;"
            )
            v_head.addWidget(lbl_v_count)
            cv_layout.addLayout(v_head)

            primary_v = report.video_streams[0]
            res_label = get_resolution_label(primary_v.width, primary_v.height)
            lbl_res = QLabel(res_label)
            lbl_res.setStyleSheet(f"font-size: 18px; font-weight: 800; color: {text_primary}; border: none; background: transparent;")
            cv_layout.addWidget(lbl_res)

            # Chips Grid
            chips_row = QHBoxLayout()
            chips_row.setSpacing(8)

            # Codec chip
            chip_codec = QLabel(primary_v.codec.upper())
            chip_codec.setFixedHeight(24)
            chip_codec.setStyleSheet(
                f"background-color: {badge_bg}; color: {text_primary}; border: 1px solid {badge_border}; "
                f"border-radius: 12px; font-weight: 700; font-size: 11px; padding: 0 10px;"
            )
            chips_row.addWidget(chip_codec)

            # FPS chip
            if primary_v.fps > 0:
                chip_fps = QLabel(f"{primary_v.fps:.3f} fps")
                chip_fps.setFixedHeight(24)
                chip_fps.setStyleSheet(
                    f"background-color: {badge_bg}; color: {text_primary}; border: 1px solid {badge_border}; "
                    f"border-radius: 12px; font-weight: 600; font-size: 11px; padding: 0 10px;"
                )
                chips_row.addWidget(chip_fps)

            # HDR / Dolby Vision chip
            hdr_txt = primary_v.hdr_format or "SDR (Rec.709)"
            chip_hdr = QLabel(hdr_txt)
            chip_hdr.setFixedHeight(24)
            hdr_color = "#2fb16b" if primary_v.hdr_format else text_secondary
            chip_hdr.setStyleSheet(
                f"background-color: {badge_bg}; color: {hdr_color}; border: 1px solid {badge_border}; "
                f"border-radius: 12px; font-weight: 700; font-size: 11px; padding: 0 10px;"
            )
            chips_row.addWidget(chip_hdr)

            # Bit depth chip
            chip_depth = QLabel(f"{primary_v.bit_depth}-bit")
            chip_depth.setFixedHeight(24)
            chip_depth.setStyleSheet(
                f"background-color: {badge_bg}; color: {text_secondary}; border: 1px solid {badge_border}; "
                f"border-radius: 12px; font-weight: 600; font-size: 11px; padding: 0 10px;"
            )
            chips_row.addWidget(chip_depth)

            chips_row.addStretch()
            cv_layout.addLayout(chips_row)

            self.report_layout.addWidget(card_video)

        # ----------------------------------------------------------------------
        # 4. Audio Streams Card
        # ----------------------------------------------------------------------
        if report.audio_streams:
            card_audio = QFrame()
            card_audio.setObjectName("cardInspectorAudio")
            card_audio.setProperty("class", "inspectorCard")
            card_audio.setStyleSheet(
                f"QFrame#cardInspectorAudio {{ background-color: {card_bg}; border: 1px solid {card_border}; border-radius: 20px; }} "
                f"QLabel {{ border: none; background: transparent; }}"
            )
            ca_layout = QVBoxLayout(card_audio)
            ca_layout.setContentsMargins(18, 14, 18, 14)
            ca_layout.setSpacing(10)

            a_head = QHBoxLayout()
            a_title = QLabel("Faixas de Áudio")
            a_title.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {text_primary}; border: none; background: transparent;")
            a_head.addWidget(a_title)
            a_head.addStretch()

            lbl_a_count = QLabel(f"{len(report.audio_streams)} faixa(s)")
            lbl_a_count.setStyleSheet(
                f"background-color: {badge_bg}; color: {text_secondary}; border: 1px solid {badge_border}; "
                f"border-radius: 10px; font-size: 10px; font-weight: 600; padding: 2px 8px;"
            )
            a_head.addWidget(lbl_a_count)
            ca_layout.addLayout(a_head)

            for idx, a_stream in enumerate(report.audio_streams):
                track_row = QFrame()
                track_row.setObjectName(f"trackRow_{idx}")
                track_row.setStyleSheet(
                    f"QFrame#trackRow_{idx} {{ background-color: {row_bg}; border: 1px solid {row_border}; border-radius: 12px; }} "
                    f"QLabel {{ border: none; background: transparent; }}"
                )
                tr_layout = QHBoxLayout(track_row)
                tr_layout.setContentsMargins(8, 4, 8, 4)
                tr_layout.setSpacing(10)

                # Track index chip
                chip_idx = QLabel(f"A{idx + 1:02d}")
                chip_idx.setFixedHeight(22)
                chip_idx.setStyleSheet(
                    f"background-color: {badge_bg}; color: {text_primary}; border: 1px solid {badge_border}; "
                    f"border-radius: 11px; font-weight: 700; font-size: 10px; padding: 0 8px;"
                )
                tr_layout.addWidget(chip_idx)

                # Language chip
                lang_str = (a_stream.language or "und").upper()
                chip_lang = QLabel(lang_str)
                chip_lang.setFixedHeight(22)
                chip_lang.setStyleSheet(
                    f"background-color: {badge_bg}; color: {text_secondary}; border: 1px solid {badge_border}; "
                    f"border-radius: 11px; font-weight: 700; font-size: 10px; padding: 0 8px;"
                )
                tr_layout.addWidget(chip_lang)

                # Title and details text
                track_details = []
                if a_stream.title:
                    track_details.append(a_stream.title)
                track_details.append(a_stream.codec.upper())

                lbl_track_info = QLabel("  •  ".join(track_details))
                lbl_track_info.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {text_primary}; border: none; background: transparent;")
                tr_layout.addWidget(lbl_track_info, 1)

                # Channel layout badge
                layout_txt = a_stream.immersive_type or format_channel_layout_label(a_stream.channels, a_stream.channel_layout)
                badge_ch = QLabel(layout_txt)
                badge_ch.setFixedHeight(22)
                badge_ch_color = "#2fb16b" if a_stream.is_immersive or a_stream.channels >= 8 else text_secondary
                badge_ch.setStyleSheet(
                    f"background-color: {badge_bg}; color: {badge_ch_color}; border: 1px solid {badge_border}; "
                    f"border-radius: 11px; font-weight: 700; font-size: 10px; padding: 0 8px;"
                )
                tr_layout.addWidget(badge_ch)

                # Sample rate & Bitrate
                specs = []
                if a_stream.sample_rate > 0:
                    specs.append(f"{a_stream.sample_rate:,} Hz".replace(",", "."))
                if a_stream.bit_rate > 0:
                    kbps = int(round(a_stream.bit_rate / 1000.0))
                    specs.append(f"{kbps} kbps")
                if specs:
                    lbl_specs = QLabel(" · ".join(specs))
                    lbl_specs.setStyleSheet(f"font-size: 11px; color: {text_secondary}; border: none; background: transparent;")
                    tr_layout.addWidget(lbl_specs)

                ca_layout.addWidget(track_row)

            self.report_layout.addWidget(card_audio)

        # ----------------------------------------------------------------------
        # 5. Subtitles & Chapters Card (if any or if container supports)
        # ----------------------------------------------------------------------
        if report.subtitle_streams or report.chapter_count > 0:
            card_subs = QFrame()
            card_subs.setObjectName("cardInspectorSubs")
            card_subs.setProperty("class", "inspectorCard")
            card_subs.setStyleSheet(
                f"QFrame#cardInspectorSubs {{ background-color: {card_bg}; border: 1px solid {card_border}; border-radius: 20px; }} "
                f"QLabel {{ border: none; background: transparent; }}"
            )
            cs_layout = QVBoxLayout(card_subs)
            cs_layout.setContentsMargins(18, 14, 18, 14)
            cs_layout.setSpacing(8)

            s_head = QHBoxLayout()
            s_title = QLabel("Legendas e Capítulos")
            s_title.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {text_primary};")
            s_head.addWidget(s_title)
            s_head.addStretch()

            details_parts = []
            if report.subtitle_streams:
                details_parts.append(f"{len(report.subtitle_streams)} legenda(s)")
            if report.chapter_count > 0:
                details_parts.append(f"{report.chapter_count} capítulo(s)")
            lbl_counts = QLabel(" · ".join(details_parts))
            lbl_counts.setStyleSheet(f"font-size: 11px; color: {text_secondary};")
            s_head.addWidget(lbl_counts)
            cs_layout.addLayout(s_head)

            if report.subtitle_streams:
                subs_chips = QHBoxLayout()
                subs_chips.setSpacing(6)
                for s in report.subtitle_streams[:8]:  # show up to first 8
                    lang = (s.language or "und").upper()
                    codec = (s.codec or "sub").upper()
                    chip = QLabel(f"{lang} ({codec})")
                    chip.setFixedHeight(22)
                    chip.setStyleSheet(
                        f"background-color: {badge_bg}; color: {text_secondary}; border: 1px solid {badge_border}; "
                        f"border-radius: 11px; font-size: 10px; font-weight: 600; padding: 0 8px;"
                    )
                    subs_chips.addWidget(chip)
                if len(report.subtitle_streams) > 8:
                    chip_more = QLabel(f"+{len(report.subtitle_streams) - 8}")
                    chip_more.setFixedHeight(22)
                    chip_more.setStyleSheet(
                        f"background-color: {badge_bg}; color: {text_secondary}; border: 1px solid {badge_border}; "
                        f"border-radius: 11px; font-size: 10px; font-weight: 600; padding: 0 8px;"
                    )
                    subs_chips.addWidget(chip_more)
                subs_chips.addStretch()
                cs_layout.addLayout(subs_chips)

            self.report_layout.addWidget(card_subs)

        # ----------------------------------------------------------------------
        # 6. Connective Action Footer (Add second file seamlessly)
        # ----------------------------------------------------------------------
        card_action = QFrame()
        card_action.setObjectName("cardInspectorAction")
        ca_foot_layout = QVBoxLayout(card_action)
        ca_foot_layout.setContentsMargins(0, 4, 0, 0)
        ca_foot_layout.setSpacing(8)

        btn_connective = QPushButton("Arraste uma segunda fonte ou clique para selecionar e ativar o sincronizador")
        btn_connective.setObjectName("btnConnectiveAction")
        btn_connective.setFixedHeight(50)
        btn_connective.setCursor(Qt.PointingHandCursor)
        if is_light:
            btn_connective.setStyleSheet(
                "QPushButton#btnConnectiveAction { "
                "  border: 2px dashed #b8bcc8; "
                "  border-radius: 22px; "
                "  background-color: #ffffff; "
                "  color: #16181d; "
                "  font-size: 13px; "
                "  font-weight: 700; "
                "  padding: 0 20px; "
                "} "
                "QPushButton#btnConnectiveAction:hover { "
                "  border-color: #2fb16b; "
                "  background-color: #f5f6fa; "
                "  color: #000000; "
                "} "
                "QPushButton#btnConnectiveAction:pressed { "
                "  border-color: #1e7e48; "
                "  background-color: #e5e7ef; "
                "}"
            )
        else:
            btn_connective.setStyleSheet(
                "QPushButton#btnConnectiveAction { "
                "  border: 2px dashed #33343b; "
                "  border-radius: 22px; "
                "  background-color: #16171b; "
                "  color: #f2f3f7; "
                "  font-size: 13px; "
                "  font-weight: 700; "
                "  padding: 0 20px; "
                "} "
                "QPushButton#btnConnectiveAction:hover { "
                "  border-color: #2fb16b; "
                "  background-color: #1c1d22; "
                "  color: #ffffff; "
                "} "
                "QPushButton#btnConnectiveAction:pressed { "
                "  border-color: #1e7e48; "
                "  background-color: #121316; "
                "}"
            )
        btn_connective.clicked.connect(self.add_second_source_clicked.emit)
        ca_foot_layout.addWidget(btn_connective)

        self.report_layout.addWidget(card_action)

    def set_theme_mode(self, mode: str):
        """Updates styling for dark or light theme."""
        self.theme_mode = mode
        if mode == "light":
            self.setStyleSheet(
                "QFrame#mediaInspectorView { background-color: #f1f2f6; border-radius: 20px; border: none; } "
                "QFrame.inspectorCard { background-color: #ffffff; border-radius: 20px; border: 1px solid #dcdfe8; } "
            )
            self.lbl_loading_title.setStyleSheet("font-size: 14px; font-weight: 700; color: #16181d;")
            self.lbl_error_details.setStyleSheet("font-size: 12px; color: #16181d;")
        else:
            self.setStyleSheet(
                "QFrame#mediaInspectorView { background-color: #1b1c20; border-radius: 20px; border: 1px solid #2c2d34; } "
                "QFrame.inspectorCard { background-color: #222329; border-radius: 20px; border: 1px solid #33343b; } "
            )
            self.lbl_loading_title.setStyleSheet("font-size: 14px; font-weight: 700; color: #f2f3f7;")
            self.lbl_error_details.setStyleSheet("font-size: 12px; color: #f2f3f7;")
        if hasattr(self, "_report") and self._report:
            self.set_report(self._report)
