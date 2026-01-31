from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QPixmap, QDesktopServices
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QLineEdit,
    QDialog,
    QListWidget,
    QListWidgetItem,
    QAbstractItemView, QGroupBox,
    QInputDialog,
    QFileDialog,
    QScrollArea,
)
from typing import Dict, List, Optional
import base64
import mimetypes
import urllib.request

from weegit import settings


class ClickableImageLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._original_pixmap: Optional[QPixmap] = None

    def set_pixmap(self, pixmap: Optional[QPixmap], display_pixmap: Optional[QPixmap] = None):
        self._original_pixmap = pixmap
        if pixmap is None:
            self.clear()
            return
        self.setPixmap(display_pixmap or pixmap)

    def mouseDoubleClickEvent(self, event):
        if self._original_pixmap is None:
            return
        dialog = QDialog(self)
        dialog.setWindowTitle("Channels mapping image")
        layout = QVBoxLayout(dialog)
        scroll = QScrollArea()
        label = QLabel()
        label.setPixmap(self._original_pixmap)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        scroll.setWidget(label)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
        dialog.resize(800, 600)
        dialog.exec()


class ChannelSelectionDialog(QDialog):
    def __init__(self, channel_labels: Dict[int, str], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select channels")
        self._channel_labels = channel_labels
        self._selected: List[int] = []
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        for channel_idx, label in self._channel_labels.items():
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, channel_idx)
            self.list_widget.addItem(item)
        layout.addWidget(self.list_widget)

        area_layout = QHBoxLayout()
        area_layout.addWidget(QLabel("Area name:"))
        self.area_input = QLineEdit()
        self.area_input.setPlaceholderText("Enter area name")
        area_layout.addWidget(self.area_input)
        layout.addLayout(area_layout)

        btn_layout = QHBoxLayout()
        self.btn_ok = QPushButton("Add")
        self.btn_cancel = QPushButton("Cancel")
        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_ok)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)

    def selected_channels(self) -> List[int]:
        selected = []
        for item in self.list_widget.selectedItems():
            selected.append(item.data(Qt.ItemDataRole.UserRole))
        return selected

    def area_name(self) -> str:
        return self.area_input.text()


