"""Drag and drop file selection card with stream selector."""

import os
from typing import List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget
)

from ...core.models import StreamMetadata
from ...core.disk_utils import format_bytes


class FileDropCard(QFrame):
    """
    Card supporting Drag & Drop and manual file browsing for media files.
    Displays stream information badges and stream selection dropdown.
    """
    file_selected = Signal(str)
    stream_changed = Signal(int)
    multiple_files_dropped = Signal(list)

    def __init__(
        self,
        title: str,
        subtitle: str,
        file_filter: str = "Arquivos de Mídia (*.mkv *.mp4 *.m4v *.avi *.wav *.flac);;Todos (*.*)",
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.title_text = title
        self.subtitle_text = subtitle
        self.file_filter = file_filter
        self.current_file_path: Optional[str] = None
        self.streams: List[StreamMetadata] = []

        self.setObjectName("bentoCard")
        self.setProperty("class", "bentoCard")
        self.setAcceptDrops(True)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(16, 16, 16, 16)

        # Title and badges header
        header_layout = QHBoxLayout()
        self.title_label = QLabel(self.title_text)
        self.title_label.setProperty("class", "cardTitle")
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()

        self.badge_status = QLabel("Aguardando arquivo")
        self.badge_status.setProperty("class", "badgeAmber")
        header_layout.addWidget(self.badge_status)
        layout.addLayout(header_layout)

        # Drag & Drop Target Area
        self.drop_area = QFrame()
        self.drop_area.setStyleSheet("""
            QFrame {
                border: 2px dashed #33343b;
                border-radius: 24px;
                background-color: #1b1c20;
                padding: 14px;
            }
            QFrame:hover {
                border-color: #ffffff;
                background-color: #26272d;
            }
        """)
        drop_layout = QVBoxLayout(self.drop_area)
        drop_layout.setAlignment(Qt.AlignCenter)
        drop_layout.setSpacing(6)

        self.drop_label = QLabel("Arraste e solte o arquivo MKV aqui\nou clique para navegar")
        self.drop_label.setAlignment(Qt.AlignCenter)
        self.drop_label.setStyleSheet("background: transparent; color: #9a9eac; font-size: 12px; border: none;")
        drop_layout.addWidget(self.drop_label)

        btn_browse = QPushButton("Selecionar Arquivo...")
        btn_browse.setProperty("class", "btnSecondary")
        btn_browse.setFixedWidth(160)
        btn_browse.clicked.connect(self._open_file_dialog)
        drop_layout.addWidget(btn_browse, alignment=Qt.AlignCenter)

        layout.addWidget(self.drop_area)

        # File metadata info
        self.info_label = QLabel("Nenhum arquivo carregado")
        self.info_label.setProperty("class", "subText")
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)

        # Stream selector row
        stream_layout = QHBoxLayout()
        stream_lbl = QLabel("Faixa Ativa:")
        stream_lbl.setStyleSheet("background: transparent; color: #f2f3f7; font-weight: 600; border: none;")
        stream_layout.addWidget(stream_lbl)

        self.combo_streams = QComboBox()
        self.combo_streams.currentIndexChanged.connect(self._on_combo_index_changed)
        stream_layout.addWidget(self.combo_streams, 1)

        layout.addLayout(stream_layout)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.drop_area.setStyleSheet("""
                QFrame {
                    border: 2px dashed #ffffff;
                    border-radius: 24px;
                    background-color: #26272d;
                }
            """)

    def dragLeaveEvent(self, event):
        self.drop_area.setStyleSheet("""
            QFrame {
                border: 2px dashed #33343b;
                border-radius: 24px;
                background-color: #1b1c20;
            }
        """)

    def dropEvent(self, event: QDropEvent):
        self.dragLeaveEvent(event)
        urls = event.mimeData().urls()
        valid_paths = [u.toLocalFile() for u in urls if os.path.isfile(u.toLocalFile())]
        if len(valid_paths) >= 2:
            self.multiple_files_dropped.emit(valid_paths)
        elif valid_paths:
            self.set_file_path(valid_paths[0])

    def _open_file_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            f"Selecionar {self.title_text}",
            os.path.expanduser("~"),
            self.file_filter
        )
        if file_path:
            self.set_file_path(file_path)

    def set_file_path(self, path: str):
        self.current_file_path = os.path.abspath(path)
        basename = os.path.basename(path)
        size_bytes = os.path.getsize(path)
        size_str = format_bytes(size_bytes)
        
        self.drop_label.setText(f"Arquivo carregado:\n{basename}")
        self.drop_label.setStyleSheet("background: transparent; color: #38bdf8; font-weight: 600; font-size: 12px; border: none;")
        self.info_label.setText(f"Caminho: {path}\nTamanho: {size_str}")
        self.badge_status.setText("Pronto")
        self.badge_status.setProperty("class", "badgeGreen")
        self.badge_status.setStyle(self.badge_status.style())

        self.file_selected.emit(self.current_file_path)

    def update_streams(self, streams: List[StreamMetadata], default_stream_id: Optional[int] = None):
        """Populates the combo box with available audio/video streams."""
        self.streams = streams
        self.combo_streams.blockSignals(True)
        self.combo_streams.clear()

        selected_idx = 0
        for i, s in enumerate(streams):
            label = s.display_label()
            self.combo_streams.addItem(label, userData=s.id)
            if default_stream_id is not None and s.id == default_stream_id:
                selected_idx = i

        if streams:
            self.combo_streams.setCurrentIndex(selected_idx)
            self.combo_streams.setEnabled(True)
        else:
            self.combo_streams.addItem("Nenhuma faixa detectada", userData=-1)
            self.combo_streams.setEnabled(False)

        self.combo_streams.blockSignals(False)
        self._on_combo_index_changed(self.combo_streams.currentIndex())

    def _on_combo_index_changed(self, index: int):
        if index >= 0 and self.combo_streams.count() > 0:
            track_id = self.combo_streams.currentData()
            if track_id is not None and track_id >= 0:
                self.stream_changed.emit(track_id)

    def get_selected_track_id(self) -> Optional[int]:
        data = self.combo_streams.currentData()
        return data if (data is not None and data >= 0) else None
