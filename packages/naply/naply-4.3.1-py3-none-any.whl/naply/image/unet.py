"""
UNet Architecture
=================

UNet backbone for diffusion models.
"""

import numpy as np
from typing import Optional
from ..tensor import Tensor
from ..layers import Module, Linear, Sequential, LayerNorm
from ..attention import MultiHeadAttention


class UNet(Module):
    """
    UNet architecture for diffusion models.
    
    Processes noisy images and timestep embeddings to predict noise.
    """
    
    def __init__(
        self,
        in_channels: int = 3,
        out_channels: int = 3,
        time_emb_dim: int = 128,
        hidden_dims: list = [64, 128, 256, 512],
        n_heads: int = 4
    ):
        super().__init__()
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.time_emb_dim = time_emb_dim
        
        # Time embedding
        self.time_embed = Sequential(
            Linear(1, time_emb_dim),
            Linear(time_emb_dim, time_emb_dim)
        )
        
        # Encoder (downsampling)
        self.encoder_blocks = []
        in_ch = in_channels
        for hidden_dim in hidden_dims:
            block = self._build_block(in_ch, hidden_dim)
            self.encoder_blocks.append(block)
            in_ch = hidden_dim
            self.add_module(f'encoder_{len(self.encoder_blocks)}', block)
        
        # Middle block
        self.middle_block = self._build_block(hidden_dims[-1], hidden_dims[-1])
        
        # Decoder (upsampling)
        self.decoder_blocks = []
        hidden_dims_rev = hidden_dims[::-1]
        for i, hidden_dim in enumerate(hidden_dims_rev[:-1]):
            in_ch = hidden_dims_rev[i] + hidden_dims_rev[i + 1]  # Skip connection
            block = self._build_block(in_ch, hidden_dims_rev[i + 1])
            self.decoder_blocks.append(block)
            self.add_module(f'decoder_{len(self.decoder_blocks)}', block)
        
        # Output projection
        self.output_proj = Linear(hidden_dims[0], out_channels)
    
    def _build_block(self, in_channels: int, out_channels: int) -> Module:
        """Build a UNet block."""
        from ..layers import Sequential
        
        return Sequential(
            Linear(in_channels, out_channels),
            LayerNorm(out_channels),
            MultiHeadAttention(n_embd=out_channels, n_head=4),
            Linear(out_channels, out_channels),
            LayerNorm(out_channels)
        )
    
    def forward(self, x: Tensor, timestep: Tensor) -> Tensor:
        """
        Forward pass.
        
        Args:
            x: Noisy image (batch, channels, height, width)
            timestep: Diffusion timestep (batch, 1)
            
        Returns:
            Predicted noise (batch, channels, height, width)
        """
        # Time embedding
        t_emb = self.time_embed(timestep)
        
        # Encoder
        encoder_outputs = []
        h = x
        for block in self.encoder_blocks:
            h = block(h)
            # Add time embedding
            h = h + t_emb.unsqueeze(-1).unsqueeze(-1)
            encoder_outputs.append(h)
        
        # Middle
        h = self.middle_block(h)
        h = h + t_emb.unsqueeze(-1).unsqueeze(-1)
        
        # Decoder with skip connections
        for i, block in enumerate(self.decoder_blocks):
            # Concatenate with encoder output
            skip = encoder_outputs[-(i + 1)]
            h = Tensor(np.concatenate([h.data, skip.data], axis=1))
            h = block(h)
            h = h + t_emb.unsqueeze(-1).unsqueeze(-1)
        
        # Output
        output = self.output_proj(h)
        
        return output


class DiffusionUNet(UNet):
    """UNet specifically for diffusion models."""
    pass
