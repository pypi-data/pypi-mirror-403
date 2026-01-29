"""Data serialization utilities."""

import json
from typing import Any


def serialize_data(data: Any) -> str:
    """Convert any input data to a string representation."""
    if isinstance(data, str):
        return data
    elif isinstance(data, (dict, list)):
        try:
            return json.dumps(data, indent=2, default=str)
        except (TypeError, ValueError):
            return str(data)
    else:
        return str(data)
