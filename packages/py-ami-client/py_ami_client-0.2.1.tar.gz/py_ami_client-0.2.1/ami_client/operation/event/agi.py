from dataclasses import dataclass
from typing import Optional

from ._base import Event, ChannelMixin

class AGI:
    """Marker base for all AGI events"""


@dataclass
class AGIMixin:
    Command: Optional[str] = None
    CommandId: Optional[str] = None


@dataclass
class AGIExecEnd(Event, ChannelMixin, AGIMixin):
    """Raised when a received AGI command completes processing."""
    ResultCode: Optional[str] = None
    Result: Optional[str] = None

    def __post_init__(self):
        self._asterisk_name = 'AGIExecEnd'
        self._label = 'AGI Exec End'
        return super().__post_init__()


@dataclass
class AGIExecStart(Event, ChannelMixin, AGIMixin):
    """Raised when a received AGI command starts processing."""

    def __post_init__(self):
        self._asterisk_name = 'AGIExecStart'
        self._label = 'AGI Exec Start'
        return super().__post_init__()
