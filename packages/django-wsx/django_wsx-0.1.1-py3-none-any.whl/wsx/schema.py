from __future__ import annotations
from .routes import Route


def _ser_fields(ser):
    if not ser:
        return None
    return list(getattr(ser, "_declared_fields", {}).keys())


def schema_for_view(view_cls):
    routes: dict[str, Route] = view_cls.get_routes()
    out = {"view": view_cls.__name__, "actions": {}}
    for action, r in routes.items():
        out["actions"][action] = {
            "handler": r.handler,
            "allow_unauthenticated": bool(r.allow_unauthenticated),
            "request_fields": _ser_fields(r.request),
            "response_fields": _ser_fields(r.response),
            "response_many": bool(r.response_many),
            "permissions": [p.__name__ for p in (r.permissions or [])],
            "throttles": [t.__name__ for t in (r.throttles or [])],
        }
    return out