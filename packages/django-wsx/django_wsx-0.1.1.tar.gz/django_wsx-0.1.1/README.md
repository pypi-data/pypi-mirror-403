# django-wsx (WSX)
## DRF-style WebSockets for Django & Channels

WSX brings **Django REST Framework semantics to WebSockets**.

No giant `receive()` methods.  
No accidental unauthenticated handlers.  
No ad-hoc authentication hacks.

> **One sentence**  
> **WSX is DRF for WebSockets — actions, serializers, permissions, throttles, and middleware-first authentication.**

---

## Why WSX exists

Django Channels is powerful but intentionally low-level. In real projects, teams repeatedly rebuild:

- Message routing by `"action"`
- Authentication that doesn’t leak handlers
- Permission checks
- Throttling / rate limits
- Serializer-based validation
- Consistent request/response envelopes

WSX provides these as **first-class primitives**, using patterns Django developers already understand from DRF.

---

## Core guarantees (Security model)

WSX is designed to **fail closed by default**.

### Middleware-first authentication

When using `WSXHandshakeAuthMiddleware`:

- Authentication happens **before** your `WSView` runs
- Unauthorized messages **never reach user code**
- Unauthenticated actions must be explicitly allowed
- DRF authentication classes work unchanged

This avoids the most common WebSocket mistake:
> “The connection was already processing messages before auth finished.”

---

### Explicit unauthenticated routes only

Nothing is public unless you explicitly declare it:

```python
public.ping = Route("ping", allow_unauthenticated=True)
```

All other actions require authentication.

---

### What WSX does NOT promise

WSX does **not** claim:

- Binary messages are secure by default
- Origin checks are authentication
- WebSockets replace authorization logic

You still need:
- TLS (`wss://`)
- Strong authentication (JWT)
- Server-side permissions
- Rate limiting

WSX enforces boundaries — it does not replace security fundamentals.

---

## Installation

```bash
pip install django-wsx
```

Recommended production extras (Redis throttles, multi-instance):

```bash
pip install django-wsx[redis]
```

---

## Requirements

- Python ≥ 3.10
- Django ≥ 4.2
- channels ≥ 4.0

Production deployments should also use:
- channels-redis
- redis / django-redis

---

## Core concepts

### WSView
Equivalent to a DRF `APIView` / `ViewSet`, but for WebSockets.

### Actions
Named WebSocket endpoints identified by `"action"` strings.

### Route
Defines:
- handler method
- request serializer
- response serializer
- permissions
- throttles
- unauth policy

### Middleware guard
Runs **before** the view is instantiated.

---

## Quickstart

### Define a WebSocket view

```python
from wsx import WSView, Parent, Route
from wsx.permissions import IsAuthenticated
from wsx.serializers import Serializer, CharField
from .auth import HybridJWTAuthentication

class SendIn(Serializer):
    text = CharField(max_length=4000)

class SendOut(Serializer):
    user = CharField()
    text = CharField()

class ChatWS(WSView):
    authentication_classes = [HybridJWTAuthentication]

    class Actions:
        public = Parent("public")
        chat = Parent("chat")

        public.ping = Route(
            "ping",
            allow_unauthenticated=True,
        )

        chat.send = Route(
            "send_message",
            request=SendIn,
            response=SendOut,
            permissions=[IsAuthenticated],
        )

    async def ping(self, request):
        return {"pong": True}

    async def send_message(self, request):
        return {
            "user": request.user.username,
            "text": request.data["text"],
        }
```

---

## WebSocket routing

```python
from wsx import wsx_path
from .ws import ChatWS

websocket_urlpatterns = [
    wsx_path("ws/chat/<slug:room>/", ChatWS),
]
```

---

## ASGI wiring

```python
from channels.routing import ProtocolTypeRouter
from channels.security.websocket import OriginValidator

from wsx import WSXHandshakeAuthMiddleware, WSXURLRouter
import chat.routing

application = ProtocolTypeRouter({
    "websocket": OriginValidator(
        WSXHandshakeAuthMiddleware(
            WSXURLRouter(chat.routing.websocket_urlpatterns)
        ),
        ["http://localhost:3000"],
    ),
})
```

---

## Handshake protocol

WSX uses a **secondary handshake** for authentication.

### Server → client

