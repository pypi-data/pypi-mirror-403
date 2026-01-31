from typing import Optional
from dataclasses import dataclass

from ._base import Action

@dataclass
class Originate(Action):
    Channel: Optional[str] = None
    Exten: Optional[str] = None
    Context: Optional[str] = None
    Priority: Optional[str] = None
    Application: Optional[str] = None
    Data: Optional[str] = None
    Timeout: Optional[str] = None
    CallerID: Optional[str] = None
    Variable: Optional[str] = None
    Account: Optional[str] = None
    EarlyMedia: Optional[str] = None
    Async: Optional[str] = None
    Codecs: Optional[str] = None
    ChannelId: Optional[str] = None
    OtherChannelId: Optional[str] = None
    PreDialGoSub: Optional[str] = None

    def __post_init__(self):
        self._asterisk_name = 'Originate'
        self._label = 'Originate'
        super().__post_init__()
