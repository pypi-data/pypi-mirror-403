"""."""

import numpy as np
import pytest

from kinematic_tracker import NdKkfTracker


def test_reset(tracker1: NdKkfTracker) -> None:
    tracker1.reset()
    tracker1.advance(0, [np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])])
    assert len(tracker1.tracks) == 1
    ref = np.array([1.0, 0.0, 0.0, 2.0, 0.0, 0.0, 3.0, 0.0, 0.0, 4.0, 5.0, 6.0]).reshape(12, 1)
    assert tracker1.tracks[0].kkf.kalman_filter.statePost == pytest.approx(ref)
