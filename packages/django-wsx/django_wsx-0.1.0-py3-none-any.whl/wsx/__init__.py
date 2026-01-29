# wsx/__init__.py
"""
Public WSX API surface.

Goal:
- Keep imports stable for users (from wsx import X)
- Expose core framework primitives + serializers/permissions/throttles
- Include Redis throttles (django-cache based) + direct-redis option
"""

from __future__ import annotations

# -------------------------
# Core primitives
# -------------------------
from .views import WSView
from .actions import Parent
from .routes import Route

# -------------------------
# Routing / ASGI guard
# -------------------------
from .router import WSXURLRouter, wsx_path
from .middleware import WSXHandshakeAuthMiddleware

# -------------------------
# Request / Response
# -------------------------
from .request import WSRequest
from .response import WSResponse

# -------------------------
# Errors / Exceptions
# -------------------------
from .exceptions import (
    WSXError,
    WSXBadRequest,
    WSXValidationError,
    WSXNotAuthenticated,
    WSXPermissionDenied,
    WSXNotFound,
    WSXThrottled,
    WSXServerError,
)

# -------------------------
# Serializers
# -------------------------
from .serializers import (
    Serializer,
    Field,
    CharField,
    IntField,
    BoolField,
)

# -------------------------
# Permissions
# -------------------------
from .permissions import (
    BasePermission,
    AllowAny,
    IsAuthenticated,
)

# -------------------------
# Throttles (base + in-memory default)
# -------------------------
from .throttles import (
    BaseThrottle,
    ThrottleDecision,
    ThrottleStore,
    MemoryThrottleStore,
    UserActionThrottle,
)

# -------------------------
# Redis throttles (Django cache / django-redis)
# -------------------------
from .redis_throttles import (
    RedisThrottleConfig,
    RedisTokenBucketThrottle,
)

# -------------------------
# Redis throttles (direct redis.asyncio) - optional
# NOTE: Only import if module exists in your package; otherwise delete this block.
# -------------------------


# -------------------------
# Groups + ORM helper
# -------------------------
from .groups import Groups
from .orm import ORM

# -------------------------
# Settings / utils / schema
# -------------------------
from .settings import WSXSettings, DEFAULT_WSX_SETTINGS
from .utils import new_trace_id
from .schema import schema_for_view

__all__ = [
    # core
    "WSView",
    "Parent",
    "Route",

    # routing / guard
    "WSXURLRouter",
    "wsx_path",
    "WSXHandshakeAuthMiddleware",

    # request/response
    "WSRequest",
    "WSResponse",

    # exceptions
    "WSXError",
    "WSXBadRequest",
    "WSXValidationError",
    "WSXNotAuthenticated",
    "WSXPermissionDenied",
    "WSXNotFound",
    "WSXThrottled",
    "WSXServerError",

    # serializers
    "Serializer",
    "Field",
    "CharField",
    "IntField",
    "BoolField",

    # permissions
    "BasePermission",
    "AllowAny",
    "IsAuthenticated",

    # throttles (base + memory)
    "BaseThrottle",
    "ThrottleDecision",
    "ThrottleStore",
    "MemoryThrottleStore",
    "UserActionThrottle",

    # throttles (redis via django cache)
    "RedisThrottleConfig",
    "RedisTokenBucketThrottle",

    # throttles (redis direct, optional)


    # groups / orm
    "Groups",
    "ORM",

    # misc
    "WSXSettings",
    "DEFAULT_WSX_SETTINGS",
    "new_trace_id",
    "schema_for_view",
]