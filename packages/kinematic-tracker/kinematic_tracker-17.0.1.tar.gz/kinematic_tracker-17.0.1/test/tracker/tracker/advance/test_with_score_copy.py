"""."""

import numpy as np
import pytest

from kinematic_tracker import NdKkfTracker
from kinematic_tracker.tracker.score_copy import ScoreCopy


def test_with_score_copy(tracker1: NdKkfTracker) -> None:
    rv = tracker1.advance(2000_000_000, [np.linspace(1.1, 6.1, num=6)], return_score=True)
    assert isinstance(rv, ScoreCopy)
    assert rv.score_rt == pytest.approx(0.84785213)
    assert rv.score_rt.ndim == 2
    assert rv.creation_ids == pytest.approx([0])
