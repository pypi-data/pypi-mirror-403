from dataclasses import dataclass, field
from typing import Any, Dict

ASTERISK_BANNER: str = 'Asterisk Call Manager'

@dataclass
class Operation:
    _label: str = field(init=False, repr=False)
    _asterisk_name: str = field(init=False, repr=False)

    def to_dict(self) -> Dict[str, Any]:
        return {
            k.replace('_', '-'): v for k, v in self.__dict__.items() if not k.startswith('_') and v is not None
        }

    def to_raw(self) -> str:
        return self.dict_to_raw(self.to_dict())


    @staticmethod
    def parse_raw(raw: str) -> Dict[str, Any]:
        """
        Parse `Asterisk` operation content to dictionary.

        Args:
            raw(str): Asterisk content.
        
        Returns:
            Dict[str, Any]: Asterisk data as dictionary.
        """
        lines = raw.strip().split('\r\n')
        operation_dict: Dict[str, Any] = {}
        for line in lines:
            if ASTERISK_BANNER in line: continue
            key, value = line.split(':', 1)
            operation_dict[key.lstrip().replace('-', '_')] = value.lstrip()

        return operation_dict

    @staticmethod
    def dict_to_raw(operation_dict: Dict[str, Any]) -> str:
        """
        Converts dictionary to `Asterisk` data.

        Args:
            operation_dict(Dict[str, Any]): Asterisk data as dictionary.
        
        Returns:
           str: Asterisk content.
        """
        raw_operation: str = ''
        for key, value in operation_dict.items():
            raw_operation += f'{key.replace('_', '-')}: {value}\r\n'

        raw_operation += '\r\n'
        return raw_operation


    def __str__(self) -> str:
        return f'<Operation: {self._asterisk_name}>'

    def __repr__(self) -> str:
        return f'<Operation: {self._asterisk_name}>'


@dataclass(init=False)
class NotImplementedOperation(Operation):
    def __init__(self, *args, **kwargs) -> None:
        self.args = args
        self.kwargs = kwargs

        for k, v in self.kwargs.items():
            setattr(self, k.replace('-', '_'), v)


        self._asterisk_name: str = getattr(
            self, 'Event', getattr(
                self, 'Response', getattr(
                    self, 'Action', 'UnkhownAsteriskName'
                )
            )
        )
        if self._asterisk_name == 'UnkhownAsteriskName':
            raise ValueError('Unkhown Operation type: Must have `Event` or `Response` or `Action` as keyword argument')

        self._label: str = self._asterisk_name
