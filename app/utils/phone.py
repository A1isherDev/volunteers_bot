"""Phone normalization and validation for registration (manual entry fallback)."""

from __future__ import annotations

import re


def normalize_phone_digits(raw: str) -> str:
    return re.sub(r"\D", "", raw or "")


def is_valid_phone(raw: str) -> bool:
    digits = normalize_phone_digits(raw)
    return 9 <= len(digits) <= 16


def store_phone(raw: str) -> str:
    """Collapse whitespace; keep leading + if present; cap DB length."""
    s = (raw or "").strip()
    if not s:
        return ""
    if len(s) > 64:
        s = s[:64]
    return s
