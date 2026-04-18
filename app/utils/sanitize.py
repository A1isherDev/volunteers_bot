from __future__ import annotations

import html
import re


def sanitize_user_text(text: str, *, max_len: int = 8000) -> str:
    """Strip control chars, trim length, escape HTML entities for safe display."""
    if not text:
        return ""
    s = "".join(ch for ch in text if ord(ch) >= 32 or ch in "\n\r\t")
    s = s.strip()[:max_len]
    return html.escape(s, quote=True)


def strip_invisible(text: str) -> str:
    return re.sub(r"[\u200b\u200c\u200d\ufeff]", "", text)
