import json
import os
from concurrent.futures import ThreadPoolExecutor
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Optional, List, Dict, Tuple

import numpy as np
from pydantic import BaseModel, Field, model_validator
from scipy.signal import find_peaks
from weegit.logger import weegit_logger

from weegit import settings
from weegit.core.header import Header
from weegit.core.conversions.transformations import BaseTransformation
from weegit.core.conversions.filters import (
    FilterConfig,
    required_sample_rate_for_filters,
)
from weegit.core.exceptions import BrokenSessionFileError, SessionAlreadyExistsError
from weegit.converter.weegit_io import WeegitIO


class RightPanelWidgetEnum(Enum):
    EEG_SETTINGS = "eeg_settings"
    INFORMATION = "information"
    LOGS = "logs"
    CHANNELS_DESCRIPTION = "channels_description"
    ANALYSIS = "analysis"


class EventsTableFormat(Enum):
    DICT = "dict"
    MARKDOWN = "markdown"


class EventTableRow(BaseModel):
    name: str
    sweep_idx: int
    time_ms: float
    is_bad: bool
    periods: List[str]


class AnalogueChannelSetup(BaseModel):
    scale: float = 1.0
    color: str = "red"


class GuiSetup(BaseModel):
    right_panel_widgets: List[RightPanelWidgetEnum] = Field(
        default_factory=lambda: [
            RightPanelWidgetEnum.EEG_SETTINGS,
            RightPanelWidgetEnum.CHANNELS_DESCRIPTION,
            RightPanelWidgetEnum.INFORMATION,
            RightPanelWidgetEnum.ANALYSIS,
            RightPanelWidgetEnum.LOGS,
        ])
    filters: List[FilterConfig] = Field(default_factory=list)
    transformations: List[BaseTransformation] = Field(default_factory=list)

    traces_are_shown: bool = True
    events_are_shown: bool = True
    periods_are_shown: bool = True
    analogue_panel_is_shown: bool = False
    spikes_are_shown: bool = True
    csd_is_shown: bool = False

    current_sweep_idx: int = 0
    start_point: int = 0
    duration_ms: int = 10000
    time_step_ms: int = 1000
    autoscroll_step_interval_ms: int = settings.AUTO_SCROLL_STEP_INTERVAL_MS
    scale: float = 1.0
    number_of_dots_to_display: int = settings.EEG_DEFAULT_NUMBER_OF_DOTS_TO_DISPLAY
    number_of_channels_to_show: int = settings.MAX_VISIBLE_CHANNELS
    visible_channel_indexes: List[int] = Field(default_factory=list)
    analogue_channels_setup: List[AnalogueChannelSetup] = Field(default_factory=list)
    analogue_panel_height: int = settings.ANALOGUE_PANEL_HEIGHT

    channels_description: Dict[int, str] = Field(default_factory=dict)
    channels_mapping_img: str = ""

    class Config:
        arbitrary_types_allowed = True


class Period(BaseModel):
    period_name_id: int
    start_sweep_idx: int
    start_time_ms: float
    end_sweep_idx: int
    end_time_ms: float


class Event(BaseModel):
    event_name_id: int
    sweep_idx: int
    time_ms: float
    is_bad: bool = False


class Spike(BaseModel):
    time_ms: float
    value: float


class Spikes(BaseModel):
    threshold: float = settings.DEFAULT_SPIKES_THRESHOLD
    spikes_by_channel: Dict[int, List[Spike]] = Field(default_factory=dict)


