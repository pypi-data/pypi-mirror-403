"""
DateTime utilities for Cindergrace applications.

Provides:
- utcnow(): Timezone-aware UTC datetime
- generate_id(): ULID-based unique identifier

Usage:
    from cgc_common import utcnow, generate_id

    timestamp = utcnow()
    unique_id = generate_id()
"""

from datetime import datetime, timezone


def utcnow() -> datetime:
    """Return current UTC time as timezone-aware datetime.

    Returns:
        datetime: Current UTC time with timezone info

    Example:
        >>> from cgc_common import utcnow
        >>> now = utcnow()
        >>> now.tzinfo is not None
        True
    """
    return datetime.now(timezone.utc)


def generate_id() -> str:
    """Generate a unique identifier using ULID.

    ULIDs are sortable, URL-safe, and more readable than UUIDs.
    Falls back to UUID4 if ulid-py is not installed.

    Returns:
        str: Unique identifier string

    Example:
        >>> from cgc_common import generate_id
        >>> id1 = generate_id()
        >>> id2 = generate_id()
        >>> id1 != id2
        True
    """
    try:
        from ulid import ULID

        return str(ULID())
    except ImportError:
        import uuid

        return str(uuid.uuid4())
