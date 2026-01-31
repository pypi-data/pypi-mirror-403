from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QDoubleSpinBox,
    QPushButton,
    QGroupBox,
    QApplication,
    QCheckBox,
    QDialog,
    QTextEdit,
    QApplication,
)

from pathlib import Path
from weegit import settings
from weegit.core.analysis.script_template import TEMPLATE, EVENTS_BLOCK, SPIKES_BLOCK
from weegit.gui.dialogs.loading_dialog import LoadingDialog


class AnalysisPanel(QWidget):
    """Panel for analysis settings and spike detection."""

    def __init__(self, session_manager, parent=None):
        super().__init__(parent)
        self._session_manager = session_manager
        self.setup_ui()
        self.connect_signals()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(8)

        spikes_group = QGroupBox("Analysis")
        spikes_layout = QVBoxLayout(spikes_group)
        spikes_threshold_layout = QHBoxLayout()
        spikes_threshold_layout.addWidget(QLabel("Spikes threshold:"))
        self.spikes_threshold_spinbox = QDoubleSpinBox()
        self.spikes_threshold_spinbox.setRange(0.0, 1e9)
        self.spikes_threshold_spinbox.setSingleStep(0.1)
        self.spikes_threshold_spinbox.setValue(5.0)
        spikes_threshold_layout.addWidget(self.spikes_threshold_spinbox)
        spikes_layout.addLayout(spikes_threshold_layout)

        self.spikes_recalculate_btn = QPushButton("Find spikes in current window")
        spikes_layout.addWidget(self.spikes_recalculate_btn)

        layout.addWidget(spikes_group)

        scripts_group = QGroupBox("Scripts")
        scripts_layout = QVBoxLayout(scripts_group)
        include_layout = QHBoxLayout()
        self.include_events_checkbox = QCheckBox("Include events")
        self.include_spikes_checkbox = QCheckBox("Include spikes")
        include_layout.addWidget(self.include_events_checkbox)
        include_layout.addWidget(self.include_spikes_checkbox)
        include_layout.addStretch(1)
        scripts_layout.addLayout(include_layout)
        self.generate_script_btn = QPushButton("Generate script")
        scripts_layout.addWidget(self.generate_script_btn)
        layout.addWidget(scripts_group)

        layout.addStretch(1)

    def connect_signals(self):
        self.spikes_recalculate_btn.clicked.connect(self.on_spikes_recalculate_clicked)
        self.generate_script_btn.clicked.connect(self.on_generate_script_clicked)
        self._session_manager.session_loaded.connect(self.on_session_loaded)
        self._session_manager.spikes_changed.connect(self.on_spikes_changed)

    def on_session_loaded(self):
        session = self._session_manager.current_user_session
        if session and session.cached_spikes:
            current_spikes = session.cached_spikes.get(session.gui_setup.current_sweep_idx)
            if current_spikes is not None:
                self.spikes_threshold_spinbox.setValue(current_spikes.threshold)

    def on_spikes_changed(self, spikes):
        self.spikes_threshold_spinbox.blockSignals(True)
        self.spikes_threshold_spinbox.setValue(spikes.threshold)
        self.spikes_threshold_spinbox.blockSignals(False)

    def on_spikes_recalculate_clicked(self):
        if not self._session_manager.session_is_active:
            return

        threshold = float(self.spikes_threshold_spinbox.value())
        loading = LoadingDialog("Detecting spikes...", self)
        loading.show()
        loading.raise_()
        loading.activateWindow()
        QApplication.processEvents()

        session = self._session_manager.current_user_session
        experiment = self._session_manager.experiment_data
        if not session or not experiment:
            loading.close()
            return

        sweep_idx = session.gui_setup.current_sweep_idx
        channel_indexes = [idx for idx in session.eeg_channel_indexes]
        spikes = experiment.detect_spikes(
            threshold=threshold,
            sweep_idx=sweep_idx,
            channel_indexes=channel_indexes,
            params=self._session_manager.gui_setup,
        )
        self._session_manager.set_spikes(sweep_idx, spikes)
        loading.close()

    def on_generate_script_clicked(self):
        if not self._session_manager.session_is_active:
            return
        out_folder = ""
        if self._session_manager.weegit_experiment_folder:
            out_folder = str(self._session_manager.weegit_experiment_folder)
        session_name = ""
        session = self._session_manager.current_user_session
        if session:
            session_name = Path(session.session_filename).stem

        events_block = EVENTS_BLOCK if self.include_events_checkbox.isChecked() else ""
        spikes_block = SPIKES_BLOCK if self.include_spikes_checkbox.isChecked() else ""
        script = TEMPLATE.format(
            out_weegit_folder=out_folder,
            session_name=session_name,
            events_block=events_block,
            spikes_block=spikes_block,
        )

        dialog = QDialog(self)
        dialog.setWindowTitle("Generated script")
        layout = QVBoxLayout(dialog)
        header_layout = QHBoxLayout()
        copy_btn = QPushButton("Copy to clipboard")
        header_layout.addStretch(1)
        header_layout.addWidget(copy_btn)
        layout.addLayout(header_layout)
        editor = QTextEdit()
        editor.setReadOnly(True)
        editor.setPlainText(script)
        layout.addWidget(editor)
        copy_btn.clicked.connect(lambda: QApplication.clipboard().setText(script))
        dialog.resize(800, 600)
        dialog.exec()