class ChannelsDescriptionPanel(QWidget):
    """Panel for editing per-channel area descriptions."""

    def __init__(self, session_manager, parent=None):
        super().__init__(parent)
        self._session_manager = session_manager
        self._updating = False
        self._mapping_pixmap: Optional[QPixmap] = None
        self._mapping_text: str = ""
        self._mapping_link_url: str = ""
        self.setup_ui()
        self.connect_signals()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(8)

        channels_description_group = QGroupBox("Channels description")
        vertical_layout = QVBoxLayout(channels_description_group)
        header_layout = QHBoxLayout()
        title_label = QLabel("Channels description")
        title_label.setStyleSheet("font-weight: bold;")
        header_layout.addWidget(title_label)
        header_layout.addStretch(1)

        self.btn_add = QPushButton("Add")
        self.btn_delete = QPushButton("Delete")
        header_layout.addWidget(self.btn_add)
        header_layout.addWidget(self.btn_delete)
        vertical_layout.addLayout(header_layout)

        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Channel", "Area"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        vertical_layout.addWidget(self.table)
        layout.addWidget(channels_description_group)

        mapping_group = QGroupBox("Channels mapping image")
        mapping_layout = QVBoxLayout(mapping_group)
        mapping_header = QHBoxLayout()
        mapping_header.addWidget(QLabel("Channels mapping image"))
        mapping_header.addStretch(1)
        mapping_layout.addLayout(mapping_header)

        buttons_layout = QHBoxLayout()
        self.btn_attach_link = QPushButton("Attach link")
        self.btn_attach_file = QPushButton("Attach file")
        buttons_layout.addWidget(self.btn_attach_link)
        buttons_layout.addWidget(self.btn_attach_file)
        mapping_layout.addLayout(buttons_layout)

        self.mapping_text_label = QLabel("")
        self.mapping_text_label.setWordWrap(True)
        self.mapping_text_label.setTextFormat(Qt.TextFormat.RichText)
        self.mapping_text_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        self.mapping_text_label.setOpenExternalLinks(False)
        mapping_layout.addWidget(self.mapping_text_label)

        self.mapping_image_label = ClickableImageLabel()
        self.mapping_image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.mapping_image_label.setMinimumWidth(settings.CHANNELS_MAPPING_IMG_DEFAULT_WIDTH)
        mapping_layout.addWidget(self.mapping_image_label)

        layout.addWidget(mapping_group)

    def connect_signals(self):
        self.btn_add.clicked.connect(self.on_add_clicked)
        self.btn_delete.clicked.connect(self.on_delete_clicked)
        self.btn_attach_link.clicked.connect(self.on_attach_link_clicked)
        self.btn_attach_file.clicked.connect(self.on_attach_file_clicked)
        self._session_manager.session_loaded.connect(self.on_session_loaded)
        self._session_manager.channels_description_changed.connect(self.on_channels_description_changed)
        self._session_manager.channels_mapping_img_changed.connect(self.on_channels_mapping_img_changed)
        self.mapping_text_label.linkActivated.connect(self.on_mapping_link_activated)

    def on_session_loaded(self):
        self.refresh_table(self._session_manager.gui_setup.channels_description)
        self._update_mapping_display(self._session_manager.gui_setup.channels_mapping_img)

    def on_channels_description_changed(self, channels_description: Dict[int, str]):
        self.refresh_table(channels_description)

    def on_channels_mapping_img_changed(self, channels_mapping_img: str):
        self._update_mapping_display(channels_mapping_img)

    def refresh_table(self, channels_description: Dict[int, str]):
        if not self._session_manager.header:
            return
        self._updating = True
        try:
            self.table.setRowCount(0)
            for channel_idx, area in sorted(channels_description.items()):
                self._add_row(channel_idx, area)
        finally:
            self._updating = False

    def _channel_label(self, channel_idx: int) -> str:
        header = self._session_manager.header
        if header and 0 <= channel_idx < len(header.channel_info.name):
            name = header.channel_info.name[channel_idx]
        else:
            name = ""
        return f"{channel_idx} [{name}]"

    def _add_row(self, channel_idx: int, area: str):
        row = self.table.rowCount()
        self.table.insertRow(row)

        channel_item = QTableWidgetItem(self._channel_label(channel_idx))
        channel_item.setData(Qt.ItemDataRole.UserRole, channel_idx)
        channel_item.setFlags(channel_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.table.setItem(row, 0, channel_item)

        area_item = QTableWidgetItem(area or "")
        area_item.setFlags(area_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.table.setItem(row, 1, area_item)

    def on_add_clicked(self):
        if not self._session_manager.header:
            return
        existing = set(self._session_manager.gui_setup.channels_description.keys())
        channel_labels = {
            idx: self._channel_label(idx)
            for idx in range(self._session_manager.header.number_of_channels)
            if idx not in existing
        }
        if not channel_labels:
            return
        dialog = ChannelSelectionDialog(channel_labels, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        selected = dialog.selected_channels()
        if not selected:
            return
        area = dialog.area_name()
        updates = dict(self._session_manager.gui_setup.channels_description)
        for idx in selected:
            updates[idx] = area
        self._session_manager.set_channels_description(updates)

    def on_delete_clicked(self):
        selected_rows = {idx.row() for idx in self.table.selectionModel().selectedRows()}
        if not selected_rows:
            return
        channel_indexes = []
        for row in selected_rows:
            item = self.table.item(row, 0)
            if item is not None:
                channel_indexes.append(item.data(Qt.ItemDataRole.UserRole))
        if channel_indexes:
            self._session_manager.remove_channel_descriptions(channel_indexes)

    def on_attach_link_clicked(self):
        link, ok = QInputDialog.getText(self, "Attach link", "Paste image link:")
        if not ok:
            return
        link = link.strip()
        self._session_manager.set_channels_mapping_img(link)

    def on_attach_file_clicked(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select image",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.gif);;All Files (*)",
        )
        if not file_path:
            return
        try:
            with open(file_path, "rb") as file:
                data = file.read()
        except OSError:
            return
        mime, _ = mimetypes.guess_type(file_path)
        if not mime:
            mime = "image/png"
        encoded = base64.b64encode(data).decode("ascii")
        data_url = f"data:{mime};base64,{encoded}"
        self._session_manager.set_channels_mapping_img(data_url)

    def _update_mapping_display(self, channels_mapping_img: str):
        self._mapping_text = channels_mapping_img or ""
        self._mapping_pixmap = None
        self._mapping_link_url = ""
        self.mapping_image_label.set_pixmap(None)
        if not self._mapping_text:
            self.mapping_text_label.setText("")
            return

        if self._mapping_text.startswith("http://") or self._mapping_text.startswith("https://"):
            self._mapping_link_url = self._mapping_text
            self.mapping_text_label.setText('<a href="mapping">Attached link (click)</a> (double click to view)')
            try:
                with urllib.request.urlopen(self._mapping_text, timeout=5) as response:
                    raw = response.read()
            except Exception:
                self.mapping_text_label.setText(
                    '<a href="mapping">Attached link (click)</a><br>Failed to load image from link'
                )
                return
            pixmap = QPixmap()
            if pixmap.loadFromData(raw):
                self._set_mapping_pixmap(pixmap)
            else:
                self.mapping_text_label.setText(
                    '<a href="mapping">Attached link (click)</a><br>Failed to decode image from link'
                )
            return

        if self._mapping_text.startswith("data:"):
            self.mapping_text_label.setText("Attached file (double click to view)")
            parts = self._mapping_text.split(",", 1)
            if len(parts) != 2:
                self.mapping_text_label.setText("Failed to decode attached file")
                return
            try:
                raw = base64.b64decode(parts[1])
            except Exception:
                self.mapping_text_label.setText("Failed to decode attached file")
                return
            pixmap = QPixmap()
            if pixmap.loadFromData(raw):
                self._set_mapping_pixmap(pixmap)
            else:
                self.mapping_text_label.setText("Failed to decode attached file")
            return

        self.mapping_text_label.setText(self._mapping_text)

    def on_mapping_link_activated(self, link: str):
        if not self._mapping_link_url:
            return
        QDesktopServices.openUrl(QUrl(self._mapping_link_url))

    def _set_mapping_pixmap(self, pixmap: QPixmap):
        self._mapping_pixmap = pixmap
        self._apply_scaled_pixmap()

    def _apply_scaled_pixmap(self):
        if self._mapping_pixmap is None:
            self.mapping_image_label.set_pixmap(None)
            return
        target_width = self.mapping_image_label.width()
        if target_width <= 1:
            target_width = settings.CHANNELS_MAPPING_IMG_DEFAULT_WIDTH
        display = self._mapping_pixmap.scaledToWidth(
            target_width,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.mapping_image_label.set_pixmap(self._mapping_pixmap, display)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._mapping_pixmap is not None:
            self._apply_scaled_pixmap()
