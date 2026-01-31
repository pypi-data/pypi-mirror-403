from dataclasses import dataclass
from typing import Optional

from ._base import Event, ChannelEventMixin

class AsyncAGI:
    """Marker base for all AsyncAGI events"""

@dataclass
class AsyncAGIEnd(Event, ChannelEventMixin, AsyncAGI):
    """Raised when a channel stops AsyncAGI command processing."""

    def __post_init__(self):
        self._asterisk_name = 'AsyncAGIEnd'
        self._label = 'Async AGI Ended'
        return super().__post_init__()


@dataclass
class AsyncAGIExec(Event, ChannelEventMixin, AsyncAGI):
    """Raised when AsyncAGI completes an AGI command."""
    CommandID: Optional[str] = None
    Result: Optional[str] = None

    def __post_init__(self):
        self._asterisk_name = 'AsyncAGIExec'
        self._label = 'Async AGI Executed'
        return super().__post_init__()


@dataclass
class AsyncAGIStart(Event, ChannelEventMixin, AsyncAGI):
    """Raised when a channel starts AsyncAGI command processing."""
    Env:  Optional[str] = None

    def __post_init__(self):
        self._asterisk_name = 'AsyncAGIStart'
        self._label = 'Async AGI Started'
        return super().__post_init__()

