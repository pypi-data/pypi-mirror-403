from dataclasses import dataclass
from typing import Optional

from ._base import Event

class BaseAlarm:
    """Marker base for all Alarm events"""


@dataclass
class AlarmMixin:
    DAHDIChannel: Optional[str] = None


@dataclass
class Alarm(Event, BaseAlarm, AlarmMixin):
    """Raised when an alarm is set on a DAHDI channel."""
    Alarm: Optional[str] = None

    def __post_init__(self):
        self._asterisk_name = 'Alarm'
        self._label = 'Alarm'
        return super().__post_init__()


@dataclass
class AlarmClear(Event, BaseAlarm, AlarmMixin):
    """Raised when an alarm is cleared on a DAHDI channel."""
    def __post_init__(self):
        self._asterisk_name = 'AlarmClear'
        self._label = 'Alarm Clear'
        return super().__post_init__()

