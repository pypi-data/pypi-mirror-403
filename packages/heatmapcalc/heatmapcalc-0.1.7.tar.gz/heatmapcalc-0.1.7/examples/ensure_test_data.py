import urllib.request
from pathlib import Path


def ensure_test_data(image_path: Path | str, download_url: str):
    """Ensure that the test data is available.

    Checks if the file exists, if not it downloads it from the given URL.
    """

    image_path = Path(image_path)
    image_path.parent.mkdir(parents=True, exist_ok=True)

    def download_file(url, local_filename):
        with urllib.request.urlopen(url) as response:
            with open(local_filename, "wb") as f:
                f.write(response.read())
        return local_filename

    if not image_path.exists():
        print("Downloading test file...")
        download_file(download_url, image_path)
