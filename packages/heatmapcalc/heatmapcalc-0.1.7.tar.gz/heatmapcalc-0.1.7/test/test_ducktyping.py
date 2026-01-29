import numpy as np
import pytest

from heatmapcalc import heatmapcalc


def test_heatmapcalc_empty_input():
    shape = (10, 10)
    result = heatmapcalc([], shape)
    expected = np.zeros(shape, dtype=np.int32)
    assert np.array_equal(result, expected)


def test_heatmapcalc_invalid_input():
    shape = (10, 10)
    with pytest.raises(ValueError):
        heatmapcalc([(1, 2, 3)], shape)  # Invalid input, not all tuples have 4 elements


def test_heatmapcalc_integer_coordinates():
    shape = (10, 10)
    detects = [(1, 2, 3, 4), (5, 6, 7, 8)]
    result = heatmapcalc(detects, shape)
    assert isinstance(result, np.ndarray)


def test_heatmapcalc_float_coordinates():
    shape = (10, 10)
    detects = [(1.0, 2.0, 3.0, 4.0), (5.0, 6.0, 7.0, 8.0)]
    result = heatmapcalc(detects, shape)
    assert isinstance(result, np.ndarray)


class Detect:
    def __init__(self, box):
        self.box = box


def test_heatmapcalc_object_with_box():
    shape = (10, 10)
    detects = [Detect((1, 2, 3, 4)), Detect((5, 6, 7, 8))]
    result = heatmapcalc(detects, shape)
    assert isinstance(result, np.ndarray)


def test_heatmapcalc_object_with_float_box():
    shape = (10, 10)
    detects = [Detect((1.1, 2.1, 3.1, 4.0)), Detect((5.1, 6.1, 7.1, 8))]
    result = heatmapcalc(detects, shape)
    assert isinstance(result, np.ndarray)
