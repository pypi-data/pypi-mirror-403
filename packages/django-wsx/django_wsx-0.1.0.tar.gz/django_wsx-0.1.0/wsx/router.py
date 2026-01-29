from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, List, Optional, Any

from django.urls.resolvers import RoutePattern


@dataclass(frozen=True)
class WSXRoute:
    pattern: Any
    view_class: type
    app: Callable


def wsx_path(route: str, view_class: type, name: Optional[str] = None) -> WSXRoute:
    pattern = RoutePattern(route, is_endpoint=True)
    return WSXRoute(pattern=pattern, view_class=view_class, app=view_class.as_asgi())


class WSXURLRouter:
    """
    Like URLRouter, but:
    - matches path
    - injects scope["wsx_view_class"]
    so middleware can read view_class.Actions routes & auth classes.
    """
    def __init__(self, routes: List[WSXRoute]):
        self.routes = routes

    async def __call__(self, scope, receive, send):
        path = (scope.get("path") or "").lstrip("/")
        for r in self.routes:
            match = r.pattern.match(path)
            if match is None:
                continue

            new_scope = dict(scope)
            new_scope.setdefault("url_route", {})
            new_scope["url_route"]["kwargs"] = match.kwargs
            new_scope["wsx_view_class"] = r.view_class

            return await r.app(new_scope, receive, send)

        await send({"type": "websocket.close", "code": 4404, "reason": "not_found"})