import numpy as np
import pytest

from kinematic_tracker import NdKkfTracker


def test_get_creation_ids_one(tracker1: NdKkfTracker) -> None:
    ids = tracker1.get_creation_ids()
    assert ids == pytest.approx([0])


def test_get_creation_ids_two(tracker1: NdKkfTracker) -> None:
    det_rz = np.linspace(1.0, 12, 12).reshape(2, 6)
    tracker1.advance(2000_000_000, det_rz)
    ids = tracker1.get_creation_ids()
    assert ids == pytest.approx([0, 1])
