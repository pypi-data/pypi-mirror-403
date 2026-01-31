"""
NAPLY Image Generation (Diffusion Models)
==========================================

Build diffusion models for image generation from scratch.

Core Pipeline:
    Noise → Denoise → Image

Example:
    from naply.image import ImageTrainer
    
    trainer = ImageTrainer(
        dataset="anime_faces/",
        image_size=256
    )
    trainer.train(steps=50000)
    trainer.save("anime_model.pt")
"""

from .trainer import ImageTrainer
from .inference import ImageInference, generate_image, generate_images
from .vae import VAE, VariationalAutoencoder
from .unet import UNet, DiffusionUNet
from .diffusion import DiffusionModel, DiffusionScheduler
from .dataset import ImageDataset, ImageDataLoader

__all__ = [
    'ImageTrainer',
    'ImageInference',
    'generate_image',
    'generate_images',
    'VAE',
    'VariationalAutoencoder',
    'UNet',
    'DiffusionUNet',
    'DiffusionModel',
    'DiffusionScheduler',
    'ImageDataset',
    'ImageDataLoader',
]
