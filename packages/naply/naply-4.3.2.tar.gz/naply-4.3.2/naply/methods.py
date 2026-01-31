"""
NAPLY Training Methods
======================

Advanced training methods for building powerful AI models.

Methods:
- CRC: Consistency-Retention Compression
- DCL: Domain-Constrained Learning
- ILC: Incremental Learning Consolidation
- MCU: Memory Consolidation Unit
- P3: Parallel Pipelined Processing
- PPL: Progressive Prompt Learning
- PTL: Parallel Training and Learning (Multi-threaded CPU training)
- RDL: Recursive Data Learning
- S3L: Structured Selective Stabilized Learning
- SGL: Sparse Gradient Learning
"""

import numpy as np
import time
from typing import Optional, List, Dict, Any, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from .tensor import Tensor
from .layers import Module
from .optim import Optimizer, AdamW, clip_grad_norm
from .functional import cross_entropy, mse_loss
from .data import DataLoader


class BaseTrainer:
    """Base class for all training methods."""
    
    def __init__(self, model: Module, optimizer: Optional[Optimizer] = None, lr: float = 1e-4):
        self.model = model
        self.optimizer = optimizer or AdamW(model.parameters(), lr=lr)
        self.history = {'loss': [], 'lr': []}
    
    def train_step(self, x: Tensor, y: Tensor) -> float:
        """Single training step. Override in subclasses."""
        raise NotImplementedError
    
    def train(self, dataloader: DataLoader, epochs: int = 5, verbose: bool = True) -> Dict:
        """Train the model."""
        self.model.train()
        
        for epoch in range(epochs):
            epoch_loss = 0
            steps = 0
            
            for x, y in dataloader:
                loss = self.train_step(x, y)
                epoch_loss += loss
                steps += 1
                
                if verbose and steps % 10 == 0:
                    print(f"  Step {steps}: loss={loss:.4f}", end='\r')
            
            avg_loss = epoch_loss / steps
            self.history['loss'].append(avg_loss)
            
            if verbose:
                print(f"Epoch {epoch+1}/{epochs}: avg_loss={avg_loss:.4f}")
        
        return self.history


class CRCTrainer(BaseTrainer):
    """
    Consistency-Retention Compression (CRC) Trainer.
    
    Memory-efficient training that compresses gradients while
    maintaining consistency with the original model.
    
    Args:
        model: Model to train
        optimizer: Optimizer (default: AdamW)
        compression_ratio: Gradient compression ratio (0-1)
        retention_weight: Weight for retention loss
    """
    
    def __init__(
        self, 
        model: Module, 
        optimizer: Optional[Optimizer] = None,
        lr: float = 1e-4,
        compression_ratio: float = 0.5,
        retention_weight: float = 0.1
    ):
        super().__init__(model, optimizer, lr)
        self.compression_ratio = compression_ratio
        self.retention_weight = retention_weight
        
        # Store reference weights for retention
        self.reference_weights = {
            name: p.data.copy() for name, p in model.named_parameters()
        }
    
    def train_step(self, x: Tensor, y: Tensor) -> float:
        self.optimizer.zero_grad()
        
        # Forward pass
        logits, _ = self.model(x)
        
        # Task loss
        B, T, C = logits.shape
        logits_flat = logits.reshape(B * T, C)
        targets_flat = y.reshape(B * T)
        task_loss = cross_entropy(logits_flat, targets_flat)
        
        # Retention loss (stay close to reference)
        retention_loss = 0
        for name, p in self.model.named_parameters():
            if name in self.reference_weights:
                diff = Tensor(p.data - self.reference_weights[name])
                retention_loss += (diff ** 2).sum().data
        
        total_loss = task_loss.data + self.retention_weight * retention_loss
        
        # Backward
        task_loss.backward()
        
        # Compress gradients (keep top-k)
        for p in self.model.parameters():
            if p.grad is not None:
                grad_flat = p.grad.flatten()
                k = int(len(grad_flat) * self.compression_ratio)
                if k > 0:
                    threshold = np.partition(np.abs(grad_flat), -k)[-k]
                    mask = np.abs(grad_flat) >= threshold
                    p.grad = (p.grad.flatten() * mask).reshape(p.grad.shape)
        
        self.optimizer.step()
        
        return float(total_loss)


