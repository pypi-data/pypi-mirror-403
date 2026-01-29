# heatmapcalc

`heatmapcalc` is a minimalistic python package that provides a fast function to
add circles to a numpy array, based on a list of bounding boxes.

It is written in Rust for performance.

## Installation

Install with `pip`:

```sh
pip install heatmapcalc
```

With Rust installed, you can build the package from source:

```sh
pip install .
```

## Usage

Here is a simple example:

```python
from heatmapcalc import heatmapcalc

# Example boxes: list of tuples (x1, y1, x2, y2)
boxes = [
    (10, 300, 100, 600),
    (150, 300, 300, 600),
    (250, 215, 450, 425),
    (430, 215, 550, 425),
]

# Shape of the heatmap
shape = (600, 800)

# Calculate the heatmap, an np.ndarray of shape (600, 800) and type i64
# Note: The output is NOT normalized - values represent raw overlap counts
heatmap = heatmapcalc(boxes, shape)
```

This can now be used to visualize it and overlay it on an image.
This is shown in [the example script](examples/simple.py).

## Development

- _Deploy_: To deploy on PyPi, trigger the [CI](.github/workflows/CI.yml)
workflow on GitHub with the latest commit tag. The workflow builds and uploads
the wheels for Linux and MacOS.
- _Test_: Test with `pytest`.
