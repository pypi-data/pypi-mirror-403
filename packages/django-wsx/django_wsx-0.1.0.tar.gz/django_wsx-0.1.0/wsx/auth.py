from urllib.parse import parse_qs
from .exceptions import WSXNotAuthenticated

class BaseAuthentication:
    async def authenticate(self, request):
        return None

class SessionAuthentication(BaseAuthentication):
    async def authenticate(self, request):
        user = request.scope.get("user")
        if user and getattr(user, "is_authenticated", False):
            return (user, "session")
        return None

class QueryTokenAuthentication(BaseAuthentication):
    query_key = "token"
    async def get_user_from_token(self, token: str):
        return None
    async def authenticate(self, request):
        raw = request.scope.get("query_string", b"") or b""
        qs = parse_qs(raw.decode("utf-8")) if raw else {}
        token = (qs.get(self.query_key) or [None])[0]
        if not token:
            return None
        user = await self.get_user_from_token(token)
        if not user:
            raise WSXNotAuthenticated("Invalid token")
        return (user, token)

class HeaderTokenAuthentication(BaseAuthentication):
    header_name = b"authorization"
    prefix = "bearer "
    async def get_user_from_token(self, token: str):
        return None
    async def authenticate(self, request):
        headers = dict(request.scope.get("headers", []) or [])
        raw = headers.get(self.header_name)
        if not raw:
            return None
        val = raw.decode("utf-8").strip()
        if not val.lower().startswith(self.prefix):
            return None
        token = val[len(self.prefix):].strip()
        user = await self.get_user_from_token(token)
        if not user:
            raise WSXNotAuthenticated("Invalid token")
        return (user, token)

class SimpleJWTAuthentication(BaseAuthentication):
    """
    Production JWT auth for Django REST Framework SimpleJWT.

    Accepts:
      - Authorization: Bearer <jwt>
      - OR ?token=<jwt> query param (optional)

    Requires: rest_framework_simplejwt installed.
    """
    header_name = b"authorization"
    prefix = "bearer "
    query_key = "token"

    async def authenticate(self, request):
        token = self._from_header(request) or self._from_query(request)
        if not token:
            return None

        try:
            from rest_framework_simplejwt.authentication import JWTAuthentication
        except Exception:
            raise WSXNotAuthenticated("SimpleJWT not installed")

        # JWTAuthentication is sync; safe to call because it doesn't hit DB except user fetch
        # but user fetch can be DB. We'll do minimal sync_to_async around it.
        from asgiref.sync import sync_to_async

        jwt_auth = JWTAuthentication()

        @sync_to_async
        def _do():
            # Fake DRF request object not needed; JWTAuthentication expects django HttpRequest normally.
            # We'll manually validate and get user.
            validated = jwt_auth.get_validated_token(token)
            user = jwt_auth.get_user(validated)
            return user

        user = await _do()
        if not user or not getattr(user, "is_authenticated", False):
            raise WSXNotAuthenticated("Invalid token")
        return (user, token)

    def _from_header(self, request):
        headers = dict(request.scope.get("headers", []) or [])
        raw = headers.get(self.header_name)
        if not raw:
            return None
        val = raw.decode("utf-8").strip()
        if not val.lower().startswith(self.prefix):
            return None
        return val[len(self.prefix):].strip()

    def _from_query(self, request):
        raw = request.scope.get("query_string", b"") or b""
        qs = parse_qs(raw.decode("utf-8")) if raw else {}
        return (qs.get(self.query_key) or [None])[0]