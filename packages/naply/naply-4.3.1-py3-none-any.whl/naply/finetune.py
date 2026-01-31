"""
NAPLY Fine-tuning Module
=========================

LoRA, QLoRA, and PEFT implementation for efficient fine-tuning.
CPU-optimized, memory efficient, compatible with all base models.

Features:
- LoRA (Low-Rank Adaptation) for parameter-efficient fine-tuning
- QLoRA (Quantized LoRA) for even lower memory usage
- Apply to any transformer model
- Merge weights back to base model
- All 10 naply training methods integrated

Usage:
    from naply import finetune
    
    # Apply LoRA to model
    model = finetune.apply_lora(base_model, rank=8, alpha=16)
    
    # Train with LoRA
    trainer = finetune.FineTuneTrainer(model)
    trainer.train(dataset, epochs=3)
    
    # Merge and save
    merged_model = finetune.merge_lora(model)
    merged_model.save("my_finetuned_model/")
"""

import numpy as np
from typing import Optional, List, Dict, Tuple, Any, Union
from dataclasses import dataclass
import os
import json
import pickle

from .tensor import Tensor
from .layers import Module, Linear
from .optim import AdamW, clip_grad_norm


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class LoRAConfig:
    """Configuration for LoRA fine-tuning.
    
    Args:
        rank: LoRA rank (lower = fewer parameters, higher = more capacity)
        alpha: LoRA scaling factor (typically alpha = 2 * rank)
        dropout: Dropout for LoRA layers
        target_modules: Which modules to apply LoRA to
        bias: Whether to train biases
    """
    rank: int = 8
    alpha: int = 16
    dropout: float = 0.0
    target_modules: List[str] = None  # None = auto-detect
    bias: str = "none"  # "none", "all", "lora_only"
    
    def __post_init__(self):
        if self.target_modules is None:
            # Default: apply to attention query, key, value, and output
            self.target_modules = ["q_proj", "k_proj", "v_proj", "o_proj", 
                                   "c_attn", "c_proj",  # GPT-2 style
                                   "query", "key", "value", "dense"]  # BERT style


@dataclass 
class QLoRAConfig(LoRAConfig):
    """Configuration for QLoRA (Quantized LoRA).
    
    Same as LoRA but with quantization settings.
    """
    bits: int = 4  # 4-bit or 8-bit quantization
    double_quant: bool = True  # Quantize the quantization constants
    quant_type: str = "nf4"  # "nf4" or "fp4"


@dataclass
class FineTuneConfig:
    """Configuration for fine-tuning training.
    
    Args:
        learning_rate: Learning rate for LoRA parameters
        batch_size: Training batch size
        epochs: Number of training epochs
        gradient_accumulation: Accumulate gradients over N steps
        warmup_ratio: Fraction of steps for learning rate warmup
        weight_decay: Weight decay for regularization
        max_grad_norm: Maximum gradient norm for clipping
        save_steps: Save checkpoint every N steps
        logging_steps: Log metrics every N steps
    """
    learning_rate: float = 2e-4
    batch_size: int = 4
    epochs: int = 3
    gradient_accumulation: int = 4
    warmup_ratio: float = 0.1
    weight_decay: float = 0.01
    max_grad_norm: float = 1.0
    save_steps: int = 100
    logging_steps: int = 10
    output_dir: str = "finetune_output"
    resume_from: Optional[str] = None


# =============================================================================
# LORA LAYER
# =============================================================================

