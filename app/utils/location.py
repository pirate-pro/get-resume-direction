def normalize_location(raw: str | None) -> tuple[str | None, str | None, str | None, str]:
    if not raw:
        return None, None, None, "cn::unknown"

    text = raw.strip().replace("市", "").replace("省", "")
    parts = [p for p in text.replace("/", "-").split("-") if p]

    province = parts[0] if len(parts) >= 1 else None
    city = parts[1] if len(parts) >= 2 else parts[0] if province else None
    district = parts[2] if len(parts) >= 3 else None

    key = f"cn::{province or 'unknown'}::{city or 'unknown'}::{district or 'unknown'}"
    return province, city, district, key
