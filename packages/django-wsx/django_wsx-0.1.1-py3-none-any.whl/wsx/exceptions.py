from __future__ import annotations


class WSXError(Exception):
    code = "error"
    status = 400
    close_code = 4400

    def __init__(self, detail="Error", *, fields=None, extra=None):
        super().__init__(detail)
        self.detail = detail
        self.fields = fields or {}
        self.extra = extra or {}

    def to_payload(self):
        payload = {"code": self.code, "detail": self.detail}
        if self.fields:
            payload["fields"] = self.fields
        if self.extra:
            payload["extra"] = self.extra
        return payload


class WSXBadRequest(WSXError):
    code = "bad_request"
    status = 400
    close_code = 4400


class WSXValidationError(WSXError):
    code = "validation_error"
    status = 400
    close_code = 4400


class WSXNotAuthenticated(WSXError):
    code = "not_authenticated"
    status = 401
    close_code = 4401


class WSXPermissionDenied(WSXError):
    code = "permission_denied"
    status = 403
    close_code = 4403


class WSXNotFound(WSXError):
    code = "not_found"
    status = 404
    close_code = 4404


class WSXThrottled(WSXError):
    code = "throttled"
    status = 429
    close_code = 4408


class WSXServerError(WSXError):
    code = "server_error"
    status = 500
    close_code = 1011