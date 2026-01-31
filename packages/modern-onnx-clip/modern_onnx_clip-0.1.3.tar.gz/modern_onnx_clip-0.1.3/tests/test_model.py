import json
import os
import tempfile
from unittest.mock import MagicMock

import numpy as np
import pytest
from PIL import Image

from onnx_clip.model import OnnxClip


class TestOnnxClipInit:
    """Tests for OnnxClip initialization."""

    def test_init_with_missing_dir_uses_defaults(self):
        """Test that missing config uses default values."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create minimal config
            config = {"image_size": 224, "context_length": 77}
            with open(os.path.join(tmpdir, "config.json"), "w") as f:
                json.dump(config, f)

            # This will fail to load ONNX models but should init preprocessor
            model = OnnxClip(model_dir=tmpdir, device="cpu", silent=True)
            assert model.preprocessor is not None
            assert model.preprocessor.size == 224

    def test_init_sets_providers_for_cpu(self):
        """Test that CPU provider is set correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {"image_size": 224}
            with open(os.path.join(tmpdir, "config.json"), "w") as f:
                json.dump(config, f)

            model = OnnxClip(model_dir=tmpdir, device="cpu", silent=True)
            assert "CPUExecutionProvider" in model.providers

    def test_init_loads_config(self):
        """Test that config is loaded correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {
                "model_name": "ViT-B-32",
                "image_size": 224,
                "context_length": 77,
            }
            with open(os.path.join(tmpdir, "config.json"), "w") as f:
                json.dump(config, f)

            model = OnnxClip(model_dir=tmpdir, device="cpu", silent=True)
            assert model.config["model_name"] == "ViT-B-32"
            assert model.config["image_size"] == 224


class TestPreprocessorIntegration:
    """Tests for Preprocessor integration with OnnxClip."""

    def test_preprocessor_uses_config_size(self):
        """Test that preprocessor uses image_size from config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {"image_size": 336}
            with open(os.path.join(tmpdir, "config.json"), "w") as f:
                json.dump(config, f)

            model = OnnxClip(model_dir=tmpdir, device="cpu", silent=True)
            assert model.preprocessor.size == 336

    def test_preprocessor_defaults_to_224(self):
        """Test that preprocessor defaults to 224 if not in config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {}
            with open(os.path.join(tmpdir, "config.json"), "w") as f:
                json.dump(config, f)

            model = OnnxClip(model_dir=tmpdir, device="cpu", silent=True)
            assert model.preprocessor.size == 224


class TestTokenizerSelection:
    """Tests for tokenizer selection logic."""

    def test_uses_simple_tokenizer_by_default(self):
        """Test that SimpleTokenizer is used when no tokenizer.json exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {"image_size": 224}
            with open(os.path.join(tmpdir, "config.json"), "w") as f:
                json.dump(config, f)

            model = OnnxClip(model_dir=tmpdir, device="cpu", silent=True)
            assert model._tokenizer_type == "simple"


