from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QLabel, QProgressBar, QVBoxLayout


class LoadingDialog(QDialog):
    def __init__(self, text="Loading...", parent=None,):
        super().__init__(parent)
        self.setup_ui(text)

    def setup_ui(self, text):
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.FramelessWindowHint
        )
        self.setFixedSize(300, 75)

        # Remove close button
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowCloseButtonHint)

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)

        # Message label
        self.message_label = QLabel(text)
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.message_label.setStyleSheet("font-size: 14px; margin-bottom: 20px;")

        # Progress bar (indeterminate)
        # self.progress_bar = QProgressBar()
        # self.progress_bar.setRange(0, 0)  # This makes it indeterminate
        # self.progress_bar.setTextVisible(False)
        # self.progress_bar.setFixedHeight(20)

        # Add widgets to layout
        layout.addWidget(self.message_label)
        # layout.addWidget(self.progress_bar)
        layout.addStretch()

        self.setLayout(layout)
