from enum import Enum

import numpy as np
from PyQt6.QtCore import Qt, QRect, pyqtSignal, QPoint, QLineF, QEvent, QSize, QTimer
from PyQt6.QtGui import QPainter, QColor, QFont, QPen, QWheelEvent, QMouseEvent, QKeyEvent, QPixmap, QFontMetrics, QImage
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QScrollBar, QHBoxLayout, QPushButton
from typing import Optional, List, Dict, Tuple
import math

from weegit import settings
from weegit.core.weegit_session import AnalogueChannelSetup, Spikes
from weegit.gui._utils import milliseconds_to_readable
from weegit.gui.qt_weegit_session_manager_wrapper import QtWeegitSessionManagerWrapper


class TopNavigatorWidget(QWidget):
    """Widget for displaying event names with navigation arrows"""

    event_navigation_requested = pyqtSignal(int)  # Emits new start_point

    def __init__(self, left_margin, right_margin, parent=None):
        super().__init__(parent)
        self._BG_COLOR = QColor(240, 240, 240)  # Same as SignalWidget
        self._TEXT_COLOR = QColor(0, 0, 255)
        self._TEXT_BAD_COLOR = QColor(255, 0, 0)
        self._ARROW_COLOR = QColor(100, 100, 100)
        self._ARROW_HOVER_COLOR = QColor(0, 0, 200)
        self._left_margin = left_margin
        self._right_margin = right_margin

        self._all_events = []
        self._visible_events = []
        self._events_vocabulary: Dict[int, str] = {}
        self._all_periods = []
        self._visible_periods = []
        self._periods_vocabulary: Dict[int, str] = {}
        self._current_sweep_idx: int = 0
        self._start_point = 0
        self._duration_ms = 0.0
        self._sample_rate = 1.0
        self._header_points_per_sweep = 0
        self._start_time_ms = 0.0
        self._axis_offset_px = 0

        # For hover tracking
        self._hovered_arrow: Optional[Tuple[int, str]] = None  # (event_index, 'left'/'right')
        self.setMouseTracking(True)

        self._font = QFont()
        self._font.setPointSize(12)
        self._font_metrics = QFontMetrics(self._font)

    def update_events(
            self,
            all_events: List,
            visible_events: List,
            events_vocabulary: Dict[int, str],
            all_periods: List,
            visible_periods: List,
            periods_vocabulary: Dict[int, str],
            sweep_idx: int,
            start_point: int,
            duration_ms: float,
            sample_rate: float,
            start_time_ms: float,
            header_points_per_sweep: int,
            axis_offset_px: int = 0,
    ):
        """Update event data for display"""
        self._all_events = all_events or []
        self._visible_events = visible_events or []
        self._events_vocabulary = events_vocabulary or {}
        self._all_periods = all_periods or []
        self._visible_periods = visible_periods or []
        self._periods_vocabulary = periods_vocabulary or {}
        self._current_sweep_idx = sweep_idx
        self._start_point = start_point
        self._duration_ms = duration_ms
        self._sample_rate = sample_rate
        self._start_time_ms = start_time_ms
        self._header_points_per_sweep = header_points_per_sweep
        self._axis_offset_px = max(0, int(axis_offset_px))
        self.update()

    def paintEvent(self, event):
        if self._duration_ms <= 0:
            return

        painter = QPainter(self)
        painter.fillRect(self.rect(), self._BG_COLOR)
        if not self._visible_events and not self._visible_periods:
            return

        painter.setFont(self._font)

        # Draw events with arrows
        axis_start_x = self._left_margin + self._axis_offset_px
        start_time_ms = self._start_time_ms
        axis_width = self.width() - self._right_margin - axis_start_x
        if axis_width <= 0:
            return

        # Draw arrows
        arrow_size = 10
        arrow_y = 15

        for event in self._visible_events:
            # Draw event name
            name = self._events_vocabulary[event.event_name_id]
            # Bad events are drawn in red
            if getattr(event, "is_bad", False):
                painter.setPen(self._TEXT_BAD_COLOR)
            else:
                painter.setPen(self._TEXT_COLOR)
            text_width = self._font_metrics.horizontalAdvance(name)
            x = axis_start_x + ((event.time_ms - start_time_ms) / self._duration_ms) * axis_width
            x_pos = int(x)
            text_rect = QRect(int(x_pos - text_width // 2), 5, text_width, 20)
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, name)

            event_idx = self._all_events.index(event)
            # Left arrow
            left_arrow_rect = QRect(int(x_pos - text_width // 2 - arrow_size - 5), arrow_y - arrow_size // 2,
                                    arrow_size, arrow_size)
            self._draw_arrow(painter, left_arrow_rect, 'left',
                             (event_idx, 'left') == self._hovered_arrow)

            # Right arrow
            right_arrow_rect = QRect(int(x_pos + text_width // 2 + 5), arrow_y - arrow_size // 2,
                                     arrow_size, arrow_size)
            self._draw_arrow(painter, right_arrow_rect, 'right',
                             (event_idx, 'right') == self._hovered_arrow)

        # Draw period labels (start/end)
        if self._visible_periods:
            painter.setPen(self._TEXT_COLOR)
            for period in self._visible_periods:
                name = self._periods_vocabulary.get(period.period_name_id, "")
                if not name:
                    continue

                for time_ms, suffix in (
                    (period.start_time_ms, "(s)"),
                    (period.end_time_ms, "(e)"),
                ):
                    if not (start_time_ms <= time_ms <= start_time_ms + self._duration_ms):
                        continue

                    label = f"{name}{suffix}"
                    text_width = self._font_metrics.horizontalAdvance(label)
                    x = axis_start_x + ((time_ms - start_time_ms) / self._duration_ms) * axis_width
                    x_pos = int(x)
                    text_rect = QRect(int(x_pos - text_width // 2), 5, text_width, 20)
                    painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, label)

    def _draw_arrow(self, painter: QPainter, rect: QRect, direction: str, hovered: bool):
        """Draw an arrow in the given rectangle"""
        color = self._ARROW_HOVER_COLOR if hovered else self._ARROW_COLOR
        painter.setPen(QPen(color, 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)

        # Draw arrow as triangle
        points = []
        if direction == 'left':
            points = [
                QPoint(rect.right(), rect.top()),
                QPoint(rect.left(), rect.center().y()),
                QPoint(rect.right(), rect.bottom())
            ]
        else:  # 'right'
            points = [
                QPoint(rect.left(), rect.top()),
                QPoint(rect.right(), rect.center().y()),
                QPoint(rect.left(), rect.bottom())
            ]

        painter.drawPolygon(points)

    def mouseMoveEvent(self, event):
        """Track mouse movement for arrow hover effects"""
        pos = event.position().toPoint()
        old_hover = self._hovered_arrow
        self._hovered_arrow = None

        axis_start_x = self._left_margin + self._axis_offset_px
        start_time_ms = self._start_time_ms
        axis_width = self.width() - self._right_margin - axis_start_x
        if axis_width <= 0:
            return
        for event in self._visible_events:
            name = self._events_vocabulary[event.event_name_id]
            text_width = self._font_metrics.horizontalAdvance(name)
            x = axis_start_x + ((event.time_ms - start_time_ms) / self._duration_ms) * axis_width
            x_pos = int(x)
            arrow_size = 10

            # Check left arrow
            left_arrow_rect = QRect(int(x_pos - text_width // 2 - arrow_size - 5), 15 - arrow_size // 2,
                                    arrow_size, arrow_size)
            if left_arrow_rect.contains(pos):
                self._hovered_arrow = (self._all_events.index(event), 'left')
                break

            # Check right arrow
            right_arrow_rect = QRect(int(x_pos + text_width // 2 + 5), 15 - arrow_size // 2,
                                     arrow_size, arrow_size)
            if right_arrow_rect.contains(pos):
                self._hovered_arrow = (self._all_events.index(event), 'right')
                break

        if old_hover != self._hovered_arrow:
            self.update()

    def mousePressEvent(self, event):
        """Handle arrow clicks for navigation"""
        if event.button() == Qt.MouseButton.LeftButton and self._hovered_arrow:
            event_idx, direction = self._hovered_arrow
            self._navigate_to_neighbor_event(event_idx, direction)

    def _navigate_to_neighbor_event(self, current_event_idx: int, direction: str):
        """Calculate and emit new start_point to center neighbor event"""
        if not self._all_events:
            return

        current_event = self._all_events[current_event_idx]
        event_name_id = current_event.event_name_id
        sweep_idx = current_event.sweep_idx

        # Find all events with same name in current sweep
        same_name_events = [
            event for event in self._all_events
            if event.event_name_id == event_name_id and event.sweep_idx == sweep_idx
        ]

        if not same_name_events:
            return

        # Find current event in the list
        current_in_list_idx = same_name_events.index(current_event)
        if current_in_list_idx == -1:
            return

        # Get neighbor event
        if direction == 'left':
            neighbor_idx = current_in_list_idx - 1
        else:  # 'right'
            neighbor_idx = current_in_list_idx + 1

        if 0 <= neighbor_idx < len(same_name_events):
            neighbor_event = same_name_events[neighbor_idx]
            # Calculate new start_point to center this event
            new_start_point = self._calculate_start_point_to_center(neighbor_event.time_ms)
            self.event_navigation_requested.emit(new_start_point)

    def _calculate_start_point_to_center(self, target_time_ms: float) -> int:
        """Calculate start_point that centers the target event"""
        # Convert time to samples
        target_samples = int((target_time_ms / 1000.0) * self._sample_rate)

        # Calculate samples for half duration
        half_duration_samples = int((self._duration_ms / 2000.0) * self._sample_rate)

        # Calculate start_point to center the event
        new_start_point = target_samples - half_duration_samples

        # Ensure we don't go out of bounds
        new_start_point = max(0, new_start_point)
        max_start = max(0, self._header_points_per_sweep -
                        int((self._duration_ms / 1000.0) * self._sample_rate))
        new_start_point = min(new_start_point, max_start)

        return new_start_point


class SignalWidget(QWidget):
    """Custom widget for signal display that handles its own paint events"""

    def __init__(self, left_margin, right_margin, bottom_margin, parent=None):
        super().__init__(parent)
        self.pixmap_cache = QPixmap()
        self._BG_COLOR = QColor(240, 240, 240)
        self._GRID_COLOR = QColor(200, 200, 200)
        self._SIGNAL_COLOR = QColor(0, 0, 0)
        self._TEXT_COLOR = QColor(0, 0, 0)
        self._AXIS_COLOR = QColor(100, 100, 100)
        self._CHANNEL_SPACING = 5
        self._left_margin = left_margin
        self._right_margin = right_margin
        self._bottom_margin = bottom_margin

        self._channel_height = 0
        self._cached_x_coords: Optional[np.ndarray] = None
        self._cached_x_width: int = -1
        self._cached_x_points: int = -1
        self._lines_cache: Dict[Tuple[int, int], List[QLineF]] = {}
        self._axis_start_point = 0  # in samples within sweep
        self._axis_duration_ms = 0.0
        self._sample_rate = 1.0
        self._start_time_ms = 0.0
        self._end_time_ms = 0.0
        self._axis_start_x = 0
        self._axis_width = 0
        self._visible_events = []
        self._visible_periods = []
        self._current_sweep_idx: int = 0
        self._traces_are_visible = True
        self._events_are_visible = True
        self._periods_are_visible = True
        self._csd_is_visible = False
        self._overlay_widget: Optional['OverlayWidget'] = None
        self._eeg_channel_rects: List[Tuple[int, QRect]] = []
        self._channel_names: List[str] = []
        self._cached_spikes: Optional[Spikes] = None
        self._spikes_are_visible: bool = False
        self._analogue_visible = False
        self._analogue_panel_height = 0
        self._analogue_channel_indexes: List[int] = []
        self._analogue_channels_setup: List[AnalogueChannelSetup] = []
        self._signal_pixmap_offset = QPoint(self._left_margin, 0)

    def set_overlay_widget(self, overlay_widget: Optional['OverlayWidget']):
        """Attach an overlay widget that mirrors the signal widget geometry."""
        self._overlay_widget = overlay_widget
        if self._overlay_widget:
            self._overlay_widget.setParent(self)
            self._overlay_widget.setGeometry(self.rect())
            self._overlay_widget.raise_()

    def reset_data_and_redraw(
            self,
            processed_data,
            visible_channel_indexes,
            channel_names,
            voltage_scale,
            *,
            start_point: int,
            duration_ms: float,
            start_time_ms: float,
            sample_rate: float,
            visible_events=None,
            visible_periods=None,
            sweep_idx: int = 0,
            events_are_visible: bool = True,
            periods_are_visible: bool = True,
            traces_are_visible: bool = True,
            csd_is_visible: bool = False,
            analogue_visible: bool = False,
            analogue_channel_indexes: Optional[List[int]] = None,
            analogue_channels_setup: Optional[List[AnalogueChannelSetup]] = None,
            analogue_panel_height: int = 0,
            cached_spikes: Optional[Spikes] = None,
            spikes_are_visible: bool = False,
    ):
        self._axis_start_point = max(0, start_point)
        self._axis_duration_ms = max(0.0, duration_ms)
        self._sample_rate = sample_rate if sample_rate > 0 else 1.0
        self._start_time_ms = start_time_ms
        self._end_time_ms = self._start_time_ms + self._axis_duration_ms
        self._visible_events = visible_events
        self._visible_periods = visible_periods
        self._current_sweep_idx = sweep_idx
        self._events_are_visible = events_are_visible
        self._periods_are_visible = periods_are_visible
        self._traces_are_visible = traces_are_visible
        self._csd_is_visible = csd_is_visible
        self._channel_names = channel_names or []
        self._analogue_visible = bool(analogue_visible)
        self._analogue_panel_height = max(0, int(analogue_panel_height))
        self._analogue_channel_indexes = analogue_channel_indexes or []
        self._analogue_channels_setup = analogue_channels_setup or []
        self._cached_spikes = cached_spikes
        self._spikes_are_visible = bool(spikes_are_visible)
        self._eeg_channel_rects = []

        signal_width = max(0, self.width() - self._left_margin - self._right_margin)
        draw_area_height = max(0, self.height() - self._bottom_margin)
        self._signal_pixmap_offset = QPoint(self._left_margin, 0)
        self._axis_start_x = 0
        self._axis_width = signal_width
        if signal_width == 0 or draw_area_height == 0:
            self.pixmap_cache = QPixmap()
            self.update()
            return
        self.pixmap_cache = QPixmap(signal_width, draw_area_height)

        painter = QPainter(self.pixmap_cache)
        painter.fillRect(0, 0, signal_width, draw_area_height, self._BG_COLOR)

        analogue_height = 0
        if self._analogue_visible:
            analogue_height = min(draw_area_height, self._analogue_panel_height)
        eeg_area_height = max(0, draw_area_height - analogue_height)

        if processed_data and visible_channel_indexes:
            channel_height = int((eeg_area_height / len(visible_channel_indexes)) - self._CHANNEL_SPACING)
            self._channel_height = max(0, channel_height)
        else:
            self._channel_height = 0

        # Draw channel backgrounds and names
        for cur_draw_idx, channel_idx in enumerate(visible_channel_indexes):
            y_pos = cur_draw_idx * (self._channel_height + self._CHANNEL_SPACING)
            channel_rect = QRect(0, y_pos, signal_width, self._channel_height)
            self._eeg_channel_rects.append((channel_idx, channel_rect))

        if self._csd_is_visible:
            self._draw_csd(
                painter,
                processed_data,
                visible_channel_indexes,
                signal_width,
                eeg_area_height,
            )

        for channel_idx, channel_rect in self._eeg_channel_rects:
            if self._traces_are_visible:
                self._draw_middle_line(painter, channel_rect)

        if self._traces_are_visible:
            for cur_draw_idx, (channel_idx, channel_rect) in enumerate(self._eeg_channel_rects):
                self._draw_signal(
                    painter,
                    processed_data[channel_idx],
                    channel_rect,
                    voltage_scale,
                    channel_idx,
                    cur_draw_idx,
                    eeg_area_height,
                )

        if self._spikes_are_visible:
            self._draw_spikes(painter, signal_width, eeg_area_height, voltage_scale)

        if self._periods_are_visible:
            self._draw_periods(painter, signal_width, draw_area_height)

        if analogue_height > 0:
            self._draw_analogue_panel(
                painter,
                processed_data,
                signal_width,
                eeg_area_height,
                analogue_height,
            )

        if self._events_are_visible:
            self._draw_events(painter, signal_width, draw_area_height)

        self.update()  # Trigger paint event

    def _draw_time_axis(self, painter: QPainter, width: int, height: int):
        if self._axis_duration_ms <= 0:
            return

        axis_rect_top = max(0, height - self._bottom_margin)
        axis_y = axis_rect_top + min(5, self._bottom_margin // 6)
        axis_start_x = self._left_margin
        axis_end_x = max(axis_start_x, width - self._right_margin)
        axis_width = axis_end_x - axis_start_x
        if axis_width <= 0:
            return

        painter.fillRect(0, axis_rect_top, width, height - axis_rect_top, self._BG_COLOR)

        pen = QPen(self._AXIS_COLOR, 2)
        painter.setPen(pen)
        painter.drawLine(axis_start_x, axis_y, axis_end_x, axis_y)

        visible_points = int((self._axis_duration_ms / 1000.0) * self._sample_rate)
        if visible_points <= 0:
            return

        total_time_ms = self._end_time_ms - self._start_time_ms
        if total_time_ms <= 0:
            return

        target_ticks = 8
        rough_interval = total_time_ms / target_ticks
        if rough_interval <= 0:
            return

        exponent = math.floor(math.log10(rough_interval))
        mantissa = rough_interval / (10 ** exponent)

        if mantissa < 1.5:
            tick_interval = 10 ** exponent
        elif mantissa < 3:
            tick_interval = 2 * 10 ** exponent
        elif mantissa < 7:
            tick_interval = 5 * 10 ** exponent
        else:
            tick_interval = 10 ** (exponent + 1)

        font = QFont()
        font.setPointSize(12)
        painter.setFont(font)
        painter.setPen(self._AXIS_COLOR)

        time_ms = math.ceil(self._start_time_ms / tick_interval) * tick_interval
        label_offset = 8
        while time_ms <= self._end_time_ms:
            x = axis_start_x + ((time_ms - self._start_time_ms) / self._axis_duration_ms) * axis_width
            painter.drawLine(int(x), axis_y, int(x), axis_y + 6)
            label = milliseconds_to_readable(time_ms, wrap=False)
            text_rect = QRect(int(x) - 50, axis_y + label_offset, 100, 15)
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, label)

            time_ms += tick_interval

    def _draw_events(self, painter: QPainter, signal_width: int, draw_area_height: int):
        """Draw vertical lines for events in the current sweep/time window."""
        if not self._visible_events or self._axis_duration_ms <= 0 or self._sample_rate <= 0:
            return

        axis_width = max(0, self._axis_width)
        if axis_width <= 0:
            return

        for event in self._visible_events:
            x = self._axis_start_x + ((event.time_ms - self._start_time_ms) / self._axis_duration_ms) * axis_width
            x_int = int(x)
            # Bad events are red, others are blue
            color = QColor(255, 0, 0) if event.is_bad else QColor(0, 0, 255)
            painter.setPen(QPen(color, 1.5))
            # Vertical line across signal area (no labels here)
            painter.drawLine(x_int, 0, x_int, draw_area_height)

    def _draw_periods(self, painter: QPainter, signal_width: int, draw_area_height: int):
        if not self._visible_periods or self._axis_duration_ms <= 0 or self._sample_rate <= 0:
            return

        axis_width = max(0, self._axis_width)
        if axis_width <= 0:
            return

        pen = QPen(QColor(0, 128, 0), 1.5)
        painter.setPen(pen)
        for period in self._visible_periods:
            for time_ms in (period.start_time_ms, period.end_time_ms):
                if not (self._start_time_ms <= time_ms <= self._end_time_ms):
                    continue
                x = self._axis_start_x + ((time_ms - self._start_time_ms) / self._axis_duration_ms) * axis_width
                x_int = int(x)
                painter.drawLine(x_int, 0, x_int, draw_area_height)

    def _draw_csd(
            self,
            painter: QPainter,
            processed_data,
            visible_channel_indexes: List[int],
            signal_width: int,
            eeg_area_height: int,
    ):
        return
        if not processed_data or not visible_channel_indexes:
            return
        if signal_width <= 0 or eeg_area_height <= 0:
            return

        n_channels = len(visible_channel_indexes)
        if n_channels < 3:
            return

        first_idx = visible_channel_indexes[0]
        if first_idx not in processed_data:
            return
        n_points = len(processed_data[first_idx])
        if n_points < 2:
            return

        channel_data = []
        for channel_idx in visible_channel_indexes:
            data = processed_data.get(channel_idx)
            if data is None or len(data) != n_points:
                data = np.zeros(n_points, dtype=np.float64)
            channel_data.append(data)

        data_matrix = np.stack(channel_data, axis=0)
        csd = np.zeros_like(data_matrix)
        csd[1:-1] = data_matrix[:-2] - 2.0 * data_matrix[1:-1] + data_matrix[2:]

        time_idx = np.linspace(0, n_points - 1, signal_width).astype(np.int64)
        csd_time = csd[:, time_idx]

        channel_idx = np.linspace(0, n_channels - 1, eeg_area_height).astype(np.int64)
        csd_img = csd_time[channel_idx, :]

        scale = np.percentile(np.abs(csd_img), 98)
        if scale <= 1e-12:
            return

        csd_norm = np.clip(csd_img / scale, -1.0, 1.0)
        abs_v = np.abs(csd_norm)
        green = (255 * (1.0 - abs_v)).astype(np.uint8)

        rgb = np.empty((eeg_area_height, signal_width, 3), dtype=np.uint8)
        rgb[..., 1] = green
        pos = csd_norm >= 0
        rgb[..., 0] = np.where(pos, 0, 255).astype(np.uint8)
        rgb[..., 2] = np.where(pos, 255, 0).astype(np.uint8)

        img = QImage(
            rgb.data,
            signal_width,
            eeg_area_height,
            3 * signal_width,
            QImage.Format.Format_RGB888,
        ).copy()
        painter.drawImage(0, 0, img)

    def _draw_spikes(self, painter: QPainter, signal_width: int, eeg_area_height: int, voltage_scale):
        if self._cached_spikes is None or self._axis_duration_ms <= 0 or self._sample_rate <= 0:
            return

        axis_width = max(0, self._axis_width)
        if axis_width <= 0:
            return

        pen = QPen(QColor(255, 0, 0))
        painter.setPen(pen)
        painter.setBrush(QColor(255, 0, 0))

        size = 4
        half = size // 2
        for channel_idx, channel_rect in self._eeg_channel_rects:
            spikes_list = self._cached_spikes.spikes_by_channel.get(channel_idx)
            if not spikes_list:
                continue
            y = channel_rect.center().y()
            for spike in spikes_list:
                if not (self._start_time_ms <= spike.time_ms <= self._end_time_ms):
                    continue
                x = ((spike.time_ms - self._start_time_ms) / self._axis_duration_ms) * axis_width
                x_int = int(x)

                # scale_factor = self.get_channel_scale(channel_idx)
                # full_scale = voltage_scale * settings.EEG_VOLTAGE_SCALE * scale_factor
                # y_offset = int(spike.value * full_scale)
                # painter.drawRect(x_int - half, y - half - y_offset, size, size)
                painter.drawRect(x_int - half, y - half, size, size)

    def _draw_analogue_panel(
            self,
            painter: QPainter,
            processed_data,
            signal_width: int,
            eeg_area_height: int,
            analogue_height: int,
    ):
        if analogue_height <= 0:
            return

        separator_y = float(eeg_area_height)
        separator_pen = QPen(self._GRID_COLOR, 1, Qt.PenStyle.DotLine)
        painter.setPen(separator_pen)
        painter.drawLine(0, int(separator_y), signal_width, int(separator_y))

        center_y = eeg_area_height + analogue_height / 2.0
        pen = QPen(self._GRID_COLOR, 2, Qt.PenStyle.DotLine)
        painter.setPen(pen)
        painter.drawLine(0, int(center_y), signal_width, int(center_y))

        for channel_idx in self._analogue_channel_indexes:
            if channel_idx not in processed_data:
                continue

            channel_data = processed_data[channel_idx]
            if channel_data is None or len(channel_data) < 2:
                continue

            setup: Optional[AnalogueChannelSetup] = None
            if 0 <= channel_idx < len(self._analogue_channels_setup):
                setup = self._analogue_channels_setup[channel_idx]

            scale = setup.scale if setup is not None else 1.0
            color_str = setup.color if (setup is not None and setup.color) else "#000000"

            self._draw_analogue_signal(
                painter,
                channel_data,
                channel_idx,
                scale,
                color_str,
                signal_width,
                center_y,
                separator_y,
            )

    def _draw_analogue_signal(
            self,
            painter: QPainter,
            channel_data: np.ndarray,
            channel_idx: int,
            channel_scale: float,
            color_str: str,
            signal_width: int,
            center_y: float,
            separator_y: float,
    ):
        if channel_data is None or len(channel_data) < 2:
            return

        try:
            color = QColor(color_str)
            if not color.isValid():
                color = self._SIGNAL_COLOR
        except Exception:
            color = self._SIGNAL_COLOR

        pen = QPen(color, 1.5)
        painter.setPen(pen)

        n_points = len(channel_data)
        x_coords = self._get_cached_x_coords(signal_width, n_points)

        y_offsets = channel_data * channel_scale
        y_coords = center_y - y_offsets

        line_buffer = self._get_line_buffer((1, channel_idx), n_points - 1)
        draw_count = 0
        for i in range(n_points - 1):
            y0 = float(y_coords[i])
            y1 = float(y_coords[i + 1])
            if y0 < separator_y or y1 < separator_y:
                continue
            line_buffer[draw_count].setLine(
                float(x_coords[i]),
                y0,
                float(x_coords[i + 1]),
                y1
            )
            draw_count += 1

        if draw_count:
            painter.drawLines(line_buffer[:draw_count])

    def draw_channel_info(self, painter: QPainter, channel_idx: int, channel_rect: QRect):
        """Draw channel name and index on the left"""
        font = QFont()
        font.setPointSize(11)
        painter.setFont(font)
        painter.setPen(self._TEXT_COLOR)

        if 0 <= channel_idx < len(self._channel_names):
            channel_name = self._channel_names[channel_idx]
        else:
            channel_name = ""
        text_rect = QRect(0, channel_rect.top(), self._left_margin - 10, channel_rect.height())

        # Draw channel index and name
        text = f"{channel_idx} [{channel_name}]" if channel_name else f"{channel_idx}"
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, text)

    def _draw_middle_line(self, painter, channel_rect):
        zero_y = channel_rect.top() + channel_rect.height() // 2
        pen = QPen(self._GRID_COLOR, 2, Qt.PenStyle.DotLine)
        painter.setPen(pen)
        painter.drawLine(channel_rect.left(), zero_y, channel_rect.right(), zero_y)

    def _draw_signal(self, painter: QPainter, channel_data: np.ndarray, channel_rect: QRect,
                    voltage_scale, channel_idx: int, cur_draw_idx: int, eeg_area_height: int):
        """Draw EEG signal for a single channel while keeping every sample."""
        if channel_data is None or len(channel_data) < 2:
            return

        pen = QPen(self._SIGNAL_COLOR, 1.5)
        painter.setPen(pen)

        n_points = len(channel_data)
        x_coords = self._get_cached_x_coords(channel_rect.width(), n_points)

        scale_factor = self.get_channel_scale(channel_idx)
        full_scale = voltage_scale * settings.EEG_VOLTAGE_SCALE * scale_factor
        channel_mid_y = channel_rect.top() + channel_rect.height() / 2.0
        y_offsets = channel_data * full_scale
        y_coords = channel_mid_y - y_offsets

        line_buffer = self._get_line_buffer((0, cur_draw_idx), n_points - 1)
        draw_count = 0
        for i in range(n_points - 1):
            y0 = float(y_coords[i])
            y1 = float(y_coords[i + 1])
            if y0 > eeg_area_height or y1 > eeg_area_height:
                continue
            line_buffer[draw_count].setLine(
                float(x_coords[i]),
                y0,
                float(x_coords[i + 1]),
                y1
            )
            draw_count += 1

        if draw_count:
            painter.drawLines(line_buffer[:draw_count])

    def get_channel_scale(self, channel_idx: int) -> float:
        return 1.0

    def _value_to_pixel_voltage(self, value, voltage_scale, channel_idx: Optional[int] = None):
        if channel_idx is not None:
            scale_factor = self.get_channel_scale(channel_idx)
        else:
            scale_factor = 1.0

        return value * voltage_scale * settings.EEG_VOLTAGE_SCALE * scale_factor

    def _get_cached_x_coords(self, signal_width: int, n_points: int) -> np.ndarray:
        """Cache evenly-spaced X coordinates for a given width/data length."""
        if (self._cached_x_coords is not None and
                self._cached_x_width == signal_width and
                self._cached_x_points == n_points):
            return self._cached_x_coords

        if n_points < 2 or signal_width <= 0:
            coords = np.array([0.0], dtype=np.float32)
        else:
            coords = np.linspace(0.0, signal_width - 1, n_points, dtype=np.float32)

        self._cached_x_coords = coords
        self._cached_x_width = signal_width
        self._cached_x_points = n_points
        return coords

    def _get_line_buffer(self, cache_key: Tuple[int, int], required: int) -> List[QLineF]:
        """Ensure a reusable QLineF buffer exists for the channel."""
        buffer = self._lines_cache.setdefault(cache_key, [])
        missing = required - len(buffer)
        if missing > 0:
            buffer.extend(QLineF() for _ in range(missing))
        return buffer

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._overlay_widget:
            self._overlay_widget.setGeometry(self.rect())

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), self._BG_COLOR)
        if not self.pixmap_cache.isNull():
            painter.drawPixmap(self._signal_pixmap_offset, self.pixmap_cache)

        for channel_idx, channel_rect in self._eeg_channel_rects:
            self.draw_channel_info(painter, channel_idx, channel_rect)

        self._draw_time_axis(painter, self.width(), self.height())


class OverlayModeEnum(Enum):
    NONE = 0
    TIME_VOLTAGE_BAR = 1
    EVENT_ADD = 2
    EVENT_BAD_SET = 3
    EVENT_BAD_UNSET = 4
    EVENT_REMOVE = 5
    PERIOD_ADD = 6


class OverlayWidget(QWidget):
    """Transparent overlay that draws time/voltage scale bars at the cursor."""

    def __init__(self, left_margin, right_margin, bottom_margin, bar_width, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        self._left_margin = left_margin
        self._right_margin = right_margin
        self._bottom_margin = bottom_margin
        self._bar_width = bar_width

        self._cursor_pos: Optional[QPoint] = None
        self._overlay_mode = OverlayModeEnum.NONE
        self._channel_height = 0
        self._duration_ms = 0.0
        self._start_time_ms = 0.0
        self._selection_start_time_ms: Optional[float] = None
        self._scale_value = 1.0
        self._font = QFont()
        self._font.setPointSize(12)
        self._font_metrics = QFontMetrics(self._font)
        
    def update_state(self, *, cursor_pos: Optional[QPoint], overlay_mode: OverlayModeEnum,
                     channel_height: int, duration_ms: float, scale_value: float,
                     start_time_ms: float, selection_start_time_ms: Optional[float]):
        self._cursor_pos = cursor_pos
        self._overlay_mode = overlay_mode
        self._channel_height = max(0, channel_height)
        self._duration_ms = max(0.0, duration_ms)
        self._scale_value = scale_value if scale_value > 0 else 1.0
        self._start_time_ms = start_time_ms
        self._selection_start_time_ms = selection_start_time_ms
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if not self._cursor_pos:
            return

        # Crosshair for interactive modes
        if self._overlay_mode in (
            OverlayModeEnum.EVENT_ADD,
            OverlayModeEnum.EVENT_BAD_SET,
            OverlayModeEnum.EVENT_BAD_UNSET,
            OverlayModeEnum.EVENT_REMOVE,
            OverlayModeEnum.PERIOD_ADD,
        ):
            pen = QPen(Qt.GlobalColor.green, 1, Qt.PenStyle.SolidLine)
            painter.setPen(pen)
            painter.drawLine(0, self._cursor_pos.y(), self.width(), self._cursor_pos.y())
            painter.drawLine(self._cursor_pos.x(), 0, self._cursor_pos.x(), self.height())
            self._draw_mode_label(painter)

            # Selection area for edit modes after the first click
            if self._overlay_mode in (
                OverlayModeEnum.EVENT_BAD_SET,
                OverlayModeEnum.EVENT_BAD_UNSET,
                OverlayModeEnum.EVENT_REMOVE,
                OverlayModeEnum.PERIOD_ADD,
            ) and self._selection_start_time_ms is not None:
                self._draw_selection_area(painter)

        elif self._overlay_mode == OverlayModeEnum.TIME_VOLTAGE_BAR:
            painter.setPen(QPen(QColor(255, 0, 0)))
            painter.setFont(self._font)
            self._draw_voltage_scale_bar(painter)
            self._draw_time_scale_bar(painter)

    def _signal_width(self) -> int:
        return max(0, self.width() - self._left_margin - self._right_margin)

    def _axis_start_x(self) -> int:
        return self._left_margin

    def _axis_end_x(self) -> int:
        return self._axis_start_x() + self._signal_width()

    def _time_to_x(self, time_ms: float) -> Optional[float]:
        """Map absolute time in ms to X coordinate within the signal area."""
        signal_width = self._signal_width()
        if signal_width <= 0 or self._duration_ms <= 0:
            return None

        axis_start_x = self._axis_start_x()
        rel = (time_ms - self._start_time_ms) / self._duration_ms
        return axis_start_x + rel * signal_width

    def _draw_mode_label(self, painter: QPainter):
        """Draw mode name slightly to the bottom-right of the crosshair."""
        painter.setFont(self._font)
        mode_labels = {
            OverlayModeEnum.EVENT_ADD: "Add event",
            OverlayModeEnum.EVENT_BAD_SET: "Set bad",
            OverlayModeEnum.EVENT_BAD_UNSET: "Unset bad",
            OverlayModeEnum.EVENT_REMOVE: "Remove events",
            OverlayModeEnum.PERIOD_ADD: "Add period",
        }
        label = mode_labels.get(self._overlay_mode)
        if not label:
            return

        text_width = self._font_metrics.horizontalAdvance(label) + 8
        text_height = self._font_metrics.height() + 4

        x = self._cursor_pos.x() + 6
        y = self._cursor_pos.y() + 6

        # Ensure label stays within widget bounds
        if x + text_width > self.width():
            x = self.width() - text_width - 2
        if y + text_height > self.height():
            y = self.height() - text_height - 2

        rect = QRect(int(x), int(y), int(text_width), int(text_height))
        # Background
        bg_color = QColor(255, 255, 255, 220)
        painter.fillRect(rect, bg_color)
        # Text
        painter.setPen(QColor(0, 0, 0))
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, label)

    def _draw_selection_area(self, painter: QPainter):
        """Draw semi-transparent selection area between first point and current cursor."""
        signal_width = self._signal_width()
        if signal_width <= 0 or self._duration_ms <= 0:
            return

        axis_start_x = self._axis_start_x()
        axis_end_x = self._axis_end_x()

        first_x = self._time_to_x(self._selection_start_time_ms)
        if first_x is None:
            return

        # Clamp selection start to visible signal area
        first_x_clamped = max(axis_start_x, min(axis_end_x, first_x))

        # Current cursor position clamped to signal area
        cur_x = max(axis_start_x, min(axis_end_x, self._cursor_pos.x()))

        x_left = int(min(first_x_clamped, cur_x))
        x_right = int(max(first_x_clamped, cur_x))

        if x_right <= x_left:
            return

        # Vertical span: whole signal drawing area (excluding bottom axis)
        top = 0
        bottom = max(0, self.height() - self._bottom_margin)

        color = QColor(0, 0, 255, 40)
        painter.fillRect(QRect(x_left, top, x_right - x_left, bottom - top), color)

    def _draw_voltage_scale_bar(self, painter: QPainter):
        bar_height = min(50, self._channel_height // 4)
        if bar_height <= 0:
            return

        x = self._cursor_pos.x() - self._bar_width // 2
        y = self._cursor_pos.y() - bar_height

        painter.fillRect(int(x), int(y), self._bar_width, bar_height, QColor(255, 0, 0))

        voltage_value = (bar_height / settings.EEG_VOLTAGE_SCALE) / self._scale_value
        label_text = f"{voltage_value:.1f} µV"
        x_size = self._font_metrics.horizontalAdvance(label_text) + 10
        label_rect = QRect(int(x) - x_size, int(y + bar_height // 2), x_size, 16)
        painter.drawText(label_rect, Qt.AlignmentFlag.AlignCenter, label_text)

    def _draw_time_scale_bar(self, painter: QPainter):
        signal_width = self._signal_width()
        if signal_width <= 0 or self._duration_ms <= 0:
            return

        time_bar_pixels = max(10, min(signal_width // 10, 120))
        y = self._cursor_pos.y() - self._bar_width
        x = self._cursor_pos.x()
        x = max(0, min(x, self.width() - self._right_margin - time_bar_pixels))

        painter.fillRect(int(x), int(y), time_bar_pixels, self._bar_width, QColor(255, 0, 0))

        time_value_ms = (time_bar_pixels / signal_width) * self._duration_ms
        if time_value_ms < 1000:
            label_text = f"{time_value_ms:.1f} ms"
        else:
            label_text = f"{time_value_ms / 1000:.2f} s"

        label_rect = QRect(int(x), int(y) + self._bar_width + 2, time_bar_pixels, 16)
        painter.drawText(label_rect, Qt.AlignmentFlag.AlignCenter, label_text)



class EegSignalPanel(QWidget):
    """High-performance EEG signal visualization panel with scrolling and optimization"""
    channel_scroll_changed = pyqtSignal()

    def __init__(self, session_manager, parent=None):
        super().__init__(parent)

        self._session_manager: QtWeegitSessionManagerWrapper = session_manager
        self._cached_processed_data: Dict[int, np.ndarray[np.float64]] = {}

        # Scale bar
        self._current_overlay_mode = OverlayModeEnum.NONE
        self._current_mouse_pos = None
        self._BAR_WIDTH = 3
        self._current_event_add_id: Optional[int] = None
        self._current_event_edit_mode: Optional[OverlayModeEnum] = None
        self._current_event_edit_first_time_ms: Optional[float] = None
        self._current_period_add_id: Optional[int] = None
        self._current_period_add_first_point: Optional[Tuple[int, float]] = None  # (sweep_idx, time_ms)

        # UI constants
        self._TOP_MARGIN = 30  # Space for future graphics
        self._BOTTOM_MARGIN = 30  # Space for time axis
        self._LEFT_MARGIN = 80  # Space for channel names
        self._RIGHT_MARGIN = 20
        self._CHANNEL_SPACING = 5

        self._channel_height = 60

        # Scroll state
        self._channel_scroll_offset = 0

        # Colors and styles
        self._bg_color = QColor(240, 240, 240)
        self._grid_color = QColor(200, 200, 200)
        self._SIGNAL_COLOR = QColor(0, 0, 0)
        self._text_color = QColor(0, 0, 0)
        self._axis_color = QColor(100, 100, 100)

        self.setup_ui()
        self.connect_signals()
        self._start_time_ms = 0.0
        self._end_time_ms = 0.0
        self._auto_scroll_timer = QTimer(self)
        self._auto_scroll_timer.setInterval(settings.AUTO_SCROLL_STEP_INTERVAL_MS)
        self._auto_scroll_timer.timeout.connect(self._on_auto_scroll_tick)
        self._auto_scroll_direction = 0

    def setup_ui(self):
        """Setup the UI with scrollbars"""
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMinimumSize(600, 400)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Top navigator widget for event names with arrows
        self.top_navigator_widget = TopNavigatorWidget(self._LEFT_MARGIN, self._RIGHT_MARGIN)
        self.top_navigator_widget.setFixedHeight(self._TOP_MARGIN)
        main_layout.addWidget(self.top_navigator_widget)

        # Connect navigation signal
        self.top_navigator_widget.event_navigation_requested.connect(
            self._session_manager.set_start_point
        )

        # Main content area with scrollbars
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Left vertical scrollbar for channels
        self.channel_scrollbar = QScrollBar(Qt.Orientation.Vertical)
        self.channel_scrollbar.setSingleStep(1)
        self.channel_scrollbar.setPageStep(1)
        content_layout.addWidget(self.channel_scrollbar)

        # Signal display area
        self.signal_widget = SignalWidget(self._LEFT_MARGIN, self._RIGHT_MARGIN, self._BOTTOM_MARGIN)
        self.signal_widget.setMouseTracking(True)
        self.signal_widget.installEventFilter(self)
        self.overlay_widget = OverlayWidget(self._LEFT_MARGIN, self._RIGHT_MARGIN,
                                            self._BOTTOM_MARGIN, self._BAR_WIDTH, self.signal_widget, )
        self.signal_widget.set_overlay_widget(self.overlay_widget)
        content_layout.addWidget(self.signal_widget, 1)

        main_layout.addLayout(content_layout, 4)

        # Bottom time axis and horizontal scrollbar
        bottom_layout = QHBoxLayout()

        # Double left arrow
        self.btn_double_left = QPushButton("<<")
        self.btn_double_left.setFixedWidth(40)
        bottom_layout.addWidget(self.btn_double_left)

        # Single left arrow
        self.btn_single_left = QPushButton("<")
        self.btn_single_left.setFixedWidth(30)
        bottom_layout.addWidget(self.btn_single_left)

        # Horizontal scrollbar
        self.time_scrollbar = QScrollBar(Qt.Orientation.Horizontal)
        bottom_layout.addWidget(self.time_scrollbar, 1)

        # Single right arrow
        self.btn_single_right = QPushButton(">")
        self.btn_single_right.setFixedWidth(30)
        bottom_layout.addWidget(self.btn_single_right)

        # Double right arrow
        self.btn_double_right = QPushButton(">>")
        self.btn_double_right.setFixedWidth(40)
        bottom_layout.addWidget(self.btn_double_right)

        main_layout.addLayout(bottom_layout)

    def connect_signals(self):
        """Connect all signals to their handlers"""
        # Time parameter changes
        self.channel_scrollbar.valueChanged.connect(self.on_channel_scroll)
        self.btn_double_left.clicked.connect(self.on_double_left_click)
        self.btn_single_left.clicked.connect(self.on_single_left_click)
        self.time_scrollbar.valueChanged.connect(self.on_time_scroll)
        self.btn_single_right.clicked.connect(self.on_single_right_click)
        self.btn_double_right.clicked.connect(self.on_double_right_click)

        self._session_manager.session_loaded.connect(self.on_session_loaded)
        self._session_manager.start_point_changed.connect(self.on_start_point_changed)
        self._session_manager.analogue_panel_height_changed.connect(self._redraw_data)

    def eventFilter(self, watched, event):
        if watched is self.signal_widget:
            if event.type() == QEvent.Type.MouseMove and isinstance(event, QMouseEvent):
                pos = event.position().toPoint()
                if self.signal_widget.rect().contains(pos):
                    self._current_mouse_pos = pos
                    if not self._current_overlay_mode == OverlayModeEnum.NONE:
                        self.setCursor(Qt.CursorShape.BlankCursor)
                else:
                    self._current_mouse_pos = None
                    self.unsetCursor()

                self._update_overlay_widget()
            elif event.type() == QEvent.Type.Leave:
                self._current_mouse_pos = None
                self.unsetCursor()
                self._update_overlay_widget()
            elif event.type() == QEvent.Type.MouseButtonPress and isinstance(event, QMouseEvent):
                button = event.button()
                if self._current_overlay_mode == OverlayModeEnum.EVENT_ADD:
                    if button == Qt.MouseButton.LeftButton:
                        self._handle_event_add_click(event)
                        return True
                    if button == Qt.MouseButton.RightButton:
                        self._stop_event_add_mode()
                        return True
                elif self._current_overlay_mode in (
                    OverlayModeEnum.EVENT_BAD_SET,
                    OverlayModeEnum.EVENT_BAD_UNSET,
                    OverlayModeEnum.EVENT_REMOVE,
                ):
                    if button == Qt.MouseButton.LeftButton:
                        self._handle_event_edit_click(event)
                        return True
                    if button == Qt.MouseButton.RightButton:
                        self._stop_event_edit_mode()
                        return True
                elif self._current_overlay_mode == OverlayModeEnum.PERIOD_ADD:
                    if button == Qt.MouseButton.LeftButton:
                        self._handle_period_add_click(event)
                        return True
                    if button == Qt.MouseButton.RightButton:
                        self._stop_period_add_mode()
                        return True
        return super().eventFilter(watched, event)

    def reset_data_and_redraw(self, processed_data):
        self._cached_processed_data = processed_data
        self._redraw_data()

    def _redraw_data(self):
        if not self._cached_processed_data:
            return

        gui_setup = self._session_manager.gui_setup
        if not gui_setup:
            return

        self.update_scrollbars()

        sample_rate = self._session_manager.header.sample_rate
        self._start_time_ms = (gui_setup.start_point / sample_rate) * 1000.0
        self._end_time_ms = self._start_time_ms + gui_setup.duration_ms

        all_events = self._session_manager.events if gui_setup.events_are_shown else []
        visible_events = []
        if gui_setup.events_are_shown:
            visible_events = self._get_events_for_current_window(gui_setup)

        all_periods = self._session_manager.periods if gui_setup.periods_are_shown else []
        visible_periods = []
        if gui_setup and gui_setup.periods_are_shown:
            visible_periods = self._get_periods_for_current_window(gui_setup)

        axis_offset_px = self.channel_scrollbar.width() if self.channel_scrollbar.isVisible() else 0
        self.top_navigator_widget.update_events(
            all_events=all_events,
            visible_events=visible_events,
            events_vocabulary=self._session_manager.events_vocabulary,
            all_periods=all_periods,
            visible_periods=visible_periods,
            periods_vocabulary=self._session_manager.periods_vocabulary,
            sweep_idx=gui_setup.current_sweep_idx,
            start_point=gui_setup.start_point,
            duration_ms=gui_setup.duration_ms,
            sample_rate=sample_rate,
            start_time_ms=self._start_time_ms,
            header_points_per_sweep=self._session_manager.header.number_of_points_per_sweep,
            axis_offset_px=axis_offset_px,
        )

        # Update signal widget (without event labels)
        analogue_visible = bool(gui_setup.analogue_panel_is_shown)
        analogue_channel_indexes = self.get_visible_analogue_channel_indexes() if analogue_visible else []
        cached_spikes = self._session_manager.current_user_session.cached_spikes.get(gui_setup.current_sweep_idx)
        self.signal_widget.reset_data_and_redraw(
            self._cached_processed_data,
            self.get_visible_channel_indexes(),
            self._session_manager.header.channel_info.name,
            gui_setup.scale,
            start_point=gui_setup.start_point,
            duration_ms=gui_setup.duration_ms,
            start_time_ms=self._start_time_ms,
            sample_rate=sample_rate,
            visible_events=visible_events,
            visible_periods=visible_periods,
            sweep_idx=gui_setup.current_sweep_idx,
            events_are_visible=gui_setup.events_are_shown,
            periods_are_visible=gui_setup.periods_are_shown,
            traces_are_visible=gui_setup.traces_are_shown,
            csd_is_visible=gui_setup.csd_is_shown,
            analogue_visible=analogue_visible,
            analogue_channel_indexes=analogue_channel_indexes,
            analogue_channels_setup=gui_setup.analogue_channels_setup,
            analogue_panel_height=gui_setup.analogue_panel_height,
            cached_spikes=cached_spikes,
            spikes_are_visible=gui_setup.spikes_are_shown,
        )

        self._update_overlay_widget()

    def _get_events_for_current_window(self, gui_setup):
        """Return events that fall into the current time window and sweep."""
        if not self._session_manager or not self._session_manager.current_user_session:
            return []

        header = self._session_manager.header
        if not header:
            return []

        events = getattr(self._session_manager, "events", [])
        if not events:
            return []

        sweep_idx = gui_setup.current_sweep_idx
        return [
            e
            for e in events
            if e.sweep_idx == sweep_idx and self._start_time_ms <= e.time_ms <= self._end_time_ms
        ]

    def _get_periods_for_current_window(self, gui_setup):
        """Return periods that overlap with the current time window and sweep.
        
        Note: Period start_time_ms and end_time_ms are relative to sweep start (like events).
        """
        if not self._session_manager or not self._session_manager.current_user_session:
            return []

        header = self._session_manager.header
        if not header:
            return []

        periods = getattr(self._session_manager, "periods", [])
        if not periods:
            return []

        sweep_idx = gui_setup.current_sweep_idx
        # Return periods that overlap with current sweep and time window
        # Period times are relative to sweep start (like events)
        return [
            p
            for p in periods
            if (p.start_sweep_idx <= sweep_idx <= p.end_sweep_idx and
                not (p.end_time_ms < self._start_time_ms or p.start_time_ms > self._end_time_ms))
        ]

    def _update_overlay_widget(self):
        if (not hasattr(self, 'overlay_widget') or self.overlay_widget is None
                or not self._session_manager.session_is_active):
            return

        gui_setup = self._session_manager.gui_setup if self._session_manager else None
        duration_ms = gui_setup.duration_ms if gui_setup else 0.0
        scale_value = gui_setup.scale if gui_setup else 1.0
        start_time_ms = self._start_time_ms if gui_setup else 0.0
        channel_height = self.signal_widget._channel_height or self._channel_height

        # Determine selection_start_time_ms based on current mode
        selection_start_time_ms = None
        if self._current_overlay_mode in (
            OverlayModeEnum.EVENT_BAD_SET,
            OverlayModeEnum.EVENT_BAD_UNSET,
            OverlayModeEnum.EVENT_REMOVE,
        ):
            selection_start_time_ms = self._current_event_edit_first_time_ms
        elif self._current_overlay_mode == OverlayModeEnum.PERIOD_ADD:
            if self._current_period_add_first_point is not None:
                selection_start_time_ms = self._current_period_add_first_point[1]  # Extract time_ms

        self.overlay_widget.update_state(
            cursor_pos=self._current_mouse_pos,
            overlay_mode=self._current_overlay_mode,
            channel_height=channel_height,
            duration_ms=duration_ms,
            scale_value=scale_value,
            start_time_ms=start_time_ms,
            selection_start_time_ms=selection_start_time_ms,
        )

    # ---- Events helper API ----
    def start_event_add_mode(self, event_name_id: int):
        """Enable interactive event placement for the given vocabulary id."""
        self._current_event_add_id = event_name_id
        self._current_overlay_mode = OverlayModeEnum.EVENT_ADD
        self.setCursor(Qt.CursorShape.BlankCursor)
        self._update_overlay_widget()

    def _stop_event_add_mode(self):
        self._current_event_add_id = None
        if self._current_overlay_mode == OverlayModeEnum.EVENT_ADD:
            self._current_overlay_mode = OverlayModeEnum.NONE
            self.unsetCursor()
        self._update_overlay_widget()

    def _stop_period_add_mode(self):
        self._current_period_add_id = None
        self._current_period_add_first_point = None
        if self._current_overlay_mode == OverlayModeEnum.PERIOD_ADD:
            self._current_overlay_mode = OverlayModeEnum.NONE
            self.unsetCursor()
        self._update_overlay_widget()

    # ---- Events edit (bad / remove) API ----
    def start_set_bad_event_mode(self):
        """Start interactive mode to mark events as bad inside a selected time window."""
        self._start_event_edit_mode(OverlayModeEnum.EVENT_BAD_SET)

    def start_unset_bad_event_mode(self):
        """Start interactive mode to unset 'bad' flag for events inside a selected time window."""
        self._start_event_edit_mode(OverlayModeEnum.EVENT_BAD_UNSET)

    def start_event_remove_mode(self):
        """Start interactive mode to remove events inside a selected time window."""
        self._start_event_edit_mode(OverlayModeEnum.EVENT_REMOVE)

    def _start_event_edit_mode(self, mode: OverlayModeEnum):
        """Common initializer for all 'edit events in window' modes."""
        # Cancel any ongoing add modes
        self._stop_event_add_mode()
        self._stop_period_add_mode()

        self._current_event_edit_mode = mode
        self._current_event_edit_first_time_ms = None
        self._current_overlay_mode = mode
        self.setCursor(Qt.CursorShape.BlankCursor)
        self._update_overlay_widget()

    def _stop_event_edit_mode(self):
        self._current_event_edit_mode = None
        self._current_event_edit_first_time_ms = None
        if self._current_overlay_mode in (
            OverlayModeEnum.EVENT_BAD_SET,
            OverlayModeEnum.EVENT_BAD_UNSET,
            OverlayModeEnum.EVENT_REMOVE,
        ):
            self._current_overlay_mode = OverlayModeEnum.NONE
            self.unsetCursor()
        self._update_overlay_widget()

    # ---- Periods helper API ----
    def start_period_add_mode(self, period_name_id: int):
        """Enable interactive period placement for the given vocabulary id."""
        # Cancel any ongoing event modes
        self._stop_event_add_mode()
        self._stop_event_edit_mode()

        self._current_period_add_id = period_name_id
        self._current_period_add_first_point = None
        self._current_overlay_mode = OverlayModeEnum.PERIOD_ADD
        self.setCursor(Qt.CursorShape.BlankCursor)
        self._update_overlay_widget()

    def _handle_period_add_click(self, event: QMouseEvent):
        """Handle left click when in PERIOD_ADD mode: collect two points and create period."""
        if self._current_period_add_id is None:
            return

        gui_setup = self._session_manager.gui_setup
        if not gui_setup:
            return

        time_ms = self._mouse_event_to_time_ms(event)
        if time_ms is None:
            return

        current_sweep_idx = gui_setup.current_sweep_idx

        if self._current_period_add_first_point is None:
            # First point: store and wait for the second
            self._current_period_add_first_point = (current_sweep_idx, time_ms)
            self._update_overlay_widget()
            return

        # Second point: determine start/end and create period
        first_sweep_idx, first_time_ms = self._current_period_add_first_point
        second_sweep_idx = current_sweep_idx
        second_time_ms = time_ms

        # Determine which point is earlier: compare sweep_idx first, then time_ms
        if first_sweep_idx < second_sweep_idx or (
            first_sweep_idx == second_sweep_idx and first_time_ms <= second_time_ms
        ):
            start_sweep_idx = first_sweep_idx
            start_time_ms = first_time_ms
            end_sweep_idx = second_sweep_idx
            end_time_ms = second_time_ms
        else:
            start_sweep_idx = second_sweep_idx
            start_time_ms = second_time_ms
            end_sweep_idx = first_sweep_idx
            end_time_ms = first_time_ms

        self._session_manager.add_period(
            period_name_id=self._current_period_add_id,
            start_sweep_idx=start_sweep_idx,
            start_time_ms=start_time_ms,
            end_sweep_idx=end_sweep_idx,
            end_time_ms=end_time_ms,
        )

        self._stop_period_add_mode()

    def _handle_event_add_click(self, event: QMouseEvent):
        """Handle left click when in EVENT_ADD mode: compute time_ms and create event."""
        if self._current_event_add_id is None:
            return

        time_ms = self._mouse_event_to_time_ms(event)
        if time_ms is None:
            return

        gui_setup = self._session_manager.gui_setup
        if not gui_setup:
            return

        self._session_manager.add_event(
            event_name_id=self._current_event_add_id,
            sweep_idx=gui_setup.current_sweep_idx,
            time_ms=time_ms,
        )

    def _handle_event_edit_click(self, event: QMouseEvent):
        """Handle left click for EVENT_BAD_SET / EVENT_BAD_UNSET / EVENT_REMOVE modes."""
        if self._current_event_edit_mode is None:
            return

        time_ms = self._mouse_event_to_time_ms(event)
        if time_ms is None:
            return

        if self._current_event_edit_first_time_ms is None:
            # First point: store and wait for the second
            self._current_event_edit_first_time_ms = time_ms
            return

        # Second point: apply modification for events inside the window
        start_ms = min(self._current_event_edit_first_time_ms, time_ms)
        end_ms = max(self._current_event_edit_first_time_ms, time_ms)
        self._apply_event_edit_in_window(start_ms, end_ms)
        self._stop_event_edit_mode()

    def _mouse_event_to_time_ms(self, event: QMouseEvent) -> Optional[float]:
        """Convert mouse X position on the signal widget to absolute time in ms."""
        pos = event.position().toPoint()
        # Only allow clicks inside signal area horizontally
        left = self._LEFT_MARGIN
        right = self.signal_widget.width() - self._RIGHT_MARGIN
        if right <= left or pos.x() < left or pos.x() > right:
            return None

        gui_setup = self._session_manager.gui_setup
        if not gui_setup:
            return None

        sample_rate = self._session_manager.header.sample_rate
        # start_time_ms = (gui_setup.start_point / sample_rate) * 1000.0
        duration_ms = gui_setup.duration_ms
        if duration_ms <= 0:
            return None

        rel = (pos.x() - left) / (right - left)
        rel = max(0.0, min(1.0, rel))
        return self._start_time_ms + rel * duration_ms

    def _apply_event_edit_in_window(self, start_ms: float, end_ms: float):
        """Apply current edit mode to all events in [start_ms, end_ms] for current sweep."""
        gui_setup = self._session_manager.gui_setup
        if not gui_setup:
            return

        events = self._session_manager.events
        if not events:
            return

        sweep_idx = gui_setup.current_sweep_idx
        affected_events = [
            e for e in events
            if e.sweep_idx == sweep_idx and start_ms <= e.time_ms <= end_ms
        ]
        if not affected_events:
            return

        if self._current_event_edit_mode in (OverlayModeEnum.EVENT_BAD_SET, OverlayModeEnum.EVENT_BAD_UNSET):
            is_bad = self._current_event_edit_mode == OverlayModeEnum.EVENT_BAD_SET
            self._session_manager.set_events_bad_flag(affected_events, is_bad)
        elif self._current_event_edit_mode == OverlayModeEnum.EVENT_REMOVE:
            self._session_manager.remove_events(affected_events)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._redraw_data()

    def _current_visible_channel_indexes(self):
        visible_indexes = self._session_manager.gui_setup.visible_channel_indexes
        if not visible_indexes:
            visible_indexes = list(range(self._session_manager.header.number_of_channels))

        return visible_indexes

    def update_scrollbars(self):
        """Update scrollbar ranges based on current data and settings"""
        if not self._session_manager.header or not self._session_manager.gui_setup:
            return

        # Channel scrollbar
        eeg_channels = self._session_manager.current_user_session.eeg_channel_indexes
        visible_channel_indexes = [ch for ch in eeg_channels if ch in self._current_visible_channel_indexes()]

        total_channels = len(visible_channel_indexes)
        if total_channels > self._session_manager.gui_setup.number_of_channels_to_show:
            self.channel_scrollbar.setMaximum(
                total_channels - self._session_manager.gui_setup.number_of_channels_to_show)
            self.channel_scrollbar.setVisible(True)
        else:
            self.channel_scrollbar.setMaximum(0)
            self.channel_scrollbar.setVisible(False)

    def get_visible_channel_indexes(self) -> List[int]:
        """Get currently visible channels considering scroll position"""
        if not self._session_manager.current_user_session:
            return []

        eeg_channels = self._session_manager.current_user_session.eeg_channel_indexes
        visible_channel_indexes = [ch for ch in eeg_channels if ch in self._current_visible_channel_indexes()]

        start_idx = self._channel_scroll_offset
        end_idx = start_idx + self._session_manager.gui_setup.number_of_channels_to_show
        return visible_channel_indexes[start_idx:end_idx]

    def get_visible_analogue_channel_indexes(self) -> List[int]:
        """Get currently visible analogue channels"""
        if not self._session_manager.current_user_session:
            return []

        analogue_channels = self._session_manager.current_user_session.analogue_input_channel_indexes
        visible_channel_indexes = [ch for ch in analogue_channels if ch in self._current_visible_channel_indexes()]
        return visible_channel_indexes

    def set_analogue_panel_visible(self, visible: bool):
        """Show or hide the analogue signal panel"""
        self._redraw_data()

    def on_channel_scroll(self, value):
        """Handle channel scrollbar movement"""
        self._channel_scroll_offset = value
        self.channel_scroll_changed.emit()

    def on_time_scroll(self, value):
        """Handle time scrollbar movement"""
        self._session_manager.set_start_point(value)

    def on_start_point_changed(self, value):
        self.time_scrollbar.setValue(value)

    def on_session_loaded(self):
        total_points = self._session_manager.header.number_of_points_per_sweep
        visible_points = int((self._session_manager.gui_setup.duration_ms / 1000.0) *
                             self._session_manager.header.sample_rate)
        self.time_scrollbar.setMaximum(max(0, total_points - visible_points))
        self.time_scrollbar.setValue(self._session_manager.gui_setup.start_point)

    def on_single_left_click(self):
        """Handle single left arrow click"""
        step = self._time_step_samples()
        if step <= 0:
            return
        self.time_scrollbar.setValue(self._session_manager.gui_setup.start_point - step)

    def on_single_right_click(self):
        step = self._time_step_samples()
        if step <= 0:
            return
        self.time_scrollbar.setValue(self._session_manager.gui_setup.start_point + step)

    def on_double_right_click(self):
        self._toggle_auto_scroll(direction=1)

    def on_double_left_click(self):
        self._toggle_auto_scroll(direction=-1)

    def _time_step_samples(self) -> int:
        if not self._session_manager.gui_setup or not self._session_manager.header:
            return 0
        interval = self._session_manager.header.sample_interval_microseconds
        if interval <= 0:
            return 0
        return int((self._session_manager.gui_setup.time_step_ms * 1000) / interval)

    def _toggle_auto_scroll(self, direction: int):
        if self._auto_scroll_timer.isActive() and self._auto_scroll_direction == direction:
            self._auto_scroll_timer.stop()
            self._auto_scroll_direction = 0
            return
        self._auto_scroll_direction = direction
        if self._session_manager.gui_setup:
            self._auto_scroll_timer.setInterval(
                self._session_manager.gui_setup.autoscroll_step_interval_ms
            )
        self._auto_scroll_timer.start()
        self._on_auto_scroll_tick()

    def _on_auto_scroll_tick(self):
        if not self._session_manager.gui_setup:
            self._auto_scroll_timer.stop()
            self._auto_scroll_direction = 0
            return
        step = self._time_step_samples()
        if step <= 0:
            self._auto_scroll_timer.stop()
            self._auto_scroll_direction = 0
            return
        delta = step if self._auto_scroll_direction > 0 else -step
        self.time_scrollbar.setValue(self._session_manager.gui_setup.start_point + delta)

    # FOR FUN
    def keyPressEvent(self, event):
        """Handle keyboard events"""
        key = event.key()
        if key in {Qt.Key.Key_M, Qt.Key.Key_P, Qt.Key.Key_Escape}:
            if key == Qt.Key.Key_Escape:
                if self._current_overlay_mode == OverlayModeEnum.EVENT_ADD:
                    self._stop_event_add_mode()
                    self._update_overlay_widget()
                    event.accept()
                    return
                elif self._current_overlay_mode == OverlayModeEnum.PERIOD_ADD:
                    self._stop_period_add_mode()
                    self._update_overlay_widget()
                    event.accept()
                    return
            if key == Qt.Key.Key_M:
                # Toggle voltage scale bar with 'M' key
                if self._current_overlay_mode == OverlayModeEnum.NONE:
                    self._current_overlay_mode = OverlayModeEnum.TIME_VOLTAGE_BAR
                    self.setCursor(Qt.CursorShape.BlankCursor)
                elif self._current_overlay_mode == OverlayModeEnum.TIME_VOLTAGE_BAR:
                    self._current_overlay_mode = OverlayModeEnum.NONE
                    self.unsetCursor()

            self._update_overlay_widget()
            event.accept()
        else:
            super().keyPressEvent(event)

    def leaveEvent(self, event):
        """Hide scale when mouse leaves"""
        self._update_overlay_widget()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        """Set focus when clicked"""
        self.setFocus()
        super().mousePressEvent(event)

    def wheelEvent(self, event):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier and self._session_manager.gui_setup:
            cursor_x = event.position().x()
            widget_width = self.width()

            if cursor_x < 0 or cursor_x > widget_width:
                return

            rel_pos = cursor_x / widget_width
            current_zoom = 10000 / self._session_manager.gui_setup.duration_ms
            scale_factor = 2.0 + (0.1 / max(1.0, current_zoom ** 0.5))
            voltage_scale_dif = 0.2
            delta = event.angleDelta().y()
            if delta > 0:  # zoom in
                new_duration = self._session_manager.gui_setup.duration_ms / scale_factor
                new_start_point = (self._session_manager.gui_setup.start_point
                                   + (self._session_manager.gui_setup.duration_ms - new_duration) / 1000.0
                                   * self._session_manager.header.sample_rate * rel_pos)
                new_scale = min(self._session_manager.gui_setup.scale + voltage_scale_dif, settings.MAX_SCALE)
            else:  # zoom out
                new_duration = self._session_manager.gui_setup.duration_ms * scale_factor
                new_start_point = (self._session_manager.gui_setup.start_point
                                   - (new_duration - self._session_manager.gui_setup.duration_ms) / 1000.0
                                   * self._session_manager.header.sample_rate * rel_pos)
                new_scale = max(self._session_manager.gui_setup.scale - voltage_scale_dif, settings.MIN_SCALE)

            self._session_manager.set_start_point(int(new_start_point))
            self._session_manager.set_duration_ms(int(new_duration))
            self._session_manager.set_scale(new_scale)
            event.accept()
        else:
            super().wheelEvent(event)