```json
{
  "action": "socket.handshake",
  "data": {
    "authorize": "socket.authorize",
    "attempts": 2,
    "lock_seconds": 20,
    "timeout_seconds": 20,
    "allow_unauth": ["public.ping"]
  }
}
```

### Client → server

```json
{
  "id": "auth1",
  "action": "socket.authorize",
  "data": {
    "token": "JWT_TOKEN"
  }
}
```

### Server → client

```json
{
  "action": "socket.authorized",
  "data": {
    "authenticated": true
  }
}
```

Only after this does the `WSView` start.

---

## Message format

### Request

```json
{
  "id": "req_1",
  "action": "chat.send",
  "data": {
    "text": "hello"
  },
  "trace_id": "abc123"
}
```

### Success response

```json
{
  "id": "req_1",
  "ok": true,
  "data": {
    "user": "alice",
    "text": "hello"
  },
  "trace_id": "abc123"
}
```

### Error response

```json
{
  "id": "req_1",
  "ok": false,
  "error": {
    "code": "validation_error",
    "detail": "Error",
    "fields": {
      "text": ["Max length exceeded"]
    }
  },
  "trace_id": "abc123"
}
```

---

## Authentication

### DRF authentication classes

Any DRF auth class works if it implements:

```python
authenticate(HttpRequest) -> (user, auth) | None
```

#### Handshake-only authentication

If a DRF auth class defines:

```python
handshake_compatible = True
```

Then:
- It is **only used during the handshake**
- It always receives the handshake token
- It cannot authenticate via headers, query params, or sessions
- Handshake bypass is impossible

This is enforced by middleware.

---

## Permissions

Permissions work like DRF:

```python
from wsx.permissions import BasePermission

class IsRoomMember(BasePermission):
    async def has_permission(self, request) -> bool:
        return True
```

Attach to a route:

```python
chat.send = Route(
    "send_message",
    permissions=[IsAuthenticated, IsRoomMember]
)
```

---

## Throttling

### In-memory throttle (development)

```python
from wsx.throttles import UserActionThrottle
```

### Redis token bucket throttle (production)

```python
from wsx.throttles_redis import RedisTokenBucketThrottle, RedisThrottleConfig

class ChatSendThrottle(RedisTokenBucketThrottle):
    rate = "30/min"
    config = RedisThrottleConfig(cache_alias="throttle")
```

Attach to a route:

```python
chat.send = Route(
    "send_message",
    throttles=[ChatSendThrottle]
)
```

---

## Redis configuration

### Channels Redis

```python
CHANNEL_LAYERS = {
  "default": {
    "BACKEND": "channels_redis.core.RedisChannelLayer",
    "CONFIG": {"hosts": [("127.0.0.1", 6379)]},
  }
}
```

### Django cache (throttles)

```python
CACHES = {
  "default": {
    "BACKEND": "django_redis.cache.RedisCache",
    "LOCATION": "redis://127.0.0.1:6379/1",
  },
  "throttle": {
    "BACKEND": "django_redis.cache.RedisCache",
    "LOCATION": "redis://127.0.0.1:6379/2",
  },
}
```

---

## Groups / broadcasting

```python
await self.groups.join("room:general")
await self.groups.broadcast(
    "room:general",
    action="chat.message",
    data={"text": "hello"}
)
```

---

## ORM helper

WSX provides a small async ORM helper:

```python
room = await self.orm(ChatRoom).filter(slug=slug).first()
messages = await self.orm(ChatMessage).filter(room=room).limit(20).all()
```

---

## Production checklist

- Use TLS (`wss://`)
- Use OriginValidator
- Use Redis channel layer
- Use Redis throttles
- Enforce connection limits (nginx / Cloudflare)
- Log `trace_id` for debugging
- Keep unauth routes minimal

---

## FAQ

### Why not raw Channels consumers?
You can. WSX is for teams that want structure, safety, and consistency.

### Is WSX secure?
WSX enforces boundaries. Security still depends on correct auth, TLS, and permissions.

### Can Postman connect?
Yes — with a valid token. Origin checks reduce casual abuse but are not authentication.

---

## License

MIT

---

## Status

Early but production-minded.  
API stability guaranteed after `1.0`.

**This project prioritizes correctness over convenience.**