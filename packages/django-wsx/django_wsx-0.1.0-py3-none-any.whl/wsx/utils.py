from __future__ import annotations

import json
import uuid
from typing import Any, Dict

from .exceptions import WSXBadRequest


def new_trace_id() -> str:
    return uuid.uuid4().hex


def safe_json_loads(text: str) -> Dict[str, Any]:
    try:
        obj = json.loads(text)
    except Exception as e:
        raise WSXBadRequest("bad_json") from e
    if not isinstance(obj, dict):
        raise WSXBadRequest("message must be an object")
    return obj


def must_be_str(x: Any, name: str) -> str:
    if not isinstance(x, str) or not x:
        raise WSXBadRequest(f"missing/invalid {name}")
    return x


def must_be_dict(x: Any, name: str) -> dict:
    if x is None:
        return {}
    if not isinstance(x, dict):
        raise WSXBadRequest(f"{name} must be an object")
    return x