"""
NAPLY Optimizers
================

Optimizers and learning rate schedulers for training.
"""

import numpy as np
from typing import List, Optional, Callable
from .tensor import Tensor


class Optimizer:
    """
    Base class for optimizers.
    
    All optimizers should inherit from this class.
    """
    
    def __init__(self, parameters: List[Tensor], lr: float = 1e-3):
        self.parameters = parameters
        self.lr = lr
        self.t = 0  # Step counter
    
    def zero_grad(self):
        """Reset all gradients to None."""
        for p in self.parameters:
            p.grad = None
    
    def step(self):
        """Update parameters. To be implemented by subclasses."""
        raise NotImplementedError


class SGD(Optimizer):
    """
    Stochastic Gradient Descent with momentum.
    
    Args:
        parameters: List of parameters to optimize
        lr: Learning rate
        momentum: Momentum factor (default: 0)
        weight_decay: Weight decay (L2 regularization)
        nesterov: Whether to use Nesterov momentum
    """
    
    def __init__(
        self, 
        parameters: List[Tensor], 
        lr: float = 1e-2,
        momentum: float = 0.0,
        weight_decay: float = 0.0,
        nesterov: bool = False
    ):
        super().__init__(parameters, lr)
        self.momentum = momentum
        self.weight_decay = weight_decay
        self.nesterov = nesterov
        
        # Velocity for momentum
        self.velocities = [np.zeros_like(p.data) for p in parameters]
    
    def step(self):
        self.t += 1
        for i, p in enumerate(self.parameters):
            if p.grad is None:
                continue
            
            grad = p.grad.copy()
            
            # Weight decay
            if self.weight_decay > 0:
                grad += self.weight_decay * p.data
            
            # Momentum
            if self.momentum > 0:
                self.velocities[i] = self.momentum * self.velocities[i] + grad
                if self.nesterov:
                    grad = grad + self.momentum * self.velocities[i]
                else:
                    grad = self.velocities[i]
            
            p.data -= self.lr * grad


class AdamW(Optimizer):
    """
    AdamW optimizer (Adam with decoupled weight decay).
    
    This is the recommended optimizer for training language models.
    
    Args:
        parameters: List of parameters to optimize
        lr: Learning rate (default: 1e-3)
        betas: Coefficients for computing running averages (default: (0.9, 0.999))
        eps: Term added for numerical stability (default: 1e-8)
        weight_decay: Weight decay coefficient (default: 0.01)
        
    Example:
        optimizer = AdamW(model.parameters(), lr=1e-4, weight_decay=0.01)
    """
    
    def __init__(
        self, 
        parameters: List[Tensor], 
        lr: float = 1e-3,
        betas: tuple = (0.9, 0.999),
        eps: float = 1e-8,
        weight_decay: float = 0.01
    ):
        super().__init__(parameters, lr)
        self.betas = betas
        self.eps = eps
        self.weight_decay = weight_decay
        
        # First and second moment estimates
        self.m = [np.zeros_like(p.data) for p in parameters]
        self.v = [np.zeros_like(p.data) for p in parameters]
    
    def step(self):
        self.t += 1
        beta1, beta2 = self.betas
        
        for i, p in enumerate(self.parameters):
            if p.grad is None:
                continue
            
            grad = p.grad
            
            # Update biased first moment estimate
            self.m[i] = beta1 * self.m[i] + (1 - beta1) * grad
            # Update biased second raw moment estimate
            self.v[i] = beta2 * self.v[i] + (1 - beta2) * (grad ** 2)
            
            # Bias correction
            m_hat = self.m[i] / (1 - beta1 ** self.t)
            v_hat = self.v[i] / (1 - beta2 ** self.t)
            
            # Update with weight decay (decoupled)
            p.data -= self.lr * (m_hat / (np.sqrt(v_hat) + self.eps) + self.weight_decay * p.data)


class Adam(Optimizer):
    """
    Standard Adam optimizer.
    
    Args:
        parameters: List of parameters to optimize
        lr: Learning rate
        betas: Coefficients for running averages
        eps: Term for numerical stability
    """
    
    def __init__(
        self, 
        parameters: List[Tensor], 
        lr: float = 1e-3,
        betas: tuple = (0.9, 0.999),
        eps: float = 1e-8
    ):
        super().__init__(parameters, lr)
        self.betas = betas
        self.eps = eps
        
        self.m = [np.zeros_like(p.data) for p in parameters]
        self.v = [np.zeros_like(p.data) for p in parameters]
    
    def step(self):
        self.t += 1
        beta1, beta2 = self.betas
        
        for i, p in enumerate(self.parameters):
            if p.grad is None:
                continue
            
            grad = p.grad
            
            self.m[i] = beta1 * self.m[i] + (1 - beta1) * grad
            self.v[i] = beta2 * self.v[i] + (1 - beta2) * (grad ** 2)
            
            m_hat = self.m[i] / (1 - beta1 ** self.t)
            v_hat = self.v[i] / (1 - beta2 ** self.t)
            
            p.data -= self.lr * m_hat / (np.sqrt(v_hat) + self.eps)


