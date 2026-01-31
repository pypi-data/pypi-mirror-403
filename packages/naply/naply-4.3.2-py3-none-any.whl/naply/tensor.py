"""
NAPLY Tensor - Autograd Engine
==============================

Custom tensor implementation with automatic differentiation.
Supports all standard operations with gradient tracking.
"""

import numpy as np
from typing import Optional, Tuple, List, Union, Callable


class Tensor:
    """
    A multi-dimensional array with automatic gradient computation.
    
    This is the core building block for neural networks in NAPLY.
    All operations are tracked for backpropagation.
    
    Example:
        x = Tensor([[1, 2], [3, 4]], requires_grad=True)
        y = x * 2
        z = y.sum()
        z.backward()
        print(x.grad)  # Gradients computed!
    """
    
    def __init__(
        self, 
        data: Union[np.ndarray, list, float, int],
        requires_grad: bool = False,
        _children: Tuple['Tensor', ...] = (),
        _op: str = ''
    ):
        if isinstance(data, np.ndarray):
            self.data = data.astype(np.float32)
        elif isinstance(data, (list, tuple)):
            self.data = np.array(data, dtype=np.float32)
        else:
            self.data = np.array(data, dtype=np.float32)
        
        self.requires_grad = requires_grad
        self.grad: Optional[np.ndarray] = None
        self._backward: Callable = lambda: None
        self._prev = set(_children)
        self._op = _op
    
    @property
    def shape(self) -> Tuple[int, ...]:
        return self.data.shape
    
    @property
    def dtype(self):
        return self.data.dtype
    
    @property
    def T(self) -> 'Tensor':
        return self.transpose()
    
    def __repr__(self) -> str:
        return f"Tensor({self.data}, requires_grad={self.requires_grad})"
    
    def __len__(self) -> int:
        return len(self.data)
    
    def __getitem__(self, idx) -> 'Tensor':
        out = Tensor(self.data[idx], requires_grad=self.requires_grad, _children=(self,), _op='slice')
        
        def _backward():
            if self.requires_grad:
                if self.grad is None:
                    self.grad = np.zeros_like(self.data)
                grad = np.zeros_like(self.data)
                grad[idx] = out.grad
                self.grad += grad
        
        out._backward = _backward
        return out
    
    # ==========================================================================
    # Arithmetic Operations
    # ==========================================================================
    
    def __add__(self, other: Union['Tensor', float, int]) -> 'Tensor':
        other = other if isinstance(other, Tensor) else Tensor(other)
        out = Tensor(
            self.data + other.data,
            requires_grad=self.requires_grad or other.requires_grad,
            _children=(self, other),
            _op='+'
        )
        
        def _backward():
            if self.requires_grad:
                if self.grad is None:
                    self.grad = np.zeros_like(self.data)
                grad = out.grad
                # Handle broadcasting
                if self.shape != out.shape:
                    grad = _unbroadcast(grad, self.shape)
                self.grad += grad
            if other.requires_grad:
                if other.grad is None:
                    other.grad = np.zeros_like(other.data)
                grad = out.grad
                if other.shape != out.shape:
                    grad = _unbroadcast(grad, other.shape)
                other.grad += grad
        
        out._backward = _backward
        return out
    
    def __radd__(self, other: Union['Tensor', float, int]) -> 'Tensor':
        return self.__add__(other)
    
    def __sub__(self, other: Union['Tensor', float, int]) -> 'Tensor':
        return self + (-other)
    
    def __rsub__(self, other: Union['Tensor', float, int]) -> 'Tensor':
        return (-self) + other
    
    def __neg__(self) -> 'Tensor':
        return self * -1
    
    def __mul__(self, other: Union['Tensor', float, int]) -> 'Tensor':
        other = other if isinstance(other, Tensor) else Tensor(other)
        out = Tensor(
            self.data * other.data,
            requires_grad=self.requires_grad or other.requires_grad,
            _children=(self, other),
            _op='*'
        )
        
        def _backward():
            if self.requires_grad:
                if self.grad is None:
                    self.grad = np.zeros_like(self.data)
                grad = other.data * out.grad
                if self.shape != out.shape:
                    grad = _unbroadcast(grad, self.shape)
                self.grad += grad
            if other.requires_grad:
                if other.grad is None:
                    other.grad = np.zeros_like(other.data)
                grad = self.data * out.grad
                if other.shape != out.shape:
                    grad = _unbroadcast(grad, other.shape)
                other.grad += grad
        
        out._backward = _backward
        return out
    
    def __rmul__(self, other: Union['Tensor', float, int]) -> 'Tensor':
        return self.__mul__(other)
    
    def __truediv__(self, other: Union['Tensor', float, int]) -> 'Tensor':
        return self * (other ** -1)
    
    def __rtruediv__(self, other: Union['Tensor', float, int]) -> 'Tensor':
        return other * (self ** -1)
    
    def __pow__(self, power: Union[int, float]) -> 'Tensor':
        out = Tensor(
            self.data ** power,
            requires_grad=self.requires_grad,
            _children=(self,),
            _op=f'**{power}'
        )
        
        def _backward():
            if self.requires_grad:
                if self.grad is None:
                    self.grad = np.zeros_like(self.data)
                self.grad += power * (self.data ** (power - 1)) * out.grad
        
        out._backward = _backward
        return out
    
    # ==========================================================================
    # Matrix Operations
    # ==========================================================================
    
    def matmul(self, other: 'Tensor') -> 'Tensor':
        """Matrix multiplication."""
        out = Tensor(
            np.matmul(self.data, other.data),
            requires_grad=self.requires_grad or other.requires_grad,
            _children=(self, other),
            _op='@'
        )
        
        def _backward():
            if self.requires_grad:
                if self.grad is None:
                    self.grad = np.zeros_like(self.data)
                # For N-D tensors, we swap only the last two dimensions
                other_T = np.swapaxes(other.data, -1, -2)
                grad = np.matmul(out.grad, other_T)
                if self.shape != grad.shape:
                    grad = _unbroadcast(grad, self.shape)
                self.grad += grad
            if other.requires_grad:
                if other.grad is None:
                    other.grad = np.zeros_like(other.data)
                self_T = np.swapaxes(self.data, -1, -2)
                grad = np.matmul(self_T, out.grad)
                if other.shape != grad.shape:
                    grad = _unbroadcast(grad, other.shape)
                other.grad += grad
        
        out._backward = _backward
        return out
    
    def __matmul__(self, other: 'Tensor') -> 'Tensor':
        return self.matmul(other)
    
    def transpose(self, *axes) -> 'Tensor':
        """Transpose the tensor."""
        if not axes:
            axes = None
        out = Tensor(
            np.transpose(self.data, axes),
            requires_grad=self.requires_grad,
            _children=(self,),
            _op='T'
        )
        
        def _backward():
            if self.requires_grad:
                if self.grad is None:
                    self.grad = np.zeros_like(self.data)
                if axes is None:
                    self.grad += np.transpose(out.grad)
                else:
                    inv_axes = np.argsort(axes)
                    self.grad += np.transpose(out.grad, inv_axes)
        
        out._backward = _backward
        return out
    
    def swapaxes(self, axis1: int, axis2: int) -> 'Tensor':
        """Swap two axes of the tensor."""
        out = Tensor(
            np.swapaxes(self.data, axis1, axis2),
            requires_grad=self.requires_grad,
            _children=(self,),
            _op='swapaxes'
        )
        
        def _backward():
            if self.requires_grad:
                if self.grad is None:
                    self.grad = np.zeros_like(self.data)
                self.grad += np.swapaxes(out.grad, axis1, axis2)
        
        out._backward = _backward
        return out
    
    def reshape(self, *shape) -> 'Tensor':
        """Reshape the tensor."""
        if len(shape) == 1 and isinstance(shape[0], (tuple, list)):
            shape = shape[0]
        out = Tensor(
            self.data.reshape(shape),
            requires_grad=self.requires_grad,
            _children=(self,),
            _op='reshape'
        )
        
        def _backward():
            if self.requires_grad:
                if self.grad is None:
                    self.grad = np.zeros_like(self.data)
                self.grad += out.grad.reshape(self.shape)
        
        out._backward = _backward
        return out
    
    def view(self, *shape) -> 'Tensor':
        """Alias for reshape."""
        return self.reshape(*shape)
    
    def flatten(self, start_dim: int = 0, end_dim: int = -1) -> 'Tensor':
        """Flatten dimensions."""
        shape = list(self.shape)
        if end_dim < 0:
            end_dim = len(shape) + end_dim
        new_shape = shape[:start_dim] + [-1] + shape[end_dim+1:]
        return self.reshape(*new_shape)
    
    # ==========================================================================
    # Reduction Operations
    # ==========================================================================
    
    def sum(self, axis: Optional[int] = None, keepdims: bool = False) -> 'Tensor':
        """Sum reduction."""
        out = Tensor(
            np.sum(self.data, axis=axis, keepdims=keepdims),
            requires_grad=self.requires_grad,
            _children=(self,),
            _op='sum'
        )
        
        def _backward():
            if self.requires_grad:
                if self.grad is None:
                    self.grad = np.zeros_like(self.data)
                grad = out.grad
                if axis is not None and not keepdims:
                    grad = np.expand_dims(grad, axis)
                self.grad += np.broadcast_to(grad, self.shape)
        
        out._backward = _backward
        return out
    
    def mean(self, axis: Optional[int] = None, keepdims: bool = False) -> 'Tensor':
        """Mean reduction."""
        n = self.data.size if axis is None else self.data.shape[axis]
        return self.sum(axis=axis, keepdims=keepdims) / n
    
    def max(self, axis: Optional[int] = None, keepdims: bool = False) -> 'Tensor':
        """Max reduction."""
        out = Tensor(
            np.max(self.data, axis=axis, keepdims=keepdims),
            requires_grad=self.requires_grad,
            _children=(self,),
            _op='max'
        )
        
        def _backward():
            if self.requires_grad:
                if self.grad is None:
                    self.grad = np.zeros_like(self.data)
                max_vals = np.max(self.data, axis=axis, keepdims=True)
                mask = (self.data == max_vals).astype(np.float32)
                grad = out.grad
                if axis is not None and not keepdims:
                    grad = np.expand_dims(grad, axis)
                self.grad += mask * np.broadcast_to(grad, self.shape)
        
        out._backward = _backward
        return out
    
    def argmax(self, axis: Optional[int] = None) -> np.ndarray:
        """Argmax (returns numpy array, not tracked)."""
        return np.argmax(self.data, axis=axis)
    
    # ==========================================================================
    # Activation Functions
    # ==========================================================================
    
    def relu(self) -> 'Tensor':
        """ReLU activation."""
        out = Tensor(
            np.maximum(0, self.data),
            requires_grad=self.requires_grad,
            _children=(self,),
            _op='relu'
        )
        
        def _backward():
            if self.requires_grad:
                if self.grad is None:
                    self.grad = np.zeros_like(self.data)
                self.grad += (self.data > 0).astype(np.float32) * out.grad
        
        out._backward = _backward
        return out
    
    def gelu(self) -> 'Tensor':
        """GELU activation."""
        # Approximation: 0.5 * x * (1 + tanh(sqrt(2/pi) * (x + 0.044715 * x^3)))
        x = self.data
        cdf = 0.5 * (1 + np.tanh(np.sqrt(2 / np.pi) * (x + 0.044715 * x**3)))
        out = Tensor(
            x * cdf,
            requires_grad=self.requires_grad,
            _children=(self,),
            _op='gelu'
        )
        
        def _backward():
            if self.requires_grad:
                if self.grad is None:
                    self.grad = np.zeros_like(self.data)
                # Approximate gradient
                x = self.data
                tanh_arg = np.sqrt(2 / np.pi) * (x + 0.044715 * x**3)
                tanh_val = np.tanh(tanh_arg)
                sech2 = 1 - tanh_val**2
                grad = 0.5 * (1 + tanh_val) + 0.5 * x * sech2 * np.sqrt(2 / np.pi) * (1 + 3 * 0.044715 * x**2)
                self.grad += grad * out.grad
        
        out._backward = _backward
        return out
    
    def silu(self) -> 'Tensor':
        """SiLU/Swish activation: x * sigmoid(x)."""
        sigmoid = 1 / (1 + np.exp(-self.data))
        out = Tensor(
            self.data * sigmoid,
            requires_grad=self.requires_grad,
            _children=(self,),
            _op='silu'
        )
        
        def _backward():
            if self.requires_grad:
                if self.grad is None:
                    self.grad = np.zeros_like(self.data)
                x = self.data
                sig = 1 / (1 + np.exp(-x))
                grad = sig + x * sig * (1 - sig)
                self.grad += grad * out.grad
        
        out._backward = _backward
        return out
    
    def sigmoid(self) -> 'Tensor':
        """Sigmoid activation."""
        sig = 1 / (1 + np.exp(-np.clip(self.data, -500, 500)))
        out = Tensor(
            sig,
            requires_grad=self.requires_grad,
            _children=(self,),
            _op='sigmoid'
        )
        
        def _backward():
            if self.requires_grad:
                if self.grad is None:
                    self.grad = np.zeros_like(self.data)
                s = out.data
                self.grad += s * (1 - s) * out.grad
        
        out._backward = _backward
        return out
    
    def tanh(self) -> 'Tensor':
        """Tanh activation."""
        out = Tensor(
            np.tanh(self.data),
            requires_grad=self.requires_grad,
            _children=(self,),
            _op='tanh'
        )
        
        def _backward():
            if self.requires_grad:
                if self.grad is None:
                    self.grad = np.zeros_like(self.data)
                self.grad += (1 - out.data**2) * out.grad
        
        out._backward = _backward
        return out
    
    def softmax(self, axis: int = -1) -> 'Tensor':
        """Softmax activation."""
        exp_x = np.exp(self.data - np.max(self.data, axis=axis, keepdims=True))
        out = Tensor(
            exp_x / np.sum(exp_x, axis=axis, keepdims=True),
            requires_grad=self.requires_grad,
            _children=(self,),
            _op='softmax'
        )
        
        def _backward():
            if self.requires_grad:
                if self.grad is None:
                    self.grad = np.zeros_like(self.data)
                s = out.data
                # Jacobian-vector product
                self.grad += s * (out.grad - np.sum(out.grad * s, axis=axis, keepdims=True))
        
        out._backward = _backward
        return out
    
    def log_softmax(self, axis: int = -1) -> 'Tensor':
        """Log-softmax for numerical stability."""
        max_val = np.max(self.data, axis=axis, keepdims=True)
        shifted = self.data - max_val
        log_sum_exp = np.log(np.sum(np.exp(shifted), axis=axis, keepdims=True))
        out = Tensor(
            shifted - log_sum_exp,
            requires_grad=self.requires_grad,
            _children=(self,),
            _op='log_softmax'
        )
        
        def _backward():
            if self.requires_grad:
                if self.grad is None:
                    self.grad = np.zeros_like(self.data)
                s = np.exp(out.data)
                self.grad += out.grad - s * np.sum(out.grad, axis=axis, keepdims=True)
        
        out._backward = _backward
        return out
    
    # ==========================================================================
    # Mathematical Functions
    # ==========================================================================
    
    def exp(self) -> 'Tensor':
        """Exponential."""
        out = Tensor(
            np.exp(self.data),
            requires_grad=self.requires_grad,
            _children=(self,),
            _op='exp'
        )
        
        def _backward():
            if self.requires_grad:
                if self.grad is None:
                    self.grad = np.zeros_like(self.data)
                self.grad += out.data * out.grad
        
        out._backward = _backward
        return out
    
    def log(self) -> 'Tensor':
        """Natural logarithm."""
        out = Tensor(
            np.log(self.data + 1e-8),
            requires_grad=self.requires_grad,
            _children=(self,),
            _op='log'
        )
        
        def _backward():
            if self.requires_grad:
                if self.grad is None:
                    self.grad = np.zeros_like(self.data)
                self.grad += (1 / (self.data + 1e-8)) * out.grad
        
        out._backward = _backward
        return out
    
    def sqrt(self) -> 'Tensor':
        """Square root."""
        return self ** 0.5
    
    def abs(self) -> 'Tensor':
        """Absolute value."""
        out = Tensor(
            np.abs(self.data),
            requires_grad=self.requires_grad,
            _children=(self,),
            _op='abs'
        )
        
        def _backward():
            if self.requires_grad:
                if self.grad is None:
                    self.grad = np.zeros_like(self.data)
                self.grad += np.sign(self.data) * out.grad
        
        out._backward = _backward
        return out
    
    def clip(self, min_val: float, max_val: float) -> 'Tensor':
        """Clip values."""
        out = Tensor(
            np.clip(self.data, min_val, max_val),
            requires_grad=self.requires_grad,
            _children=(self,),
            _op='clip'
        )
        
        def _backward():
            if self.requires_grad:
                if self.grad is None:
                    self.grad = np.zeros_like(self.data)
                mask = ((self.data >= min_val) & (self.data <= max_val)).astype(np.float32)
                self.grad += mask * out.grad
        
        out._backward = _backward
        return out
    
    # ==========================================================================
    # Concatenation & Stacking
    # ==========================================================================
    
    @staticmethod
    def cat(tensors: List['Tensor'], axis: int = 0) -> 'Tensor':
        """Concatenate tensors along an axis."""
        data = np.concatenate([t.data for t in tensors], axis=axis)
        requires_grad = any(t.requires_grad for t in tensors)
        out = Tensor(data, requires_grad=requires_grad, _children=tuple(tensors), _op='cat')
        
        def _backward():
            if not requires_grad:
                return
            # Split gradient back to each tensor
            splits = np.cumsum([t.shape[axis] for t in tensors[:-1]])
            grads = np.split(out.grad, splits, axis=axis)
            for t, g in zip(tensors, grads):
                if t.requires_grad:
                    if t.grad is None:
                        t.grad = np.zeros_like(t.data)
                    t.grad += g
        
        out._backward = _backward
        return out
    
    @staticmethod
    def stack(tensors: List['Tensor'], axis: int = 0) -> 'Tensor':
        """Stack tensors along a new axis."""
        data = np.stack([t.data for t in tensors], axis=axis)
        requires_grad = any(t.requires_grad for t in tensors)
        out = Tensor(data, requires_grad=requires_grad, _children=tuple(tensors), _op='stack')
        
        def _backward():
            if not requires_grad:
                return
            grads = np.split(out.grad, len(tensors), axis=axis)
            for t, g in zip(tensors, grads):
                if t.requires_grad:
                    if t.grad is None:
                        t.grad = np.zeros_like(t.data)
                    t.grad += np.squeeze(g, axis=axis)
        
        out._backward = _backward
        return out
    
    # ==========================================================================
    # Backpropagation
    # ==========================================================================
    
    def backward(self):
        """Compute gradients via reverse-mode autodiff."""
        # Topological order
        topo = []
        visited = set()
        
        def build_topo(v):
            if v not in visited:
                visited.add(v)
                for child in v._prev:
                    build_topo(child)
                topo.append(v)
        
        build_topo(self)
        
        # Start with gradient of 1 for the output
        self.grad = np.ones_like(self.data)
        
        # Backward pass
        for v in reversed(topo):
            v._backward()
    
    def zero_grad(self):
        """Reset gradients to None."""
        self.grad = None
    
    # ==========================================================================
    # Pickle Support (for checkpoint saving)
    # ==========================================================================
    
    def __getstate__(self):
        """Prepare state for pickling - exclude the unpicklable _backward lambda."""
        state = self.__dict__.copy()
        # Remove the _backward function as lambdas can't be pickled
        state['_backward'] = None
        # Convert _prev set to a picklable format (list of None placeholders)
        # We don't preserve the computation graph across pickle boundaries
        state['_prev'] = set()
        return state
    
    def __setstate__(self, state):
        """Restore state after unpickling."""
        self.__dict__.update(state)
        # Restore _backward to a no-op lambda
        self._backward = lambda: None
    
    # ==========================================================================
    # Utility Methods
    # ==========================================================================
    
    def detach(self) -> 'Tensor':
        """Create a tensor with no gradient tracking."""
        return Tensor(self.data.copy(), requires_grad=False)
    
    def numpy(self) -> np.ndarray:
        """Convert to numpy array."""
        return self.data.copy()
    
    def item(self) -> float:
        """Get scalar value."""
        return float(self.data.flatten()[0])
    
    def copy(self) -> 'Tensor':
        """Create a copy."""
        return Tensor(self.data.copy(), requires_grad=self.requires_grad)
    
    @staticmethod
    def zeros(*shape, requires_grad: bool = False) -> 'Tensor':
        """Create tensor of zeros."""
        return Tensor(np.zeros(shape), requires_grad=requires_grad)
    
    @staticmethod
    def ones(*shape, requires_grad: bool = False) -> 'Tensor':
        """Create tensor of ones."""
        return Tensor(np.ones(shape), requires_grad=requires_grad)
    
    @staticmethod
    def randn(*shape, requires_grad: bool = False) -> 'Tensor':
        """Create tensor with random normal values."""
        return Tensor(np.random.randn(*shape).astype(np.float32), requires_grad=requires_grad)
    
    @staticmethod
    def rand(*shape, requires_grad: bool = False) -> 'Tensor':
        """Create tensor with random uniform values [0, 1)."""
        return Tensor(np.random.rand(*shape).astype(np.float32), requires_grad=requires_grad)
    
    @staticmethod
    def arange(start, stop=None, step=1, requires_grad: bool = False) -> 'Tensor':
        """Create a range tensor."""
        if stop is None:
            start, stop = 0, start
        return Tensor(np.arange(start, stop, step).astype(np.float32), requires_grad=requires_grad)


def _unbroadcast(grad: np.ndarray, shape: Tuple[int, ...]) -> np.ndarray:
    """Sum out broadcasted dimensions."""
    # Add dimensions at the front if needed
    while len(grad.shape) > len(shape):
        grad = grad.sum(axis=0)
    # Sum along dimensions that were broadcast
    for i, (g, s) in enumerate(zip(grad.shape, shape)):
        if s == 1 and g > 1:
            grad = grad.sum(axis=i, keepdims=True)
    return grad
