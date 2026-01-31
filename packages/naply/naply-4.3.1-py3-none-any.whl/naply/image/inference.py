"""
Image Inference
===============

Generate images using trained diffusion models.
"""

import numpy as np
from typing import Optional, List
from pathlib import Path
from PIL import Image

from .diffusion import DiffusionModel
from ..tensor import Tensor


class ImageInference:
    """
    Image inference for generation.
    """
    
    def __init__(
        self,
        model: Optional[DiffusionModel] = None,
        model_path: Optional[str] = None
    ):
        if model:
            self.model = model
        elif model_path:
            self.model = self._load_model(model_path)
        else:
            raise ValueError("Must provide either model or model_path")
    
    def _load_model(self, path: str) -> DiffusionModel:
        """Load model from path."""
        import json
        import pickle
        
        # Load config
        config_path = Path(path) / "config.json"
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Create model
        model = DiffusionModel(
            image_size=config['image_size'],
            in_channels=config['in_channels'],
            num_timesteps=config['num_timesteps']
        )
        
        # Load weights
        weights_path = Path(path) / "model.pkl"
        with open(weights_path, 'rb') as f:
            state_dict = pickle.load(f)
        model.load_state_dict(state_dict)
        
        return model
    
    def generate(
        self,
        batch_size: int = 1,
        num_inference_steps: int = 50,
        guidance_scale: float = 1.0
    ) -> np.ndarray:
        """
        Generate images.
        
        Args:
            batch_size: Number of images to generate
            num_inference_steps: Number of denoising steps
            guidance_scale: Classifier-free guidance scale
            
        Returns:
            Generated images as numpy arrays (batch, C, H, W)
        """
        # Generate
        images = self.model.sample(
            batch_size=batch_size,
            num_inference_steps=num_inference_steps,
            guidance_scale=guidance_scale
        )
        
        # Convert to numpy and denormalize
        images_np = images.data
        images_np = (images_np + 1.0) / 2.0  # [-1, 1] -> [0, 1]
        images_np = np.clip(images_np, 0.0, 1.0)
        images_np = (images_np * 255).astype(np.uint8)
        
        return images_np
    
    def save_image(self, image: np.ndarray, path: str):
        """Save image to file."""
        # Convert from (C, H, W) to (H, W, C)
        if image.shape[0] == 3:
            image = np.transpose(image, (1, 2, 0))
        
        # Convert to PIL and save
        img = Image.fromarray(image)
        img.save(path)
    
    def save_images(self, images: np.ndarray, output_dir: str, prefix: str = "image"):
        """Save multiple images."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        for i, image in enumerate(images):
            path = output_path / f"{prefix}_{i:04d}.png"
            self.save_image(image, str(path))


def generate_image(
    model_path: str,
    output_path: str,
    num_inference_steps: int = 50
) -> np.ndarray:
    """
    Quick image generation function.
    
    Args:
        model_path: Path to trained model
        output_path: Path to save generated image
        num_inference_steps: Number of denoising steps
        
    Returns:
        Generated image
    """
    inference = ImageInference(model_path=model_path)
    image = inference.generate(batch_size=1, num_inference_steps=num_inference_steps)
    inference.save_image(image[0], output_path)
    return image[0]


def generate_images(
    model_path: str,
    output_dir: str,
    num_images: int = 4,
    num_inference_steps: int = 50
) -> List[np.ndarray]:
    """
    Generate multiple images.
    
    Args:
        model_path: Path to trained model
        output_dir: Directory to save images
        num_images: Number of images to generate
        num_inference_steps: Number of denoising steps
        
    Returns:
        List of generated images
    """
    inference = ImageInference(model_path=model_path)
    images = inference.generate(batch_size=num_images, num_inference_steps=num_inference_steps)
    inference.save_images(images, output_dir)
    return [images[i] for i in range(num_images)]
