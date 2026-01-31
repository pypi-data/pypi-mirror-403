import os

import numpy as np
import pytest
from PIL import Image

from onnx_clip import OnnxClip

MODEL_DIR = os.environ.get("ONNX_CLIP_MODEL_DIR")

# IMPORTANT: BATCH = 1, as the current model is exported with a fixed size
BATCH = 1
TEXTS = ["a photo of a cat"]

# Tolerances for verification
# 1e-4 is too strict for different engines (PyTorch uses PIL Bicubic, ONNX might differ)
# 0.05 (5%) is a normal margin of error for preprocessing differences
RELAXED_COS_DIFF = 0.05


@pytest.mark.skipif(
    not MODEL_DIR or not os.path.exists(MODEL_DIR), reason="ONNX_CLIP_MODEL_DIR not set or does not exist"
)
def test_onnx_vs_torch_consistency():
    clip = pytest.importorskip("clip")
    torch = pytest.importorskip("torch")
    pytest.importorskip("onnx")

    if BATCH != len(TEXTS):
        raise ValueError(f"Batch size ({BATCH}) does not match number of texts ({len(TEXTS)})")

    # UTILS
    def l2_normalize(x: np.ndarray) -> np.ndarray:
        """L2 normalization of vectors so their length becomes 1."""
        return x / np.linalg.norm(x, axis=1, keepdims=True)

    def cosine_similarity(a: np.ndarray, b: np.ndarray) -> np.ndarray:
        """Dot product of normalized vectors (cosine similarity)."""
        return a @ b.T

    # 1. LOAD TORCH CLIP (Reference)
    print("Loading PyTorch CLIP (reference)...")
    torch_model, preprocess = clip.load("ViT-B/32", device="cpu")
    torch_model.eval()

    # 2. LOAD ONNX CLIP (Tested model)
    print("Loading ONNX CLIP via API...")
    try:
        onnx_model = OnnxClip(model_dir=MODEL_DIR, device="cpu")
    except Exception as e:
        print(f"\n❌ Error loading ONNX model from {MODEL_DIR}")
        print("Ensure visual.onnx and textual.onnx exist there.")
        raise e

    # 3. PREPARE INPUTS
    print(f"Generating inputs (Batch size: {BATCH})...")
    # Generate "random" white images 224x224
    images = [Image.new("RGB", (224, 224), color="white") for _ in range(BATCH)]
    texts = TEXTS

    # 4. INFERENCE: TORCH
    print("Running inference on PyTorch...")
    with torch.no_grad():
        # Preprocess -> Image Encoder
        torch_input_imgs = torch.stack([preprocess(img) for img in images])
        img_t = torch_model.encode_image(torch_input_imgs).cpu().numpy()

        # Tokenize -> Text Encoder
        torch_input_txt = clip.tokenize(texts)
        txt_t = torch_model.encode_text(torch_input_txt).cpu().numpy()

    # Normalization
    img_t = l2_normalize(img_t)
    txt_t = l2_normalize(txt_t)

    # 5. INFERENCE: ONNX
    print("Running inference on ONNX...")
    # OnnxClip performs preprocessing internally
    img_o = onnx_model.get_image_embedding(images)
    txt_o = onnx_model.get_text_embedding(texts)

    # Normalization
    img_o = l2_normalize(img_o)
    txt_o = l2_normalize(txt_o)

    # 6. COMPARE & REPORT
    # Absolute difference of values in vectors
    img_abs_diff = np.abs(img_t - img_o).max()
    txt_abs_diff = np.abs(txt_t - txt_o).max()

    img_consistency = np.diag(cosine_similarity(img_t, img_o))
    txt_consistency = np.diag(cosine_similarity(txt_t, txt_o))

    # Invert: 0.0 - perfect, 1.0 - terrible
    img_cos_error = 1.0 - img_consistency
    txt_cos_error = 1.0 - txt_consistency

    print("\n" + "=" * 30)
    print("       TEST RESULTS")
    print("=" * 30)

    print(f"Max Absolute Diff (Image): {img_abs_diff:.6f}")
    print(f"Max Absolute Diff (Text) : {txt_abs_diff:.6f}")
    print("-" * 30)
    print(f"Max Cosine Error (Image) : {img_cos_error.max():.6f}")
    print(f"Max Cosine Error (Text)  : {txt_cos_error.max():.6f}")

    # 7. ASSERTS
    print("\nVerifying results...")

    # Check not bitwise match, but semantic (cosine) match
    if img_cos_error.max() > RELAXED_COS_DIFF:
        pytest.fail(f"❌ Image embeddings diverge too much! Max cosine error: {img_cos_error.max():.6f}")
    else:
        print(f"✅ Image embeddings are consistent (Error < {RELAXED_COS_DIFF})")

    if txt_cos_error.max() > RELAXED_COS_DIFF:
        pytest.fail(f"❌ Text embeddings diverge too much! Max cosine error: {txt_cos_error.max():.6f}")
    else:
        print(f"✅ Text embeddings are consistent (Error < {RELAXED_COS_DIFF})")

    print("\n🎉 SUCCESS: ONNX model behaves similarly to PyTorch!")
