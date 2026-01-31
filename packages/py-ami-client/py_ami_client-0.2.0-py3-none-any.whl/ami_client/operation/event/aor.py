from dataclasses import dataclass
from typing import Optional

from ._base import Event

class AOR:
    """Marker base for all Alarm events"""


@dataclass
class AORMixin:
    ObjectType: Optional[str] = None
    ObjectName: Optional[str] = None
    MinimumExpiration: Optional[str] = None
    MaximumExpiration: Optional[str] = None
    DefaultExpiration: Optional[str] = None
    QualifyFrequency: Optional[str] = None
    AuthenticateQualify: Optional[str] = None
    MaxContacts: Optional[str] = None
    RemoveExisting: Optional[str] = None
    RemoveUnavailable: Optional[str] = None
    Mailboxes: Optional[str] = None
    OutboundProxy: Optional[str] = None
    SupportPath: Optional[str] = None
    Qualify2xxOnly: Optional[str] = None
    QualifyTimeout: Optional[str] = None
    VoicemailExtension: Optional[str] = None
    Contacts: Optional[str] = None


@dataclass
class AorDetail(Event, AOR, AORMixin):
    """Provide details about an Address of Record (AoR) section."""
    TotalContacts: Optional[str] = None
    ContactsRegistered: Optional[str] = None
    EndpointName: Optional[str] = None

    def __post_init__(self):
        self._asterisk_name = 'AorDetail'
        self._label = 'Aor Detail'
        return super().__post_init__()


@dataclass
class AorList(Event, AOR, AORMixin):
    """Provide details about an Address of Record (AoR) section."""
    def __post_init__(self):
        self._asterisk_name = 'AorList'
        self._label = 'Aor List'
        return super().__post_init__()


@dataclass
class AorListComplete(Event, AOR):
    """Provide final information about an aor list."""
    EventList: Optional[str] = None
    ListItems: Optional[str] = None

    def __post_init__(self):
        self._asterisk_name = 'AorListComplete'
        self._label = 'Aor List Complete'
        return super().__post_init__()
