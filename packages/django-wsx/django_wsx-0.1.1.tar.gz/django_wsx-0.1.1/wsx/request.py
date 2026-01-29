from __future__ import annotations
from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class WSRequest:
    id: Any
    action: str
    data: dict
    scope: dict
    view: Any
    user: Any = None
    auth: Any = None
    trace_id: str | None = None

    @property
    def kwargs(self) -> dict:
        return self.scope.get("url_route", {}).get("kwargs", {})