import os

import numpy as np
import pytest

from onnx_clip import OnnxClip

# Use environment variable to allow local configuration
MODEL_DIR = os.environ.get("ONNX_CLIP_MODEL_DIR")


@pytest.mark.skipif(
    not MODEL_DIR or not os.path.exists(MODEL_DIR), reason="ONNX_CLIP_MODEL_DIR not set or does not exist"
)
def test_tokenizer_consistency():
    clip = pytest.importorskip("clip")

    # 1. Tokenization via PyTorch CLIP
    print("--- PyTorch Tokenizer ---")
    text = ["a photo of a cat"]
    torch_tokens = clip.tokenize(text).numpy()  # Returns int32 or int64
    print(f"Shape: {torch_tokens.shape}, Dtype: {torch_tokens.dtype}")
    print("Tokens:", torch_tokens[0, :10])

    # 2. Tokenization via Modern ONNX Clip
    print("\n--- ONNX CLIP Tokenizer ---")
    onnx_pipeline = OnnxClip(model_dir=MODEL_DIR, device="cpu")

    # The tokenize method returns np.ndarray
    onnx_tokens = onnx_pipeline._tokenizer.tokenize(text)
    print(f"Shape: {onnx_tokens.shape}, Dtype: {onnx_tokens.dtype}")
    print("Tokens:", onnx_tokens[0, :10])

    # 3. Comparison
    print("\n--- Comparison ---")
    # Cast to the same type (usually int32 vs int64)
    if np.array_equal(torch_tokens.astype(np.int64), onnx_tokens.astype(np.int64)):
        print("✅ TOKENS MATCH!")
    else:
        print("❌ TOKENS MISMATCH!")

        # Show the difference
        diff_indices = np.where(torch_tokens != onnx_tokens)
        print("\nFirst 5 mismatches:")
        for idx in range(min(5, len(diff_indices[0]))):
            r, c = diff_indices[0][idx], diff_indices[1][idx]
            t_val = torch_tokens[r, c]
            o_val = onnx_tokens[r, c]
            print(f"  At [{r}, {c}]: PyTorch={t_val} vs ONNX={o_val}")

        pytest.fail("Token mismatch between PyTorch CLIP and ONNX CLIP")
