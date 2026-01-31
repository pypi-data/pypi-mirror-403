from dataclasses import dataclass
from typing import Optional

from ._base import Event, ChannelMixin

@dataclass
class Hangup(Event, ChannelMixin):
    Cause: Optional[str] = None
    Cause_txt: Optional[str] = None

    def __post_init__(self):
        self._asterisk_name = 'Hangup'
        self._label = 'Hangup'
        return super().__post_init__()