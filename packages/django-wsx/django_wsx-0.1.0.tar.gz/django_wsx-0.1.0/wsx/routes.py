from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Optional, Type

from .serializers import Serializer
from .permissions import BasePermission
from .throttles import BaseThrottle


@dataclass(frozen=True, slots=True)
class Route:
    handler: str

    request: Optional[Type[Serializer]] = None
    response: Optional[Type[Serializer]] = None
    response_many: bool = False

    permissions: Optional[list[type[BasePermission]]] = None
    throttles: Optional[list[type[BaseThrottle]]] = None
    queryset: Optional[Callable] = None

    # ✅ YOU DEMANDED: unauth policy declared HERE (Actions routes)
    allow_unauthenticated: bool = False