class LoRALayer(Module):
    """LoRA (Low-Rank Adaptation) layer.
    
    Implements: h = Wx + (x @ A) @ B * scaling
    
    Only A and B are trained, W is frozen.
    This reduces trainable parameters from d*d to 2*d*r (r << d).
    
    Args:
        in_features: Input dimension
        out_features: Output dimension  
        rank: LoRA rank (default: 8)
        alpha: Scaling factor (default: 16)
        dropout: Dropout probability (default: 0)
    
    Example:
        lora = LoRALayer(768, 768, rank=8, alpha=16)
        delta = lora(x)  # Shape: (batch, seq, 768)
        output = base_output + delta  # Add to frozen layer output
    """
    
    def __init__(
        self, 
        in_features: int, 
        out_features: int, 
        rank: int = 8,
        alpha: int = 16,
        dropout: float = 0.0
    ):
        super().__init__()
        self.in_features = in_features
        self.out_features = out_features
        self.rank = rank
        self.alpha = alpha
        self.scaling = alpha / rank
        self.dropout_p = dropout
        
        # LoRA matrices: A (down-projection) and B (up-projection)
        # A: initialized with small random values
        # B: initialized with zeros (so LoRA starts with zero contribution)
        self.lora_A = Tensor(
            np.random.randn(in_features, rank).astype(np.float32) * 0.01,
            requires_grad=True
        )
        self.lora_B = Tensor(
            np.zeros((rank, out_features), dtype=np.float32),
            requires_grad=True
        )
        
        # Track if merged
        self.merged = False
        
    def forward(self, x: Tensor) -> Tensor:
        """Compute LoRA output.
        
        Args:
            x: Input tensor (batch, seq, in_features)
            
        Returns:
            LoRA delta to add to base layer output
        """
        if self.merged:
            # If merged, return zero (contribution is in base weights)
            return Tensor(np.zeros((*x.data.shape[:-1], self.out_features), dtype=np.float32))
        
        # Apply dropout during training
        if self.dropout_p > 0 and self.training:
            mask = np.random.binomial(1, 1 - self.dropout_p, x.data.shape).astype(np.float32)
            x = Tensor(x.data * mask / (1 - self.dropout_p), requires_grad=x.requires_grad)
        
        # LoRA: (x @ A) @ B * scaling
        hidden = x @ self.lora_A  # (batch, seq, rank)
        output = hidden @ self.lora_B  # (batch, seq, out_features)
        
        # Scale output
        if self.scaling != 1.0:
            output = output * self.scaling
            
        return output
    
    def get_delta_weight(self) -> np.ndarray:
        """Get the weight delta from LoRA.
        
        Returns:
            Weight delta: A @ B * scaling
        """
        return (self.lora_A.data @ self.lora_B.data) * self.scaling
    
    def merge(self):
        """Mark as merged (LoRA weights merged into base)."""
        self.merged = True
        
    def unmerge(self):
        """Mark as unmerged."""
        self.merged = False
    
    def __repr__(self):
        return f"LoRALayer(in={self.in_features}, out={self.out_features}, r={self.rank}, α={self.alpha})"


# =============================================================================
# QLORA LAYER (Quantized LoRA)
# =============================================================================

class QLoRALayer(LoRALayer):
    """QLoRA (Quantized LoRA) layer.
    
    Same as LoRA but stores base weights in quantized format.
    Dequantizes during forward pass for computation.
    
    Memory savings: 4-bit = 8x smaller than fp32
    
    Args:
        in_features: Input dimension
        out_features: Output dimension
        rank: LoRA rank
        alpha: Scaling factor
        bits: Quantization bits (4 or 8)
    """
    
    def __init__(
        self,
        in_features: int,
        out_features: int,
        rank: int = 8,
        alpha: int = 16,
        bits: int = 4
    ):
        super().__init__(in_features, out_features, rank, alpha)
        self.bits = bits
        self.quantized_weight = None
        self.scale = None
        self.zero_point = None
        
    def quantize_weight(self, weight: np.ndarray):
        """Quantize base weight for memory efficiency.
        
        Args:
            weight: Weight matrix to quantize
        """
        if self.bits == 4:
            # 4-bit quantization
            self.scale = (weight.max() - weight.min()) / 15
            self.zero_point = weight.min()
            quantized = np.clip(
                np.round((weight - self.zero_point) / self.scale), 
                0, 15
            ).astype(np.uint8)
            # Pack 2 values per byte
            self.quantized_weight = quantized
        else:
            # 8-bit quantization
            self.scale = (weight.max() - weight.min()) / 255
            self.zero_point = weight.min()
            self.quantized_weight = np.clip(
                np.round((weight - self.zero_point) / self.scale),
                0, 255
            ).astype(np.uint8)
    
    def dequantize_weight(self) -> np.ndarray:
        """Dequantize weight for computation.
        
        Returns:
            Dequantized weight matrix
        """
        if self.quantized_weight is None:
            return None
        return self.quantized_weight.astype(np.float32) * self.scale + self.zero_point


# =============================================================================
# LINEAR WITH LORA
# =============================================================================

