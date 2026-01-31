"""
NAPLY Functional Operations
===========================

Standalone functions for neural network operations.
"""

import numpy as np
from typing import Optional
from .tensor import Tensor


def cross_entropy(logits: Tensor, targets: Tensor, ignore_index: int = -100) -> Tensor:
    """
    Cross-entropy loss with numerical stability.
    
    Args:
        logits: (B, C) or (B*T, C) logits
        targets: (B,) or (B*T,) target indices
        ignore_index: Index to ignore in loss computation
        
    Returns:
        Scalar loss tensor
    """
    # Handle shapes
    if len(logits.shape) == 3:
        B, T, C = logits.shape
        logits = logits.reshape(B * T, C)
        targets = targets.reshape(B * T)
    
    B, C = logits.shape
    
    # Log-softmax for numerical stability
    log_probs = logits.log_softmax(axis=-1)
    
    # Get target indices
    target_idx = targets.data.astype(np.int32)
    
    # Mask for valid targets
    mask = (target_idx != ignore_index).astype(np.float32)
    target_idx = np.clip(target_idx, 0, C - 1)
    
    # Gather log probabilities
    batch_idx = np.arange(B)
    gathered = Tensor(log_probs.data[batch_idx, target_idx], requires_grad=log_probs.requires_grad)
    
    # Apply mask and compute mean
    masked = Tensor(gathered.data * mask, requires_grad=gathered.requires_grad)
    loss = -(masked.sum() / max(mask.sum(), 1))
    
    # Manual backward for gathered
    def _backward():
        if log_probs.requires_grad:
            if log_probs.grad is None:
                log_probs.grad = np.zeros_like(log_probs.data)
            grad = np.zeros_like(log_probs.data)
            grad[batch_idx, target_idx] = -mask / max(mask.sum(), 1)
            log_probs.grad += grad * loss.grad if loss.grad is not None else grad
    
    loss._backward = _backward
    loss._prev = {log_probs}
    
    return loss


def mse_loss(pred: Tensor, target: Tensor, reduction: str = 'mean') -> Tensor:
    """Mean Squared Error loss."""
    diff = pred - target
    squared = diff * diff
    if reduction == 'mean':
        return squared.mean()
    elif reduction == 'sum':
        return squared.sum()
    else:
        return squared


def kl_divergence(p: Tensor, q: Tensor) -> Tensor:
    """KL Divergence: KL(P || Q)."""
    return (p * (p.log() - q.log())).sum()


def focal_loss(logits: Tensor, targets: Tensor, gamma: float = 2.0, alpha: float = 0.25) -> Tensor:
    """Focal loss for class imbalance."""
    probs = logits.softmax(axis=-1)
    B, C = logits.shape
    
    target_idx = targets.data.astype(np.int32)
    batch_idx = np.arange(B)
    p_t = Tensor(probs.data[batch_idx, target_idx])
    
    focal_weight = alpha * ((1 - p_t) ** gamma)
    ce = -p_t.log()
    
    return (focal_weight * ce).mean()


# =============================================================================
# Activation Functions
# =============================================================================

def relu(x: Tensor) -> Tensor:
    """ReLU activation."""
    return x.relu()


def gelu(x: Tensor) -> Tensor:
    """GELU activation."""
    return x.gelu()


def silu(x: Tensor) -> Tensor:
    """SiLU/Swish activation."""
    return x.silu()


def swish(x: Tensor) -> Tensor:
    """Swish activation (alias for SiLU)."""
    return x.silu()


def sigmoid(x: Tensor) -> Tensor:
    """Sigmoid activation."""
    return x.sigmoid()


def tanh(x: Tensor) -> Tensor:
    """Tanh activation."""
    return x.tanh()


def softmax(x: Tensor, axis: int = -1) -> Tensor:
    """Softmax activation."""
    return x.softmax(axis=axis)


def log_softmax(x: Tensor, axis: int = -1) -> Tensor:
    """Log-softmax activation."""
    return x.log_softmax(axis=axis)


def leaky_relu(x: Tensor, negative_slope: float = 0.01) -> Tensor:
    """Leaky ReLU activation."""
    out = Tensor(
        np.where(x.data > 0, x.data, negative_slope * x.data),
        requires_grad=x.requires_grad,
        _children=(x,),
        _op='leaky_relu'
    )
    
    def _backward():
        if x.requires_grad:
            if x.grad is None:
                x.grad = np.zeros_like(x.data)
            grad = np.where(x.data > 0, 1.0, negative_slope)
            x.grad += grad * out.grad
    
    out._backward = _backward
    return out


def elu(x: Tensor, alpha: float = 1.0) -> Tensor:
    """ELU activation."""
    out = Tensor(
        np.where(x.data > 0, x.data, alpha * (np.exp(x.data) - 1)),
        requires_grad=x.requires_grad,
        _children=(x,),
        _op='elu'
    )
    
    def _backward():
        if x.requires_grad:
            if x.grad is None:
                x.grad = np.zeros_like(x.data)
            grad = np.where(x.data > 0, 1.0, out.data + alpha)
            x.grad += grad * out.grad
    
    out._backward = _backward
    return out


# =============================================================================
# Normalization Functions
# =============================================================================

def layer_norm(x: Tensor, weight: Optional[Tensor] = None, bias: Optional[Tensor] = None, 
               eps: float = 1e-5) -> Tensor:
    """Layer normalization."""
    mean = x.mean(axis=-1, keepdims=True)
    var = ((x - mean) ** 2).mean(axis=-1, keepdims=True)
    x_norm = (x - mean) / ((var + eps) ** 0.5)
    
    if weight is not None:
        x_norm = x_norm * weight
    if bias is not None:
        x_norm = x_norm + bias
    
    return x_norm


