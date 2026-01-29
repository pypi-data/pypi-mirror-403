# wsx/settings.py
from __future__ import annotations
from dataclasses import dataclass
from django.conf import settings as dj_settings


@dataclass(frozen=True, slots=True)
class WSXSettings:
    # "required" | "optional" | "disabled"
    HANDSHAKE_MODE: str = "required"

    # If True, and token is present in headers/query at connect time,
    # the server may authorize during the handshake phase without requiring client to send socket.authorize.
    AUTO_AUTHORIZE_FROM_SCOPE: bool = False

    # Handshake timeouts / policy
    HANDSHAKE_TIMEOUT_SECONDS: int = 20
    HANDSHAKE_MAX_ATTEMPTS: int = 2
    HANDSHAKE_LOCK_SECONDS: int = 20

    # Which action name is used for authorize step
    AUTHORIZE_ACTION: str = "socket.authorize"

    # Which actions can run pre-auth (only relevant when HANDSHAKE_MODE != "disabled")
    DEFAULT_ALLOW_UNAUTH_ACTIONS: tuple[str, ...] = ("public.ping",)


def get_wsx_settings() -> WSXSettings:
    cfg = getattr(dj_settings, "WSX", None) or {}
    return WSXSettings(
        HANDSHAKE_MODE=cfg.get("HANDSHAKE_MODE", WSXSettings.HANDSHAKE_MODE),
        AUTO_AUTHORIZE_FROM_SCOPE=cfg.get("AUTO_AUTHORIZE_FROM_SCOPE", WSXSettings.AUTO_AUTHORIZE_FROM_SCOPE),
        HANDSHAKE_TIMEOUT_SECONDS=cfg.get("HANDSHAKE_TIMEOUT_SECONDS", WSXSettings.HANDSHAKE_TIMEOUT_SECONDS),
        HANDSHAKE_MAX_ATTEMPTS=cfg.get("HANDSHAKE_MAX_ATTEMPTS", WSXSettings.HANDSHAKE_MAX_ATTEMPTS),
        HANDSHAKE_LOCK_SECONDS=cfg.get("HANDSHAKE_LOCK_SECONDS", WSXSettings.HANDSHAKE_LOCK_SECONDS),
        AUTHORIZE_ACTION=cfg.get("AUTHORIZE_ACTION", WSXSettings.AUTHORIZE_ACTION),
        DEFAULT_ALLOW_UNAUTH_ACTIONS=tuple(cfg.get("DEFAULT_ALLOW_UNAUTH_ACTIONS", WSXSettings.DEFAULT_ALLOW_UNAUTH_ACTIONS)),
    )