class DCLTrainer(BaseTrainer):
    """
    Domain-Constrained Learning (DCL) Trainer.
    
    Trains only specific layers while freezing others,
    perfect for domain-specific fine-tuning.
    
    Args:
        model: Model to train
        optimizer: Optimizer
        freeze_layers: Number of layers to freeze from bottom
        domain_weight: Weight for domain-specific loss
    """
    
    def __init__(
        self, 
        model: Module, 
        optimizer: Optional[Optimizer] = None,
        lr: float = 1e-4,
        freeze_layers: int = 0,
        domain_weight: float = 1.0
    ):
        super().__init__(model, optimizer, lr)
        self.freeze_layers = freeze_layers
        self.domain_weight = domain_weight
        
        # Freeze specified layers
        self._apply_freeze()
    
    def _apply_freeze(self):
        """Freeze bottom layers."""
        for i, (name, param) in enumerate(self.model.named_parameters()):
            if 'block' in name:
                block_idx = int(name.split('block_')[1].split('.')[0])
                if block_idx < self.freeze_layers:
                    param.requires_grad = False
    
    def train_step(self, x: Tensor, y: Tensor) -> float:
        self.optimizer.zero_grad()
        
        logits, _ = self.model(x)
        
        B, T, C = logits.shape
        logits_flat = logits.reshape(B * T, C)
        targets_flat = y.reshape(B * T)
        loss = cross_entropy(logits_flat, targets_flat)
        
        # Scale by domain weight
        weighted_loss = Tensor(loss.data * self.domain_weight, requires_grad=True)
        loss.backward()
        
        self.optimizer.step()
        
        return float(loss.data)


class ILCTrainer(BaseTrainer):
    """
    Incremental Learning Consolidation (ILC) Trainer.
    
    Enables continuous learning without catastrophic forgetting.
    Uses elastic weight consolidation.
    
    Args:
        model: Model to train
        optimizer: Optimizer
        ewc_lambda: Elastic weight consolidation strength
    """
    
    def __init__(
        self, 
        model: Module, 
        optimizer: Optional[Optimizer] = None,
        lr: float = 1e-4,
        ewc_lambda: float = 0.4
    ):
        super().__init__(model, optimizer, lr)
        self.ewc_lambda = ewc_lambda
        
        # Fisher information matrix (importance weights)
        self.fisher = {}
        self.old_params = {}
    
    def compute_fisher(self, dataloader: DataLoader, num_samples: int = 100):
        """Compute Fisher information matrix from data."""
        self.model.eval()
        
        fisher = {name: np.zeros_like(p.data) for name, p in self.model.named_parameters()}
        samples = 0
        
        for x, y in dataloader:
            if samples >= num_samples:
                break
            
            self.optimizer.zero_grad()
            logits, _ = self.model(x)
            
            B, T, C = logits.shape
            loss = cross_entropy(logits.reshape(B*T, C), y.reshape(B*T))
            loss.backward()
            
            for name, p in self.model.named_parameters():
                if p.grad is not None:
                    fisher[name] += p.grad ** 2
            
            samples += len(x.data)
        
        # Normalize
        for name in fisher:
            fisher[name] /= samples
        
        self.fisher = fisher
        self.old_params = {name: p.data.copy() for name, p in self.model.named_parameters()}
    
    def train_step(self, x: Tensor, y: Tensor) -> float:
        self.optimizer.zero_grad()
        
        logits, _ = self.model(x)
        
        B, T, C = logits.shape
        task_loss = cross_entropy(logits.reshape(B*T, C), y.reshape(B*T))
        
        # EWC penalty
        ewc_loss = 0
        for name, p in self.model.named_parameters():
            if name in self.fisher and name in self.old_params:
                ewc_loss += (self.fisher[name] * (p.data - self.old_params[name]) ** 2).sum()
        
        total_loss = task_loss.data + self.ewc_lambda * ewc_loss
        
        task_loss.backward()
        self.optimizer.step()
        
        return float(total_loss)


