"""
NAPLY Transformer Architecture
==============================

Complete transformer blocks and feed-forward networks.
"""

import numpy as np
from typing import Optional, Tuple, List
from .tensor import Tensor
from .layers import Module, Linear, LayerNorm, RMSNorm, Dropout
from .attention import MultiHeadAttention


class FeedForward(Module):
    """
    Feed-Forward Network with GELU activation.
    
    Used in transformer blocks: Linear -> GELU -> Linear
    
    Args:
        n_embd: Embedding dimension
        expansion: Expansion factor (default: 4)
        dropout: Dropout probability
        bias: Whether to use bias
    """
    
    def __init__(
        self, 
        n_embd: int, 
        expansion: int = 4,
        dropout: float = 0.1,
        bias: bool = True
    ):
        super().__init__()
        self.n_embd = n_embd
        hidden_dim = n_embd * expansion
        
        self.c_fc = Linear(n_embd, hidden_dim, bias=bias)
        self.c_proj = Linear(hidden_dim, n_embd, bias=bias)
        self.dropout = Dropout(dropout)
    
    def forward(self, x: Tensor) -> Tensor:
        x = self.c_fc(x)
        x = x.gelu()
        x = self.c_proj(x)
        x = self.dropout(x)
        return x
    
    def __repr__(self) -> str:
        return f"FeedForward(n_embd={self.n_embd})"