class UserSession(BaseModel):
    session_filename: str
    changes_saved: bool = True
    eeg_channel_indexes: List[int] = Field(default_factory=list)
    analogue_input_channel_indexes: List[int] = Field(default_factory=list)
    events_vocabulary: Dict[int, str] = Field(default_factory=dict)
    events: List[Event] = Field(default_factory=list)
    periods_vocabulary: Dict[int, str] = Field(default_factory=dict)
    periods: List[Period] = Field(default_factory=list)
    cached_spikes: Dict[int, Spikes] = Field(default_factory=dict)
    experiment_description: str = ""
    gui_setup: GuiSetup = Field(default_factory=GuiSetup)

    class Config:
        arbitrary_types_allowed = True

    def save_session(self, dest_folder: Path):
        dest_folder.mkdir(exist_ok=True)
        dest_filepath = dest_folder / self.session_filename
        json_dump = self.model_dump_json(exclude={"session_filename", "changes_saved"}, indent=4)
        with open(dest_filepath, "w") as dest_file:
            dest_file.write(json_dump)

    def change_name(self, new_session_name: str):
        self.session_filename = new_session_name + settings.SESSION_EXTENSION

    @staticmethod
    def parse_session_file(session_filepath: Path):
        if session_filepath.exists():
            with open(session_filepath, "r") as prev_session_file:
                try:
                    json_string = prev_session_file.read()
                    session_dict = json.loads(json_string)
                    session_dict["session_filename"] = session_filepath.name
                    return UserSession.model_validate(session_dict)
                except Exception:
                    raise BrokenSessionFileError(session_filepath)

        return None

    @staticmethod
    def load_from_default_folder(weegit_experiment_folder, session_filename: str) -> "UserSession":
        session_filepath = UserSession.sessions_folder(weegit_experiment_folder) / session_filename
        return UserSession.parse_session_file(session_filepath)

    @staticmethod
    def session_name_to_filename(session_name: str) -> str:
        return session_name + settings.SESSION_EXTENSION

    @staticmethod
    def is_session_file(filename: str) -> bool:
        return filename.endswith(settings.SESSION_EXTENSION)

    @staticmethod
    def sessions_folder(weegit_experiment_folder: Path):
        folder = weegit_experiment_folder / settings.OTHER_SESSIONS_FOLDER
        folder.mkdir(exist_ok=True)
        return folder

    def add_event_vocabulary(self, name: str) -> int:
        next_id = max(self.events_vocabulary.keys(), default=-1) + 1
        event_name = name.strip() if name else f"Event {next_id}"
        self.events_vocabulary[next_id] = event_name
        return next_id

    def rename_event_vocabulary(self, event_vocabulary_id: int, name: str):
        if event_vocabulary_id not in self.events_vocabulary:
            return

        new_name = name.strip() or self.events_vocabulary[event_vocabulary_id]
        self.events_vocabulary[event_vocabulary_id] = new_name

    def remove_event_vocabulary(self, event_vocabulary_id: int):
        if event_vocabulary_id not in self.events_vocabulary:
            return

        self.events_vocabulary = {key: value for key, value in self.events_vocabulary.items()
                                  if key != event_vocabulary_id}
        self.clear_events_for_vocabulary_id(event_vocabulary_id)

    def add_period_vocabulary(self, name: str) -> int:
        next_id = max(self.periods_vocabulary.keys(), default=-1) + 1
        period_name = name.strip() if name else f"Period {next_id}"
        self.periods_vocabulary[next_id] = period_name
        return next_id

    def rename_period_vocabulary(self, period_vocabulary_id: int, name: str):
        if period_vocabulary_id not in self.periods_vocabulary:
            return

        new_name = name.strip() or self.periods_vocabulary[period_vocabulary_id]
        self.periods_vocabulary[period_vocabulary_id] = new_name

    def remove_period_vocabulary(self, period_vocabulary_id: int):
        if period_vocabulary_id not in self.periods_vocabulary:
            return

        self.periods_vocabulary = {
            key: value for key, value in self.periods_vocabulary.items()
            if key != period_vocabulary_id
        }
        # Remove periods that reference this vocabulary id
        self.periods = [p for p in self.periods if p.period_name_id != period_vocabulary_id]

    def add_event(self, event_name_id: int, sweep_idx: int, time_ms: float) -> Event:
        """Add a new event to the session."""
        new_event = Event(event_name_id=event_name_id, sweep_idx=sweep_idx, time_ms=time_ms)
        self.events.append(new_event)
        self.events.sort(key=lambda event: event.time_ms)
        return new_event

    def remove_event(self, event: Event):
        """Remove a specific event instance from the session."""
        try:
            self.events.remove(event)
        except ValueError:
            pass

    def event_set_bad_flag(self, event: Event, is_bad: bool):
        try:
            event_pos = self.events.index(event)
            self.events[event_pos].is_bad = is_bad
        except ValueError:
            pass

    def clear_events_for_vocabulary_id(self, event_name_id: int):
        """Remove all events that reference the given vocabulary id."""
        self.events = [e for e in self.events if e.event_name_id != event_name_id]

    def add_period(self, period_name_id: int, start_sweep_idx: int, start_time_ms: float,
                   end_sweep_idx: int, end_time_ms: float) -> Period:
        period = Period(
            period_name_id=period_name_id,
            start_sweep_idx=start_sweep_idx,
            start_time_ms=start_time_ms,
            end_sweep_idx=end_sweep_idx,
            end_time_ms=end_time_ms,
        )
        self.periods.append(period)
        return period

    def remove_period(self, period: Period):
        try:
            self.periods.remove(period)
        except ValueError:
            pass

    def set_analogue_input_channel_indexes(self, indexes: List[int], header: Optional['Header'] = None):
        """Set analogue input channel indexes and ensure analogue_channels_setup is synchronized.
        
        Args:
            indexes: List of channel indexes to set as analogue input channels
            header: Optional header to determine total number of channels for setup list sizing
        """
        self.analogue_input_channel_indexes = indexes
        
        # Ensure analogue_channels_setup has one entry per channel index
        if header:
            total_channels = header.number_of_channels
            setup_list = self.gui_setup.analogue_channels_setup
            # Extend with default setups if needed
            while len(setup_list) < total_channels:
                setup_list.append(AnalogueChannelSetup())
            # Trim if somehow longer
            if len(setup_list) > total_channels:
                del setup_list[total_channels:]

    def set_analogue_channel_setup(self, channel_idx: int, *, scale: float, color: str, header: Optional['Header'] = None):
        """Set per-channel analogue setup (scale and color) for a given channel index.
        
        Args:
            channel_idx: Channel index to set setup for
            scale: Scale value for the channel
            color: Color string (hex format) for the channel
            header: Optional header to determine total number of channels for setup list sizing
        """
        if header:
            total_channels = header.number_of_channels
            if channel_idx < 0 or channel_idx >= total_channels:
                return
            
            setup_list = self.gui_setup.analogue_channels_setup
            # Ensure list size
            while len(setup_list) < total_channels:
                setup_list.append(AnalogueChannelSetup())
            
            setup = setup_list[channel_idx]
            setup.scale = float(scale)
            setup.color = color

    @property
    def current_spikes_threshold(self):
        cur_sweep_spikes_cache = self.cached_spikes.get(self.gui_setup.current_sweep_idx)
        if cur_sweep_spikes_cache is not None:
            return cur_sweep_spikes_cache.threshold

        return settings.DEFAULT_SPIKES_THRESHOLD

    @property
    def events_table(self, table_format: EventsTableFormat = EventsTableFormat.DICT):
        result = []
        for event in self.events:
            event_periods = []
            for period in self.periods:
                if period.start_time_ms <= event.time_ms <= period.end_time_ms:
                    event_periods.append(self.periods_vocabulary[period.period_name_id])
            result.append(EventTableRow(
                name=self.events_vocabulary[event.event_name_id],
                sweep_idx=event.sweep_idx,
                time_ms=event.time_ms,
                is_bad=event.is_bad,
                periods=event_periods,
            ))
        return result