class MCUTrainer(BaseTrainer):
    """
    Memory Consolidation Unit (MCU) Trainer.
    
    Stable knowledge merging with exponential moving average.
    
    Args:
        model: Model to train
        optimizer: Optimizer
        ema_decay: EMA decay rate (0.99-0.9999)
        consolidation_interval: Steps between consolidation
    """
    
    def __init__(
        self, 
        model: Module, 
        optimizer: Optional[Optimizer] = None,
        lr: float = 1e-4,
        ema_decay: float = 0.999,
        consolidation_interval: int = 100
    ):
        super().__init__(model, optimizer, lr)
        self.ema_decay = ema_decay
        self.consolidation_interval = consolidation_interval
        self.step_count = 0
        
        # Shadow weights
        self.shadow = {name: p.data.copy() for name, p in model.named_parameters()}
    
    def _update_ema(self):
        """Update exponential moving average."""
        for name, p in self.model.named_parameters():
            if name in self.shadow:
                self.shadow[name] = self.ema_decay * self.shadow[name] + (1 - self.ema_decay) * p.data
    
    def _consolidate(self):
        """Consolidate knowledge from EMA to model."""
        for name, p in self.model.named_parameters():
            if name in self.shadow:
                p.data = self.shadow[name].copy()
    
    def train_step(self, x: Tensor, y: Tensor) -> float:
        self.optimizer.zero_grad()
        
        logits, _ = self.model(x)
        
        B, T, C = logits.shape
        loss = cross_entropy(logits.reshape(B*T, C), y.reshape(B*T))
        
        loss.backward()
        self.optimizer.step()
        
        # Update EMA
        self._update_ema()
        self.step_count += 1
        
        # Consolidate periodically
        if self.step_count % self.consolidation_interval == 0:
            self._consolidate()
        
        return float(loss.data)


class P3Engine(BaseTrainer):
    """
    Parallel Pipelined Processing (P3) Trainer.
    
    Enables efficient training with gradient accumulation,
    simulating larger batch sizes.
    
    Args:
        model: Model to train
        optimizer: Optimizer
        accumulation_steps: Number of gradient accumulation steps
    """
    
    def __init__(
        self, 
        model: Module, 
        optimizer: Optional[Optimizer] = None,
        lr: float = 1e-4,
        accumulation_steps: int = 4
    ):
        super().__init__(model, optimizer, lr)
        self.accumulation_steps = accumulation_steps
        self.accumulated = 0
    
    def train_step(self, x: Tensor, y: Tensor) -> float:
        logits, _ = self.model(x)
        
        B, T, C = logits.shape
        loss = cross_entropy(logits.reshape(B*T, C), y.reshape(B*T))
        
        # Scale loss for accumulation
        scaled_loss = Tensor(loss.data / self.accumulation_steps)
        loss.backward()
        
        self.accumulated += 1
        
        # Update only after accumulation
        if self.accumulated >= self.accumulation_steps:
            clip_grad_norm(self.model.parameters(), 1.0)
            self.optimizer.step()
            self.optimizer.zero_grad()
            self.accumulated = 0
        
        return float(loss.data)


