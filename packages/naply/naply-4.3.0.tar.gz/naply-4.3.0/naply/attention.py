"""
NAPLY Attention Mechanisms
==========================

Multi-head attention and variants for transformer models.
"""

import numpy as np
from typing import Optional, Tuple
from .tensor import Tensor
from .layers import Module, Linear


class MultiHeadAttention(Module):
    """
    Multi-Head Self-Attention with causal masking.
    
    Args:
        n_embd: Embedding dimension
        n_head: Number of attention heads
        dropout: Attention dropout probability
        bias: Whether to use bias in projections
        
    Example:
        attn = MultiHeadAttention(768, n_head=12)
        output = attn(x)  # (B, T, 768) -> (B, T, 768)
    """
    
    def __init__(
        self, 
        n_embd: int, 
        n_head: int, 
        dropout: float = 0.1,
        bias: bool = True,
        causal: bool = True
    ):
        super().__init__()
        assert n_embd % n_head == 0, f"n_embd ({n_embd}) must be divisible by n_head ({n_head})"
        
        self.n_embd = n_embd
        self.n_head = n_head
        self.head_dim = n_embd // n_head
        self.dropout = dropout
        self.causal = causal
        
        # Combined QKV projection for efficiency
        self.c_attn = Linear(n_embd, 3 * n_embd, bias=bias)
        # Output projection
        self.c_proj = Linear(n_embd, n_embd, bias=bias)
        
        self.scale = 1.0 / np.sqrt(self.head_dim)
    
    def forward(
        self, 
        x: Tensor, 
        mask: Optional[np.ndarray] = None,
        past_kv: Optional[Tuple[Tensor, Tensor]] = None
    ) -> Tuple[Tensor, Optional[Tuple[Tensor, Tensor]]]:
        """
        Args:
            x: Input tensor (B, T, C)
            mask: Optional attention mask
            past_kv: Optional past key-value for incremental decoding
            
        Returns:
            output: Attention output (B, T, C)
            present_kv: Current key-value for caching
        """
        B, T, C = x.shape
        
        # Compute Q, K, V
        qkv = self.c_attn(x)

        
        # Actually split properly
        qkv_split = qkv.reshape(B, T, 3, self.n_head, self.head_dim)
        qkv_trans = qkv_split.transpose(0, 2, 3, 1, 4)
        
        q = qkv_trans[:, 0]  # (B, H, T, D)
        k = qkv_trans[:, 1]  # (B, H, T, D)
        v = qkv_trans[:, 2]  # (B, H, T, D)
        
        # Handle KV cache for incremental decoding
        if past_kv is not None:
            past_k, past_v = past_kv
            k = Tensor.cat([past_k, k], axis=2)
            v = Tensor.cat([past_v, v], axis=2)
        
        present_kv = (k, v)
        
        # Attention scores: (B, H, T, T)
        k_T = k.transpose(0, 1, 3, 2)
        scores = (q @ k_T) * self.scale
        
        # Causal mask
        if self.causal:
            T_k = k.shape[2]
            causal_mask = np.triu(np.ones((T, T_k)), k=1).astype(bool)
            if T_k > T:  # Handle incremental decoding
                causal_mask = np.triu(np.ones((T, T_k)), k=T_k-T+1).astype(bool)
            scores_data = scores.data.copy()
            scores_data[:, :, causal_mask] = -1e9
            scores = Tensor(scores_data, requires_grad=scores.requires_grad)
        
        # Additional mask
        if mask is not None:
            scores_data = scores.data.copy()
            scores_data[~mask] = -1e9
            scores = Tensor(scores_data, requires_grad=scores.requires_grad)
        
        # Softmax
        attn_weights = scores.softmax(axis=-1)
        
        # Dropout during training
        if self.training and self.dropout > 0:
            drop_mask = (np.random.rand(*attn_weights.shape) > self.dropout).astype(np.float32)
            attn_weights = Tensor(attn_weights.data * drop_mask / (1 - self.dropout), 
                                  requires_grad=attn_weights.requires_grad)
        
        # Apply attention to values
        out = attn_weights @ v  # (B, H, T, D)
        
        # Reshape back: (B, H, T, D) -> (B, T, C)
        out = Tensor(out.data.transpose(0, 2, 1, 3).reshape(B, T, C), requires_grad=out.requires_grad)
        
        # Output projection
        out = self.c_proj(out)
        
        return out, present_kv
    
    def __repr__(self) -> str:
        return f"MultiHeadAttention(n_embd={self.n_embd}, n_head={self.n_head})"


