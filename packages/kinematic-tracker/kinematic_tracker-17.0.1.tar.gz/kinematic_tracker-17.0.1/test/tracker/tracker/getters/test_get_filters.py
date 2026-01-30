"""."""

from kinematic_tracker import NdKkfTracker


def test_get_filters(tracker1: NdKkfTracker) -> None:
    """."""
    filters = tracker1.get_filters()
    assert len(filters) == 1
