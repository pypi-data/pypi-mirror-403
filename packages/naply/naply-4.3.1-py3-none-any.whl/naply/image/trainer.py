"""
Image Trainer
=============

High-level API for training image generation models.
"""

import os
from typing import Optional, Dict
from pathlib import Path

from ..trainer import UnifiedTrainer
from ..optim import AdamW, CosineScheduler
from ..functional import mse_loss
from .diffusion import DiffusionModel, DiffusionScheduler
from .dataset import ImageDataset, ImageDataLoader
from ..tensor import Tensor
import numpy as np


class ImageTrainer:
    """
    Image trainer for building diffusion models.
    
    Example:
        trainer = ImageTrainer(
            dataset="anime_faces/",
            image_size=256
        )
        trainer.train(steps=50000)
        trainer.save("anime_model.pt")
    """
    
    def __init__(
        self,
        dataset: str,
        image_size: int = 256,
        in_channels: int = 3,
        num_timesteps: int = 1000,
        checkpoint_dir: Optional[str] = None,
        log_dir: Optional[str] = None
    ):
        self.dataset_path = dataset
        self.image_size = image_size
        self.in_channels = in_channels
        self.num_timesteps = num_timesteps
        
        # Initialize components
        print("🖼️ Initializing Image Trainer...")
        
        # Load dataset
        self.dataset = ImageDataset(
            data_path=dataset,
            image_size=image_size,
            channels=in_channels
        )
        
        print(f"   Loaded {len(self.dataset)} images")
        
        # Build diffusion model
        self.model = DiffusionModel(
            image_size=image_size,
            in_channels=in_channels,
            num_timesteps=num_timesteps
        )
        
        # Diffusion scheduler
        self.scheduler = DiffusionScheduler(num_timesteps=num_timesteps)
        
        # Setup trainer
        checkpoint_dir = checkpoint_dir or os.path.join(dataset, "checkpoints")
        self.trainer = UnifiedTrainer(
            model=self.model,
            checkpoint_dir=checkpoint_dir,
            log_dir=log_dir,
            learning_rate=1e-4
        )
        
        print("✅ Image Trainer initialized!")
    
    def train(
        self,
        steps: int = 50000,
        batch_size: int = 4,
        learning_rate: float = 1e-4,
        **kwargs
    ) -> Dict:
        """
        Train the diffusion model.
        
        Args:
            steps: Number of training steps
            batch_size: Batch size
            learning_rate: Learning rate
        """
        print(f"\n🎨 Training Diffusion Model")
        print(f"   Steps: {steps}")
        print(f"   Batch Size: {batch_size}")
        print(f"   Learning Rate: {learning_rate}\n")
        
        # Create data loader
        dataloader = ImageDataLoader(
            self.dataset,
            batch_size=batch_size,
            shuffle=True
        )
        
        # Override forward pass for diffusion
        original_forward = self.trainer._forward_pass
        
        def diffusion_forward(x: Tensor, y: Tensor) -> Tensor:
            """Diffusion forward pass with noise."""
            # Sample timesteps
            batch_size = x.shape[0]
            t = self.scheduler.sample_timesteps(batch_size)
            
            # Add noise
            noisy_x, noise = self.scheduler.add_noise(x, t)
            
            # Predict noise
            t_tensor = Tensor(t.reshape(-1, 1).astype(np.float32))
            noise_pred = self.model(noisy_x, t_tensor)
            
            # Compute loss
            return mse_loss(noise_pred, noise)
        
        self.trainer._forward_pass = diffusion_forward
        
        # Compute epochs from steps
        steps_per_epoch = len(dataloader)
        epochs = (steps + steps_per_epoch - 1) // steps_per_epoch
        
        # Train
        history = self.trainer.train(
            train_dataloader=dataloader,
            epochs=epochs,
            learning_rate=learning_rate,
            **kwargs
        )
        
        print("\n✅ Training complete!")
        return history
    
    def save(self, path: str):
        """Save trained model."""
        save_path = Path(path)
        save_path.mkdir(parents=True, exist_ok=True)
        
        # Save model
        import pickle
        with open(save_path / "model.pkl", 'wb') as f:
            pickle.dump(self.model.state_dict(), f)
        
        # Config
        config = {
            'image_size': self.image_size,
            'in_channels': self.in_channels,
            'num_timesteps': self.num_timesteps
        }
        import json
        with open(save_path / "config.json", 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"✅ Model saved to {path}")
    
    @classmethod
    def load(cls, path: str) -> 'ImageTrainer':
        """Load trained model."""
        # Implementation for loading
        raise NotImplementedError("Loading not yet implemented")