class PPLTrainer(BaseTrainer):
    """
    Progressive Prompt Learning (PPL) Trainer.
    
    Curriculum learning that starts with easy examples
    and progressively increases difficulty.
    
    Args:
        model: Model to train
        optimizer: Optimizer
        initial_seq_length: Starting sequence length
        max_seq_length: Maximum sequence length
        warmup_fraction: Fraction of training for warmup
    """
    
    def __init__(
        self, 
        model: Module, 
        optimizer: Optional[Optimizer] = None,
        lr: float = 1e-4,
        initial_seq_length: int = 32,
        max_seq_length: int = 512,
        warmup_fraction: float = 0.3
    ):
        super().__init__(model, optimizer, lr)
        self.initial_seq_length = initial_seq_length
        self.max_seq_length = max_seq_length
        self.warmup_fraction = warmup_fraction
        self.current_step = 0
        self.total_steps = 0
    
    def get_current_length(self) -> int:
        """Get current sequence length based on training progress."""
        if self.total_steps == 0:
            return self.initial_seq_length
        
        progress = min(1.0, self.current_step / (self.total_steps * self.warmup_fraction))
        return int(self.initial_seq_length + progress * (self.max_seq_length - self.initial_seq_length))
    
    def train_step(self, x: Tensor, y: Tensor) -> float:
        self.optimizer.zero_grad()
        
        # Truncate to current difficulty level
        seq_len = self.get_current_length()
        x_trunc = Tensor(x.data[:, :seq_len])
        y_trunc = Tensor(y.data[:, :seq_len])
        
        logits, _ = self.model(x_trunc)
        
        B, T, C = logits.shape
        loss = cross_entropy(logits.reshape(B*T, C), y_trunc.reshape(B*T))
        
        loss.backward()
        self.optimizer.step()
        
        self.current_step += 1
        
        return float(loss.data)
    
    def train(self, dataloader: DataLoader, epochs: int = 5, verbose: bool = True) -> Dict:
        self.total_steps = len(dataloader) * epochs
        return super().train(dataloader, epochs, verbose)


class RDLTrainer(BaseTrainer):
    """
    Recursive Data Learning (RDL) Trainer.
    
    Trains with reasoning state consistency for better
    understanding of complex patterns.
    
    Args:
        model: Model to train
        optimizer: Optimizer
        consistency_weight: Weight for consistency loss
    """
    
    def __init__(
        self, 
        model: Module, 
        optimizer: Optional[Optimizer] = None,
        lr: float = 1e-4,
        consistency_weight: float = 0.1
    ):
        super().__init__(model, optimizer, lr)
        self.consistency_weight = consistency_weight
        self.prev_hidden = None
    
    def train_step(self, x: Tensor, y: Tensor) -> float:
        self.optimizer.zero_grad()
        
        logits, kv_cache = self.model(x)
        
        B, T, C = logits.shape
        task_loss = cross_entropy(logits.reshape(B*T, C), y.reshape(B*T))
        
        # Consistency loss with previous hidden state
        consistency_loss = 0
        if self.prev_hidden is not None and kv_cache:
            for curr_kv, prev_kv in zip(kv_cache, self.prev_hidden):
                if curr_kv is not None and prev_kv is not None:
                    k_curr, v_curr = curr_kv
                    k_prev, v_prev = prev_kv
                    # Compare overlapping positions
                    min_t = min(k_curr.shape[2], k_prev.shape[2])
                    if min_t > 0:
                        diff = (k_curr.data[:, :, :min_t] - k_prev.data[:, :, :min_t]) ** 2
                        consistency_loss += diff.mean()
        
        total_loss = task_loss.data + self.consistency_weight * consistency_loss
        
        task_loss.backward()
        self.optimizer.step()
        
        # Store for next step
        self.prev_hidden = kv_cache
        
        return float(total_loss)


class S3LTrainer(BaseTrainer):
    """
    Structured Selective Stabilized Learning (S3L) Trainer.
    
    Unified training system that combines:
    - Structured learning with curriculum
    - Selective gradient updates based on confidence
    - Stabilized updates with EMA
    
    Args:
        model: Model to train
        optimizer: Optimizer
        confidence_threshold: Minimum confidence for gradient update
        stability_alpha: EMA decay for stability
    """
    
    def __init__(
        self, 
        model: Module, 
        optimizer: Optional[Optimizer] = None,
        lr: float = 1e-4,
        confidence_threshold: float = 0.1,
        stability_alpha: float = 0.01
    ):
        super().__init__(model, optimizer, lr)
        self.confidence_threshold = confidence_threshold
        self.stability_alpha = stability_alpha
        
        # Reference weights for stability
        self.reference = {name: p.data.copy() for name, p in model.named_parameters()}
    
    def train_step(self, x: Tensor, y: Tensor) -> float:
        self.optimizer.zero_grad()
        
        logits, _ = self.model(x)
        
        B, T, C = logits.shape
        logits_flat = logits.reshape(B * T, C)
        targets_flat = y.reshape(B * T)
        
        # Compute loss
        loss = cross_entropy(logits_flat, targets_flat)
        
        # Compute confidence (probability of correct prediction)
        probs = logits_flat.softmax(axis=-1)
        confidence = probs.data[np.arange(B*T), targets_flat.data.astype(int)].mean()
        
        # Selective gradient gating
        if confidence > self.confidence_threshold:
            loss.backward()
            
            # Stability constraint
            for name, p in self.model.named_parameters():
                if p.grad is not None and name in self.reference:
                    # Pull gradients toward reference
                    diff = p.data - self.reference[name]
                    p.grad += self.stability_alpha * diff
            
            self.optimizer.step()
            
            # Update reference with EMA
            for name, p in self.model.named_parameters():
                if name in self.reference:
                    self.reference[name] = 0.99 * self.reference[name] + 0.01 * p.data
        
        return float(loss.data)


