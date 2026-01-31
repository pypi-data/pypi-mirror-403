import argparse
import os
import sys


def convert_command(args: argparse.Namespace):
    """Executes the model conversion command.

    Args:
        args (argparse.Namespace): Parsed CLI arguments.
    """
    try:
        from .exporter import Exporter
    except ImportError:
        print("Error: Export dependencies not installed. Run `pip install .[export]` or `uv pip install .[export]`")
        sys.exit(1)

    print(f"Converting {args.model} ({args.pretrained}) to ONNX...")
    exporter = Exporter(
        model_name=args.model,
        pretrained=args.pretrained,
        output_dir=args.output,
        opset=args.opset,
    )
    exporter.export()


def run_command(args: argparse.Namespace):
    """Executes the inference test command.

    Args:
        args (argparse.Namespace): Parsed CLI arguments.
    """
    from PIL import Image

    from .model import OnnxClip

    if not os.path.exists(args.model_dir):
        print(f"Error: Model directory '{args.model_dir}' does not exist.")
        sys.exit(1)

    model = OnnxClip(model_dir=args.model_dir, device="cpu")

    img = None
    if args.image:
        if not os.path.exists(args.image):
            print(f"Error: Image '{args.image}' not found.")
            sys.exit(1)
        img = Image.open(args.image)
        emb = model.get_image_embedding(img)
        print("Image Embedding Shape:", emb.shape)
        print("First 5 values:", emb[0, :5])

    if args.text:
        emb = model.get_text_embedding([args.text])
        print("Text Embedding Shape:", emb.shape)
        print("First 5 values:", emb[0, :5])

    if img and args.text:
        img_emb = model.get_image_embedding(img)
        txt_emb = model.get_text_embedding([args.text])
        score = (img_emb @ txt_emb.T)[0][0]
        print(f"Similarity score: {score:.4f}")


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(description="Modern ONNX CLIP CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Convert
    convert_parser = subparsers.add_parser("convert", help="Convert OpenCLIP model to ONNX")
    convert_parser.add_argument("--model", type=str, default="ViT-B-32", help="Model architecture")
    convert_parser.add_argument(
        "--pretrained",
        type=str,
        default="laion2b_s34b_b79k",
        help="Pretrained weights tag",
    )
    convert_parser.add_argument("--output", type=str, required=True, help="Output directory")
    convert_parser.add_argument("--opset", type=int, default=14, help="ONNX Opset version")
    convert_parser.set_defaults(func=convert_command)

    # Run
    run_parser = subparsers.add_parser("run", help="Run inference")
    run_parser.add_argument("--model-dir", type=str, required=True, help="Path to model directory")
    run_parser.add_argument("--image", type=str, help="Path to image file")
    run_parser.add_argument("--text", type=str, help="Text query")
    run_parser.set_defaults(func=run_command)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
