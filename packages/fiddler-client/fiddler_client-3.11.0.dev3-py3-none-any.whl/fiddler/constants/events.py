"""Internal constants for event publishing operations.

This module defines internal constants used by the Fiddler client for event
publishing operations. These constants are not part of the public API.
"""

import enum


@enum.unique
class PublishEventsSourceType(str, enum.Enum):
    """Internal enum for event publishing source types.

    Used internally to distinguish between different data sources
    when publishing events to the Fiddler platform.
    """

    EVENTS = 'EVENTS'
    """Direct event data source (e.g., list of dictionaries, DataFrame)."""

    FILE = 'FILE'
    """File-based data source (e.g., CSV, Parquet files)."""
