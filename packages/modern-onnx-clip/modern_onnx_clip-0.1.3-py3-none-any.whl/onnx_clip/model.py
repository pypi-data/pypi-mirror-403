import json
import logging
import os

import numpy as np
import onnxruntime as ort
from PIL import Image

from .preprocessor import Preprocessor
from .tokenizer import SimpleTokenizer

try:
    from tokenizers import Tokenizer as HFTokenizer
except ImportError:
    HFTokenizer = None


class OnnxClip:
    """A class for running CLIP models using ONNX Runtime.

    This class handles the initialization of ONNX sessions for both visual and textual
    encoders, manages preprocessing for images, and handles tokenization for text.
    It supports both CPU and GPU (CUDA) execution providers.

    Attributes:
        model_dir (str): Directory containing the converted ONNX models and config.
        config (dict): Configuration dictionary loaded from `config.json`.
        preprocessor (Preprocessor): Image preprocessor instance.
        visual_session (ort.InferenceSession): ONNX Runtime session for image encoder.
        textual_session (ort.InferenceSession): ONNX Runtime session for text encoder.
    """

    def __init__(self, model_dir: str, device: str = "cpu", silent: bool = False):
        """Initializes the OnnxClip model.

        Args:
            model_dir (str): Path to directory containing `.onnx` and `config.json`.
            device (str, optional): Computation device. 'cpu' or 'cuda'.
            silent (bool, optional): If True, suppresses logging output.

        Raises:
            RuntimeError: If model files are missing or initialization fails.
        """
        self.model_dir = model_dir
        self.logger = logging.getLogger("OnnxClip")
        if not silent:
            logging.basicConfig(level=logging.INFO)

        # Provider configuration
        self.providers = ["CPUExecutionProvider"]
        if device == "cuda":
            if "CUDAExecutionProvider" in ort.get_available_providers():
                self.providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
            else:
                self.logger.warning("CUDA requested but not available. Fallback to CPU.")

        # Load Config
        self.config_path = os.path.join(model_dir, "config.json")
        self.config = self._load_config(self.config_path)

        # Initialize Preprocessor
        self.preprocessor = Preprocessor(size=self.config.get("image_size", 224))

        # Load Sessions
        self.visual_path = os.path.join(model_dir, "visual.onnx")
        self.textual_path = os.path.join(model_dir, "textual.onnx")

        self.visual_session = None
        self.textual_session = None

        if os.path.exists(self.visual_path):
            self.visual_session = ort.InferenceSession(self.visual_path, providers=self.providers)

        if os.path.exists(self.textual_path):
            self.textual_session = ort.InferenceSession(self.textual_path, providers=self.providers)

        # Initialize Tokenizer
        tokenizer_json = os.path.join(model_dir, "tokenizer.json")
        if os.path.exists(tokenizer_json) and HFTokenizer is not None:
            self.logger.info("Loading HF Tokenizer from tokenizer.json")
            self._tokenizer = HFTokenizer.from_file(tokenizer_json)
            self._tokenizer_type = "hf"
        else:
            self.logger.info("Using SimpleTokenizer (OpenAI CLIP default)")
            vocab_path = os.path.join(model_dir, "bpe_simple_vocab_16e6.txt.gz")
            if not os.path.exists(vocab_path):
                vocab_path = None
            self._tokenizer = SimpleTokenizer(bpe_path=vocab_path)
            self._tokenizer_type = "simple"

    def _load_config(self, path: str) -> dict:
        """Loads the model configuration JSON.

        Args:
            path (str): Path to the config file.

        Returns:
            dict: Configuration dictionary or empty dict if not found.
        """
        if not os.path.exists(path):
            self.logger.warning(f"Config not found at {path}. Using defaults.")
            return {}
        with open(path) as f:
            return json.load(f)

    def get_image_embedding(self, images: Image.Image | list[Image.Image] | np.ndarray) -> np.ndarray:
        """Generates embeddings for one or more images.

        Args:
            images: Input image(s).

        Returns:
            np.ndarray: A NumPy array of normalized embeddings.
        """
        if self.visual_session is None:
            raise RuntimeError("Visual model not loaded.")

        processed_images: Image.Image | list[Image.Image] | np.ndarray = images
        if isinstance(images, np.ndarray):
            if images.ndim == 3:  # HWC
                processed_images = Image.fromarray(images[:, :, ::-1])
            else:
                processed_images = images

        input_tensor: np.ndarray
        if isinstance(processed_images, (Image.Image, list)):
            input_tensor = self.preprocessor(processed_images)
        else:
            input_tensor = processed_images

        # Run inference
        input_name = self.visual_session.get_inputs()[0].name
        output_name = self.visual_session.get_outputs()[0].name

        outputs = self.visual_session.run([output_name], {input_name: input_tensor})
        embeddings = np.array(outputs[0])

        # Normalize
        norm = np.linalg.norm(embeddings, axis=1, keepdims=True)
        return embeddings / norm

    def get_text_embedding(self, texts: str | list[str]) -> np.ndarray:
        """Generates embeddings for one or more text strings.

        Args:
            texts: Input text(s).

        Returns:
            np.ndarray: A NumPy array of normalized embeddings.
        """
        if self.textual_session is None:
            raise RuntimeError("Textual model not loaded.")

        if isinstance(texts, str):
            texts = [texts]

        context_length = self.config.get("context_length", 77)

        if self._tokenizer_type == "hf" and HFTokenizer is not None:
            # Type ignore for HFTokenizer attributes as it's an optional import
            encoded = self._tokenizer.encode_batch(texts)  # type: ignore
            ids = [e.ids for e in encoded]
            padded_ids = []
            for seq in ids:
                if len(seq) > context_length:
                    seq = seq[:context_length]
                else:
                    seq = seq + [0] * (context_length - len(seq))
                padded_ids.append(seq)
            tokens = np.array(padded_ids, dtype=np.int64)
        else:
            # SimpleTokenizer logic
            tokens = self._tokenizer.tokenize(texts, context_length=context_length)

        input_name = self.textual_session.get_inputs()[0].name
        output_name = self.textual_session.get_outputs()[0].name

        outputs = self.textual_session.run([output_name], {input_name: tokens})
        embeddings = np.array(outputs[0])

        # Normalize
        norm = np.linalg.norm(embeddings, axis=1, keepdims=True)
        return embeddings / norm
