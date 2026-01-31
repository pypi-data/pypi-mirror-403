"""
NAPLY Neural Network Layers
===========================

Core building blocks for neural networks.
"""

import numpy as np
from typing import Optional, List, Dict, Any
from .tensor import Tensor


class Module:
    """
    Base class for all neural network modules.
    
    All custom layers should inherit from this class.
    
    Example:
        class MyLayer(Module):
            def __init__(self, in_features, out_features):
                super().__init__()
                self.weight = Tensor.randn(in_features, out_features, requires_grad=True)
            
            def forward(self, x):
                return x @ self.weight
    """
    
    def __init__(self):
        self._modules: Dict[str, 'Module'] = {}
        self._parameters: Dict[str, Tensor] = {}
        self.training: bool = True
    
    def __setattr__(self, name: str, value: Any):
        if isinstance(value, Module):
            self._modules[name] = value
        elif isinstance(value, Tensor) and value.requires_grad:
            self._parameters[name] = value
        object.__setattr__(self, name, value)
    
    def __call__(self, *args, **kwargs) -> Tensor:
        return self.forward(*args, **kwargs)
    
    def forward(self, *args, **kwargs) -> Tensor:
        raise NotImplementedError("Subclasses must implement forward()")
    
    def parameters(self) -> List[Tensor]:
        """Get all trainable parameters."""
        params = list(self._parameters.values())
        for module in self._modules.values():
            params.extend(module.parameters())
        return params
    
    def named_parameters(self) -> List[tuple]:
        """Get named parameters."""
        params = [(name, p) for name, p in self._parameters.items()]
        for mod_name, module in self._modules.items():
            for param_name, p in module.named_parameters():
                params.append((f"{mod_name}.{param_name}", p))
        return params
    
    def zero_grad(self):
        """Zero all gradients."""
        for p in self.parameters():
            p.grad = None
    
    def train(self, mode: bool = True):
        """Set training mode."""
        self.training = mode
        for module in self._modules.values():
            module.train(mode)
        return self
    
    def eval(self):
        """Set evaluation mode."""
        return self.train(False)
    
    def state_dict(self) -> Dict[str, np.ndarray]:
        """Get all parameters as numpy arrays."""
        state = {}
        for name, param in self.named_parameters():
            state[name] = param.data.copy()
        return state
    
    def load_state_dict(self, state_dict: Dict[str, np.ndarray]):
        """Load parameters from state dict."""
        for name, param in self.named_parameters():
            if name in state_dict:
                param.data = state_dict[name].copy()
    
    def count_parameters(self) -> int:
        """Count total trainable parameters."""
        return sum(np.prod(p.shape) for p in self.parameters())
    
    def __repr__(self) -> str:
        lines = [f"{self.__class__.__name__}("]
        for name, module in self._modules.items():
            lines.append(f"  ({name}): {module}")
        lines.append(")")
        return "\n".join(lines)


class Linear(Module):
    """
    Linear (fully connected) layer.
    
    Args:
        in_features: Input dimension
        out_features: Output dimension
        bias: Whether to include bias (default: True)
        
    Example:
        layer = Linear(768, 3072)
        output = layer(input)  # (B, T, 768) -> (B, T, 3072)
    """
    
    def __init__(self, in_features: int, out_features: int, bias: bool = True):
        super().__init__()
        self.in_features = in_features
        self.out_features = out_features
        
        # Xavier/Glorot initialization
        std = np.sqrt(2.0 / (in_features + out_features))
        self.weight = Tensor(
            np.random.randn(in_features, out_features).astype(np.float32) * std,
            requires_grad=True
        )
        
        if bias:
            self.bias = Tensor(np.zeros(out_features, dtype=np.float32), requires_grad=True)
        else:
            self.bias = None
    
    def forward(self, x: Tensor) -> Tensor:
        out = x @ self.weight
        if self.bias is not None:
            out = out + self.bias
        return out
    
    def __repr__(self) -> str:
        return f"Linear(in_features={self.in_features}, out_features={self.out_features}, bias={self.bias is not None})"


class Embedding(Module):
    """
    Embedding layer - lookup table for indices.
    
    Args:
        num_embeddings: Vocabulary size
        embedding_dim: Embedding dimension
        
    Example:
        embed = Embedding(50000, 768)
        output = embed(token_ids)  # (B, T) -> (B, T, 768)
    """
    
    def __init__(self, num_embeddings: int, embedding_dim: int):
        super().__init__()
        self.num_embeddings = num_embeddings
        self.embedding_dim = embedding_dim
        
        # Initialize with normal distribution
        self.weight = Tensor(
            np.random.randn(num_embeddings, embedding_dim).astype(np.float32) * 0.02,
            requires_grad=True
        )
    
    def forward(self, idx: Tensor) -> Tensor:
        """
        Args:
            idx: Tensor of indices (B, T) with integer values
            
        Returns:
            Tensor of embeddings (B, T, embedding_dim)
        """
        indices = idx.data.astype(np.int32)
        embedded = self.weight.data[indices]
        
        out = Tensor(embedded, requires_grad=self.weight.requires_grad, _children=(self.weight,), _op='embed')
        
        def _backward():
            if self.weight.requires_grad:
                if self.weight.grad is None:
                    self.weight.grad = np.zeros_like(self.weight.data)
                np.add.at(self.weight.grad, indices.flatten(), out.grad.reshape(-1, self.embedding_dim))
        
        out._backward = _backward
        return out
    
    def __repr__(self) -> str:
        return f"Embedding(num_embeddings={self.num_embeddings}, embedding_dim={self.embedding_dim})"


