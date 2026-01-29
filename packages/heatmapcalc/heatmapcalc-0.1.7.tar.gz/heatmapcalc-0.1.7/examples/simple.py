from examples.ensure_test_data import ensure_test_data
from heatmapcalc import apply_heatmap, heatmapcalc

# Example boxes: list of tuples (x1, y1, x2, y2)
boxes = [
    (10, 300, 100, 600),
    (150, 300, 300, 600),
    (250, 215, 450, 425),
    (430, 215, 550, 425),
]

# Shape of the heatmap
shape = (600, 800)

# Calculate the heatmap
heatmap = heatmapcalc(boxes, shape)

# An example image is downloaded (800x600)
img_file = "/tmp/person.jpg"
ensure_test_data(img_file, "https://picsum.photos/id/22/800/600")

# Applying the heatmap to the image
try:
    import cv2
except ImportError:
    raise ImportError("OpenCV is required Applying the heatmap")
img = cv2.imread(img_file)
img_with_heatmap_overlay = apply_heatmap(heatmap, img)
cv2.imwrite("/tmp/person_heatmap.jpg", img_with_heatmap_overlay)
