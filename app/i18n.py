import json
from pathlib import Path
from typing import Any

_CACHE: dict[str, dict[str, Any]] = {}


def _load(lang: str) -> dict[str, Any]:
    if lang not in _CACHE:
        path = Path(__file__).parent / "locales" / f"{lang}.json"
        if not path.exists():
            path = Path(__file__).parent / "locales" / "uz.json"
        with open(path, encoding="utf-8") as f:
            _CACHE[lang] = json.load(f)
    return _CACHE[lang]


def t(lang: str, key: str, **kwargs: Any) -> str:
    data = _load(lang if lang in ("uz", "ru") else "uz")
    parts = key.split(".")
    cur: Any = data
    for p in parts:
        cur = cur.get(p, key) if isinstance(cur, dict) else key
        if cur == key and isinstance(cur, str):
            break
    if not isinstance(cur, str):
        cur = key
    try:
        return cur.format(**kwargs) if kwargs else cur
    except KeyError:
        return cur


def other_lang(lang: str) -> str:
    return "ru" if lang == "uz" else "uz"
