from PyQt6.QtCore import QObject, pyqtSignal
from typing import List, Optional, Dict
from pathlib import Path

from weegit import settings
from weegit.core.conversions.filters import BaseFilter
from weegit.core.conversions.transformations import BaseTransformation
from weegit.core.header import Header
from weegit.core.weegit_session import (
    WeegitSessionManager,
    GuiSetup,
    RightPanelWidgetEnum,
    UserSession,
    Event,
    Period,
    AnalogueChannelSetup,
    Spikes,
)

from weegit.gui.commands.base import BaseCommand
from weegit.gui.commands.events import (
    AddEventCommand,
    RemoveEventsCommand,
    SetEventsBadFlagCommand,
    AddEventVocabularyCommand,
    SetEventVocabularyNameCommand,
    RemoveEventVocabularyCommand,
)
from weegit.gui.commands.periods import (
    AddPeriodCommand,
    RemovePeriodsCommand,
    AddPeriodVocabularyCommand,
    SetPeriodVocabularyNameCommand,
    RemovePeriodVocabularyCommand,
)


def user_session_modification(func):
    def wrapper(self, *args, **kwargs):
        if self._session_manager.current_user_session:
            self._session_manager.current_user_session.changes_saved = False
            return func(self, *args, **kwargs)
        else:
            return None

    return wrapper


