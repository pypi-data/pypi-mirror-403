from dataclasses import dataclass

from ._base import Action

@dataclass
class Logoff(Action):
    def __post_init__(self):
        self._asterisk_name = 'Logoff'
        self._label = 'Logoff'
        super().__post_init__()