class TestGetImageEmbedding:
    """Tests for get_image_embedding method."""

    def test_raises_if_visual_not_loaded(self, sample_image: Image.Image):
        """Test that error is raised if visual model not loaded."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {"image_size": 224}
            with open(os.path.join(tmpdir, "config.json"), "w") as f:
                json.dump(config, f)

            model = OnnxClip(model_dir=tmpdir, device="cpu", silent=True)

            with pytest.raises(RuntimeError, match="Visual model not loaded"):
                model.get_image_embedding(sample_image)

    def test_accepts_pil_image(self):
        """Test that PIL Image input is accepted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {"image_size": 224}
            with open(os.path.join(tmpdir, "config.json"), "w") as f:
                json.dump(config, f)

            model = OnnxClip(model_dir=tmpdir, device="cpu", silent=True)

            # Create a mock visual session
            mock_session = MagicMock()
            mock_session.get_inputs.return_value = [MagicMock(name="image")]
            mock_session.get_outputs.return_value = [MagicMock(name="embedding")]
            mock_session.run.return_value = [np.random.randn(1, 512).astype(np.float32)]
            model.visual_session = mock_session

            img = Image.new("RGB", (256, 256), color="red")
            result = model.get_image_embedding(img)

            assert isinstance(result, np.ndarray)
            assert result.shape == (1, 512)

    def test_accepts_numpy_array(self):
        """Test that numpy array input is accepted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {"image_size": 224}
            with open(os.path.join(tmpdir, "config.json"), "w") as f:
                json.dump(config, f)

            model = OnnxClip(model_dir=tmpdir, device="cpu", silent=True)

            mock_session = MagicMock()
            mock_session.get_inputs.return_value = [MagicMock(name="image")]
            mock_session.get_outputs.return_value = [MagicMock(name="embedding")]
            mock_session.run.return_value = [np.random.randn(1, 512).astype(np.float32)]
            model.visual_session = mock_session

            # Create HWC numpy array (BGR format like OpenCV)
            img_np = np.zeros((256, 256, 3), dtype=np.uint8)
            result = model.get_image_embedding(img_np)

            assert isinstance(result, np.ndarray)

    def test_normalizes_embeddings(self):
        """Test that embeddings are normalized."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {"image_size": 224}
            with open(os.path.join(tmpdir, "config.json"), "w") as f:
                json.dump(config, f)

            model = OnnxClip(model_dir=tmpdir, device="cpu", silent=True)

            mock_session = MagicMock()
            mock_session.get_inputs.return_value = [MagicMock(name="image")]
            mock_session.get_outputs.return_value = [MagicMock(name="embedding")]
            # Return unnormalized embedding
            mock_session.run.return_value = [np.array([[3.0, 4.0]], dtype=np.float32)]  # norm = 5
            model.visual_session = mock_session

            img = Image.new("RGB", (256, 256), color="red")
            result = model.get_image_embedding(img)

            # Check that result is normalized (norm should be ~1)
            norm = np.linalg.norm(result, axis=1)
            np.testing.assert_array_almost_equal(norm, [1.0])


class TestGetTextEmbedding:
    """Tests for get_text_embedding method."""

    def test_raises_if_textual_not_loaded(self):
        """Test that error is raised if textual model not loaded."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {"image_size": 224, "context_length": 77}
            with open(os.path.join(tmpdir, "config.json"), "w") as f:
                json.dump(config, f)

            model = OnnxClip(model_dir=tmpdir, device="cpu", silent=True)

            with pytest.raises(RuntimeError, match="Textual model not loaded"):
                model.get_text_embedding("hello")

    def test_accepts_single_string(self):
        """Test that single string input is accepted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {"image_size": 224, "context_length": 77}
            with open(os.path.join(tmpdir, "config.json"), "w") as f:
                json.dump(config, f)

            model = OnnxClip(model_dir=tmpdir, device="cpu", silent=True)

            mock_session = MagicMock()
            mock_session.get_inputs.return_value = [MagicMock(name="text")]
            mock_session.get_outputs.return_value = [MagicMock(name="embedding")]
            mock_session.run.return_value = [np.random.randn(1, 512).astype(np.float32)]
            model.textual_session = mock_session

            result = model.get_text_embedding("hello world")

            assert isinstance(result, np.ndarray)
            assert result.shape == (1, 512)

    def test_accepts_list_of_strings(self):
        """Test that list of strings input is accepted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {"image_size": 224, "context_length": 77}
            with open(os.path.join(tmpdir, "config.json"), "w") as f:
                json.dump(config, f)

            model = OnnxClip(model_dir=tmpdir, device="cpu", silent=True)

            mock_session = MagicMock()
            mock_session.get_inputs.return_value = [MagicMock(name="text")]
            mock_session.get_outputs.return_value = [MagicMock(name="embedding")]
            mock_session.run.return_value = [np.random.randn(3, 512).astype(np.float32)]
            model.textual_session = mock_session

            texts = ["cat", "dog", "bird"]
            result = model.get_text_embedding(texts)

            assert isinstance(result, np.ndarray)
            assert result.shape == (3, 512)

    def test_normalizes_embeddings(self):
        """Test that text embeddings are normalized."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {"image_size": 224, "context_length": 77}
            with open(os.path.join(tmpdir, "config.json"), "w") as f:
                json.dump(config, f)

            model = OnnxClip(model_dir=tmpdir, device="cpu", silent=True)

            mock_session = MagicMock()
            mock_session.get_inputs.return_value = [MagicMock(name="text")]
            mock_session.get_outputs.return_value = [MagicMock(name="embedding")]
            mock_session.run.return_value = [np.array([[3.0, 4.0]], dtype=np.float32)]  # norm = 5
            model.textual_session = mock_session

            result = model.get_text_embedding("test")

            norm = np.linalg.norm(result, axis=1)
            np.testing.assert_array_almost_equal(norm, [1.0])
