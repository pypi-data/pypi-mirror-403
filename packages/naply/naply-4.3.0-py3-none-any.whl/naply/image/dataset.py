"""
Image Dataset
=============

Dataset loading and preprocessing for image models.
"""

import os
import numpy as np
from typing import List, Tuple, Optional
from pathlib import Path
from PIL import Image
from ..tensor import Tensor


class ImageDataset:
    """
    Dataset for image training.
    
    Loads images and preprocesses them for diffusion models.
    """
    
    def __init__(
        self,
        data_path: str,
        image_size: int = 256,
        channels: int = 3
    ):
        self.data_path = Path(data_path)
        self.image_size = image_size
        self.channels = channels
        
        # Load image files
        self.image_files = self._load_image_files()
        
        if len(self.image_files) == 0:
            raise ValueError(f"No image files found in {data_path}")
        
        print(f"Loaded {len(self.image_files)} images")
    
    def _load_image_files(self) -> List[str]:
        """Load all image files from directory."""
        image_files = []
        
        # Supported formats
        extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.webp']
        
        for ext in extensions:
            for file_path in self.data_path.rglob(f'*{ext}'):
                image_files.append(str(file_path))
        
        return image_files
    
    def _load_image(self, path: str) -> np.ndarray:
        """Load and preprocess image."""
        # Load image
        img = Image.open(path).convert('RGB')
        
        # Resize
        img = img.resize((self.image_size, self.image_size), Image.LANCZOS)
        
        # Convert to numpy array
        img_array = np.array(img, dtype=np.float32)
        
        # Normalize to [-1, 1]
        img_array = (img_array / 127.5) - 1.0
        
        # Transpose to (C, H, W)
        img_array = np.transpose(img_array, (2, 0, 1))
        
        return img_array
    
    def __len__(self) -> int:
        return len(self.image_files)
    
    def __getitem__(self, idx: int) -> Tensor:
        """Get a sample."""
        image_path = self.image_files[idx]
        image = self._load_image(image_path)
        return Tensor(image)


class ImageDataLoader:
    """
    Data loader for image datasets.
    """
    
    def __init__(
        self,
        dataset: ImageDataset,
        batch_size: int = 4,
        shuffle: bool = True
    ):
        self.dataset = dataset
        self.batch_size = batch_size
        self.shuffle = shuffle
        self.indices = list(range(len(dataset)))
    
    def __len__(self) -> int:
        return (len(self.dataset) + self.batch_size - 1) // self.batch_size
    
    def __iter__(self):
        """Iterate over batches."""
        if self.shuffle:
            np.random.shuffle(self.indices)
        
        for i in range(0, len(self.indices), self.batch_size):
            batch_indices = self.indices[i:i + self.batch_size]
            batch = [self.dataset[idx] for idx in batch_indices]
            
            # Stack
            batch_tensor = Tensor(np.stack([img.data for img in batch]))
            
            # For diffusion training, input = target (we'll add noise in trainer)
            yield batch_tensor, batch_tensor