class GroupedQueryAttention(Module):
    """
    Grouped-Query Attention (GQA) - used in LLaMA 2, Mistral.
    
    More efficient than MHA by sharing K,V heads.
    
    Args:
        n_embd: Embedding dimension
        n_head: Number of query heads
        n_kv_head: Number of key-value heads (shared across query heads)
        dropout: Attention dropout probability
    """
    
    def __init__(
        self, 
        n_embd: int, 
        n_head: int,
        n_kv_head: int,
        dropout: float = 0.1,
        bias: bool = False
    ):
        super().__init__()
        assert n_head % n_kv_head == 0, "n_head must be divisible by n_kv_head"
        
        self.n_embd = n_embd
        self.n_head = n_head
        self.n_kv_head = n_kv_head
        self.n_rep = n_head // n_kv_head  # Number of repetitions per KV head
        self.head_dim = n_embd // n_head
        self.dropout = dropout
        
        # Separate projections
        self.wq = Linear(n_embd, n_head * self.head_dim, bias=bias)
        self.wk = Linear(n_embd, n_kv_head * self.head_dim, bias=bias)
        self.wv = Linear(n_embd, n_kv_head * self.head_dim, bias=bias)
        self.wo = Linear(n_head * self.head_dim, n_embd, bias=bias)
        
        self.scale = 1.0 / np.sqrt(self.head_dim)
    
    def forward(self, x: Tensor) -> Tensor:
        B, T, C = x.shape
        
        # Compute Q, K, V
        q = self.wq(x).reshape(B, T, self.n_head, self.head_dim).data.transpose(0, 2, 1, 3)
        k = self.wk(x).reshape(B, T, self.n_kv_head, self.head_dim).data.transpose(0, 2, 1, 3)
        v = self.wv(x).reshape(B, T, self.n_kv_head, self.head_dim).data.transpose(0, 2, 1, 3)
        
        # Repeat K, V for each query group
        k = np.repeat(k, self.n_rep, axis=1)
        v = np.repeat(v, self.n_rep, axis=1)
        
        q = Tensor(q, requires_grad=x.requires_grad)
        k = Tensor(k, requires_grad=x.requires_grad)
        v = Tensor(v, requires_grad=x.requires_grad)
        
        # Attention
        scores = (q @ k.transpose(0, 1, 3, 2)) * self.scale
        
        # Causal mask
        causal_mask = np.triu(np.ones((T, T)), k=1).astype(bool)
        scores_data = scores.data.copy()
        scores_data[:, :, causal_mask] = -1e9
        scores = Tensor(scores_data, requires_grad=scores.requires_grad)
        
        attn_weights = scores.softmax(axis=-1)
        out = attn_weights @ v
        
        # Reshape and project
        out = Tensor(out.data.transpose(0, 2, 1, 3).reshape(B, T, C), requires_grad=out.requires_grad)
        return self.wo(out)
    
    def __repr__(self) -> str:
        return f"GroupedQueryAttention(n_embd={self.n_embd}, n_head={self.n_head}, n_kv_head={self.n_kv_head})"


