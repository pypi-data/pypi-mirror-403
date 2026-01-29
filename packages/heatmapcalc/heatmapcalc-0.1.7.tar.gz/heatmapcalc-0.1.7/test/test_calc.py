import random

import numpy as np
import pytest

from heatmapcalc import heatmapcalc

# Detect is a type alias for a tuple of 4 ints
Detect = tuple[int, int, int, int]


def calc_longterm_heatmap_orig(
    detects: list[Detect], shape: tuple[int, int]
) -> np.ndarray:
    """Python version for testing comparison"""
    heatmap = np.zeros(shape[:2], dtype=np.int32)
    for detect in detects:
        box = detect
        center = (int((box[0] + box[2]) // 2), int((box[1] + box[3]) // 2))
        radius = min(int(box[2]) - int(box[0]), int(box[3]) - int(box[1])) // 2
        if radius <= 0:
            continue
        y, x = np.ogrid[0 : heatmap.shape[0], 0 : heatmap.shape[1]]
        mask = (x - center[0]) ** 2 + (y - center[1]) ** 2 <= radius**2
        heatmap += 2 * mask
    return heatmap


@pytest.fixture
def random_detects():
    return [
        (
            random.randint(0, 800),
            random.randint(0, 600),
            random.randint(0, 800),
            random.randint(0, 600),
        )
        for _ in range(2000)
    ]


def test_equal():
    x = calc_longterm_heatmap_orig([(10, 10, 20, 20)], (100, 100))
    print(x)
    assert np.sum(x) > 0
    y = heatmapcalc([(10, 10, 20, 20)], (100, 100))
    print(y)
    assert np.sum(y) > 0
    assert np.array_equal(x, y)


def test_equal_random(random_detects: list[tuple[int, int, int, int]]):  # noqa: F811
    x = calc_longterm_heatmap_orig(random_detects, (800, 600))
    print(x)
    assert np.sum(x) > 0
    y = heatmapcalc(random_detects, (800, 600))
    print(y)
    assert np.sum(y) > 0
    assert np.array_equal(x, y)


def test_measure_runtime(random_detects: list[tuple[int, int, int, int]]):  # noqa: F811
    import timeit

    rusttime = timeit.timeit(lambda: heatmapcalc(random_detects, (800, 600)), number=5)
    origtime = timeit.timeit(
        lambda: calc_longterm_heatmap_orig(random_detects, (800, 600)), number=5
    )
    print(f"Original time: {origtime}")
    print(f"Rust time: {rusttime}")
