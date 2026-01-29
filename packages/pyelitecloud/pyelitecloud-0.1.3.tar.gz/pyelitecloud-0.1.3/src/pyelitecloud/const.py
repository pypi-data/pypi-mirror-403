"""Constants for the EliteCloud library."""
import logging
from datetime import datetime, timezone

_LOGGER: logging.Logger = logging.getLogger(__package__)


AUTH_API_URL = 'https://auth.api.elitecloud.co.nz'
PANEL_API_URL = 'https://panel.api.elitecloud.co.nz'
SERVER_API_URL = 'https://serverutils.api.elitecloud.co.nz'
PANEL_API_WS = 'wss://panel.api.elitecloud.co.nz'

AUTH_DEVICE_NAME = "Android"

ACCESS_TOKEN_EXPIRE_MARGIN = 60 # seconds
DEVICE_TOKEN_EXPIRE_MARGIN = 24*60*60   # 1 day in seconds

# Sync/Async detection
CALL_CONTEXT_SYNC = "SYNC"
CALL_CONTEXT_ASYNC = "ASYNC"

# Global helper functions
utcnow_dt = lambda: datetime.now(timezone.utc)
utcnow_ts = lambda: datetime.now(timezone.utc).timestamp()
