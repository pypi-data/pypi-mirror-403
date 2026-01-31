from typing import Optional
from dataclasses import dataclass

from ._base import Action

@dataclass
class Ping(Action):
    def __post_init__(self):
        self._asterisk_name = 'Ping'
        self._label = 'Ping'
        super().__post_init__()
