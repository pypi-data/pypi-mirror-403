"""
NAPLY Utilities
===============

Utility functions for training, checkpointing, and model management.
"""

import os
import json
import time
import pickle
import hashlib
import numpy as np
from typing import Dict, List, Optional, Any, Callable
from .tensor import Tensor
from .layers import Module


# =============================================================================
# Checkpointing
# =============================================================================

class Checkpoint:
    """
    Model checkpointing for saving and resuming training.
    
    Example:
        ckpt = Checkpoint("checkpoints/")
        ckpt.save(model, optimizer, epoch=5, loss=0.5)
        model, optimizer, metadata = ckpt.load_latest()
    """
    
    def __init__(self, save_dir: str, max_checkpoints: int = 5):
        self.save_dir = save_dir
        self.max_checkpoints = max_checkpoints
        os.makedirs(save_dir, exist_ok=True)
    
    def save(
        self, 
        model: Module, 
        optimizer=None, 
        epoch: int = 0,
        step: int = 0,
        loss: float = 0.0,
        **metadata
    ):
        """Save a checkpoint."""
        timestamp = int(time.time())
        filename = f"checkpoint_epoch{epoch}_step{step}_{timestamp}.pkl"
        filepath = os.path.join(self.save_dir, filename)
        
        checkpoint = {
            'model_state': model.state_dict(),
            'epoch': epoch,
            'step': step,
            'loss': loss,
            'timestamp': timestamp,
            **metadata
        }
        
        if optimizer:
            checkpoint['optimizer_state'] = {
                'lr': optimizer.lr,
                't': optimizer.t,
            }
        
        with open(filepath, 'wb') as f:
            pickle.dump(checkpoint, f)
        
        # Save metadata for quick lookup
        meta_path = os.path.join(self.save_dir, "checkpoints.json")
        try:
            with open(meta_path, 'r') as f:
                meta = json.load(f)
        except:
            meta = {'checkpoints': []}
        
        meta['checkpoints'].append({
            'filename': filename,
            'epoch': epoch,
            'step': step,
            'loss': loss,
            'timestamp': timestamp
        })
        meta['latest'] = filename
        
        with open(meta_path, 'w') as f:
            json.dump(meta, f, indent=2)
        
        # Cleanup old checkpoints
        self._cleanup()
        
        print(f"💾 Saved checkpoint: {filename}")
    
    def load_latest(self, model: Module, optimizer=None) -> Dict:
        """Load the latest checkpoint."""
        meta_path = os.path.join(self.save_dir, "checkpoints.json")
        
        if not os.path.exists(meta_path):
            raise FileNotFoundError("No checkpoints found")
        
        with open(meta_path, 'r') as f:
            meta = json.load(f)
        
        return self.load(meta['latest'], model, optimizer)
    
    def load(self, filename: str, model: Module, optimizer=None) -> Dict:
        """Load a specific checkpoint."""
        filepath = os.path.join(self.save_dir, filename)
        
        with open(filepath, 'rb') as f:
            checkpoint = pickle.load(f)
        
        model.load_state_dict(checkpoint['model_state'])
        
        if optimizer and 'optimizer_state' in checkpoint:
            optimizer.lr = checkpoint['optimizer_state']['lr']
            optimizer.t = checkpoint['optimizer_state']['t']
        
        print(f"📂 Loaded checkpoint: {filename}")
        
        return {
            'epoch': checkpoint['epoch'],
            'step': checkpoint['step'],
            'loss': checkpoint['loss'],
        }
    
    def _cleanup(self):
        """Remove old checkpoints."""
        meta_path = os.path.join(self.save_dir, "checkpoints.json")
        
        try:
            with open(meta_path, 'r') as f:
                meta = json.load(f)
        except:
            return
        
        checkpoints = meta['checkpoints']
        
        if len(checkpoints) > self.max_checkpoints:
            # Sort by timestamp and remove oldest
            checkpoints.sort(key=lambda x: x['timestamp'])
            to_remove = checkpoints[:-self.max_checkpoints]
            
            for ckpt in to_remove:
                filepath = os.path.join(self.save_dir, ckpt['filename'])
                if os.path.exists(filepath):
                    os.remove(filepath)
            
            meta['checkpoints'] = checkpoints[-self.max_checkpoints:]
            
            with open(meta_path, 'w') as f:
                json.dump(meta, f, indent=2)


# =============================================================================
# Progress Tracking
# =============================================================================

class ProgressTracker:
    """
    Track training progress with metrics and logging.
    """
    
    def __init__(self, log_dir: Optional[str] = None):
        self.log_dir = log_dir
        self.metrics = {}
        self.start_time = None
        
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
    
    def start(self):
        """Start tracking."""
        self.start_time = time.time()
        self.metrics = {'loss': [], 'lr': [], 'steps': [], 'time': []}
    
    def log(self, step: int, **kwargs):
        """Log metrics for a step."""
        elapsed = time.time() - self.start_time if self.start_time else 0
        
        self.metrics['steps'].append(step)
        self.metrics['time'].append(elapsed)
        
        for key, value in kwargs.items():
            if key not in self.metrics:
                self.metrics[key] = []
            self.metrics[key].append(value)
    
    def summary(self) -> str:
        """Get training summary."""
        if not self.metrics.get('loss'):
            return "No training data recorded"
        
        final_loss = self.metrics['loss'][-1]
        best_loss = min(self.metrics['loss'])
        total_time = self.metrics['time'][-1] if self.metrics['time'] else 0
        total_steps = len(self.metrics['steps'])
        
        return (
            f"Training Summary\n"
            f"================\n"
            f"Total Steps: {total_steps}\n"
            f"Final Loss:  {final_loss:.4f}\n"
            f"Best Loss:   {best_loss:.4f}\n"
            f"Total Time:  {total_time:.1f}s\n"
        )
    
    def save(self, path: str):
        """Save metrics to file."""
        with open(path, 'w') as f:
            json.dump(self.metrics, f, indent=2)