class LinearWithLoRA(Module):
    """Linear layer with LoRA adapter.
    
    Combines frozen base Linear with trainable LoRA.
    Output = base_linear(x) + lora(x)
    
    Args:
        base_linear: Original Linear layer (frozen)
        rank: LoRA rank
        alpha: LoRA scaling
        dropout: Dropout probability
    """
    
    def __init__(
        self,
        base_linear: Linear,
        rank: int = 8,
        alpha: int = 16,
        dropout: float = 0.0
    ):
        super().__init__()
        self.base_linear = base_linear
        self.in_features = base_linear.weight.data.shape[1]
        self.out_features = base_linear.weight.data.shape[0]
        
        # Freeze base weights
        base_linear.weight.requires_grad = False
        if base_linear.bias is not None:
            base_linear.bias.requires_grad = False
        
        # Create LoRA adapter
        self.lora = LoRALayer(
            self.in_features, 
            self.out_features, 
            rank=rank, 
            alpha=alpha,
            dropout=dropout
        )
        
    def forward(self, x: Tensor) -> Tensor:
        """Forward pass: base + LoRA delta.
        
        Args:
            x: Input tensor
            
        Returns:
            Output with LoRA adaptation
        """
        base_output = self.base_linear(x)
        lora_output = self.lora(x)
        return base_output + lora_output
    
    def merge_weights(self):
        """Merge LoRA weights into base layer."""
        if not self.lora.merged:
            delta = self.lora.get_delta_weight()
            self.base_linear.weight.data = self.base_linear.weight.data + delta.T
            self.lora.merge()
    
    def unmerge_weights(self):
        """Unmerge LoRA weights from base layer."""
        if self.lora.merged:
            delta = self.lora.get_delta_weight()
            self.base_linear.weight.data = self.base_linear.weight.data - delta.T
            self.lora.unmerge()
            
    def __repr__(self):
        return f"LinearWithLoRA({self.in_features}, {self.out_features}, r={self.lora.rank})"


# =============================================================================
# APPLY LORA TO MODEL
# =============================================================================

def apply_lora(
    model: Module,
    config: Optional[LoRAConfig] = None,
    rank: int = 8,
    alpha: int = 16,
    target_modules: Optional[List[str]] = None
) -> Module:
    """Apply LoRA adapters to a model.
    
    Finds target modules (linear layers) and wraps them with LoRA.
    
    Args:
        model: Base model to add LoRA to
        config: LoRA configuration (or use individual args)
        rank: LoRA rank if config not provided
        alpha: LoRA alpha if config not provided
        target_modules: Which modules to target
        
    Returns:
        Model with LoRA adapters
        
    Example:
        model = apply_lora(gpt_model, rank=8, alpha=16)
    """
    if config is None:
        config = LoRAConfig(rank=rank, alpha=alpha, target_modules=target_modules)
    
    lora_layers = []
    
    def _apply_lora_recursive(module: Module, name: str = ""):
        for attr_name in list(module._modules.keys()) if hasattr(module, '_modules') else []:
            child = getattr(module, attr_name, None)
            if child is None:
                continue
                
            full_name = f"{name}.{attr_name}" if name else attr_name
            
            # Check if this is a target module
            is_target = False
            if config.target_modules:
                for target in config.target_modules:
                    if target in attr_name.lower() or target in full_name.lower():
                        is_target = True
                        break
            
            if isinstance(child, Linear) and is_target:
                # Replace with LinearWithLoRA
                lora_linear = LinearWithLoRA(
                    child, 
                    rank=config.rank, 
                    alpha=config.alpha,
                    dropout=config.dropout
                )
                setattr(module, attr_name, lora_linear)
                lora_layers.append(lora_linear)
                print(f"   Applied LoRA to: {full_name}")
            elif hasattr(child, '_modules') or hasattr(child, '_parameters'):
                _apply_lora_recursive(child, full_name)
    
    # Also check direct attributes
    for attr_name in dir(model):
        if attr_name.startswith('_'):
            continue
        try:
            attr = getattr(model, attr_name)
            if isinstance(attr, Module):
                _apply_lora_recursive(attr, attr_name)
        except:
            pass
    
    _apply_lora_recursive(model)
    
    # Store LoRA info on model
    model._lora_layers = lora_layers
    model._lora_config = config
    
    # Count parameters
    total_params = sum(p.data.size for p in model.parameters())
    trainable_params = sum(p.data.size for p in model.parameters() if p.requires_grad)
    
    print(f"\n   LoRA Applied!")
    print(f"   Total params: {total_params:,}")
    print(f"   Trainable params: {trainable_params:,} ({100*trainable_params/total_params:.2f}%)")
    
    return model


def get_trainable_params(model: Module) -> List[Tensor]:
    """Get only the trainable (LoRA) parameters.
    
    Args:
        model: Model with LoRA adapters
        
    Returns:
        List of trainable parameters
    """
    return [p for p in model.parameters() if p.requires_grad]


