from dataclasses import dataclass
from typing import Optional

from ._base import Event, ChannelMixin

@dataclass
class VarSet(Event, ChannelMixin):
    Variable: Optional[str] = None
    Value: Optional[str] = None

    def __post_init__(self):
        self._asterisk_name = 'VarSet'
        self._label = 'Variable Set'
        return super().__post_init__()