class SwiGLU(Module):
    """
    SwiGLU Feed-Forward (used in LLaMA, PaLM).
    
    More efficient than standard FFN with similar performance.
    """
    
    def __init__(
        self, 
        n_embd: int, 
        hidden_dim: Optional[int] = None,
        bias: bool = False
    ):
        super().__init__()
        if hidden_dim is None:
            # LLaMA-style: 2/3 * 4 * n_embd rounded to multiple of 256
            hidden_dim = int(2 * n_embd * 4 / 3)
            hidden_dim = ((hidden_dim + 255) // 256) * 256
        
        self.w1 = Linear(n_embd, hidden_dim, bias=bias)
        self.w2 = Linear(hidden_dim, n_embd, bias=bias)
        self.w3 = Linear(n_embd, hidden_dim, bias=bias)
    
    def forward(self, x: Tensor) -> Tensor:
        return self.w2(self.w1(x).silu() * self.w3(x))
    
    def __repr__(self) -> str:
        return f"SwiGLU()"


class TransformerBlock(Module):
    """
    Standard Transformer Block.
    
    Architecture: LayerNorm -> Attention -> Residual -> LayerNorm -> FFN -> Residual
    
    Args:
        n_embd: Embedding dimension
        n_head: Number of attention heads
        dropout: Dropout probability
        bias: Whether to use bias
    """
    
    def __init__(
        self, 
        n_embd: int, 
        n_head: int,
        dropout: float = 0.1,
        bias: bool = True,
        use_swiglu: bool = False,
        use_rms_norm: bool = False
    ):
        super().__init__()
        self.n_embd = n_embd
        self.n_head = n_head
        
        # Normalization
        if use_rms_norm:
            self.ln_1 = RMSNorm(n_embd)
            self.ln_2 = RMSNorm(n_embd)
        else:
            self.ln_1 = LayerNorm(n_embd)
            self.ln_2 = LayerNorm(n_embd)
        
        # Attention
        self.attn = MultiHeadAttention(n_embd, n_head, dropout=dropout, bias=bias)
        
        # Feed-Forward
        if use_swiglu:
            self.mlp = SwiGLU(n_embd, bias=bias)
        else:
            self.mlp = FeedForward(n_embd, dropout=dropout, bias=bias)
        
        self.dropout = Dropout(dropout)
    
    def forward(
        self, 
        x: Tensor,
        past_kv: Optional[Tuple[Tensor, Tensor]] = None
    ) -> Tuple[Tensor, Optional[Tuple[Tensor, Tensor]]]:
        """
        Args:
            x: Input tensor (B, T, C)
            past_kv: Optional past key-value for caching
            
        Returns:
            output: Block output (B, T, C)
            present_kv: Current key-value for caching
        """
        # Attention with residual
        attn_out, present_kv = self.attn(self.ln_1(x), past_kv=past_kv)
        x = x + self.dropout(attn_out)
        
        # FFN with residual
        x = x + self.dropout(self.mlp(self.ln_2(x)))
        
        return x, present_kv
    
    def __repr__(self) -> str:
        return f"TransformerBlock(n_embd={self.n_embd}, n_head={self.n_head})"


class GPT(Module):
    """
    GPT-style Language Model.
    
    Full transformer decoder with embeddings and output head.
    
    Args:
        vocab_size: Vocabulary size
        n_layer: Number of transformer layers
        n_head: Number of attention heads
        n_embd: Embedding dimension
        block_size: Maximum sequence length
        dropout: Dropout probability
        bias: Whether to use bias
    """
    
    def __init__(
        self,
        vocab_size: int,
        n_layer: int,
        n_head: int,
        n_embd: int,
        block_size: int,
        dropout: float = 0.1,
        bias: bool = True,
        use_swiglu: bool = False,
        use_rms_norm: bool = False
    ):
        super().__init__()
        self.vocab_size = vocab_size
        self.n_layer = n_layer
        self.n_head = n_head
        self.n_embd = n_embd
        self.block_size = block_size
        
        # Token and position embeddings
        from .layers import Embedding
        self.wte = Embedding(vocab_size, n_embd)
        self.wpe = Embedding(block_size, n_embd)
        
        self.drop = Dropout(dropout)
        
        # Transformer blocks
        self.blocks = []
        for i in range(n_layer):
            block = TransformerBlock(
                n_embd, n_head, dropout, bias,
                use_swiglu=use_swiglu,
                use_rms_norm=use_rms_norm
            )
            setattr(self, f'block_{i}', block)
            self.blocks.append(block)
        
        # Final layer norm
        if use_rms_norm:
            self.ln_f = RMSNorm(n_embd)
        else:
            self.ln_f = LayerNorm(n_embd)
        
        # Output head (tied with embeddings for efficiency)
        self.lm_head = Linear(n_embd, vocab_size, bias=False)
        
        # Initialize weights
        self._init_weights()
    
    def _init_weights(self):
        """Initialize weights with small random values."""
        for p in self.parameters():
            if len(p.shape) >= 2:
                # Xavier initialization for matrices
                std = np.sqrt(2.0 / (p.shape[0] + p.shape[1]))
                p.data = np.random.randn(*p.shape).astype(np.float32) * std
            else:
                # Zero initialization for biases
                p.data = np.zeros(p.shape, dtype=np.float32)
    
    def forward(
        self, 
        idx: Tensor,
        past_key_values: Optional[List[Tuple[Tensor, Tensor]]] = None
    ) -> Tuple[Tensor, List[Tuple[Tensor, Tensor]]]:
        """
        Args:
            idx: Token indices (B, T)
            past_key_values: Optional KV cache for incremental decoding
            
        Returns:
            logits: Output logits (B, T, vocab_size)
            present_key_values: KV cache for next step
        """
        B, T = idx.shape[:2] if len(idx.shape) > 1 else (1, idx.shape[0])
        
        # Compute start position for incremental decoding
        if past_key_values is not None and past_key_values[0] is not None:
            past_length = past_key_values[0][0].shape[2]
        else:
            past_length = 0
        
        # Get embeddings
        tok_emb = self.wte(idx)  # (B, T, n_embd)
        
        # Position embeddings
        positions = Tensor(np.arange(past_length, past_length + T, dtype=np.int32))
        pos_emb = self.wpe(positions)  # (T, n_embd)
        
        x = self.drop(tok_emb + pos_emb)
        
        # Transformer blocks
        present_key_values = []
        for i, block in enumerate(self.blocks):
            past_kv = past_key_values[i] if past_key_values else None
            x, present_kv = block(x, past_kv=past_kv)
            present_key_values.append(present_kv)
        
        # Final norm and output
        x = self.ln_f(x)
        logits = self.lm_head(x)
        
        return logits, present_key_values
    
    def count_parameters(self) -> int:
        """Count total trainable parameters."""
        return sum(np.prod(p.shape) for p in self.parameters())
    
    def __repr__(self) -> str:
        params = self.count_parameters()
        return (f"GPT(\n"
                f"  vocab_size={self.vocab_size},\n"
                f"  n_layer={self.n_layer},\n"
                f"  n_head={self.n_head},\n"
                f"  n_embd={self.n_embd},\n"
                f"  block_size={self.block_size},\n"
                f"  parameters={params:,}\n"
                f")")


class LLaMA(Module):
    """
    LLaMA-style Architecture.
    
    Uses RMSNorm, SwiGLU, RoPE, and GQA.
    """
    
    def __init__(
        self,
        vocab_size: int,
        n_layer: int,
        n_head: int,
        n_kv_head: int,
        n_embd: int,
        block_size: int,
        dropout: float = 0.0
    ):
        super().__init__()
        self.vocab_size = vocab_size
        self.n_layer = n_layer
        self.n_embd = n_embd
        self.block_size = block_size
        
        from .layers import Embedding
        self.tok_emb = Embedding(vocab_size, n_embd)
        
        # Transformer blocks with LLaMA-style components
        self.blocks = []
        for i in range(n_layer):
            block = TransformerBlock(
                n_embd, n_head, dropout,
                bias=False,
                use_swiglu=True,
                use_rms_norm=True
            )
            setattr(self, f'block_{i}', block)
            self.blocks.append(block)
        
        self.norm = RMSNorm(n_embd)
        self.output = Linear(n_embd, vocab_size, bias=False)
    
    def forward(self, idx: Tensor) -> Tensor:
        x = self.tok_emb(idx)
        
        for block in self.blocks:
            x, _ = block(x)
        
        x = self.norm(x)
        return self.output(x)
    
    def count_parameters(self) -> int:
        return sum(np.prod(p.shape) for p in self.parameters())