class LayerNorm(Module):
    """
    Layer Normalization.
    
    Args:
        normalized_shape: Input shape to normalize over
        eps: Small constant for numerical stability
        
    Example:
        norm = LayerNorm(768)
        output = norm(input)
    """
    
    def __init__(self, normalized_shape: int, eps: float = 1e-5):
        super().__init__()
        self.normalized_shape = normalized_shape
        self.eps = eps
        
        self.weight = Tensor(np.ones(normalized_shape, dtype=np.float32), requires_grad=True)
        self.bias = Tensor(np.zeros(normalized_shape, dtype=np.float32), requires_grad=True)
    
    def forward(self, x: Tensor) -> Tensor:
        mean = x.mean(axis=-1, keepdims=True)
        var = ((x - mean) ** 2).mean(axis=-1, keepdims=True)
        x_norm = (x - mean) / ((var + self.eps) ** 0.5)
        return x_norm * self.weight + self.bias
    
    def __repr__(self) -> str:
        return f"LayerNorm({self.normalized_shape}, eps={self.eps})"


class RMSNorm(Module):
    """
    RMS Normalization (used in LLaMA and modern LLMs).
    
    Args:
        dim: Dimension to normalize
        eps: Small constant for numerical stability
    """
    
    def __init__(self, dim: int, eps: float = 1e-6):
        super().__init__()
        self.dim = dim
        self.eps = eps
        self.weight = Tensor(np.ones(dim, dtype=np.float32), requires_grad=True)
    
    def forward(self, x: Tensor) -> Tensor:
        rms = ((x ** 2).mean(axis=-1, keepdims=True) + self.eps) ** 0.5
        return (x / rms) * self.weight
    
    def __repr__(self) -> str:
        return f"RMSNorm({self.dim})"


class Dropout(Module):
    """
    Dropout layer.
    
    Args:
        p: Dropout probability (default: 0.1)
    """
    
    def __init__(self, p: float = 0.1):
        super().__init__()
        self.p = p
    
    def forward(self, x: Tensor) -> Tensor:
        if not self.training or self.p == 0:
            return x
        
        mask = (np.random.rand(*x.shape) > self.p).astype(np.float32)
        scale = 1.0 / (1.0 - self.p)
        
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
    
    def __repr__(self) -> str:
        return f"Dropout(p={self.p})"


class Sequential(Module):
    """
    Sequential container for modules.
    
    Example:
        net = Sequential(
            Linear(768, 3072),
            GELU(),
            Linear(3072, 768)
        )
    """
    
    def __init__(self, *modules: Module):
        super().__init__()
        for i, module in enumerate(modules):
            self._modules[str(i)] = module
    
    def forward(self, x: Tensor) -> Tensor:
        for module in self._modules.values():
            x = module(x)
        return x
    
    def __getitem__(self, idx: int) -> Module:
        return list(self._modules.values())[idx]
    
    def __len__(self) -> int:
        return len(self._modules)


class ModuleList(Module):
    """
    List of modules.
    
    Example:
        layers = ModuleList([Linear(768, 768) for _ in range(12)])
    """
    
    def __init__(self, modules: Optional[List[Module]] = None):
        super().__init__()
        if modules:
            for i, module in enumerate(modules):
                self._modules[str(i)] = module
    
    def append(self, module: Module):
        self._modules[str(len(self))] = module
    
    def __getitem__(self, idx: int) -> Module:
        return list(self._modules.values())[idx]
    
    def __len__(self) -> int:
        return len(self._modules)
    
    def __iter__(self):
        return iter(self._modules.values())


class Adapter(Module):
    """
    Adapter layer for efficient fine-tuning.
    
    Bottleneck architecture: Linear down -> activation -> Linear up
    """
    
    def __init__(self, dim: int, bottleneck_dim: int = 64):
        super().__init__()
        self.down = Linear(dim, bottleneck_dim, bias=False)
        self.up = Linear(bottleneck_dim, dim, bias=False)
    
    def forward(self, x: Tensor) -> Tensor:
        return x + self.up(self.down(x).gelu())


class GELU(Module):
    """GELU activation as a module."""
    
    def forward(self, x: Tensor) -> Tensor:
        return x.gelu()
    
    def __repr__(self) -> str:
        return "GELU()"


class SiLU(Module):
    """SiLU/Swish activation as a module."""
    
    def forward(self, x: Tensor) -> Tensor:
        return x.silu()
    
    def __repr__(self) -> str:
        return "SiLU()"


class ReLU(Module):
    """ReLU activation as a module."""
    
    def forward(self, x: Tensor) -> Tensor:
        return x.relu()
    
    def __repr__(self) -> str:
        return "ReLU()"


class Softmax(Module):
    """Softmax activation as a module."""
    
    def __init__(self, dim: int = -1):
        super().__init__()
        self.dim = dim
    
    def forward(self, x: Tensor) -> Tensor:
        return x.softmax(axis=self.dim)
    
    def __repr__(self) -> str:
        return f"Softmax(dim={self.dim})"
