# wsx/middleware.py
from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass
from typing import Any, Optional, Tuple, Type, Dict

from asgiref.sync import sync_to_async
from django.http import HttpRequest
from django.contrib.auth.models import AnonymousUser

from .settings import DEFAULT_WSX_SETTINGS, WSXSettings
from .exceptions import WSXBadRequest
from .utils import safe_json_loads, must_be_str, must_be_dict, new_trace_id


@dataclass(slots=True)
class WSAuthRequest:
    """
    WSX-native auth request object (async-friendly).

    Attributes:
      - scope: ASGI scope
      - token: token from handshake authorize payload (preferred)
    """
    scope: dict
    token: Optional[str] = None


class WSXHandshakeAuthMiddleware:
    """
    Production-grade guard that runs BEFORE your WSView.

    Guarantees:
      ✅ WSView never sees unauth messages unless route.allow_unauthenticated=True
      ✅ Supports BOTH auth styles:
           - WSX-native async auth classes: async authenticate(WSAuthRequest)
           - DRF-compatible sync auth classes: authenticate(HttpRequest) (via sync_to_async)
      ✅ Attempts/lock/timeout enforcement
      ✅ Strict pre-auth policy: reject/close (default) or ignore forbidden actions
      ✅ Injects:
           - scope["user"]
           - scope["wsx_auth"]
           - scope["wsx_authorized"]=True

    Handshake modes:
      - "required": MUST authorize via socket.authorize
      - "optional": can authorize via socket.authorize OR scope auth (header/query/session)
      - "disabled": NO handshake protocol; authenticate from scope (optional) and start view immediately

    Special rule (your request):
      If a DRF auth class has `handshake_compatible = True`:
        - It is ONLY considered during the handshake authorize flow.
        - It ALWAYS receives the handshake token (forced into Authorization header),
          regardless of whatever headers/query/session exist.
    """

    def __init__(self, app, *, settings: WSXSettings = DEFAULT_WSX_SETTINGS):
        self.app = app
        self.settings = settings

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "websocket":
            return await self.app(scope, receive, send)

        view_class = scope.get("wsx_view_class")
        if view_class is None:
            await send({"type": "websocket.close", "code": 4404, "reason": "wsx_route_missing"})
            return

        s = self.settings

        # ---- policy from WSView (optional overrides) ----
        auth_action = getattr(view_class, "auth_action", s.auth_action)
        handshake_action = getattr(view_class, "handshake_action", s.handshake_action)
        authorized_action = getattr(view_class, "authorized_action", s.authorized_action)

        max_attempts = int(getattr(view_class, "auth_max_attempts", s.auth_max_attempts))
        lock_seconds = int(getattr(view_class, "auth_lock_seconds", s.auth_lock_seconds))
        timeout_seconds = int(getattr(view_class, "auth_timeout_seconds", s.auth_timeout_seconds))

        strict_unauth = bool(getattr(view_class, "strict_unauth_actions", s.strict_unauth_actions))
        reject_binary_pre_auth = bool(getattr(view_class, "reject_binary_pre_auth", s.reject_binary_pre_auth))

        # NEW: handshake mode + auto authorize
        handshake_mode = getattr(view_class, "handshake_mode", getattr(s, "handshake_mode", "required"))
        if handshake_mode not in ("required", "optional", "disabled"):
            handshake_mode = "required"

        auto_authorize_from_scope = bool(
            getattr(view_class, "auto_authorize_from_scope", getattr(s, "auto_authorize_from_scope", False))
        )

        # Optional: query token key (used in scope auth)
        query_token_key = getattr(view_class, "query_token_key", getattr(s, "query_token_key", "token"))

        auth_classes = list(getattr(view_class, "authentication_classes", []) or [])

        # ---- read allow_unauth from Actions routes (YOUR RULE) ----
        routes: Dict[str, Any] = {}
        if hasattr(view_class, "get_routes"):
            routes = view_class.get_routes() or {}
        allow_unauth_actions = {a for a, r in routes.items() if getattr(r, "allow_unauthenticated", False)}

        # ---- per-connection state ----
        authorized = False
        attempts = 0
        locked_until = 0.0
        deadline = time.time() + timeout_seconds

        scope["user"] = scope.get("user") or AnonymousUser()
        scope["wsx_authorized"] = False
        scope["wsx_auth"] = None

        # Inner app started ONLY after auth (except explicit allow_unauth actions)
        inner_task: Optional[asyncio.Task] = None
        inner_q: asyncio.Queue = asyncio.Queue()

        async def inner_receive():
            return await inner_q.get()

        async def start_inner_once():
            nonlocal inner_task
            if inner_task is None:
                inner_task = asyncio.create_task(self.app(scope, inner_receive, send))

        async def ws_send_obj(obj: dict):
            await send({"type": "websocket.send", "text": json.dumps(obj)})

        async def ws_close(code: int, reason: str):
            await send({"type": "websocket.close", "code": code, "reason": reason})

        async def send_handshake():
            await ws_send_obj({
                s.key_action: handshake_action,
                s.key_data: {
                    "authorize": auth_action,
                    "attempts": max_attempts,
                    "lock_seconds": lock_seconds,
                    "timeout_seconds": timeout_seconds,
                    "allow_unauth": sorted(allow_unauth_actions),
                    "mode": handshake_mode,
                },
                s.key_trace_id: new_trace_id(),
            })

        # ----------------------------
        # Token sources from ASGI scope
        # ----------------------------
        def _scope_headers() -> dict:
            # {b'header-name': b'value'}
            return dict(scope.get("headers", []) or [])

        def token_from_scope_header() -> Optional[str]:
            headers = _scope_headers()
            raw = headers.get(b"authorization")
            if not raw:
                return None
            val = raw.decode("utf-8", errors="ignore").strip()
            if val.lower().startswith("bearer "):
                return val[7:].strip()
            return None

        def token_from_scope_query() -> Optional[str]:
            from urllib.parse import parse_qs
            raw = scope.get("query_string", b"") or b""
            if not raw:
                return None
            qs = parse_qs(raw.decode("utf-8", errors="ignore"))
            return (qs.get(query_token_key) or [None])[0]

        def any_token_from_scope() -> Optional[str]:
            return token_from_scope_header() or token_from_scope_query()

        # -----------------------------------------
        # Auth class typing + handshake forcing rules
        # -----------------------------------------
        def _is_drf_auth_class(cls: Type) -> bool:
            # DRF-style: sync authenticate(HttpRequest)
            fn = getattr(cls, "authenticate", None)
            return callable(fn) and not asyncio.iscoroutinefunction(fn)

        def _handshake_forced(cls: Type) -> bool:
            # Your rule: if True, this class MUST use handshake token and is handshake-only
            return bool(getattr(cls, "handshake_compatible", False))

        def _apply_auth(user_auth: Tuple[Any, Any]):
            user, auth = user_auth
            scope["user"] = user
            scope["wsx_auth"] = auth
            scope["wsx_authorized"] = True

        # ------------------------------------------------------------
        # Unified authentication (WSX-native async + DRF-compatible sync)
        # with your `handshake_compatible=True` forcing.
        # ------------------------------------------------------------
        async def authenticate_any(
            token: Optional[str],
            *,
            source: str,  # "handshake" | "scope"
        ) -> Optional[Tuple[Any, Any]]:
            """
            Returns:
              - (user, auth) on success
              - None if not applicable (no creds / no class accepted)

            Rules:
              - WSX-native async auth classes always get WSAuthRequest(scope, token)
              - DRF auth classes get a synthetic HttpRequest
              - If DRF class has handshake_compatible=True:
                  * It is ONLY considered when source == "handshake"
                  * It ALWAYS sees the handshake token forced into Authorization header
                  * It is NOT allowed to authenticate from scope headers/query/session
            """
            if not auth_classes:
                if token:
                    raise PermissionError("No authentication_classes configured")
                return None

            ws_req = WSAuthRequest(scope=scope, token=token)

            headers = _scope_headers()

            # Build "base" META from ASGI headers (excluding Authorization),
            # then we set Authorization intentionally per-class.
            base_meta: dict[str, str] = {}
            for k, v in headers.items():
                key = k.decode("latin-1", errors="ignore").upper().replace("-", "_")
                if key == "AUTHORIZATION":
                    continue
                base_meta["HTTP_" + key] = v.decode("latin-1", errors="ignore")

            # Helper: make HttpRequest with desired Authorization behavior
            def _make_http_request(*, authz_value: Optional[str]) -> HttpRequest:
                req = HttpRequest()
                req.method = "GET"
                req.path = scope.get("path", "/")
                req.META = dict(base_meta)
                if authz_value:
                    req.META["HTTP_AUTHORIZATION"] = authz_value
                return req

            last_err: Optional[Exception] = None

            for cls in auth_classes:
                inst = cls()

                try:
                    # -------------------------
                    # WSX-native async auth
                    # -------------------------
                    if hasattr(inst, "authenticate") and asyncio.iscoroutinefunction(inst.authenticate):
                        # WSX-native classes can decide token sources however they want,
                        # but we still pass handshake token in ws_req.token when present.
                        res = await inst.authenticate(ws_req)
                        if res is not None:
                            return res
                        continue

                    # -------------------------
                    # DRF-compatible sync auth
                    # -------------------------
                    if _is_drf_auth_class(cls):
                        forced = _handshake_forced(cls)

                        # Handshake-forced DRF class:
                        # - skip if we're not in handshake
                        if forced and source != "handshake":
                            continue

                        # Build Authorization header value for this class
                        if forced:
                            # MUST use handshake token, regardless of any scope headers/query
                            if not token:
                                # handshake-forced but no token => can't auth
                                continue
                            req = _make_http_request(authz_value=f"Bearer {token}")
                        else:
                            # Non-forced DRF class:
                            # - if token param provided (handshake or scope), use it
                            # - otherwise allow scope Authorization header to be seen
                            if token:
                                req = _make_http_request(authz_value=f"Bearer {token}")
                            else:
                                raw = headers.get(b"authorization")
                                authz = raw.decode("latin-1", errors="ignore") if raw else None
                                req = _make_http_request(authz_value=authz)

                        res = await sync_to_async(inst.authenticate)(req)
                        if res is not None:
                            return res

                        continue

                except Exception as e:
                    last_err = e
                    # In handshake flow, invalid token should be a hard failure
                    if source == "handshake" and token:
                        raise PermissionError("Invalid token") from e
                    # In scope flow, let other auth classes try
                    continue

            # If we explicitly provided a handshake token and nothing accepted it -> invalid
            if source == "handshake" and token:
                raise PermissionError("Invalid token") from last_err

            return None

        # ---------------------------------------------------
        # Scope authentication (classic): session/header/query
        # ---------------------------------------------------
        async def try_scope_auth() -> Optional[Tuple[Any, Any]]:
            # If Channels auth middleware already populated scope["user"], accept it.
            u = scope.get("user")
            if u is not None and getattr(u, "is_authenticated", False):
                return (u, "session")

            token = any_token_from_scope()
            if not token:
                return None

            return await authenticate_any(token, source="scope")

        # ============================================
        # MODE: disabled (no handshake protocol at all)
        # ============================================
        if handshake_mode == "disabled":
            # Accept connection and start inner immediately, optionally populating user/auth from scope.
            # Dev is choosing "classic" behavior.
            while True:
                event = await receive()

                if event["type"] == "websocket.connect":
                    await send({"type": "websocket.accept"})
                    try:
                        res = await try_scope_auth()
                    except Exception:
                        res = None
                    if res is not None:
                        authorized = True
                        _apply_auth(res)
                    await start_inner_once()
                    continue

                if event["type"] == "websocket.disconnect":
                    if inner_task is not None:
                        await inner_q.put(event)
                    return

                if event["type"] == "websocket.receive":
                    await start_inner_once()
                    await inner_q.put(event)
                    continue

                # ignore other frames

        # ==================================================
        # MODE: required / optional (handshake protocol active)
        # ==================================================
        while True:
            event = await receive()

            if event["type"] == "websocket.connect":
                await send({"type": "websocket.accept"})
                await send_handshake()

                # OPTIONAL: auto-authorize from scope at connect (still handshake phase)
                if handshake_mode == "optional" and auto_authorize_from_scope and not authorized:
                    try:
                        res = await try_scope_auth()
                    except Exception:
                        res = None

                    if res is not None:
                        authorized = True
                        _apply_auth(res)
                        await ws_send_obj({
                            s.key_action: authorized_action,
                            s.key_data: {"authenticated": True, "via": "scope"},
                            s.key_trace_id: new_trace_id(),
                        })
                        await start_inner_once()

                continue

            if event["type"] == "websocket.disconnect":
                if inner_task is not None:
                    await inner_q.put(event)
                return

            if event["type"] != "websocket.receive":
                continue

            # Pre-auth timeout/lock enforcement
            if not authorized:
                now = time.time()
                if now > deadline:
                    await ws_close(4401, "auth_timeout")
                    return
                if locked_until and now < locked_until:
                    await ws_close(4408, "auth_locked")
                    return

            # Binary handling
            if event.get("bytes") is not None:
                if not authorized and reject_binary_pre_auth:
                    await ws_close(4400, "binary_not_allowed_pre_auth")
                    return
                await start_inner_once()
                await inner_q.put(event)
                continue

            text = event.get("text")
            if not isinstance(text, str) or not text:
                await ws_close(4400, "bad_frame")
                return

            try:
                msg = safe_json_loads(text)
            except WSXBadRequest:
                await ws_close(4400, "bad_json")
                return

            action = must_be_str(msg.get(s.key_action), s.key_action)
            data = must_be_dict(msg.get(s.key_data), s.key_data)
            trace_id = msg.get(s.key_trace_id) or new_trace_id()

            # -----------------------
            # PRE-AUTH enforcement
            # -----------------------
            if not authorized:
                # Allow explicit unauth actions declared in Actions routes
                if action in allow_unauth_actions:
                    await start_inner_once()
                    await inner_q.put({"type": "websocket.receive", "text": text})
                    continue

                # OPTIONAL mode fallback: if dev doesn't want to send socket.authorize,
                # allow "classic" scope auth to kick in on first message.
                # NOTE: handshake_forced DRF auth classes are skipped in scope auth by design.
                if handshake_mode == "optional" and not auto_authorize_from_scope:
                    try:
                        res = await try_scope_auth()
                    except Exception:
                        res = None
                    if res is not None:
                        authorized = True
                        _apply_auth(res)
                        await ws_send_obj({
                            s.key_action: authorized_action,
                            s.key_data: {"authenticated": True, "via": "scope"},
                            s.key_trace_id: trace_id,
                        })
                        await start_inner_once()
                        # Do NOT replay the triggering message (avoid duplicates)
                        continue

                # Only allow auth_action (socket.authorize) in pre-auth
                if action != auth_action:
                    if strict_unauth:
                        await ws_close(4401, "unauthorized_action")
                        return
                    # ignore
                    continue

                # Authorize flow
                token = data.get("token")
                if not isinstance(token, str) or not token:
                    attempts += 1
                    if attempts >= max_attempts:
                        locked_until = time.time() + lock_seconds
                        await ws_close(4408, "auth_locked")
                        return
                    await ws_close(4401, "missing_token")
                    return

                try:
                    user_auth = await authenticate_any(token, source="handshake")
                    if user_auth is None:
                        raise PermissionError("Invalid token")
                except Exception:
                    attempts += 1
                    if attempts >= max_attempts:
                        locked_until = time.time() + lock_seconds
                        await ws_close(4408, "auth_locked")
                        return
                    await ws_close(4401, "auth_failed")
                    return

                # Success: inject into scope and start inner app
                authorized = True
                _apply_auth(user_auth)

                await ws_send_obj({
                    s.key_action: authorized_action,
                    s.key_data: {"authenticated": True, "via": "authorize"},
                    s.key_trace_id: trace_id,
                })

                await start_inner_once()
                continue

            # -----------------------
            # POST-AUTH passthrough
            # -----------------------
            await start_inner_once()
            await inner_q.put(event)