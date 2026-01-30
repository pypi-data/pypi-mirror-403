"""."""

import numpy as np

from .det_type import FMT


def inv_out(mat: FMT, out: FMT) -> None:
    try:
        out[:] = np.linalg.inv(mat)
    except np.linalg.LinAlgError:
        print('\n', mat)
        raise
