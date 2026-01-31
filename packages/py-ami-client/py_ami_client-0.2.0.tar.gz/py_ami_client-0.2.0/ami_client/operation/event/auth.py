from dataclasses import dataclass
from typing import Literal, Optional, TypeAlias

from ._base import Event

AuthSeverity: TypeAlias = Literal[
    'Informational', 'Error'
]

class Auth:
    """Marker base for all Auth events"""


@dataclass
class AuthMixin:
    ObjectType: Optional[str] = None
    ObjectName: Optional[str] = None
    Username: Optional[str] = None
    Password: Optional[str] = None
    Md5Cred: Optional[str] = None
    Realm: Optional[str] = None
    NonceLifetime: Optional[str] = None
    AuthType: Optional[str] = None
    OauthClientid: Optional[str] = None
    OauthSecret: Optional[str] = None
    PasswordDigest: Optional[str] = None
    RefreshToken: Optional[str] = None
    SupportedAlgorithmsUac: Optional[str] = None
    SupportedAlgorithmsUas: Optional[str] = None


@dataclass
class AuthDetail(Event, Auth, AuthMixin):
    """Provide details about an authentication section."""
    EndpointName: Optional[str] = None

    def __post_init__(self):
        self._asterisk_name = 'AuthDetail'
        self._label = 'Auth Detail'
        return super().__post_init__()


@dataclass
class AuthList(Event, Auth, AuthMixin):
    """Provide details about an Address of Record (Auth) section."""

    def __post_init__(self):
        self._asterisk_name = 'AuthList'
        self._label = 'Auth List'
        return super().__post_init__()


@dataclass
class AuthListComplete(Event, Auth):
    """Provide final information about an auth list."""
    EventList: Optional[str] = None
    ListItems: Optional[str] = None

    def __post_init__(self):
        self._asterisk_name = 'AuthListComplete'
        self._label = 'Auth List Complete'
        return super().__post_init__()


@dataclass
class AuthMethodNotAllowed(Event, Auth):
    """Raised when a request used an authentication method not allowed by the service."""
    EventTV: Optional[str] = None
    Severity: Optional[AuthSeverity] = None
    Service: Optional[str] = None
    EventVersion: Optional[str] = None
    AccountID: Optional[str] = None
    SessionID: Optional[str] = None
    LocalAddress: Optional[str] = None
    RemoteAddress: Optional[str] = None
    AuthMethod: Optional[str] = None
    Module: Optional[str] = None
    SessionTV: Optional[str] = None

    def __post_init__(self):
        self._asterisk_name = 'AuthMethodNotAllowed'
        self._label = 'Auth Method Not Allowed'
        return super().__post_init__()