# =============================================================================
# Early Stopping
# =============================================================================

class EarlyStopping:
    """
    Early stopping to prevent overfitting.
    
    Example:
        stopper = EarlyStopping(patience=5)
        for epoch in range(100):
            loss = train_epoch()
            if stopper.should_stop(loss):
                break
    """
    
    def __init__(
        self, 
        patience: int = 5, 
        min_delta: float = 0.001,
        mode: str = 'min'
    ):
        self.patience = patience
        self.min_delta = min_delta
        self.mode = mode
        self.counter = 0
        self.best_score = None
        self.should_stop_flag = False
    
    def should_stop(self, score: float) -> bool:
        """Check if training should stop."""
        if self.best_score is None:
            self.best_score = score
            return False
        
        if self.mode == 'min':
            improved = score < self.best_score - self.min_delta
        else:
            improved = score > self.best_score + self.min_delta
        
        if improved:
            self.best_score = score
            self.counter = 0
        else:
            self.counter += 1
            if self.counter >= self.patience:
                self.should_stop_flag = True
                return True
        
        return False
    
    def reset(self):
        """Reset the stopper."""
        self.counter = 0
        self.best_score = None
        self.should_stop_flag = False


# =============================================================================
# Model Analysis
# =============================================================================

def count_parameters(model: Module) -> Dict[str, int]:
    """
    Count parameters in a model.
    
    Returns:
        Dict with total, trainable, and frozen parameter counts
    """
    total = 0
    trainable = 0
    
    for p in model.parameters():
        n = np.prod(p.shape)
        total += n
        if p.requires_grad:
            trainable += n
    
    return {
        'total': total,
        'trainable': trainable,
        'frozen': total - trainable,
        'total_mb': total * 4 / (1024 * 1024),  # Assuming float32
    }


def model_summary(model: Module, input_shape: tuple = None) -> str:
    """
    Generate a summary of the model architecture.
    
    Args:
        model: Model to summarize
        input_shape: Optional input shape for memory estimation
        
    Returns:
        String summary
    """
    params = count_parameters(model)
    
    lines = [
        "=" * 60,
        f"{'Layer':<30} {'Shape':<20} {'Params':>10}",
        "=" * 60,
    ]
    
    for name, p in model.named_parameters():
        shape_str = str(p.shape)
        param_count = np.prod(p.shape)
        lines.append(f"{name:<30} {shape_str:<20} {param_count:>10,}")
    
    lines.extend([
        "=" * 60,
        f"Total Parameters:     {params['total']:,}",
        f"Trainable Parameters: {params['trainable']:,}",
        f"Memory (float32):     {params['total_mb']:.2f} MB",
        "=" * 60,
    ])
    
    return "\n".join(lines)


# =============================================================================
# Reproducibility
# =============================================================================

def set_seed(seed: int):
    """
    Set random seed for reproducibility.
    
    Args:
        seed: Random seed value
    """
    np.random.seed(seed)
    # Note: Add more RNG seeds as needed


def get_reproducibility_info() -> Dict:
    """Get info for reproducibility."""
    import sys
    return {
        'python_version': sys.version,
        'numpy_version': np.__version__,
        'naply_version': '1.0.0',
    }


# =============================================================================
# Memory Management
# =============================================================================

def estimate_memory(
    vocab_size: int,
    n_layer: int,
    n_head: int,
    n_embd: int,
    batch_size: int = 1,
    seq_length: int = 512
) -> Dict[str, float]:
    """
    Estimate memory requirements for a model.
    
    Returns:
        Dict with memory estimates in MB
    """
    # Parameter count estimation
    embed_params = vocab_size * n_embd * 2  # Token + position
    layer_params = n_layer * (12 * n_embd ** 2 + 4 * n_embd)  # Attention + FFN
    total_params = embed_params + layer_params
    
    # Memory for parameters (float32)
    param_memory = total_params * 4 / (1024 * 1024)
    
    # Memory for gradients (same as params)
    grad_memory = param_memory
    
    # Memory for optimizer states (Adam: 2x for m and v)
    optim_memory = param_memory * 2
    
    # Activation memory (rough estimate)
    activation_memory = batch_size * seq_length * n_embd * n_layer * 4 / (1024 * 1024)
    
    return {
        'parameters_mb': param_memory,
        'gradients_mb': grad_memory,
        'optimizer_mb': optim_memory,
        'activations_mb': activation_memory,
        'total_mb': param_memory + grad_memory + optim_memory + activation_memory,
    }


# =============================================================================
# Data Utilities
# =============================================================================

def split_data(data: List, train_ratio: float = 0.9, shuffle: bool = True):
    """
    Split data into train and validation sets.
    
    Args:
        data: List of data items
        train_ratio: Fraction for training
        shuffle: Whether to shuffle before splitting
        
    Returns:
        (train_data, val_data)
    """
    if shuffle:
        indices = np.random.permutation(len(data))
        data = [data[i] for i in indices]
    
    split_idx = int(len(data) * train_ratio)
    return data[:split_idx], data[split_idx:]


def batch_iterator(data: List, batch_size: int, shuffle: bool = True):
    """
    Iterate over data in batches.
    
    Args:
        data: List of data items
        batch_size: Batch size
        shuffle: Whether to shuffle
        
    Yields:
        Batches of data
    """
    indices = list(range(len(data)))
    if shuffle:
        np.random.shuffle(indices)
    
    for i in range(0, len(indices), batch_size):
        batch_indices = indices[i:i + batch_size]
        yield [data[j] for j in batch_indices]