class RMSprop(Optimizer):
    """
    RMSprop optimizer.
    
    Args:
        parameters: List of parameters
        lr: Learning rate
        alpha: Smoothing constant
        eps: Term for numerical stability
    """
    
    def __init__(
        self, 
        parameters: List[Tensor], 
        lr: float = 1e-2,
        alpha: float = 0.99,
        eps: float = 1e-8
    ):
        super().__init__(parameters, lr)
        self.alpha = alpha
        self.eps = eps
        
        self.v = [np.zeros_like(p.data) for p in parameters]
    
    def step(self):
        self.t += 1
        
        for i, p in enumerate(self.parameters):
            if p.grad is None:
                continue
            
            grad = p.grad
            
            self.v[i] = self.alpha * self.v[i] + (1 - self.alpha) * (grad ** 2)
            
            p.data -= self.lr * grad / (np.sqrt(self.v[i]) + self.eps)


class AdaGrad(Optimizer):
    """
    AdaGrad optimizer.
    
    Args:
        parameters: List of parameters
        lr: Learning rate
        eps: Term for numerical stability
    """
    
    def __init__(
        self, 
        parameters: List[Tensor], 
        lr: float = 1e-2,
        eps: float = 1e-8
    ):
        super().__init__(parameters, lr)
        self.eps = eps
        
        self.v = [np.zeros_like(p.data) for p in parameters]
    
    def step(self):
        self.t += 1
        
        for i, p in enumerate(self.parameters):
            if p.grad is None:
                continue
            
            grad = p.grad
            
            self.v[i] += grad ** 2
            
            p.data -= self.lr * grad / (np.sqrt(self.v[i]) + self.eps)


# =============================================================================
# Learning Rate Schedulers
# =============================================================================

class LRScheduler:
    """Base class for learning rate schedulers."""
    
    def __init__(self, optimizer: Optimizer, last_epoch: int = -1):
        self.optimizer = optimizer
        self.base_lr = optimizer.lr
        self.last_epoch = last_epoch
    
    def step(self, epoch: Optional[int] = None):
        if epoch is None:
            self.last_epoch += 1
        else:
            self.last_epoch = epoch
        
        self.optimizer.lr = self.get_lr()
    
    def get_lr(self) -> float:
        raise NotImplementedError


class CosineScheduler(LRScheduler):
    """
    Cosine annealing learning rate scheduler.
    
    Args:
        optimizer: Optimizer to schedule
        total_steps: Total number of training steps
        min_lr: Minimum learning rate
        warmup_steps: Number of warmup steps
    """
    
    def __init__(
        self, 
        optimizer: Optimizer, 
        total_steps: int,
        min_lr: float = 0.0,
        warmup_steps: int = 0
    ):
        super().__init__(optimizer)
        self.total_steps = total_steps
        self.min_lr = min_lr
        self.warmup_steps = warmup_steps
    
    def get_lr(self) -> float:
        step = self.last_epoch
        
        # Warmup phase
        if step < self.warmup_steps:
            return self.base_lr * step / max(1, self.warmup_steps)
        
        # Cosine decay phase
        progress = (step - self.warmup_steps) / max(1, self.total_steps - self.warmup_steps)
        return self.min_lr + (self.base_lr - self.min_lr) * 0.5 * (1 + np.cos(np.pi * progress))


class WarmupScheduler(LRScheduler):
    """
    Linear warmup scheduler.
    
    Args:
        optimizer: Optimizer to schedule
        warmup_steps: Number of warmup steps
    """
    
    def __init__(self, optimizer: Optimizer, warmup_steps: int):
        super().__init__(optimizer)
        self.warmup_steps = warmup_steps
    
    def get_lr(self) -> float:
        if self.last_epoch < self.warmup_steps:
            return self.base_lr * self.last_epoch / max(1, self.warmup_steps)
        return self.base_lr


class LinearScheduler(LRScheduler):
    """
    Linear decay learning rate scheduler.
    
    Args:
        optimizer: Optimizer to schedule
        total_steps: Total number of training steps
        min_lr: Minimum learning rate
        warmup_steps: Number of warmup steps
    """
    
    def __init__(
        self, 
        optimizer: Optimizer, 
        total_steps: int,
        min_lr: float = 0.0,
        warmup_steps: int = 0
    ):
        super().__init__(optimizer)
        self.total_steps = total_steps
        self.min_lr = min_lr
        self.warmup_steps = warmup_steps
    
    def get_lr(self) -> float:
        step = self.last_epoch
        
        if step < self.warmup_steps:
            return self.base_lr * step / max(1, self.warmup_steps)
        
        progress = (step - self.warmup_steps) / max(1, self.total_steps - self.warmup_steps)
        return self.min_lr + (self.base_lr - self.min_lr) * (1 - progress)


