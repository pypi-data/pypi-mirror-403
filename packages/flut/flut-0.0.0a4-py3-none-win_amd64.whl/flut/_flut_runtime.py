"""Flut runtime utilities that don't depend on engine initialization."""

import uuid


def generate_flut_id() -> str:
    """Generate a unique ID for Flut objects."""
    return str(uuid.uuid4())