class ExperimentData(BaseModel):
    header: Header
    data_memmaps: Tuple[np.memmap, ...]

    class Config:
        arbitrary_types_allowed = True

    def process_data_pipeline(self, params: GuiSetup, sweep_idx: int, channel_indexes: List[int],
                              output_number_of_dots: int, eeg_channel_indexes: Optional[List[int]] = None
                              ) -> Dict[int, np.ndarray[np.float64]]:
        """
        Process data pipeline using multithreading for each visible channel.
        Returns array of shape (len(visible_channel_indexes), number_of_time_points)
        """
        start_sample = params.start_point
        end_sample = params.start_point + int(params.duration_ms * 1000 / self.header.sample_interval_microseconds)
        required_sample_rate = required_sample_rate_for_filters(params.filters)
        points_for_rate = int(params.duration_ms * 1_000_000 * required_sample_rate)
        target_points = max(int(output_number_of_dots), int(points_for_rate), 1)
        each_point = max(1, int((end_sample - start_sample) / target_points))
        effective_sample_rate = self.header.sample_rate / each_point if each_point > 0 else self.header.sample_rate
        eeg_channels_set = set(eeg_channel_indexes or [])

        # Collect results by waiting for each future to complete
        results = {}
        if channel_indexes:
            # Use ThreadPoolExecutor to process channels in parallel
            with ThreadPoolExecutor(max_workers=len(channel_indexes)) as executor:
                # Submit all tasks and store futures
                future_to_channel = {}
                for channel_idx in channel_indexes:
                    future = executor.submit(
                        self._process_single_channel,
                        channel_idx,
                        sweep_idx,
                        start_sample,
                        end_sample,
                        each_point,
                        effective_sample_rate,
                        params.filters,
                        output_number_of_dots,
                        channel_idx in eeg_channels_set,
                    )
                    future_to_channel[future] = channel_idx

                for future, channel_idx in future_to_channel.items():
                    try:
                        channel_data = future.result()  # This blocks until the thread completes
                        results[channel_idx] = channel_data
                    except Exception as exc:
                        weegit_logger().error(f"Channel {channel_idx} generated an exception: {exc}")
                        raise

        return results

    def detect_spikes(
        self,
        *,
        threshold: float,
        sweep_idx: int,
        channel_indexes: List[int],
        refractory_period: float = 0.001,
        params,
    ) -> Spikes:
        """Detect spikes by simple threshold crossing on raw data."""
        if not channel_indexes:
            return Spikes(threshold=threshold)

        start_sample = params.start_point
        output_number_of_dots = int(params.duration_ms * 1000 / self.header.sample_interval_microseconds)
        end_sample = params.start_point + output_number_of_dots
        spikes_by_channel: Dict[int, List[Spike]] = {}
        if channel_indexes:
            # Use ThreadPoolExecutor to process channels in parallel
            with ThreadPoolExecutor(max_workers=len(channel_indexes)) as executor:
                # Submit all tasks and store futures
                future_to_channel = {}
                for channel_idx in channel_indexes:
                    future = executor.submit(
                        self._process_single_channel,
                        channel_idx=channel_idx,
                        sweep_idx=sweep_idx,
                        start_sample=start_sample,
                        end_sample=end_sample,
                        # start_sample=0,
                        # end_sample=self.header.number_of_points_per_sweep,
                        each_point=1,
                        sample_rate=self.header.sample_rate,
                        filters=params.filters,
                        output_number_of_dots=output_number_of_dots,
                        apply_filters=True,
                    )
                    future_to_channel[future] = channel_idx

                for future, channel_idx in future_to_channel.items():
                    try:
                        channel_data = future.result()  # This blocks until the thread completes
                        mad = np.median(np.abs(channel_data - np.median(channel_data)))
                        threshold_value = threshold * mad / 0.6745
                        peaks, _ = find_peaks(-channel_data, height=threshold_value,
                                              distance=int(refractory_period * self.header.sample_rate))
                        vals = channel_data[peaks]
                        # convert to ms
                        spikes_by_channel[channel_idx] = [Spike(
                            time_ms=(start_sample + peak_sample) * 1_000 / self.header.sample_rate,
                            value=val,
                        ) for peak_sample, val in zip(peaks, vals)]

                    except Exception as exc:
                        weegit_logger().error(f"Channel {channel_idx} generated an exception: {exc}")
                        raise

        return Spikes(spikes_by_channel=spikes_by_channel, threshold=threshold)

    def _process_single_channel(self, channel_idx: int, sweep_idx: int,
                                start_sample: int, end_sample: int,
                                each_point: int, sample_rate: float,
                                filters: List[FilterConfig],
                                output_number_of_dots: int,
                                apply_filters: bool) -> np.ndarray[np.float64]:
        """
        Process a single channel's data pipeline.
        This method runs in a separate thread for each channel.
        """
        # Read only the required data for this specific channel
        channel_data = self.data_memmaps[channel_idx][sweep_idx][start_sample:end_sample:each_point].astype(np.float64)

        # Convert to voltage
        channel_data = self.from_int16_to_voltage_val(channel_data, channel_idx)

        # Apply filters in sequence (EEG channels only)
        if apply_filters and filters:
            for flt in filters:
                try:
                    channel_data = flt.apply(channel_data, sample_rate)
                except Exception:
                    continue

        # Downsample or resample to requested output size
        channel_data = self._resample_to_length(channel_data, output_number_of_dots)

        return channel_data

    @staticmethod
    def _resample_to_length(data: np.ndarray, output_len: int) -> np.ndarray[np.float64]:
        if output_len <= 0:
            return data
        n = len(data)
        if n == output_len:
            return data
        if n > output_len:
            idx = np.linspace(0, n - 1, output_len).astype(np.int64)
            return data[idx]
        x_old = np.linspace(0.0, 1.0, n)
        x_new = np.linspace(0.0, 1.0, output_len)
        return np.interp(x_new, x_old, data).astype(np.float64)

    def from_int16_to_voltage_val(self, data: np.ndarray, channel_idx: int):
        return np.multiply(self.channel_scale(self.header.channel_info.analog_max[channel_idx],
                                              self.header.channel_info.analog_min[channel_idx],
                                              self.header.channel_info.digital_max[channel_idx],
                                              self.header.channel_info.digital_min[channel_idx]),
                           data)
        # if self.header.type_before_conversion == "rhs":
        #     return np.multiply(0.195, data)
        # elif self.header.type_before_conversion == "daq":
        #     pass
        # else:
        #     raise NotImplementedError(f"from_int16_to_voltage_val is not implemented for "
        #                               f"{self.header.type_before_conversion}")

    @staticmethod
    @lru_cache(maxsize=1024)
    def channel_scale(analog_max, analog_min, digital_max, digital_min):
        return 1000.0 * (analog_max - analog_min) / (digital_max - digital_min)


