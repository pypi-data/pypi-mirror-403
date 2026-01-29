from __future__ import annotations


class BasePermission:
    async def has_permission(self, request) -> bool:
        return True


class AllowAny(BasePermission):
    async def has_permission(self, request) -> bool:
        return True


class IsAuthenticated(BasePermission):
    async def has_permission(self, request) -> bool:
        u = getattr(request, "user", None)
        return bool(u and getattr(u, "is_authenticated", False))