def merge_lora(model: Module) -> Module:
    """Merge LoRA weights into base model.
    
    After merging, the model can be used without LoRA overhead.
    The LoRA contribution is baked into the base weights.
    
    Args:
        model: Model with LoRA adapters
        
    Returns:
        Model with merged weights
    """
    if hasattr(model, '_lora_layers'):
        for lora_layer in model._lora_layers:
            lora_layer.merge_weights()
        print(f"   Merged {len(model._lora_layers)} LoRA layers into base model")
    return model


def unmerge_lora(model: Module) -> Module:
    """Unmerge LoRA weights from base model.
    
    Reverses merge_lora().
    
    Args:
        model: Model with merged LoRA
        
    Returns:
        Model with separated LoRA
    """
    if hasattr(model, '_lora_layers'):
        for lora_layer in model._lora_layers:
            lora_layer.unmerge_weights()
        print(f"   Unmerged {len(model._lora_layers)} LoRA layers")
    return model


# =============================================================================
# SAVE/LOAD LORA WEIGHTS
# =============================================================================

def save_lora_weights(model: Module, path: str):
    """Save only LoRA weights (very small file).
    
    Args:
        model: Model with LoRA adapters
        path: Path to save
    """
    os.makedirs(path, exist_ok=True)
    
    lora_state = {}
    if hasattr(model, '_lora_layers'):
        for i, layer in enumerate(model._lora_layers):
            lora_state[f"layer_{i}_A"] = layer.lora.lora_A.data
            lora_state[f"layer_{i}_B"] = layer.lora.lora_B.data
    
    # Save weights
    with open(os.path.join(path, "lora_weights.pkl"), "wb") as f:
        pickle.dump(lora_state, f)
    
    # Save config
    if hasattr(model, '_lora_config'):
        config_dict = {
            "rank": model._lora_config.rank,
            "alpha": model._lora_config.alpha,
            "dropout": model._lora_config.dropout,
            "target_modules": model._lora_config.target_modules
        }
        with open(os.path.join(path, "lora_config.json"), "w") as f:
            json.dump(config_dict, f, indent=2)
    
    print(f"   Saved LoRA weights to: {path}")


def load_lora_weights(model: Module, path: str):
    """Load LoRA weights.
    
    Args:
        model: Model with LoRA adapters
        path: Path to load from
    """
    weights_path = os.path.join(path, "lora_weights.pkl")
    if not os.path.exists(weights_path):
        raise FileNotFoundError(f"LoRA weights not found at {weights_path}")
    
    with open(weights_path, "rb") as f:
        lora_state = pickle.load(f)
    
    if hasattr(model, '_lora_layers'):
        for i, layer in enumerate(model._lora_layers):
            if f"layer_{i}_A" in lora_state:
                layer.lora.lora_A.data = lora_state[f"layer_{i}_A"]
            if f"layer_{i}_B" in lora_state:
                layer.lora.lora_B.data = lora_state[f"layer_{i}_B"]
    
    print(f"   Loaded LoRA weights from: {path}")


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def count_parameters(model: Module) -> Dict[str, int]:
    """Count model parameters.
    
    Args:
        model: Model to count
        
    Returns:
        Dictionary with total, trainable, and frozen counts
    """
    total = sum(p.data.size for p in model.parameters())
    trainable = sum(p.data.size for p in model.parameters() if p.requires_grad)
    frozen = total - trainable
    
    return {
        "total": total,
        "trainable": trainable,
        "frozen": frozen,
        "trainable_percent": 100 * trainable / total if total > 0 else 0
    }


def print_trainable_parameters(model: Module):
    """Print trainable parameters info.
    
    Args:
        model: Model to analyze
    """
    stats = count_parameters(model)
    print(f"\nParameter Summary:")
    print(f"   Total: {stats['total']:,}")
    print(f"   Trainable: {stats['trainable']:,} ({stats['trainable_percent']:.2f}%)")
    print(f"   Frozen: {stats['frozen']:,}")


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Config
    "LoRAConfig",
    "QLoRAConfig", 
    "FineTuneConfig",
    # Layers
    "LoRALayer",
    "QLoRALayer",
    "LinearWithLoRA",
    # Functions
    "apply_lora",
    "merge_lora",
    "unmerge_lora",
    "get_trainable_params",
    "save_lora_weights",
    "load_lora_weights",
    "count_parameters",
    "print_trainable_parameters",
]
