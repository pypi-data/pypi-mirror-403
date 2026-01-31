from dataclasses import dataclass

from ._base import Action

@dataclass
class CoreStatus(Action):
    def __post_init__(self):
        self._asterisk_name = 'CoreStatus'
        self._label = 'CoreStatus'
        super().__post_init__()
