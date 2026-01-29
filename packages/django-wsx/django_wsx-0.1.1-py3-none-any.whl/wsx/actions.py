from __future__ import annotations
from typing import Dict

from .routes import Route


class Parent:
    """
    Allows:
      class Actions:
          public = Parent("public")
          public.ping = Route(...)
    """

    def __init__(self, prefix: str):
        object.__setattr__(self, "prefix", prefix)
        object.__setattr__(self, "_routes", {})  # type: ignore

    def __setattr__(self, name: str, value):
        if name in {"prefix", "_routes"}:
            return object.__setattr__(self, name, value)

        if not isinstance(value, Route):
            raise TypeError("Only Route(...) can be assigned inside Actions namespaces.")

        action = f"{self.prefix}.{name}"
        self._routes[action] = value  # type: ignore

    def collect_routes(self) -> Dict[str, Route]:
        return dict(self._routes)  # type: ignore