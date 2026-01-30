"""."""

from kinematic_tracker.association.det_type import FMT, IVT


class ScoreCopy:
    def __init__(self, score_rt: FMT, creation_ids: IVT) -> None:
        self.score_rt = score_rt.copy()
        self.creation_ids = creation_ids
