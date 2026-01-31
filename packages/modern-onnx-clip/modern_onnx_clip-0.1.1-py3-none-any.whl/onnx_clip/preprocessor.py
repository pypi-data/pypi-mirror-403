import numpy as np
from PIL import Image


class Preprocessor:
    """Handles image preprocessing for CLIP models to prepare them for ONNX inference.

    This class replicates the standard CLIP preprocessing pipeline:
    Resize (bicubic) -> Center Crop -> Normalize.
    It operates using Pillow and NumPy, avoiding any dependency on torchvision.

    Attributes:
        size (int): The target size for the image (height and width).
        mean (np.ndarray): Normalization mean (RGB).
        std (np.ndarray): Normalization standard deviation (RGB).
    """

    def __init__(self, size: int = 224):
        """Initializes the preprocessor.

        Args:
            size (int, optional): The target output resolution. Defaults to 224.
        """
        self.size = size
        # CLIP mean and std constants
        self.mean = np.array([0.48145466, 0.4578275, 0.40821073], dtype=np.float32)
        self.std = np.array([0.26862954, 0.26130258, 0.27577711], dtype=np.float32)

    def _resize_and_center_crop(self, image: Image.Image) -> Image.Image:
        """Resizes the image preserving aspect ratio and performs a center crop.

        Args:
            image (Image.Image): The input PIL image.

        Returns:
            Image.Image: The transformed PIL image of size (self.size, self.size).
        """
        w, h = image.size

        # Resize logic: scale shorter side to self.size
        if w < h:
            new_w = self.size
            new_h = int(h * (self.size / w))
        else:
            new_h = self.size
            new_w = int(w * (self.size / h))

        # Standard CLIP uses BICUBIC interpolation
        image = image.resize((new_w, new_h), resample=Image.Resampling.BICUBIC)

        # Center crop
        left = (new_w - self.size) // 2
        top = (new_h - self.size) // 2
        right = left + self.size
        bottom = top + self.size

        return image.crop((left, top, right, bottom))

    def __call__(self, images: Image.Image | list[Image.Image]) -> np.ndarray:
        """Processes a single image or a list of images into a batch tensor.

        Args:
            images (Union[Image.Image, List[Image.Image]]): Single or list of images.

        Returns:
            np.ndarray: A numpy array of shape (N, 3, H, W) ready for ONNX inference.
                        Data type is float32, normalized.
        """
        if isinstance(images, Image.Image):
            images = [images]

        processed_images = []
        for img in images:
            # Ensure RGB
            if img.mode != "RGB":
                img = img.convert("RGB")

            img = self._resize_and_center_crop(img)

            # Convert to numpy and normalize
            img_np = np.array(img).astype(np.float32) / 255.0
            img_np = (img_np - self.mean) / self.std

            # CHW format (Channels, Height, Width) for ONNX/Torch
            img_np = img_np.transpose(2, 0, 1)
            processed_images.append(img_np)

        return np.stack(processed_images)
