from typing import Any

import numpy as np

from .heatmapcalc import calc_longterm_heatmap


def heatmapcalc(
    detects: list[tuple[int | float, int | float, int | float, int | float]]
    | list[Any],
    shape: tuple[int, int],
) -> np.ndarray:
    """Wrapper for calc_longterm_heatmap"""
    if len(detects) == 0:
        return np.zeros(shape[:2], dtype=np.int32)
    boxes: list[tuple[int, int, int, int]]
    if not all(isinstance(detect, tuple) for detect in detects):
        assert all(hasattr(detect, "box") for detect in detects)
        assert all(len(detect.box) == 4 for detect in detects)  # pyright: ignore[reportAttributeAccessIssue]
        detects = [detect.box for detect in detects]  # pyright: ignore[reportAttributeAccessIssue]
    if not all(len(detect) == 4 for detect in detects):
        raise ValueError("Invalid input")
    elif all(isinstance(c, int) for coords in detects for c in coords):
        boxes = detects  # pyright: ignore[reportAssignmentType]
    elif all(isinstance(c, (float, int)) for coords in detects for c in coords):
        boxes = [(int(d[0]), int(d[1]), int(d[2]), int(d[3])) for d in detects]
    else:
        raise ValueError("Invalid input")
    res = calc_longterm_heatmap(boxes, shape)
    return np.array(res)


def apply_heatmap(heatmap: np.ndarray, frame: np.ndarray) -> np.ndarray:
    """Applies the heatmap data to the given frame and return the frame
    with the heatmap overlay."""
    try:
        import cv2
    except ImportError:
        raise ImportError("OpenCV is required for this function")
    alpha = 0.5
    newframe = frame.copy()
    normalized_hm = np.zeros_like(heatmap, dtype=np.float32)
    cv2.normalize(heatmap.astype(np.float32), normalized_hm, 0, 255, cv2.NORM_MINMAX)
    normalized_hm = cv2.applyColorMap(normalized_hm.astype(np.uint8), cv2.COLORMAP_JET)
    return cv2.addWeighted(newframe, 1 - alpha, normalized_hm, alpha, 0)
