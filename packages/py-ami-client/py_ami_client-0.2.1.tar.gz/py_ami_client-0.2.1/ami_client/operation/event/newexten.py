from dataclasses import dataclass
from typing import Optional

from ._base import Event, ChannelMixin

@dataclass
class Newexten(Event, ChannelMixin):
    Extension: Optional[str] = None
    Application: Optional[str] = None
    AppData: Optional[str] = None

    def __post_init__(self):        
        self._asterisk_name = 'Newexten'
        self._label = 'New Extension'
        return super().__post_init__()