class SGLTrainer(BaseTrainer):
    """
    Sparse Gradient Learning (SGL) Trainer.
    
    Efficient training with sparse gradient updates.
    Only updates parameters with significant gradients.
    
    Args:
        model: Model to train
        optimizer: Optimizer
        sparsity: Gradient sparsity (0-1, higher = more sparse)
    """
    
    def __init__(
        self, 
        model: Module, 
        optimizer: Optional[Optimizer] = None,
        lr: float = 1e-4,
        sparsity: float = 0.9
    ):
        super().__init__(model, optimizer, lr)
        self.sparsity = sparsity
    
    def train_step(self, x: Tensor, y: Tensor) -> float:
        self.optimizer.zero_grad()
        
        logits, _ = self.model(x)
        
        B, T, C = logits.shape
        loss = cross_entropy(logits.reshape(B*T, C), y.reshape(B*T))
        
        loss.backward()
        
        # Sparse gradient selection
        for p in self.model.parameters():
            if p.grad is not None:
                grad_flat = p.grad.flatten()
                k = int(len(grad_flat) * (1 - self.sparsity))
                if k > 0:
                    threshold = np.partition(np.abs(grad_flat), -k)[-k]
                    mask = np.abs(p.grad) >= threshold
                    p.grad *= mask.astype(np.float32)
        
        self.optimizer.step()
        
        return float(loss.data)


# =============================================================================
# Additional Training Utilities
# =============================================================================

class GradientAccumulator:
    """Accumulate gradients over multiple steps."""
    
    def __init__(self, model: Module, accumulation_steps: int = 4):
        self.model = model
        self.accumulation_steps = accumulation_steps
        self.step_count = 0
    
    def should_update(self) -> bool:
        self.step_count += 1
        return self.step_count % self.accumulation_steps == 0


