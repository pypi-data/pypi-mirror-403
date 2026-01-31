"""
Diffusion Model
===============

Core diffusion model implementation.
"""

import numpy as np
from typing import Optional, Tuple
from ..tensor import Tensor
from ..layers import Module
from .unet import UNet


class DiffusionScheduler:
    """
    Diffusion noise schedule.
    
    Manages noise levels and sampling schedule.
    """
    
    def __init__(
        self,
        num_timesteps: int = 1000,
        beta_start: float = 0.0001,
        beta_end: float = 0.02,
        schedule: str = "linear"
    ):
        self.num_timesteps = num_timesteps
        
        # Compute betas
        if schedule == "linear":
            self.betas = np.linspace(beta_start, beta_end, num_timesteps)
        elif schedule == "cosine":
            # Cosine schedule
            s = 0.008
            steps = np.arange(num_timesteps + 1)
            alphas_cumprod = np.cos(((steps / num_timesteps) + s) / (1 + s) * np.pi / 2) ** 2
            alphas_cumprod = alphas_cumprod / alphas_cumprod[0]
            betas = 1 - (alphas_cumprod[1:] / alphas_cumprod[:-1])
            self.betas = np.clip(betas, 0.0001, 0.9999)
        else:
            raise ValueError(f"Unknown schedule: {schedule}")
        
        # Precompute alphas
        self.alphas = 1.0 - self.betas
        self.alphas_cumprod = np.cumprod(self.alphas)
        self.alphas_cumprod_prev = np.concatenate([[1.0], self.alphas_cumprod[:-1]])
        
        # Precompute for sampling
        self.sqrt_alphas_cumprod = np.sqrt(self.alphas_cumprod)
        self.sqrt_one_minus_alphas_cumprod = np.sqrt(1.0 - self.alphas_cumprod)
        
        # For posterior sampling
        self.posterior_variance = (
            self.betas * (1.0 - self.alphas_cumprod_prev) / (1.0 - self.alphas_cumprod)
        )
    
    def add_noise(self, x: Tensor, t: np.ndarray) -> Tuple[Tensor, Tensor]:
        """
        Add noise to image at timestep t.
        
        Returns:
            (noisy_image, noise)
        """
        sqrt_alphas_cumprod_t = self.sqrt_alphas_cumprod[t]
        sqrt_one_minus_alphas_cumprod_t = self.sqrt_one_minus_alphas_cumprod[t]
        
        # Sample noise
        noise = Tensor(np.random.normal(0, 1, x.shape))
        
        # Add noise
        noisy_x = (
            sqrt_alphas_cumprod_t.reshape(-1, 1, 1, 1) * x.data +
            sqrt_one_minus_alphas_cumprod_t.reshape(-1, 1, 1, 1) * noise.data
        )
        
        return Tensor(noisy_x), noise
    
    def sample_timesteps(self, batch_size: int) -> np.ndarray:
        """Sample random timesteps."""
        return np.random.randint(0, self.num_timesteps, size=(batch_size,))


class DiffusionModel(Module):
    """
    Diffusion model for image generation.
    
    Core: Noise → Denoise → Image
    """
    
    def __init__(
        self,
        unet: Optional[UNet] = None,
        image_size: int = 256,
        in_channels: int = 3,
        num_timesteps: int = 1000
    ):
        super().__init__()
        self.image_size = image_size
        self.in_channels = in_channels
        self.num_timesteps = num_timesteps
        
        # UNet backbone
        self.unet = unet or UNet(
            in_channels=in_channels,
            out_channels=in_channels
        )
        
        # Diffusion scheduler
        self.scheduler = DiffusionScheduler(num_timesteps=num_timesteps)
    
    def forward(self, x: Tensor, timestep: Tensor) -> Tensor:
        """
        Predict noise in noisy image.
        
        Args:
            x: Noisy image
            timestep: Diffusion timestep
            
        Returns:
            Predicted noise
        """
        return self.unet(x, timestep)
    
    def sample(
        self,
        batch_size: int = 1,
        num_inference_steps: int = 50,
        guidance_scale: float = 1.0
    ) -> Tensor:
        """
        Generate image by denoising.
        
        Args:
            batch_size: Number of images to generate
            num_inference_steps: Number of denoising steps
            guidance_scale: Classifier-free guidance scale
            
        Returns:
            Generated images
        """
        # Start from pure noise
        shape = (batch_size, self.in_channels, self.image_size, self.image_size)
        x = Tensor(np.random.normal(0, 1, shape))
        
        # Denoising loop
        timesteps = np.linspace(self.num_timesteps - 1, 0, num_inference_steps).astype(int)
        
        for i, t in enumerate(timesteps):
            # Predict noise
            t_tensor = Tensor(np.array([[t]] * batch_size))
            noise_pred = self.forward(x, t_tensor)
            
            # Compute coefficients
            alpha_t = self.scheduler.alphas_cumprod[t]
            alpha_t_prev = self.scheduler.alphas_cumprod_prev[t] if t > 0 else 1.0
            beta_t = self.scheduler.betas[t]
            
            # Predict x0
            pred_x0 = (x.data - np.sqrt(1 - alpha_t) * noise_pred.data) / np.sqrt(alpha_t)
            
            # Compute direction
            pred_dir = np.sqrt(1 - alpha_t_prev) * noise_pred.data
            
            # Compute variance
            pred_variance = self.scheduler.posterior_variance[t]
            
            # Sample
            if i < len(timesteps) - 1:
                noise = np.random.normal(0, 1, x.shape)
                x = Tensor(
                    np.sqrt(alpha_t_prev) * pred_x0 +
                    pred_dir +
                    np.sqrt(pred_variance) * noise
                )
            else:
                x = Tensor(np.sqrt(alpha_t_prev) * pred_x0 + pred_dir)
        
        return x