class QtWeegitSessionManagerWrapper(QObject):

    # Signals for RightPanelWidgetEnum list
    right_panel_widgets_changed = pyqtSignal(list)

    # Signals for filter and transformation lists
    filters_changed = pyqtSignal(list)
    transformations_changed = pyqtSignal(list)

    # Signals for boolean flags
    analogue_panel_is_shown_changed = pyqtSignal(bool)
    traces_are_shown_changed = pyqtSignal(bool)
    csd_is_shown_changed = pyqtSignal(bool)
    spikes_are_shown_changed = pyqtSignal(bool)
    events_are_shown_changed = pyqtSignal(bool)
    periods_are_shown_changed = pyqtSignal(bool)

    # Signals for numerical parameters
    start_point_changed = pyqtSignal(int)
    duration_ms_changed = pyqtSignal(int)
    time_step_ms_changed = pyqtSignal(int)
    autoscroll_step_interval_ms_changed = pyqtSignal(int)
    number_of_dots_to_display_changed = pyqtSignal(int)
    scale_changed = pyqtSignal(float)
    number_of_channels_to_show_changed = pyqtSignal(int)
    current_sweep_idx_changed = pyqtSignal(int)
    analogue_panel_height_changed = pyqtSignal(int)

    # Signals for strings
    experiment_description_changed = pyqtSignal(str)
    channels_description_changed = pyqtSignal(dict)
    channels_mapping_img_changed = pyqtSignal(str)

    # Signals for channel index lists
    eeg_channel_indexes_changed = pyqtSignal(list)
    analogue_input_channel_indexes_changed = pyqtSignal(list)
    visible_channel_indexes_changed = pyqtSignal(list)

    # Session management signals
    session_saved = pyqtSignal()
    session_loaded = pyqtSignal()

    # Event signals
    events_vocabulary_changed = pyqtSignal(dict)
    events_changed = pyqtSignal(list)
    # Period signals
    periods_vocabulary_changed = pyqtSignal(dict)
    periods_changed = pyqtSignal(list)
    spikes_changed = pyqtSignal(object)

    def __init__(self, session_manager: WeegitSessionManager):
        super().__init__()
        self._session_manager = session_manager
        self._undo_stack: List[BaseCommand] = []
        self._redo_stack: List[BaseCommand] = []

    @property
    def header(self) -> Optional[Header]:
        """Get current GUI setup"""
        if self._session_manager.experiment_data:
            return self._session_manager.experiment_data.header

        return None

    @property
    def gui_setup(self) -> Optional[GuiSetup]:
        if self._session_manager.current_user_session:
            return self._session_manager.current_user_session.gui_setup
        return None

    @property
    def current_user_session(self) -> Optional[UserSession]:
        return self._session_manager.current_user_session

    @property
    def events_vocabulary(self) -> Dict[int, str]:
        if self._session_manager.current_user_session:
            return self._session_manager.current_user_session.events_vocabulary

        return {}

    @property
    def events(self) -> List[Event]:
        if self._session_manager.current_user_session:
            return self._session_manager.current_user_session.events

        return []

    @property
    def periods_vocabulary(self) -> Dict[int, str]:
        if self._session_manager.current_user_session:
            return self._session_manager.current_user_session.periods_vocabulary

        return {}

    @property
    def periods(self) -> List[Period]:
        if self._session_manager.current_user_session:
            return self._session_manager.current_user_session.periods

        return []

    @property
    def eeg_channel_indexes(self) -> List[int]:
        if (self._session_manager.current_user_session
                and self._session_manager.current_user_session.eeg_channel_indexes):
            return self._session_manager.current_user_session.eeg_channel_indexes

        return list(range(self.header.number_of_channels))

    @user_session_modification
    def set_right_panel_widgets(self, widgets: List[RightPanelWidgetEnum]):
        self._session_manager.current_user_session.gui_setup.right_panel_widgets = widgets
        self.right_panel_widgets_changed.emit(widgets)

    @user_session_modification
    def set_filters(self, filters: List[BaseFilter]):
        self._session_manager.current_user_session.gui_setup.filters = filters
        self.filters_changed.emit(filters)

    @user_session_modification
    def set_transformations(self, transformations: List[BaseTransformation]):
        self._session_manager.current_user_session.gui_setup.transformations = transformations
        self.transformations_changed.emit(transformations)

    @user_session_modification
    def set_analogue_panel_shown(self, shown: bool):
        self._session_manager.current_user_session.gui_setup.analogue_panel_is_shown = shown
        self.analogue_panel_is_shown_changed.emit(shown)

    @user_session_modification
    def set_traces_shown(self, shown: bool):
        self._session_manager.current_user_session.gui_setup.traces_are_shown = shown
        self.traces_are_shown_changed.emit(shown)

    @user_session_modification
    def set_csd_shown(self, shown: bool):
        self._session_manager.current_user_session.gui_setup.csd_is_shown = shown
        self.csd_is_shown_changed.emit(shown)

    @user_session_modification
    def set_events_shown(self, shown: bool):
        self._session_manager.current_user_session.gui_setup.events_are_shown = shown
        self.events_are_shown_changed.emit(shown)

    @user_session_modification
    def set_periods_shown(self, shown: bool):
        self._session_manager.current_user_session.gui_setup.periods_are_shown = shown
        self.periods_are_shown_changed.emit(shown)

    @user_session_modification
    def set_spikes_shown(self, shown: bool):
        self._session_manager.current_user_session.gui_setup.spikes_are_shown = shown
        self.spikes_are_shown_changed.emit(shown)

    @user_session_modification
    def set_spikes(self, sweep_idx: int, spikes: Spikes):
        self._session_manager.current_user_session.cached_spikes[sweep_idx] = spikes
        self.spikes_changed.emit(spikes)

    @user_session_modification
    def set_start_point(self, start_point: int):
        # fixme: use duration to shift
        start_point = min(start_point, self.header.number_of_points_per_sweep)
        start_point = max(0, start_point)
        self._session_manager.current_user_session.gui_setup.start_point = start_point
        self.start_point_changed.emit(start_point)

    @user_session_modification
    def set_duration_ms(self, duration_ms: int):
        duration_ms = int(min(duration_ms, self._sweep_duration_ms))
        duration_ms = max(1, duration_ms)
        self._session_manager.current_user_session.gui_setup.duration_ms = duration_ms
        self.duration_ms_changed.emit(duration_ms)

    @user_session_modification
    def set_time_step_ms(self, time_step_ms: int):
        self._session_manager.current_user_session.gui_setup.time_step_ms = time_step_ms
        self.time_step_ms_changed.emit(time_step_ms)

    @user_session_modification
    def set_autoscroll_step_interval_ms(self, interval_ms: int):
        interval_ms = max(10, int(interval_ms))
        self._session_manager.current_user_session.gui_setup.autoscroll_step_interval_ms = interval_ms
        self.autoscroll_step_interval_ms_changed.emit(interval_ms)

    @user_session_modification
    def set_number_of_dots_to_display(self, number_of_dots_to_display: int):
        self._session_manager.current_user_session.gui_setup.number_of_dots_to_display = number_of_dots_to_display
        self.number_of_dots_to_display_changed.emit(number_of_dots_to_display)

    @user_session_modification
    def set_scale(self, scale: float):
        self._session_manager.current_user_session.gui_setup.scale = scale
        self.scale_changed.emit(scale)

    @user_session_modification
    def set_number_of_channels_to_show(self, count: int):
        self._session_manager.current_user_session.gui_setup.number_of_channels_to_show = count
        self.number_of_channels_to_show_changed.emit(count)

    @user_session_modification
    def set_analogue_panel_height(self, height: int):
        height = max(0, int(height))
        self._session_manager.current_user_session.gui_setup.analogue_panel_height = height
        self.analogue_panel_height_changed.emit(height)

    @user_session_modification
    def set_current_sweep_idx(self, sweep_idx: int):
        self._session_manager.current_user_session.gui_setup.current_sweep_idx = sweep_idx
        self.current_sweep_idx_changed.emit(sweep_idx)

    @user_session_modification
    def set_visible_channel_indexes(self, indexes: List[int]):
        self._session_manager.current_user_session.gui_setup.visible_channel_indexes = indexes
        self.visible_channel_indexes_changed.emit(indexes)

    @user_session_modification
    def set_eeg_channel_indexes(self, indexes: List[int]):
        self._session_manager.current_user_session.eeg_channel_indexes = indexes
        self.eeg_channel_indexes_changed.emit(indexes)

    @user_session_modification
    def set_analogue_input_channel_indexes(self, indexes: List[int]):
        """Update analogue input channel indexes and ensure per-channel setup list is in sync."""
        session = self._session_manager.current_user_session
        if not session:
            return

        header = self.header
        session.set_analogue_input_channel_indexes(indexes, header)
        self.analogue_input_channel_indexes_changed.emit(indexes)

    @user_session_modification
    def set_analogue_channel_setup(self, channel_idx: int, *, scale: float, color: str):
        """Set per-channel analogue setup (scale and color) for a given channel index."""
        session = self._session_manager.current_user_session
        header = self.header
        if not session or not header:
            return

        session.set_analogue_channel_setup(channel_idx, scale=scale, color=color, header=header)

    @user_session_modification
    def set_experiment_description(self, experiment_description: str):
        self._session_manager.current_user_session.experiment_description = experiment_description
        self.experiment_description_changed.emit(experiment_description)

    @user_session_modification
    def set_channel_description(self, channel_idx: int, area: str):
        self._session_manager.current_user_session.gui_setup.channels_description[channel_idx] = area
        self.channels_description_changed.emit(
            dict(self._session_manager.current_user_session.gui_setup.channels_description)
        )

    @user_session_modification
    def remove_channel_descriptions(self, channel_indexes: List[int]):
        desc = self._session_manager.current_user_session.gui_setup.channels_description
        for idx in channel_indexes:
            if idx in desc:
                del desc[idx]
        self.channels_description_changed.emit(dict(desc))

    @user_session_modification
    def set_channels_description(self, channels_description: Dict[int, str]):
        self._session_manager.current_user_session.gui_setup.channels_description = dict(channels_description)
        self.channels_description_changed.emit(dict(self._session_manager.current_user_session.gui_setup.channels_description))

    @user_session_modification
    def set_channels_mapping_img(self, channels_mapping_img: str):
        self._session_manager.current_user_session.gui_setup.channels_mapping_img = channels_mapping_img
        self.channels_mapping_img_changed.emit(channels_mapping_img)

    @user_session_modification
    def add_event_vocabulary(self, name: Optional[str] = None) -> int:
        """Add a new event vocabulary entry (with undo support)."""
        cmd = AddEventVocabularyCommand(name)
        self._execute_new_command(cmd)
        # Return the newly added ID (command stores it after execution)
        added_id = cmd.get_added_id()
        if added_id is not None:
            return added_id
        # Fallback: get max ID from current vocabulary
        return max(self.events_vocabulary.keys(), default=-1)

    @user_session_modification
    def set_event_vocabulary_name(self, event_vocabulary_id: int, name: str):
        """Rename an event vocabulary entry (with undo support)."""
        cmd = SetEventVocabularyNameCommand(event_vocabulary_id, name)
        self._execute_new_command(cmd)

    @user_session_modification
    def remove_event_vocabulary(self, event_vocabulary_id: int):
        """Remove an event vocabulary entry (with undo support)."""
        cmd = RemoveEventVocabularyCommand(event_vocabulary_id)
        self._execute_new_command(cmd)

    # ---- Periods vocabulary helpers ----
    @user_session_modification
    def add_period_vocabulary(self, name: Optional[str] = None) -> int:
        """Add a new period vocabulary entry (with undo support)."""
        cmd = AddPeriodVocabularyCommand(name)
        self._execute_new_command(cmd)
        # Return the newly added ID (command stores it after execution)
        added_id = cmd.get_added_id()
        if added_id is not None:
            return added_id
        # Fallback: get max ID from current vocabulary
        return max(self.periods_vocabulary.keys(), default=-1)

    @user_session_modification
    def set_period_vocabulary_name(self, period_vocabulary_id: int, name: str):
        """Rename an period vocabulary entry (with undo support)."""
        cmd = SetPeriodVocabularyNameCommand(period_vocabulary_id, name)
        self._execute_new_command(cmd)

    @user_session_modification
    def remove_period_vocabulary(self, period_vocabulary_id: int):
        """Remove an period vocabulary entry (with undo support)."""
        cmd = RemovePeriodVocabularyCommand(period_vocabulary_id)
        self._execute_new_command(cmd)

    # ---- Events helpers ----
    @user_session_modification
    def add_event(self, event_name_id: int, sweep_idx: int, time_ms: float):
        """Create a new event in the current user session (with undo support)."""
        cmd = AddEventCommand(event_name_id, sweep_idx, time_ms)
        self._execute_new_command(cmd)

    @user_session_modification
    def remove_events(self, events: List[Event]):
        if not events:
            return

        cmd = RemoveEventsCommand(events)
        self._execute_new_command(cmd)

    @user_session_modification
    def set_events_bad_flag(self, events: List[Event], is_bad: bool):
        if not events:
            return

        cmd = SetEventsBadFlagCommand(events, is_bad)
        self._execute_new_command(cmd)

    # ---- Periods helpers ----
    @user_session_modification
    def add_period(self, 
        period_name_id: int,
        start_sweep_idx: int,
        start_time_ms: float,
        end_sweep_idx: int,
        end_time_ms: float,):
        """Create a new period in the current user session (with undo support)."""
        cmd = AddPeriodCommand(period_name_id, start_sweep_idx, start_time_ms, end_sweep_idx, end_time_ms)
        self._execute_new_command(cmd)

    @user_session_modification
    def remove_periods(self, periods: List[Period]):
        if not periods:
            return

        cmd = RemovePeriodsCommand(periods)
        self._execute_new_command(cmd)

    # ---- Undo / Redo API ----
    def can_undo(self) -> bool:
        """Check if undo is available."""
        return bool(self._undo_stack)

    def can_redo(self) -> bool:
        """Check if redo is available."""
        return bool(self._redo_stack)

    def undo(self) -> Optional[str]:
        """Undo last command. Returns short description for status bar."""
        if not self._undo_stack:
            return None

        cmd = self._undo_stack.pop()
        cmd.undo(self)
        self._redo_stack.append(cmd)
        # Limit redo stack size
        if len(self._redo_stack) > settings.MAX_UNDO_HISTORY_SIZE:
            self._redo_stack.pop(0)

        # Mark session modified if present
        if self._session_manager.current_user_session:
            self._session_manager.current_user_session.changes_saved = False

        return f"Undo: {cmd.description}"

    def redo(self) -> Optional[str]:
        """Redo last undone command. Returns short description for status bar."""
        if not self._redo_stack:
            return None

        cmd = self._redo_stack.pop()
        cmd.do(self)
        self._undo_stack.append(cmd)
        # Limit undo stack size
        if len(self._undo_stack) > settings.MAX_UNDO_HISTORY_SIZE:
            self._undo_stack.pop(0)

        # Mark session modified if present
        if self._session_manager.current_user_session:
            self._session_manager.current_user_session.changes_saved = False

        return f"Redo: {cmd.description}"

    # Session management methods
    def new_user_session(self, session_filename: str):
        self._session_manager.new_user_session(session_filename)
        self._clear_undo_redo_history()
        self.session_loaded.emit()

    def export_current_session(self, destination_path):
        return self._session_manager.export_current_session(destination_path)

    def import_new_session(self, session_to_import):
        self._session_manager.import_new_session(session_to_import)
        self._clear_undo_redo_history()
        self.session_loaded.emit()

    def switch_sessions(self, session_filename: str):
        self._session_manager.switch_sessions(session_filename)
        self._clear_undo_redo_history()
        self.session_loaded.emit()

    def save_user_session(self):
        self._session_manager.save_user_session()
        if self._session_manager.current_user_session:
            self._session_manager.current_user_session.changes_saved = True
        self.session_saved.emit()

    def init_from_folder(self, weegit_experiment_folder: Path):
        self._session_manager.init_from_folder(weegit_experiment_folder)
        self._clear_undo_redo_history()

    def session_name_already_exists(self, session_name: str):
        return self._session_manager.session_name_already_exists(session_name)

    def session_filename_already_exists(self, session_filename: str):
        return self._session_manager.session_filename_already_exists(session_filename)

    # Property forwarding
    @property
    def session_is_active(self):
        return self._session_manager.session_is_active

    @property
    def other_session_filenames(self):
        return self._session_manager.other_session_filenames

    @property
    def user_session(self):
        return self._session_manager.user_session

    @property
    def experiment_data(self):
        return self._session_manager.experiment_data

    @property
    def weegit_experiment_folder(self):
        return self._session_manager.weegit_experiment_folder

    @property
    def _sweep_duration_ms(self):
        return (self.header.sample_interval_microseconds / 10 ** 3) * self.header.number_of_points_per_sweep

    def _execute_new_command(self, cmd: BaseCommand) -> None:
        cmd.do(self)
        self._undo_stack.append(cmd)
        if len(self._undo_stack) > settings.MAX_UNDO_HISTORY_SIZE:
            self._undo_stack.pop(0)
        self._redo_stack.clear()

    def _clear_undo_redo_history(self) -> None:
        self._undo_stack.clear()
        self._redo_stack.clear()
