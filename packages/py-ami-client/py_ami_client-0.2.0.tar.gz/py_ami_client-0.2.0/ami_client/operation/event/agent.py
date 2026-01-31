from dataclasses import dataclass
from typing import Optional, TypeAlias, Literal

from ._base import Event, ChannelEventMixin, DestChannelEventMixin

ResonOptions: TypeAlias = Literal[
    'caller', 'agent', 'transfer',
]
StatusOptions: TypeAlias = Literal[
    'AGENT_LOGGEDOFF', 'AGENT_IDLE', 'AGENT_ONCALL',
]


class Agent:
    """Marker base for all Agent events"""

@dataclass
class AgentMixin:
    Queue: Optional[str] = None
    MemberName: Optional[str] = None
    Interface: Optional[str] = None


@dataclass
class AgentCalled(Event, Agent, ChannelEventMixin, DestChannelEventMixin, AgentMixin):
    """Raised when an queue member is notified of a caller in the queue."""
    def __post_init__(self):
        self._asterisk_name = 'AgentCalled'
        self._label = 'Agent Called'
        return super().__post_init__()


@dataclass
class AgentComplete(Event, Agent, ChannelEventMixin, DestChannelEventMixin, AgentMixin):
    """Raised when a queue member has finished servicing a caller in the queue."""
    HoldTime: Optional[str] = None
    TalkTime: Optional[str] = None
    Reason: Optional[ResonOptions] = None

    def __post_init__(self):
        self._asterisk_name = 'AgentComplete'
        self._label = 'Agent Complete'
        return super().__post_init__()

@dataclass
class AgentConnect(Event, Agent, ChannelEventMixin, DestChannelEventMixin, AgentMixin):
    """Raised when a queue member answers and is bridged to a caller in the queue."""
    RingTime: Optional[str] = None
    HoldTime: Optional[str] = None

    def __post_init__(self):
        self._asterisk_name = 'AgentConnect'
        self._label = 'Agent Connect'
        return super().__post_init__()

@dataclass
class AgentDump(Event, Agent, ChannelEventMixin, DestChannelEventMixin, AgentMixin):
    """Raised when a queue member hangs up on a caller in the queue."""
    def __post_init__(self):
        self._asterisk_name = 'AgentDump'
        self._label = 'Agent Dump'
        return super().__post_init__()


@dataclass
class AgentLogin(Event, Agent, ChannelEventMixin):
    """Raised when an Agent has logged in."""
    Agent: Optional[str] = None

    def __post_init__(self):
        self._asterisk_name = 'AgentLogin'
        self._label = 'Agent Login'
        return super().__post_init__()


@dataclass
class AgentLogoff(Event, Agent, ChannelEventMixin):
    """Raised when an Agent has logged off."""
    Agent: Optional[str] = None
    Logintime: Optional[str] = None

    def __post_init__(self):
        self._asterisk_name = 'AgentLogoff'
        self._label = 'Agent Logoff'
        return super().__post_init__()


@dataclass
class AgentRingNoAnswer(Event, Agent, ChannelEventMixin, DestChannelEventMixin, AgentMixin):
    """Raised when a queue member is notified of a caller in the queue and fails to answer."""
    RingTime: Optional[str] = None

    def __post_init__(self):
        self._asterisk_name = 'AgentRingNoAnswer'
        self._label = 'Agent Ring No Answer'
        return super().__post_init__()


@dataclass
class Agents(Event, Agent, ChannelEventMixin):
    """Response event in a series to the Agents AMI action containing information about a defined agent."""
    Agent: Optional[str] = None
    Name: Optional[str] = None
    Status: Optional[StatusOptions] = None
    TalkingToChan: Optional[str] = None
    CallStarted: Optional[str] = None
    LoggedInTime: Optional[str] = None

    def __post_init__(self):
        self._asterisk_name = 'AgentRingNoAnswer'
        self._label = 'Agent Ring No Answer'
        return super().__post_init__()


@dataclass
class AgentsComplete(Event, Agent):
    """Final response event in a series of events to the Agents AMI action."""
    ActionID: Optional[int] = None

    def __post_init__(self):
        self._asterisk_name = 'Agents Complete'
        self._label = 'Agents Complete'
        return super().__post_init__()