def weegit_experiment_folder_required(method):
    def wrapper(self, *args, **kwargs):
        if self.weegit_experiment_folder is None:
            raise ValueError("Select weegit experiment folder first'")
        return method(self, *args, **kwargs)
    return wrapper


class WeegitSessionManager(BaseModel):
    weegit_experiment_folder: Optional[Path] = None
    current_user_session: Optional[UserSession] = None
    experiment_data: Optional[ExperimentData] = None

    class Config:
        arbitrary_types_allowed = True

    @property
    def user_session(self) -> UserSession:
        if self.current_user_session is None:
            raise ValueError("Select weegit experiment folder first")

        return self.current_user_session

    def session_name_already_exists(self, session_name: str):
        return self.session_filename_already_exists(UserSession.session_name_to_filename(session_name))

    def session_filename_already_exists(self, session_filename: str):
        return (session_filename in self.other_session_filenames
                or self.current_user_session is not None
                and session_filename == self.current_user_session.session_filename)

    def new_user_session(self, session_filename: str):
        if self.session_filename_already_exists(session_filename):
            raise SessionAlreadyExistsError

        all_channels = list(range(self.experiment_data.header.number_of_channels))
        self.current_user_session = UserSession(session_filename=session_filename,
                                                eeg_channel_indexes=all_channels,
                                                gui_setup=GuiSetup(visible_channel_indexes=all_channels))
        self.save_user_session()

    def export_current_session(self, destination_path: Path) -> str:
        self.current_user_session.save_session(destination_path)
        return self.current_user_session.session_filename

    @weegit_experiment_folder_required
    def import_new_session(self, user_session: UserSession):
        user_session.save_session(UserSession.sessions_folder(self.weegit_experiment_folder))

    @weegit_experiment_folder_required
    def switch_sessions(self, session_filename: str):
        self.current_user_session = UserSession.load_from_default_folder(self.weegit_experiment_folder,
                                                                         session_filename)

    @staticmethod
    def parse_session_file(session_filepath: Path):
        return UserSession.parse_session_file(session_filepath)

    @weegit_experiment_folder_required
    def save_user_session(self):
        self.current_user_session.save_session(UserSession.sessions_folder(self.weegit_experiment_folder))

    def init_from_folder(self, weegit_experiment_folder: Path):
        sessions_folder = UserSession.sessions_folder(weegit_experiment_folder)
        sessions_folder.mkdir(exist_ok=True)
        header, data_memmaps = WeegitIO.read_weegit(weegit_experiment_folder)
        self.experiment_data = ExperimentData(header=header, data_memmaps=data_memmaps)
        self.weegit_experiment_folder = weegit_experiment_folder

    @property
    def session_is_active(self):
        return self.weegit_experiment_folder is not None

    @property
    @weegit_experiment_folder_required
    def other_session_filenames(self):
        session_filenames = []
        if self.weegit_experiment_folder:
            sessions_folder = UserSession.sessions_folder(self.weegit_experiment_folder)
            for file in os.listdir(sessions_folder):
                if UserSession.is_session_file(file):
                    session_filenames.append(file)

        return session_filenames

    def update_right_panel_widgets(self, right_panel_widgets: List):
        if self.current_user_session is not None:
            self.current_user_session.gui_setup.right_panel_widgets = right_panel_widgets
