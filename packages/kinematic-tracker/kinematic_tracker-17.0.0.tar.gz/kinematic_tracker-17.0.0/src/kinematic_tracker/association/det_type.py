from typing import Sequence

import cv2
import numpy as np


FMT = np.ndarray[tuple[int, int], np.dtype[np.float64]]
FVT = np.ndarray[tuple[int], np.dtype[np.float64]]
IVT = np.ndarray[tuple[int], np.dtype[np.int64]]
DT = Sequence[FVT] | FMT | Sequence[Sequence[float]]
FT = Sequence[cv2.KalmanFilter]
