"""
Session state management.

Provides global session tracker storage for the server.
"""

from typing import Dict
from analytic_continuation import ProgressTracker

# Active progress trackers by session ID
_active_trackers: Dict[str, ProgressTracker] = {}


def get_active_trackers() -> Dict[str, ProgressTracker]:
    """Get the global active trackers dictionary."""
    return _active_trackers


def clear_all_trackers() -> None:
    """Clear all active trackers (useful for testing)."""
    _active_trackers.clear()
