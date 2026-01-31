from dataclasses import dataclass
from ._base import Response

@dataclass(init=False)
class Success(Response):
    def __init__(self, *args, **kwargs) -> None:
        self.args = args
        self.kwargs = kwargs

        for k, v in self.kwargs.items():
            setattr(self, k.replace('-', '_'), v)

        self.__post_init__()

    def __post_init__(self) -> None:
        self._asterisk_name = 'Success'
        self._label = 'Success'
        super().__post_init__()
