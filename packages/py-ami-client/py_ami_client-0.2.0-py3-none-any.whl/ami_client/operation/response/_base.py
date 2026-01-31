from dataclasses import dataclass
from typing import Optional

from ...operation._base import Operation

class ServerError(Exception):
    ...

@dataclass
class Response(Operation):
    Response: str
    ActionID: int
    Message: str

    def __post_init__(self) -> None:
        self.Response = self._asterisk_name
        self.ActionID = int(self.ActionID)

    def raise_on_status(self) -> None:
        if self.Response == 'Error':
            raise ServerError(self.Message)
