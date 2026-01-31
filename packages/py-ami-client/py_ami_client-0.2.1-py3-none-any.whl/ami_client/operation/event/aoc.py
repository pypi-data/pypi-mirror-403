from dataclasses import dataclass
from typing import Optional, TypeAlias, Literal

from ._base import Event, ChannelMixin

TypeOptions: TypeAlias = Literal[
    'NotAvailable', 'Free', 'Currency', 'Units'
]
BillingIDOptions: TypeAlias = Literal[
    'Normal','Reverse', 'CreditCard', 'CallForwardingUnconditional',
    'CallForwardingBusy', 'CallForwardingNoReply', 'CallDeflection',
    'CallTransfer', 'NotAvailable',
]
TotalTypeOptions: TypeAlias = Literal[
    'SubTotal', 'Total'
]
MultiplierOptions: TypeAlias = Literal[
    '1/1000', '1/100', '1/10', '1', '10', '100', '1000'
]
RateTypeOptions: TypeAlias = Literal[
    'NotAvailable', 'Free', 'FreeFromBeginning',
    'Duration', 'Flag', 'Volume', 'SpecialCode',
]
UnitOptions: TypeAlias = Literal[
    'Octet', 'Segment', 'Message'
]


class AOC:
    """Marker base for all AOC events"""


@dataclass
class AOCMixin:  # monetary identity
    Currency: Optional[str] = None
    Name: Optional[str] = None
    Cost: Optional[str] = None
    Multiplier: Optional[MultiplierOptions] = None


@dataclass
class AOCCommonMixin:  # charge accounting
    Charge: Optional[str] = None
    Type: Optional[TypeOptions] = None
    BillingID: Optional[BillingIDOptions] = None
    TotalType: Optional[TotalTypeOptions] = None
    Units: Optional[str] = None
    NumberOf: Optional[str] = None
    TypeOf: Optional[str] = None


@dataclass
class AOC_D(Event, AOC, ChannelMixin, AOCMixin, AOCCommonMixin):
    def __post_init__(self):
        self._asterisk_name = 'AOC-D'
        self._label = 'Advice of Charge during a call'
        super().__post_init__()


@dataclass
class AOC_E(Event, AOC, ChannelMixin, AOCMixin, AOCCommonMixin):
    ChargingAssociation: Optional[str] = None
    Number: Optional[str] = None
    Plan: Optional[str] = None
    ID: Optional[str] = None

    def __post_init__(self):
        self._asterisk_name = 'AOC-E'
        self._label = 'Advice of Charge end of a call'
        super().__post_init__()


@dataclass
class AOC_S(Event, AOC, ChannelMixin, AOCMixin):
    Chargeable: Optional[str] = None
    RateType: Optional[RateTypeOptions] = None
    ChargingType: Optional[str] = None
    StepFunction: Optional[str] = None
    Granularity: Optional[str] = None
    Length: Optional[str] = None
    Scale: Optional[str] = None
    Unit: Optional[UnitOptions] = None
    SpecialCode: Optional[str] = None

    def __post_init__(self):
        self._asterisk_name = 'AOC-S'
        self._label = 'Advice of Charge beginning of a call'
        super().__post_init__()