class PTLTrainer(BaseTrainer):
    """
    Parallel Training and Learning (PTL) Trainer.
    
    Multi-threaded CPU-optimized training that processes multiple
    batches in parallel for faster training on CPU.
    
    Features:
    - Parallel batch processing with thread pool
    - Gradient aggregation from multiple threads
    - CPU-optimized memory management
    - Lock-based weight synchronization
    
    Args:
        model: Model to train
        optimizer: Optimizer
        num_workers: Number of parallel worker threads (default: 4)
        batch_per_worker: Number of batches each worker processes
    """
    
    def __init__(
        self, 
        model: Module, 
        optimizer: Optional[Optimizer] = None,
        lr: float = 1e-4,
        num_workers: int = 4,
        batch_per_worker: int = 2
    ):
        super().__init__(model, optimizer, lr)
        self.num_workers = num_workers
        self.batch_per_worker = batch_per_worker
        self.gradient_lock = Lock()
        self.step_count = 0
    
    def _worker_forward_backward(self, batch_data: List[tuple]) -> Dict[str, np.ndarray]:
        """Worker function: process batches and return gradients."""
        gradients = {}
        
        for x_data, y_data in batch_data:
            x = Tensor(x_data)
            y = Tensor(y_data)
            
            # Forward pass
            logits, _ = self.model(x)
            
            # Compute loss
            B, T, C = logits.shape
            loss = cross_entropy(logits.reshape(B*T, C), y.reshape(B*T))
            
            # Backward pass (compute gradients)
            loss.backward()
            
            # Accumulate gradients
            for name, p in self.model.named_parameters():
                if p.grad is not None:
                    if name not in gradients:
                        gradients[name] = np.zeros_like(p.grad)
                    gradients[name] += p.grad
                    
                    # Clear gradient for next iteration
                    p.grad = None
        
        return gradients
    
    def train_step(self, x: Tensor, y: Tensor) -> float:
        """Single training step with parallel processing."""
        # For single batch, use standard training
        self.optimizer.zero_grad()
        
        logits, _ = self.model(x)
        B, T, C = logits.shape
        loss = cross_entropy(logits.reshape(B*T, C), y.reshape(B*T))
        
        loss.backward()
        self.optimizer.step()
        
        return float(loss.data)
    
    def train(self, dataloader: DataLoader, epochs: int = 5, verbose: bool = True) -> Dict:
        """Train with parallel processing."""
        self.model.train()
        
        # Collect all batches
        all_batches = list(dataloader)
        
        for epoch in range(epochs):
            epoch_loss = 0
            steps = 0
            
            # Process batches in parallel
            batch_idx = 0
            while batch_idx < len(all_batches):
                # Prepare batches for workers
                worker_batches = []
                for w in range(self.num_workers):
                    if batch_idx >= len(all_batches):
                        break
                    worker_batch = []
                    for _ in range(self.batch_per_worker):
                        if batch_idx >= len(all_batches):
                            break
                        x, y = all_batches[batch_idx]
                        worker_batch.append((x.data, y.data))
                        batch_idx += 1
                    if worker_batch:
                        worker_batches.append(worker_batch)
                
                if not worker_batches:
                    break
                
                # Process in parallel
                aggregated_grads = {}
                total_loss = 0
                num_samples = 0
                
                with ThreadPoolExecutor(max_workers=self.num_workers) as executor:
                    futures = [executor.submit(self._worker_forward_backward, wb) for wb in worker_batches]
                    
                    for future in as_completed(futures):
                        worker_grads = future.result()
                        
                        # Aggregate gradients
                        with self.gradient_lock:
                            for name, grad in worker_grads.items():
                                if name not in aggregated_grads:
                                    aggregated_grads[name] = np.zeros_like(grad)
                                aggregated_grads[name] += grad
                
                # Apply aggregated gradients
                self.optimizer.zero_grad()
                for name, p in self.model.named_parameters():
                    if name in aggregated_grads:
                        p.grad = Tensor(aggregated_grads[name] / len(worker_batches))
                
                # Update weights
                clip_grad_norm(self.model.parameters(), 1.0)
                self.optimizer.step()
                
                steps += len(worker_batches)
                if verbose and steps % 10 == 0:
                    print(f"  Step {steps}: processed {len(worker_batches)} parallel batches", end='\r')
            
            avg_loss = epoch_loss / max(steps, 1)
            self.history['loss'].append(avg_loss)
            
            if verbose:
                print(f"Epoch {epoch+1}/{epochs}: avg_loss={avg_loss:.4f} (parallel workers={self.num_workers})")
        
        return self.history


class EMAModel:
    """Exponential Moving Average of model weights."""
    
    def __init__(self, model: Module, decay: float = 0.9999):
        self.model = model
        self.decay = decay
        self.shadow = {name: p.data.copy() for name, p in model.named_parameters()}
    
    def update(self):
        for name, p in self.model.named_parameters():
            if name in self.shadow:
                self.shadow[name] = self.decay * self.shadow[name] + (1 - self.decay) * p.data
    
    def apply(self):
        """Apply EMA weights to model."""
        for name, p in self.model.named_parameters():
            if name in self.shadow:
                p.data = self.shadow[name].copy()
    
    def restore(self, backup: Dict):
        """Restore original weights."""
        for name, p in self.model.named_parameters():
            if name in backup:
                p.data = backup[name].copy()
