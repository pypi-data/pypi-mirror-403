from dataclasses import dataclass
from ._base import Response

@dataclass(init=False)
class Error(Response):
    def __init__(self, *args, **kwargs) -> None:
        self.args = args
        self.kwargs = kwargs

        for k, v in self.kwargs.items():
            setattr(self, k.replace('-', '_'), v)

        self.__post_init__()

    def __post_init__(self) -> None:
        self._asterisk_name = 'Error'
        self._label = 'Error'
        super().__post_init__()
