from datetime import datetime
import logging

from dataclasses import dataclass
from enum import Enum, StrEnum

from .const import (
    CALL_CONTEXT_SYNC,
    CALL_CONTEXT_ASYNC,
)

_LOGGER = logging.getLogger(__name__)


class CallContext(StrEnum):
    SYNC = CALL_CONTEXT_SYNC
    ASYNC = CALL_CONTEXT_ASYNC

class LoginMethod(StrEnum):
    ACCESS_TOKEN = 'Access-Token'
    RENEW_TOKEN = 'Renew-Token'
    AUTH_API = 'Auth-Api'


class EliteCloudError(Exception):
    """Exception to indicate generic error failure."""    
    
class EliteCloudConnectError(EliteCloudError):
    """Exception to indicate authentication failure."""

class EliteCloudAuthError(EliteCloudError):
    """Exception to indicate authentication or authorization failure."""

class EliteCloudDataError(EliteCloudError):
    """Exception to indicate generic data failure."""  

class EliteCloudParamError(EliteCloudError):
    """Exception to indicate invalid parameter was passed."""


@dataclass
class EliteCloudSite:
    uuid: str
    name: str
    panel_mac: str
    panel_serial: str

class EliteCloudSites(list[EliteCloudSite]):
    def get_by_uuid(self, uuid: str):
        return next( (s for s in self if s.uuid==uuid), None)

    def get_by_mac(self, mac: str):
        return next( (s for s in self if s.panel_mac==mac), None)
    
    def get_by_serial(self, serial: str):
        return next( (s for s in self if s.panel_serial==serial), None)


