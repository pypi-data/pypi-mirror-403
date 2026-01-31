"""
NAPLY Neural Network Module (nn)
================================

PyTorch-style nn module for familiar API.

Usage:
    import naply.nn as nn
    
    class MyModel(nn.Module):
        def __init__(self):
            super().__init__()
            self.linear = nn.Linear(768, 768)
            self.norm = nn.LayerNorm(768)
        
        def forward(self, x):
            return self.norm(self.linear(x))
"""

# Import all layer types for nn.* access
from .layers import (
    Module,
    Linear,
    Embedding,
    LayerNorm,
    RMSNorm,
    Dropout,
    Sequential,
    ModuleList,
    Adapter,
    GELU,
    SiLU,
    ReLU,
    Softmax,
)

from .attention import (
    MultiHeadAttention,
    GroupedQueryAttention,
    FlashAttention,
    SlidingWindowAttention,
)

from .transformer import (
    FeedForward,
    SwiGLU,
    TransformerBlock,
    GPT,
    LLaMA,
)

# Functional operations
from . import functional as F

__all__ = [
    # Base
    'Module',
    
    # Linear layers
    'Linear',
    'Embedding',
    
    # Normalization
    'LayerNorm',
    'RMSNorm',
    
    # Regularization
    'Dropout',
    
    # Containers
    'Sequential',
    'ModuleList',
    
    # Activations
    'GELU',
    'SiLU',
    'ReLU',
    'Softmax',
    
    # Attention
    'MultiHeadAttention',
    'GroupedQueryAttention',
    'FlashAttention',
    'SlidingWindowAttention',
    
    # Transformer
    'FeedForward',
    'SwiGLU',
    'TransformerBlock',
    'GPT',
    'LLaMA',
    
    # Adapter
    'Adapter',
    
    # Functional
    'F',
]