class StepScheduler(LRScheduler):
    """
    Step decay scheduler.
    
    Args:
        optimizer: Optimizer to schedule
        step_size: Number of steps between decays
        gamma: Decay factor
    """
    
    def __init__(
        self, 
        optimizer: Optimizer, 
        step_size: int,
        gamma: float = 0.1
    ):
        super().__init__(optimizer)
        self.step_size = step_size
        self.gamma = gamma
    
    def get_lr(self) -> float:
        return self.base_lr * (self.gamma ** (self.last_epoch // self.step_size))


class ReduceOnPlateau:
    """
    Reduce learning rate when a metric has stopped improving.
    
    Args:
        optimizer: Optimizer to schedule
        mode: 'min' or 'max'
        factor: Factor to reduce LR by
        patience: Number of epochs to wait
        min_lr: Minimum learning rate
    """
    
    def __init__(
        self, 
        optimizer: Optimizer,
        mode: str = 'min',
        factor: float = 0.1,
        patience: int = 10,
        min_lr: float = 1e-6
    ):
        self.optimizer = optimizer
        self.mode = mode
        self.factor = factor
        self.patience = patience
        self.min_lr = min_lr
        
        self.best = float('inf') if mode == 'min' else float('-inf')
        self.num_bad_epochs = 0
    
    def step(self, metric: float):
        is_better = (self.mode == 'min' and metric < self.best) or \
                    (self.mode == 'max' and metric > self.best)
        
        if is_better:
            self.best = metric
            self.num_bad_epochs = 0
        else:
            self.num_bad_epochs += 1
        
        if self.num_bad_epochs >= self.patience:
            old_lr = self.optimizer.lr
            new_lr = max(old_lr * self.factor, self.min_lr)
            self.optimizer.lr = new_lr
            self.num_bad_epochs = 0
            print(f"Reducing learning rate: {old_lr:.2e} -> {new_lr:.2e}")


# =============================================================================
# Gradient Utilities
# =============================================================================

def clip_grad_norm(parameters: List[Tensor], max_norm: float) -> float:
    """
    Clip gradient norm to prevent exploding gradients.
    
    Args:
        parameters: List of parameters
        max_norm: Maximum gradient norm
        
    Returns:
        Total gradient norm before clipping
    """
    total_norm = 0.0
    for p in parameters:
        if p.grad is not None:
            param_norm = np.sum(p.grad ** 2)
            total_norm += param_norm
    
    total_norm = np.sqrt(total_norm)
    clip_coef = max_norm / (total_norm + 1e-6)
    
    if clip_coef < 1:
        for p in parameters:
            if p.grad is not None:
                p.grad *= clip_coef
    
    return total_norm


def clip_grad_value(parameters: List[Tensor], clip_value: float):
    """
    Clip gradient values to a specified range.
    
    Args:
        parameters: List of parameters
        clip_value: Maximum absolute gradient value
    """
    for p in parameters:
        if p.grad is not None:
            p.grad = np.clip(p.grad, -clip_value, clip_value)


class OneCycleScheduler:
    """
    OneCycle Learning Rate Policy.
    
    Ramps learning rate up to max_lr and then decays it.
    Proven to converge faster and reach better optima ("Superconvergence").
    
    Args:
        optimizer: Optimizer to schedule
        max_lr: Maximum learning rate
        total_steps: Total number of training steps
        pct_start: Percentage of steps for warmup (default: 0.3)
        div_factor: Division factor for initial LR (default: 25.0)
        final_div_factor: Division factor for final LR (default: 1e4)
    """
    
    def __init__(
        self, 
        optimizer: Optimizer, 
        max_lr: float, 
        total_steps: int, 
        pct_start: float = 0.3, 
        div_factor: float = 25.0, 
        final_div_factor: float = 1e4
    ):
        self.optimizer = optimizer
        self.max_lr = max_lr
        self.total_steps = total_steps
        self.pct_start = pct_start
        self.initial_lr = max_lr / div_factor
        self.min_lr = self.initial_lr / final_div_factor
        
        self.step_up = int(total_steps * pct_start)
        self.step_down = total_steps - self.step_up
        self.current_step = 0
        
        # Set initial
        self.optimizer.lr = self.initial_lr
    
    def step(self) -> float:
        """Update learning rate and return current LR."""
        self.current_step += 1
        curr = self.current_step
        
        if curr <= self.step_up:
            # Phase 1: Linear increase
            progress = curr / max(1, self.step_up)
            lr = self.initial_lr + (self.max_lr - self.initial_lr) * progress
        elif curr <= self.total_steps:
            # Phase 2: Cosine annealing decrease
            progress = (curr - self.step_up) / max(1, self.step_down)
            lr = self.min_lr + (self.max_lr - self.min_lr) * 0.5 * (1 + np.cos(np.pi * progress))
        else:
            lr = self.min_lr
        
        self.optimizer.lr = lr
        return lr
    
    def get_lr(self) -> float:
        """Get current learning rate."""
        return self.optimizer.lr