class FlashAttention(Module):
    """
    Flash Attention (memory-efficient attention).
    
    Note: This is a simplified implementation. Real Flash Attention
    requires custom CUDA kernels for full efficiency.
    """
    
    def __init__(
        self, 
        n_embd: int, 
        n_head: int, 
        dropout: float = 0.0,
        causal: bool = True
    ):
        super().__init__()
        self.n_embd = n_embd
        self.n_head = n_head
        self.head_dim = n_embd // n_head
        self.dropout = dropout
        self.causal = causal
        self.scale = 1.0 / np.sqrt(self.head_dim)
        
        self.c_attn = Linear(n_embd, 3 * n_embd, bias=False)
        self.c_proj = Linear(n_embd, n_embd, bias=False)
    
    def forward(self, x: Tensor) -> Tensor:
        B, T, C = x.shape
        
        qkv = self.c_attn(x)
        qkv_split = qkv.data.reshape(B, T, 3, self.n_head, self.head_dim)
        q = qkv_split[:, :, 0].transpose(0, 2, 1, 3)
        k = qkv_split[:, :, 1].transpose(0, 2, 1, 3)
        v = qkv_split[:, :, 2].transpose(0, 2, 1, 3)
        
        # Block-wise attention for memory efficiency
        BLOCK_SIZE = min(64, T)
        out = np.zeros((B, self.n_head, T, self.head_dim), dtype=np.float32)
        
        for i in range(0, T, BLOCK_SIZE):
            i_end = min(i + BLOCK_SIZE, T)
            q_block = q[:, :, i:i_end]
            
            # Compute attention for this block
            if self.causal:
                j_end = i_end
            else:
                j_end = T
            
            scores = np.einsum('bhqd,bhkd->bhqk', q_block, k[:, :, :j_end]) * self.scale
            
            if self.causal:
                mask = np.triu(np.ones((i_end - i, j_end)), k=i+1)
                scores[:, :, mask.astype(bool)] = -1e9
            
            attn = np.exp(scores - np.max(scores, axis=-1, keepdims=True))
            attn = attn / np.sum(attn, axis=-1, keepdims=True)
            
            out[:, :, i:i_end] = np.einsum('bhqk,bhkd->bhqd', attn, v[:, :, :j_end])
        
        out = Tensor(out.transpose(0, 2, 1, 3).reshape(B, T, C), requires_grad=x.requires_grad)
        return self.c_proj(out)
    
    def __repr__(self) -> str:
        return f"FlashAttention(n_embd={self.n_embd}, n_head={self.n_head})"


class SlidingWindowAttention(Module):
    """
    Sliding Window Attention - for efficient long context.
    
    Each token only attends to the last `window_size` tokens.
    Used in Longformer, BigBird, Mistral.
    """
    
    def __init__(
        self, 
        n_embd: int, 
        n_head: int,
        window_size: int = 256,
        dropout: float = 0.1
    ):
        super().__init__()
        self.n_embd = n_embd
        self.n_head = n_head
        self.head_dim = n_embd // n_head
        self.window_size = window_size
        self.dropout = dropout
        self.scale = 1.0 / np.sqrt(self.head_dim)
        
        self.c_attn = Linear(n_embd, 3 * n_embd, bias=False)
        self.c_proj = Linear(n_embd, n_embd, bias=False)
    
    def forward(self, x: Tensor) -> Tensor:
        B, T, C = x.shape
        
        qkv = self.c_attn(x)
        qkv_split = qkv.data.reshape(B, T, 3, self.n_head, self.head_dim)
        q = Tensor(qkv_split[:, :, 0].transpose(0, 2, 1, 3), requires_grad=x.requires_grad)
        k = Tensor(qkv_split[:, :, 1].transpose(0, 2, 1, 3), requires_grad=x.requires_grad)
        v = Tensor(qkv_split[:, :, 2].transpose(0, 2, 1, 3), requires_grad=x.requires_grad)
        
        # Full attention scores
        scores = (q @ k.transpose(0, 1, 3, 2)) * self.scale
        
        # Apply sliding window + causal mask
        mask = np.ones((T, T), dtype=bool)
        for i in range(T):
            start = max(0, i - self.window_size + 1)
            mask[i, start:i+1] = False  # Unmasked positions
        
        scores_data = scores.data.copy()
        scores_data[:, :, mask] = -1e9
        scores = Tensor(scores_data, requires_grad=scores.requires_grad)
        
        attn_weights = scores.softmax(axis=-1)
        out = attn_weights @ v
        
        out = Tensor(out.data.transpose(0, 2, 1, 3).reshape(B, T, C), requires_grad=out.requires_grad)
        return self.c_proj(out)
    
    def __repr__(self) -> str:
        return f"SlidingWindowAttention(n_embd={self.n_embd}, window={self.window_size})"
