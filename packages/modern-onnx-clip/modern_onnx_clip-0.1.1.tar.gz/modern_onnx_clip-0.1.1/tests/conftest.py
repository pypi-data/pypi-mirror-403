import numpy as np
import pytest
from PIL import Image


@pytest.fixture
def sample_image() -> Image.Image:
    """Creates a sample RGB image for testing.

    Returns:
        Image.Image: A 256x256 RGB image with a gradient pattern.
    """
    # Create a gradient image
    arr = np.zeros((256, 256, 3), dtype=np.uint8)
    arr[:, :, 0] = np.linspace(0, 255, 256).reshape(1, -1)  # Red gradient horizontal
    arr[:, :, 1] = np.linspace(0, 255, 256).reshape(-1, 1)  # Green gradient vertical
    arr[:, :, 2] = 128  # Blue constant
    return Image.fromarray(arr, mode="RGB")


@pytest.fixture
def sample_image_rgba() -> Image.Image:
    """Creates a sample RGBA image for testing.

    Returns:
        Image.Image: A 256x256 RGBA image.
    """
    arr = np.zeros((256, 256, 4), dtype=np.uint8)
    arr[:, :, 0] = 255  # Red
    arr[:, :, 3] = 200  # Alpha
    return Image.fromarray(arr, mode="RGBA")


@pytest.fixture
def sample_image_grayscale() -> Image.Image:
    """Creates a sample grayscale image for testing.

    Returns:
        Image.Image: A 256x256 grayscale image.
    """
    arr = np.linspace(0, 255, 256 * 256).reshape(256, 256).astype(np.uint8)
    return Image.fromarray(arr, mode="L")


@pytest.fixture
def sample_texts() -> list[str]:
    """Sample texts for tokenization testing.

    Returns:
        list[str]: A list of sample texts.
    """
    return [
        "a photo of a cat",
        "a photo of a dog",
        "Hello, World!",
        "Testing 123 numbers",
    ]


@pytest.fixture
def sample_image_batch(sample_image: Image.Image) -> list[Image.Image]:
    """Creates a batch of sample images.

    Args:
        sample_image: The fixture sample image.

    Returns:
        list[Image.Image]: A list of 3 sample images.
    """
    return [sample_image, sample_image.copy(), sample_image.copy()]
