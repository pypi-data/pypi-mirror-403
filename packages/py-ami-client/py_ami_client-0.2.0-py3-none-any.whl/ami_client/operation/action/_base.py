import random, threading
from dataclasses import dataclass
from typing import Optional

from ...operation import Operation
from ..response import Response

@dataclass
class Action(Operation):
    ActionID: int = 0

    def __post_init__(self):
        self.Action = self._asterisk_name
        if self.ActionID in (0, None):
            self.ActionID = random.randint(1, 100_000_000_000)


class PendingAction:
    def __init__(self, action: Action) -> None:
        self.action = action
        self.__response = None
        self._thread_event = threading.Event()
    
    @property
    def response(self) -> Response:
        if self.__response:
            return self.__response
        
        else:
            return self.wait(5)

    def set_response(self, response: Response) -> None:
        self.__response = response
        self._thread_event.set()
    
    def wait(self, timeout: Optional[float] = None) -> Response:
        finished = self._thread_event.wait(timeout)
        if not finished:
            raise TimeoutError(f"No response received for action {self.action.ActionID}")

        if not self.__response: raise

        return self.__response
