# wsx/auth_request.py
from __future__ import annotations
from dataclasses import dataclass


@dataclass(slots=True)
class WSAuthRequest:
    scope: dict
    token: str | None = None  # token from authorize payload (preferred)