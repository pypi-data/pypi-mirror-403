# Modern ONNX CLIP

A modern, lightweight, and robust ONNX runtime for CLIP models.

This library allows you to run **OpenAI CLIP** and **OpenCLIP** models in production environments without installing
PyTorch. It provides a simple CLI to convert models from the massive OpenCLIP model zoo and a pure-Python inference
engine powered by `onnxruntime`, `numpy`, and `pillow`.

## 🚀 Features

- **Zero PyTorch Dependency in Production**: Run inference with just `numpy` and `onnxruntime`. Drastically reduces
  Docker image size and memory usage.
- **Easy Conversion**: Convert *any* model from [OpenCLIP](https://github.com/mlfoundations/open_clip) (ViT-B-32,
  ViT-L-14, SigLIP, etc.) with a single command.
- **Modern Tooling**: Built with `uv`, `ruff`, and strictly typed with `pyright`.
- **Fast**: Leverages ONNX Runtime (CPU or CUDA) for high-performance inference.
- **Drop-in Replacement**: Designed to replace the unmaintained `onnx_clip` package with better model support.

## 📦 Installation

### For Production (Inference Only)

If you only need to run models, install the base package. This **does not** install PyTorch.

```bash
pip install modern-onnx-clip
# or with uv
uv add modern-onnx-clip
```

### For Development & Exporting

To convert models, you need the export dependencies (PyTorch, OpenCLIP).

```bash
pip install "modern-onnx-clip[export]"
```

## 🛠️ Usage

### 1. Convert a Model

First, convert a model from the OpenCLIP registry. You need the `[export]` extras installed for this step.

```bash
# Syntax: onnx-clip convert --model <ARCH> --pretrained <TAG> --output <DIR>

# Example: Standard ViT-B-32
onnx-clip convert --model ViT-B-32 --pretrained laion2b_s34b_b79k --output ./models/vit-b-32

# Example: ViT-L-14 (Higher accuracy)
onnx-clip convert --model ViT-L-14 --pretrained openai --output ./models/vit-l-14
```

This will create a folder containing `visual.onnx`, `textual.onnx`, and configuration files.

### 2. Run Inference (Python)

Now you can use the model in your application. This step works **without PyTorch**.

```python
from onnx_clip import OnnxClip
from PIL import Image

# 1. Load the model (Provide the directory where you exported the model)
model = OnnxClip(model_dir="./models/vit-b-32", device="cpu")  # use 'cuda' for GPU

# 2. Get Image Embeddings
image = Image.open("cat.jpg")
image_features = model.get_image_embedding(image)
# shape: (1, 512)

# 3. Get Text Embeddings
text_features = model.get_text_embedding(["a photo of a cat", "a photo of a dog"])
# shape: (2, 512)

# 4. Calculate Similarity
# (The embeddings are already normalized)
similarity = image_features @ text_features.T
print(similarity)
# [[0.28, 0.15]]
```

### 3. CLI Inference (Testing)

You can also test a model directly from the CLI:

```bash
onnx-clip run --model-dir ./models/vit-b-32 --image cat.jpg --text "a cute cat"
```

## ⚙️ GPU Support

To run on NVIDIA GPUs, install `onnxruntime-gpu` instead of the standard `onnxruntime`.

```bash
pip uninstall onnxruntime
pip install onnxruntime-gpu
```

Then initialize the model with `device="cuda"`.

## 🏗️ Project Structure

- `exporter.py`: Handles loading PyTorch models and exporting them to ONNX graphs.
- `model.py`: The lightweight inference engine. Abstraction over ONNX Runtime sessions.
- `preprocessor.py`: Reimplementation of CLIP's image preprocessing using only NumPy and Pillow.
- `tokenizer.py`: Handles text tokenization (BPE) without heavy external dependencies.

## 🧪 Development & Testing

We use `pytest` for testing.

### Standard Tests

Run the standard test suite (does not require PyTorch/CLIP):

```bash
pytest
```

### Manual Verification Tests

The `tests/manual/` directory contains scripts to verify numerical consistency between this library (ONNX) and the
original PyTorch CLIP.
These tests are **skipped by default** if dependencies are missing. To run them:

1. Install the `clip` library manually (it cannot be a package dependency due to PyPI restrictions):
   ```bash
   pip install git+https://github.com/openai/CLIP.git
   ```

2. Export a model to a local directory (e.g., `../models/ViT-B-32`):
   ```bash
   onnx-clip convert --model ViT-B-32 --pretrained laion2b_s34b_b79k --output ../models/ViT-B-32
   ```

3. Set the environment variable and run:
   ```bash
   # Linux/Mac
   export ONNX_CLIP_MODEL_DIR="../models/ViT-B-32"
   pytest tests/manual/

   # Windows (PowerShell)
   $env:ONNX_CLIP_MODEL_DIR="../models/ViT-B-32"
   pytest tests/manual/
   ```

## License

MIT License.

## Acknowledgements

Built on top of the incredible work by [OpenAI](https://github.com/openai/CLIP)
and [OpenCLIP](https://github.com/mlfoundations/open_clip).
Inspired by the original `onnx_clip` package.
