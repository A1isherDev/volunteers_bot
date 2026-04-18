"""Input validation helpers for FSM flows."""

from __future__ import annotations

MAX_BIO_LEN = 2000
MAX_NAME_LEN = 255


def validate_age_text(text: str) -> int | None:
    raw = text.strip()
    if not raw.isdigit():
        return None
    age = int(raw)
    if age < 5 or age > 120:
        return None
    return age


def validate_bio(text: str) -> str | None:
    s = text.strip()
    if not s:
        return None
    if len(s) > MAX_BIO_LEN:
        return None
    return s
