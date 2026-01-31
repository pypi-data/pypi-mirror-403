import numpy as np
from PIL import Image

from onnx_clip.preprocessor import Preprocessor


class TestPreprocessorInit:
    """Tests for Preprocessor initialization."""

    def test_default_size(self):
        """Test that default size is 224."""
        preprocessor = Preprocessor()
        assert preprocessor.size == 224

    def test_custom_size(self):
        """Test that custom size is respected."""
        preprocessor = Preprocessor(size=336)
        assert preprocessor.size == 336

    def test_mean_std_values(self):
        """Test that CLIP mean and std are correctly set."""
        preprocessor = Preprocessor()
        expected_mean = np.array([0.48145466, 0.4578275, 0.40821073], dtype=np.float32)
        expected_std = np.array([0.26862954, 0.26130258, 0.27577711], dtype=np.float32)

        np.testing.assert_array_almost_equal(preprocessor.mean, expected_mean)
        np.testing.assert_array_almost_equal(preprocessor.std, expected_std)


class TestPreprocessorCall:
    """Tests for Preprocessor __call__ method."""

    def test_single_image_output_shape(self, sample_image: Image.Image):
        """Test output shape for a single image."""
        preprocessor = Preprocessor(size=224)
        output = preprocessor(sample_image)

        assert output.shape == (1, 3, 224, 224)
        assert output.dtype == np.float32

    def test_batch_images_output_shape(self, sample_image_batch: list[Image.Image]):
        """Test output shape for a batch of images."""
        preprocessor = Preprocessor(size=224)
        output = preprocessor(sample_image_batch)

        assert output.shape == (3, 3, 224, 224)
        assert output.dtype == np.float32

    def test_custom_size_output(self, sample_image: Image.Image):
        """Test output shape with custom size."""
        preprocessor = Preprocessor(size=336)
        output = preprocessor(sample_image)

        assert output.shape == (1, 3, 336, 336)

    def test_rgba_image_converted(self, sample_image_rgba: Image.Image):
        """Test that RGBA images are converted to RGB."""
        preprocessor = Preprocessor()
        output = preprocessor(sample_image_rgba)

        assert output.shape == (1, 3, 224, 224)

    def test_grayscale_image_converted(self, sample_image_grayscale: Image.Image):
        """Test that grayscale images are converted to RGB."""
        preprocessor = Preprocessor()
        output = preprocessor(sample_image_grayscale)

        assert output.shape == (1, 3, 224, 224)

    def test_normalization_applied(self, sample_image: Image.Image):
        """Test that normalization is applied (values not in 0-255 range)."""
        preprocessor = Preprocessor()
        output = preprocessor(sample_image)

        # After normalization, values should be roughly centered around 0
        assert output.min() < 0 or output.max() > 1


class TestResizeAndCenterCrop:
    """Tests for internal _resize_and_center_crop method."""

    def test_landscape_image(self):
        """Test center crop on landscape image."""
        preprocessor = Preprocessor(size=224)
        # Create a wide image (400x200)
        img = Image.new("RGB", (400, 200), color="red")
        result = preprocessor._resize_and_center_crop(img)

        assert result.size == (224, 224)

    def test_portrait_image(self):
        """Test center crop on portrait image."""
        preprocessor = Preprocessor(size=224)
        # Create a tall image (200x400)
        img = Image.new("RGB", (200, 400), color="blue")
        result = preprocessor._resize_and_center_crop(img)

        assert result.size == (224, 224)

    def test_square_image(self):
        """Test processing of already square image."""
        preprocessor = Preprocessor(size=224)
        img = Image.new("RGB", (300, 300), color="green")
        result = preprocessor._resize_and_center_crop(img)

        assert result.size == (224, 224)

    def test_small_image_upscaled(self):
        """Test that small images are upscaled."""
        preprocessor = Preprocessor(size=224)
        img = Image.new("RGB", (50, 50), color="yellow")
        result = preprocessor._resize_and_center_crop(img)

        assert result.size == (224, 224)
