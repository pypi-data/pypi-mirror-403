from dataclasses import dataclass
from typing import Optional, Literal, TypeAlias

from ._base import Event, ChannelMixin


MembershipOptions: TypeAlias = Literal[
    'dynamic', 'realtime', 'static',
]
InCallOptions: TypeAlias = Literal[
    '0', '1',
]
StatusOptions: TypeAlias = Literal[
    '0', '1', '2', '3', '4', '5', '6', '7', '8',
]
PausedOptions: TypeAlias = Literal[
    '0', '1',
]
RinginuseOptions: TypeAlias = Literal[
    '0', '1',
]


class Queue:
    """Marker base for all Queue events"""


@dataclass
class QueueMixin:
    Queue: Optional[str] = None


@dataclass
class QueueCallerMixin(QueueMixin):
    Position: Optional[str] = None


@dataclass
class QueueMemberMixin(QueueMixin):
    MemberName: Optional[str] = None
    Interface: Optional[str] = None
    StateInterface: Optional[str] = None
    Membership: Optional[MembershipOptions] = None
    Penalty: Optional[str] = None
    CallsTaken: Optional[str] = None
    LastCall: Optional[str] = None
    LastPause: Optional[str] = None
    LoginTime: Optional[str] = None
    InCall: Optional[InCallOptions] = None
    Status: Optional[StatusOptions] = None
    Paused: Optional[PausedOptions] = None
    PausedReason: Optional[str] = None
    Ringinuse: Optional[RinginuseOptions] = None
    Wrapuptime: Optional[str] = None


@dataclass
class QueueCallerAbandon(Event, Queue, QueueCallerMixin, ChannelMixin):
    """Raised when a caller abandons the queue."""
    Queue: Optional[str] = None
    OriginalPosition: Optional[str] = None
    HoldTime: Optional[str] = None

    def __post_init__(self):
        self._asterisk_name = 'QueueCallerAbandon'
        self._label = 'Queue Caller Abandon'
        return super().__post_init__()


@dataclass
class QueueCallerJoin(Event, Queue, QueueCallerMixin, ChannelMixin):
    """Raised when a caller joins a Queue."""
    Count: Optional[str] = None

    def __post_init__(self):
        self._asterisk_name = 'QueueCallerJoin'
        self._label = 'Queue Caller Join'
        return super().__post_init__()


@dataclass
class QueueCallerLeave(Event, Queue, QueueCallerMixin, ChannelMixin):
    """Raised when a caller leaves a Queue."""
    Count: Optional[str] = None

    def __post_init__(self):
        self._asterisk_name = 'QueueCallerLeave'
        self._label = 'Queue Caller Leave'
        return super().__post_init__()


@dataclass
class QueueEntry(Event, Queue, QueueCallerMixin):
    """Raised in response to the QueueStatus action."""
    Channel: Optional[str] = None
    Uniqueid: Optional[str] = None
    CallerIDNum: Optional[str] = None
    CallerIDName: Optional[str] = None
    ConnectedLineNum: Optional[str] = None
    ConnectedLineName: Optional[str] = None
    Wait: Optional[str] = None
    Priority: Optional[str] = None

    def __post_init__(self):
        self._asterisk_name = 'QueueEntry'
        self._label = 'Queue Entry'
        return super().__post_init__()


@dataclass
class QueueMemberAdded(Event, Queue, QueueMemberMixin):
    """Raised in response to the QueueStatus action."""

    def __post_init__(self):
        self._asterisk_name = 'QueueMemberAdded'
        self._label = 'Queue Member Added'
        return super().__post_init__()



@dataclass
class QueueMemberPause(Event, Queue, QueueMemberMixin):
    """Raised when a member is paused/unpaused in the queue."""

    def __post_init__(self):
        self._asterisk_name = 'QueueMemberPause'
        self._label = 'Queue Member Pause'
        return super().__post_init__()


@dataclass
class QueueMemberPenalty(Event, Queue, QueueMemberMixin):
    """Raised when a member's penalty is changed."""

    def __post_init__(self):
        self._asterisk_name = 'QueueMemberPenalty'
        self._label = 'Queue Member Penalty'
        return super().__post_init__()


@dataclass
class QueueMemberRemoved(Event, Queue, QueueMemberMixin):
    """Raised when a member is removed from the queue."""

    def __post_init__(self):
        self._asterisk_name = 'QueueMemberRemoved'
        self._label = 'Queue Member Removed'
        return super().__post_init__()


@dataclass
class QueueMemberRinginuse(Event, Queue, QueueMemberMixin):
    """Raised when a member's ringinuse setting is changed."""

    def __post_init__(self):
        self._asterisk_name = 'QueueMemberRinginuse'
        self._label = 'Queue Member Ringinuse'
        return super().__post_init__()


@dataclass
class QueueMemberStatus(Event, Queue, QueueMixin):
    """Raised when a Queue member's status has changed."""
    MemberName: Optional[str] = None
    Interface: Optional[str] = None
    StateInterface: Optional[str] = None
    Membership: Optional[MembershipOptions] = None
    Penalty: Optional[str] = None
    CallsTaken: Optional[str] = None
    LastCall: Optional[str] = None
    LastPause: Optional[str] = None
    LoginTime: Optional[str] = None
    InCall: Optional[InCallOptions] = None
    Status: Optional[StatusOptions] = None
    Paused: Optional[PausedOptions] = None
    PausedReason: Optional[str] = None
    Ringinuse: Optional[RinginuseOptions] = None
    Wrapuptime: Optional[str] = None

    def __post_init__(self):
        self._asterisk_name = 'QueueMemberStatus'
        self._label = 'Queue Member Status'
        return super().__post_init__()


@dataclass
class QueueParams(Event, Queue):
    """Raised when a Queue member's status has changed."""
    Max: Optional[str] = None
    Strategy: Optional[str] = None
    Calls: Optional[str] = None
    Holdtime: Optional[str] = None
    TalkTime: Optional[str] = None
    Completed: Optional[str] = None
    Abandoned: Optional[str] = None
    ServiceLevelPerf: Optional[str] = None
    ServiceLevelPerf2: Optional[str] = None

    def __post_init__(self):
        self._asterisk_name = 'QueueParams'
        self._label = 'Queue Params'
        return super().__post_init__()

