"""
NAPLY Configuration Classes
===========================

Configuration for models and training.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


@dataclass
class ModelConfig:
    """
    Model architecture configuration.
    
    Args:
        vocab_size: Vocabulary size
        n_layer: Number of transformer layers
        n_head: Number of attention heads
        n_embd: Embedding dimension
        block_size: Maximum context length
        dropout: Dropout probability
        bias: Whether to use bias in projections
        
    Example:
        config = ModelConfig(
            vocab_size=50000,
            n_layer=12,
            n_head=12,
            n_embd=768,
            block_size=2048
        )
    """
    vocab_size: int = 50000
    n_layer: int = 12
    n_head: int = 12
    n_embd: int = 768
    block_size: int = 2048
    dropout: float = 0.1
    bias: bool = True
    
    # Advanced options
    n_kv_head: Optional[int] = None  # For Grouped Query Attention
    use_swiglu: bool = False  # LLaMA-style FFN
    use_rms_norm: bool = False  # LLaMA-style normalization
    use_rope: bool = False  # Rotary Position Embedding
    tie_embeddings: bool = True  # Tie input/output embeddings
    
    def __post_init__(self):
        if self.n_kv_head is None:
            self.n_kv_head = self.n_head
    
    @property
    def head_dim(self) -> int:
        return self.n_embd // self.n_head
    
    def count_parameters(self) -> int:
        """Estimate total parameters."""
        # Embedding: vocab_size * n_embd
        embed_params = self.vocab_size * self.n_embd
        
        # Position embedding: block_size * n_embd
        pos_params = self.block_size * self.n_embd
        
        # Per layer:
        # - Attention: 4 * n_embd^2 (QKV + proj)
        # - FFN: 8 * n_embd^2 (up + down, expansion=4)
        # - LayerNorm: 2 * n_embd (weight + bias) * 2
        layer_params = 12 * self.n_embd ** 2 + 4 * self.n_embd
        total_layer_params = self.n_layer * layer_params
        
        # Output: n_embd * vocab_size (if not tied)
        output_params = 0 if self.tie_embeddings else self.vocab_size * self.n_embd
        
        return embed_params + pos_params + total_layer_params + output_params
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'vocab_size': self.vocab_size,
            'n_layer': self.n_layer,
            'n_head': self.n_head,
            'n_embd': self.n_embd,
            'block_size': self.block_size,
            'dropout': self.dropout,
            'bias': self.bias,
            'n_kv_head': self.n_kv_head,
            'use_swiglu': self.use_swiglu,
            'use_rms_norm': self.use_rms_norm,
            'use_rope': self.use_rope,
            'tie_embeddings': self.tie_embeddings,
        }
    
    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'ModelConfig':
        return cls(**d)


@dataclass
class TrainConfig:
    """
    Training configuration.
    
    Args:
        epochs: Number of training epochs
        batch_size: Training batch size
        learning_rate: Initial learning rate
        weight_decay: Weight decay for regularization
        warmup_steps: Number of warmup steps
        max_grad_norm: Maximum gradient norm for clipping
        
    Example:
        config = TrainConfig(
            epochs=10,
            batch_size=32,
            learning_rate=1e-4
        )
    """
    epochs: int = 5
    batch_size: int = 32
    learning_rate: float = 1e-4
    weight_decay: float = 0.01
    
    # Learning rate schedule
    warmup_steps: int = 100
    lr_decay: str = "cosine"  # "cosine", "linear", "constant"
    min_lr: float = 1e-6
    
    # Gradient settings
    max_grad_norm: float = 1.0
    gradient_accumulation_steps: int = 1
    
    # Checkpointing
    save_every: int = 1  # Save every N epochs
    eval_every: int = 100  # Evaluate every N steps
    log_every: int = 10  # Log every N steps
    
    # Data settings
    max_seq_length: int = 512
    shuffle: bool = True
    num_workers: int = 0
    
    # Advanced
    use_amp: bool = False  # Automatic Mixed Precision
    use_ema: bool = False  # Exponential Moving Average
    ema_decay: float = 0.9999
    
    # Early stopping
    early_stopping: bool = False
    patience: int = 3
    min_delta: float = 0.001
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'epochs': self.epochs,
            'batch_size': self.batch_size,
            'learning_rate': self.learning_rate,
            'weight_decay': self.weight_decay,
            'warmup_steps': self.warmup_steps,
            'lr_decay': self.lr_decay,
            'min_lr': self.min_lr,
            'max_grad_norm': self.max_grad_norm,
            'gradient_accumulation_steps': self.gradient_accumulation_steps,
            'save_every': self.save_every,
            'eval_every': self.eval_every,
            'log_every': self.log_every,
            'max_seq_length': self.max_seq_length,
            'shuffle': self.shuffle,
        }
    
    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'TrainConfig':
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


# =============================================================================
# Model Presets
# =============================================================================

PRESETS = {
    # Tiny models for testing
    "tiny": ModelConfig(
        vocab_size=5000, n_layer=2, n_head=2, n_embd=64, block_size=128
    ),
    
    # Small models for CPU training
    "small": ModelConfig(
        vocab_size=10000, n_layer=4, n_head=4, n_embd=256, block_size=256
    ),
    
    # Medium models
    "medium": ModelConfig(
        vocab_size=30000, n_layer=8, n_head=8, n_embd=512, block_size=512
    ),
    
    # Large models
    "large": ModelConfig(
        vocab_size=50000, n_layer=12, n_head=12, n_embd=768, block_size=1024
    ),
    
    # XL models
    "xl": ModelConfig(
        vocab_size=50000, n_layer=24, n_head=16, n_embd=1024, block_size=2048
    ),
    
    # XXL models
    "xxl": ModelConfig(
        vocab_size=100000, n_layer=32, n_head=24, n_embd=1536, block_size=4096
    ),
    
    # GPT-2 style
    "gpt2-small": ModelConfig(
        vocab_size=50257, n_layer=12, n_head=12, n_embd=768, block_size=1024
    ),
    "gpt2-medium": ModelConfig(
        vocab_size=50257, n_layer=24, n_head=16, n_embd=1024, block_size=1024
    ),
    "gpt2-large": ModelConfig(
        vocab_size=50257, n_layer=36, n_head=20, n_embd=1280, block_size=1024
    ),
    "gpt2-xl": ModelConfig(
        vocab_size=50257, n_layer=48, n_head=25, n_embd=1600, block_size=1024
    ),
    
    # LLaMA style (with modern features)
    "llama-small": ModelConfig(
        vocab_size=32000, n_layer=12, n_head=12, n_embd=768, block_size=2048,
        use_swiglu=True, use_rms_norm=True, use_rope=True, bias=False
    ),
    "llama-medium": ModelConfig(
        vocab_size=32000, n_layer=24, n_head=16, n_embd=1024, block_size=2048,
        use_swiglu=True, use_rms_norm=True, use_rope=True, bias=False
    ),
    "llama-large": ModelConfig(
        vocab_size=32000, n_layer=32, n_head=32, n_embd=2048, block_size=4096,
        use_swiglu=True, use_rms_norm=True, use_rope=True, bias=False
    ),
}


def get_preset(name: str) -> ModelConfig:
    """Get a preset configuration by name."""
    if name not in PRESETS:
        available = ", ".join(PRESETS.keys())
        raise ValueError(f"Unknown preset '{name}'. Available: {available}")
    return PRESETS[name]
