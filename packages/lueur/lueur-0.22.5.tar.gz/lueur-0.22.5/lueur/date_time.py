from datetime import UTC, datetime

__all__ = ["now"]


def now() -> datetime:
    return datetime.now().astimezone(UTC)
