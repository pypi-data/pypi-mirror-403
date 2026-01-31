import json
import os

try:
    import onnx
    import open_clip
    import torch
except ImportError:
    torch = None  # type: ignore
    open_clip = None  # type: ignore
    onnx = None  # type: ignore


class Exporter:
    """Handles the conversion of OpenCLIP PyTorch models to ONNX format.

    Attributes:
        model_name (str): The model architecture name.
        pretrained (str): The pretrained weight tag.
        output_dir (str): Directory where the ONNX models will be saved.
        opset (int): The ONNX opset version to use.
        device (str): Device to run export on.
    """

    def __init__(
        self, model_name: str, pretrained: str, output_dir: str, opset: int = 14
    ):
        """Initializes the Exporter.

        Args:
            model_name (str): Name of the model architecture.
            pretrained (str): Name of the pretrained weights.
            output_dir (str): Destination directory for exported files.
            opset (int, optional): ONNX opset version.
        """
        if torch is None or open_clip is None:
            raise ImportError(
                "Please install 'torch' and 'open-clip-torch' for exporter."
            )

        self.model_name = model_name
        self.pretrained = pretrained
        self.output_dir = output_dir
        self.opset = opset
        self.device = "cpu"

    def export(self):
        """Executes the export process."""
        print(f"Loading model {self.model_name} ({self.pretrained})...")
        model, _, preprocess = open_clip.create_model_and_transforms(  # type: ignore
            self.model_name, pretrained=self.pretrained, device=self.device
        )
        model.eval()

        os.makedirs(self.output_dir, exist_ok=True)

        # 1. Export Config
        image_size = 224
        # Handle different preprocess types in open_clip
        if hasattr(preprocess, "transforms"):
            for t in preprocess.transforms:  # type: ignore
                if hasattr(t, "size"):
                    if isinstance(t.size, int):
                        image_size = t.size
                    elif isinstance(t.size, (tuple, list)):
                        image_size = t.size[0]
                    break
        elif isinstance(preprocess, (list, tuple)):
            # Some versions return a tuple of transforms
            for p in preprocess:
                if hasattr(p, "transforms"):
                    for t in p.transforms:
                        if hasattr(t, "size"):
                            image_size = (
                                t.size if isinstance(t.size, int) else t.size[0]
                            )
                            break

        config = {
            "model_name": self.model_name,
            "pretrained": self.pretrained,
            "image_size": image_size,
            "context_length": model.context_length,
            "vocab_size": model.vocab_size,
            "output_dim": getattr(model.visual, "output_dim", 512),
        }

        with open(os.path.join(self.output_dir, "config.json"), "w") as f:
            json.dump(config, f, indent=4)

        print(f"Config saved. Image size detected: {image_size}")

        # 2. Export Visual
        print("Exporting Visual Model...")
        dummy_input_image = torch.randn(1, 3, image_size, image_size)  # type: ignore

        class VisualWrapper(torch.nn.Module):  # type: ignore
            def __init__(self, visual_model):
                super().__init__()
                self.visual = visual_model

            def forward(self, x):
                return self.visual(x)

        visual_wrapper = VisualWrapper(model.visual)

        torch.onnx.export(  # type: ignore
            visual_wrapper,
            (dummy_input_image,),
            os.path.join(self.output_dir, "visual.onnx"),
            input_names=["image"],
            output_names=["embedding"],
            dynamic_axes={
                "image": {0: "batch_size"},
                "embedding": {0: "batch_size"},
            },
            opset_version=self.opset,
        )

        # 3. Export Textual
        print("Exporting Textual Model...")
        context_length = int(model.context_length)  # type: ignore
        dummy_input_text = torch.zeros(  # type: ignore
            (1, context_length),
            dtype=torch.long,  # type: ignore
        )

        class TextWrapper(torch.nn.Module):  # type: ignore
            def __init__(self, model):
                super().__init__()
                self.model = model

            def forward(self, x):
                return self.model.encode_text(x)

        text_wrapper = TextWrapper(model)

        torch.onnx.export(  # type: ignore
            text_wrapper,
            (dummy_input_text,),
            os.path.join(self.output_dir, "textual.onnx"),
            input_names=["text"],
            output_names=["embedding"],
            dynamic_axes={
                "text": {0: "batch_size"},
                "embedding": {0: "batch_size"},
            },
            opset_version=self.opset,
        )

        # 4. Validate ONNX models
        print("Validating ONNX models...")
        self._validate_onnx(os.path.join(self.output_dir, "visual.onnx"))
        self._validate_onnx(os.path.join(self.output_dir, "textual.onnx"))

        print("Export complete!")
        print(f"Models saved to {self.output_dir}")

    def _validate_onnx(self, path: str) -> None:
        """Validates an ONNX model file.

        Args:
            path (str): Path to the ONNX model file.

        Raises:
            onnx.checker.ValidationError: If the model is invalid.
        """
        model = onnx.load(path)  # type: ignore
        onnx.checker.check_model(model)  # type: ignore
        print(f"  ✓ {os.path.basename(path)} is valid")