def rms_norm(x: Tensor, weight: Optional[Tensor] = None, eps: float = 1e-5) -> Tensor:
    """RMS normalization (used in LLaMA)."""
    rms = ((x ** 2).mean(axis=-1, keepdims=True) + eps) ** 0.5
    x_norm = x / rms
    
    if weight is not None:
        x_norm = x_norm * weight
    
    return x_norm


def batch_norm(x: Tensor, running_mean: Optional[np.ndarray] = None, 
               running_var: Optional[np.ndarray] = None,
               weight: Optional[Tensor] = None, bias: Optional[Tensor] = None,
               training: bool = True, momentum: float = 0.1, eps: float = 1e-5) -> Tensor:
    """Batch normalization."""
    if training:
        mean = x.mean(axis=0, keepdims=True)
        var = ((x - mean) ** 2).mean(axis=0, keepdims=True)
    else:
        if running_mean is None or running_var is None:
            raise ValueError("running_mean and running_var required in eval mode")
        mean = Tensor(running_mean)
        var = Tensor(running_var)
    
    x_norm = (x - mean) / ((var + eps) ** 0.5)
    
    if weight is not None:
        x_norm = x_norm * weight
    if bias is not None:
        x_norm = x_norm + bias
    
    return x_norm


# =============================================================================
# Dropout & Regularization
# =============================================================================

def dropout(x: Tensor, p: float = 0.1, training: bool = True) -> Tensor:
    """Dropout regularization."""
    if not training or p == 0:
        return x
    
    mask = (np.random.rand(*x.shape) > p).astype(np.float32)
    scale = 1.0 / (1.0 - p)
    
    out = Tensor(
        x.data * mask * scale,
        requires_grad=x.requires_grad,
        _children=(x,),
        _op='dropout'
    )
    
    def _backward():
        if x.requires_grad:
            if x.grad is None:
                x.grad = np.zeros_like(x.data)
            x.grad += mask * scale * out.grad
    
    out._backward = _backward
    return out


# =============================================================================
# Embedding & Positional Encoding
# =============================================================================

def one_hot(indices: np.ndarray, num_classes: int) -> Tensor:
    """Create one-hot encoding."""
    indices = np.asarray(indices).astype(np.int32)
    result = np.zeros((*indices.shape, num_classes), dtype=np.float32)
    result[np.arange(indices.size), indices.flatten()] = 1
    return Tensor(result.reshape(*indices.shape, num_classes))


def sinusoidal_position_encoding(max_len: int, d_model: int) -> Tensor:
    """Sinusoidal positional encoding."""
    position = np.arange(max_len)[:, np.newaxis]
    div_term = np.exp(np.arange(0, d_model, 2) * (-np.log(10000.0) / d_model))
    
    pe = np.zeros((max_len, d_model))
    pe[:, 0::2] = np.sin(position * div_term)
    pe[:, 1::2] = np.cos(position * div_term)
    
    return Tensor(pe)


def rotary_position_embedding(x: Tensor, base: int = 10000) -> Tensor:
    """Rotary Position Embedding (RoPE) - used in modern LLMs."""
    B, H, T, D = x.shape
    assert D % 2 == 0, "Dimension must be even for RoPE"
    
    # Compute frequencies
    inv_freq = 1.0 / (base ** (np.arange(0, D, 2) / D))
    pos = np.arange(T)
    freqs = np.outer(pos, inv_freq)
    
    # Apply rotation
    cos_freqs = np.cos(freqs)
    sin_freqs = np.sin(freqs)
    
    x1 = x.data[..., 0::2]
    x2 = x.data[..., 1::2]
    
    rotated = np.zeros_like(x.data)
    rotated[..., 0::2] = x1 * cos_freqs - x2 * sin_freqs
    rotated[..., 1::2] = x1 * sin_freqs + x2 * cos_freqs
    
    return Tensor(rotated, requires_grad=x.requires_grad)


# =============================================================================
# Utility Functions
# =============================================================================

def clip_grad_norm(parameters: list, max_norm: float) -> float:
    """Clip gradient norm to prevent exploding gradients."""
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


def masked_fill(x: Tensor, mask: np.ndarray, value: float) -> Tensor:
    """Fill tensor with value where mask is True."""
    out = Tensor(
        np.where(mask, value, x.data),
        requires_grad=x.requires_grad,
        _children=(x,),
        _op='masked_fill'
    )
    
    def _backward():
        if x.requires_grad:
            if x.grad is None:
                x.grad = np.zeros_like(x.data)
            x.grad += np.where(mask, 0, out.grad)
    
    out._backward = _backward
    return out


def cat(tensors: list, dim: int = 0) -> Tensor:
    """Concatenate tensors along specified dimension."""
    if not tensors:
        raise ValueError("Cannot concatenate empty list")
    
    data = np.concatenate([t.data for t in tensors], axis=dim)
    requires_grad = any(t.requires_grad for t in tensors)
    
    out = Tensor(data, requires_grad=requires_grad, _children=tuple(tensors), _op='cat')
    
    def _backward():
        if not requires_grad:
            return
        # Split gradient back to each tensor
        splits = np.cumsum([t.shape[dim] for t in tensors[:-1]])
        grads = np.split(out.grad, splits, axis=dim)
        for t, g in zip(tensors, grads):
            if t.requires_grad:
                if t.grad is None:
                    t.grad = np.zeros_like(t.data)
                t.grad += g
    
    out._backward = _backward
    return out