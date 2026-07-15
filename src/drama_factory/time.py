"""UTC timestamp parsing and canonical formatting."""

from datetime import datetime, timezone


def parse_utc(value: object) -> datetime:
    """Parse a timezone-aware ISO 8601 timestamp or raise ValueError."""
    if not isinstance(value, str):
        raise ValueError("must be an ISO 8601 UTC string")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("must include a timezone offset or Z")
    if parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise ValueError("must be expressed in UTC (Z or +00:00)")
    return parsed.astimezone(timezone.utc)


def format_utc(value: datetime) -> str:
    """Format a timezone-aware datetime as canonical ISO 8601 UTC."""
    if value.tzinfo is None:
        raise ValueError("datetime must be timezone-aware")
    return value.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
