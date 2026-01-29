import logging

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .const import (
    utcnow_ts,
    utcnow_dt,
)

_LOGGER = logging.getLogger(__name__)


@dataclass
class EliteCloudHistoryItem:
    dt: datetime
    op: str
    rsp: str|None = None
 
    @staticmethod
    def create(dt: datetime, context: str , request: dict|None, response: dict|None, token: dict|None) -> 'EliteCloudHistoryItem':
        item = EliteCloudHistoryItem( 
            dt = dt, 
            op = context,
        )

        # If possible, add a summary of the response status and json res and code
        if response:
            rsp_parts = []
            if "status_code" in response:
                rsp_parts.append(response["status_code"])
            if "status" in response:
                rsp_parts.append(response["status"])
            
            item.rsp = ', '.join(rsp_parts)

        return item


@dataclass
class EliteCloudHistoryDetail:
    dt: datetime
    req: dict|None
    rsp: dict|None
    token: dict|None

    @staticmethod
    def create(dt: datetime, context: str , request: dict|None, response: dict|None, token: dict|None) -> 'EliteCloudHistoryDetail':
        detail = EliteCloudHistoryDetail(
            dt = dt, 
            req = request,
            rsp = response,
            token = token,
        )
        return detail


class EliteCloudDictFactory:
    @staticmethod
    def exclude_none_values(x):
        """
        Usage:
          item = EliteCloudHistoryItem(...)
          item_as_dict = asdict(item, dict_factory=EliteCloudDictFactory.exclude_none_values)
        """
        return { k: v for (k, v) in x if v is not None }


class EliteCloudDiagnostics:
    """Elite Cloud API"""

    def __init__(self, enabled: bool):
        """Initialize the class"""

        self._enabled: bool = enabled

        self._history: list[EliteCloudHistoryItem] = list()
        self._details: dict[str, EliteCloudHistoryDetail] = dict()
        self._durations: dict[int, int] = { n: 0 for n in range(10) }
        self._methods: dict[str, int] = dict()
        self._counters: dict[str, int] = dict()


    def add(self, dt: datetime, context: str, request: dict|None, response: dict|None, token: dict|None = None):
        """Gather diagnostics"""

        if not self._enabled:
            return

        method = request.get("method", None) if request is not None else response.get("method", None) if response is not None else None
        method = method.replace("GET", "HttpGet").replace("POST", "HttpPost") if method is not None else None

        duration = response.get("elapsed", None) if response is not None else None
        duration = round(duration, 0) if duration is not None else None
        
        history_item = EliteCloudHistoryItem.create(dt, context, request, response, token)
        history_detail = EliteCloudHistoryDetail.create(dt, context, request, response, token)

        # Call durations
        if duration is not None:
            if duration in self._durations:
                self._durations[duration] += 1
            else:
                self._durations[duration] = 1

        # Call method
        if method is not None:
            if method in self._methods:
                self._methods[method] += 1
            else:
                self._methods[method] = 1

        # Call counters
        if context in self._counters:
            self._counters[context] += 1
        else:
            self._counters[context] = 1

        # Call history        
        self._history.append(history_item)
        while len(self._history) > 64:
            self._history.pop(0)

        # Call details
        self._details[context] = history_detail


    def create(self, api_data) -> dict[str, Any]:
        """Return the gathered diagnostics"""

        calls_total = sum([ n for key, n in self._counters.items() ]) or 1
        calls_counter = { key: n for key, n in self._counters.items() }
        calls_percent = { key: round(100.0 * n / calls_total, 2) for key, n in calls_counter.items() }

        durations_total = sum(self._durations.values()) or 1
        durations_counter = dict(sorted(self._durations.items()))
        durations_percent = { key: round(100.0 * n / durations_total, 2) for key, n in durations_counter.items() }

        methods_total = sum(self._methods.values()) or 1
        methods_counter = dict(sorted(self._methods.items()))
        methods_percent = { key: round(100.0 * n / methods_total, 2) for key, n in methods_counter.items() }
        
        return {
            "data": api_data,
            "diagnostics": {
                "dt": utcnow_dt(),
                "durations": {
                    "counter": durations_counter,
                    "percent": durations_percent,
                },
                "methods": {
                    "counter": methods_counter,
                    "percent": methods_percent,
                },
                "calls": {
                    "counter": calls_counter,
                    "percent": calls_percent,
                },
            },
            "history": self._history,
            "details": self._details,
        }
