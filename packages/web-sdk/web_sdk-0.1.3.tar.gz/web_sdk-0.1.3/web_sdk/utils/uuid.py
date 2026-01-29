"""Utils for working with uuid."""

import uuid


def get_uuid_chars():
    """Get chars from uuid."""
    return str(uuid.uuid4()).replace("-", "")
