"""."""

import numpy as np
import pytest

from kinematic_tracker.tracker.score_copy import ScoreCopy


def test_init() -> None:
    score_rt = np.linspace(0.5, 1.0, 6).reshape(2, 3)
    creation_ids = np.linspace(0, 2, 3, dtype=int)
    sp = ScoreCopy(score_rt, creation_ids)

    assert sp.score_rt == pytest.approx(score_rt)
    assert id(sp.score_rt) != id(score_rt)
    assert sp.creation_ids == pytest.approx(creation_ids)
    assert id(sp.creation_ids) == id(creation_ids)
