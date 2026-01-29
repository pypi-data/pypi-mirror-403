from __future__ import annotations

from channels.generic.websocket import AsyncJsonWebsocketConsumer

from .routes import Route
from .request import WSRequest
from .exceptions import (
    WSXError, WSXBadRequest, WSXNotFound, WSXNotAuthenticated,
    WSXPermissionDenied, WSXThrottled, WSXServerError
)
from .permissions import AllowAny
from .throttles import UserActionThrottle
from .groups import Groups
from .orm import ORM
from .utils import new_trace_id, must_be_str, must_be_dict


class WSView(AsyncJsonWebsocketConsumer):
    """
    Normal dev-facing class.
    Middleware MUST run before it (it enforces auth, blocks unauth frames).
    """

    # Read by middleware:
    authentication_classes = []
    auth_action = "socket.authorize"
    handshake_action = "socket.handshake"
    authorized_action = "socket.authorized"
    auth_max_attempts = 2
    auth_lock_seconds = 20
    auth_timeout_seconds = 20
    strict_unauth_actions = True
    reject_binary_pre_auth = True

    # DRF-like:
    permission_classes = [AllowAny]
    throttle_classes = [UserActionThrottle]

    _routes_cache: dict[type, dict[str, Route]] = {}

    @classmethod
    def get_routes(cls) -> dict[str, Route]:
        cached = cls._routes_cache.get(cls)
        if cached is not None:
            return cached

        routes: dict[str, Route] = {}
        actions_cls = getattr(cls, "Actions", None)
        if actions_cls:
            for v in actions_cls.__dict__.values():
                if hasattr(v, "collect_routes"):
                    routes.update(v.collect_routes())

        cls._routes_cache[cls] = routes
        return routes

    async def connect(self):
        if not self.scope.get("wsx_authorized"):
            await self.close(code=4401, reason="middleware_required")
            return

        self._routes = self.get_routes()

        # privileged tools exist ONLY after middleware auth
        self.groups = Groups(self)
        self.orm = ORM

        await self.accept()

    async def wsx_group(self, event):
        # group_send type "wsx.group" -> wsx_group
        await self.send_json({"action": event["action"], "data": event.get("data", {})})

    # ---- hooks ----
    def get_permissions(self, route: Route | None):
        perms = (route.permissions if route and route.permissions else self.permission_classes) or []
        return [p() for p in perms]

    def get_throttles(self, route: Route | None):
        th = (route.throttles if route and route.throttles else self.throttle_classes) or []
        return [t() for t in th]

    async def check_permissions(self, request: WSRequest, route: Route | None):
        for perm in self.get_permissions(route):
            ok = await perm.has_permission(request)
            if ok:
                continue
            u = request.user
            if not u or not getattr(u, "is_authenticated", False):
                raise WSXNotAuthenticated("Not authenticated")
            raise WSXPermissionDenied("Permission denied")

    async def check_throttles(self, request: WSRequest, route: Route | None):
        for thr in self.get_throttles(route):
            decision = thr.allow(request, self)
            if not decision.allowed:
                raise WSXThrottled("Throttled", extra={"wait": decision.wait})

    async def receive_json(self, content, **kwargs):
        if not isinstance(content, dict):
            await self._send_error(None, WSXBadRequest("message must be object"))
            return

        req_id = content.get("id")
        action = must_be_str(content.get("action"), "action")
        data = must_be_dict(content.get("data"), "data")
        trace_id = content.get("trace_id") or new_trace_id()

        route = self._routes.get(action)
        if not route:
            await self._send_error(req_id, WSXNotFound(f"Unknown action '{action}'"), trace_id=trace_id)
            return

        request = WSRequest(
            id=req_id,
            action=action,
            data=data,
            scope=self.scope,
            view=self,
            user=self.scope.get("user"),
            auth=self.scope.get("wsx_auth"),
            trace_id=trace_id,
        )

        try:
            # request validation
            if route.request:
                ser = route.request(data=request.data)
                ser.is_valid(raise_exception=True)
                request.data = ser.validated_data

            await self.check_permissions(request, route)
            await self.check_throttles(request, route)

            handler = getattr(self, route.handler, None)
            if not handler:
                raise WSXNotFound(f"Handler '{route.handler}' missing")

            raw = await handler(request)

            # response shaping
            out = raw
            if route.response:
                out = route.response(instance=raw, many=route.response_many).data

            if req_id is not None:
                await self.send_json({"id": req_id, "ok": True, "data": out, "trace_id": trace_id})

        except WSXError as e:
            await self._send_error(req_id, e, trace_id=trace_id)
        except Exception:
            await self._send_error(req_id, WSXServerError("server_error"), trace_id=trace_id)

    async def _send_error(self, req_id, exc: WSXError, trace_id=None):
        payload = {"ok": False, "error": exc.to_payload()}
        if req_id is not None:
            payload["id"] = req_id
        if trace_id is not None:
            payload["trace_id"] = trace_id
        await self.send_json(payload)