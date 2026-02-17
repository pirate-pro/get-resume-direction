from __future__ import annotations

import os


def parse_cookie_string(cookie_value: str) -> dict[str, str]:
    cookies: dict[str, str] = {}
    for part in cookie_value.split(";"):
        segment = part.strip()
        if not segment or "=" not in segment:
            continue
        key, value = segment.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue
        cookies[key] = value
    return cookies


def resolve_cookies(config: dict | None, *, env_keys: tuple[str, ...] = ()) -> dict[str, str] | None:
    cfg = config or {}

    value = cfg.get("cookies")
    if isinstance(value, dict):
        cookies = {str(k).strip(): str(v).strip() for k, v in value.items() if str(k).strip() and v is not None}
        return cookies or None
    if isinstance(value, str) and value.strip():
        cookies = parse_cookie_string(value)
        if cookies:
            return cookies

    cookie_string = cfg.get("cookie_string")
    if isinstance(cookie_string, str) and cookie_string.strip():
        cookies = parse_cookie_string(cookie_string)
        if cookies:
            return cookies

    for env_key in env_keys:
        raw = os.getenv(env_key)
        if not raw:
            continue
        cookies = parse_cookie_string(raw)
        if cookies:
            return cookies
    return None
