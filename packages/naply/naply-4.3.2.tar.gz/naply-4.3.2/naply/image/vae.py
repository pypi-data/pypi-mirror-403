"""
Variational Autoencoder (VAE)
==============================

VAE for encoding images to latent space and decoding back.
Used in diffusion models for efficient training.
"""

import numpy as np
from typing import Tuple
from ..tensor import Tensor
from ..layers import Module, Linear, Sequential, LayerNorm
from ..functional import relu, sigmoid


class VAE(Module):
    """
    Variational Autoencoder for image compression.
    
    Encodes images to latent space and decodes back.
    """
    
    def __init__(
        self,
        input_dim: int = 3,  # RGB channels
        latent_dim: int = 4,
        hidden_dims: list = [64, 128, 256, 512],
        image_size: int = 256
    ):
        super().__init__()
        self.input_dim = input_dim
        self.latent_dim = latent_dim
        self.image_size = image_size
        
        # Encoder
        self.encoder = self._build_encoder(input_dim, hidden_dims, latent_dim)
        
        # Decoder
        self.decoder = self._build_decoder(latent_dim, hidden_dims, input_dim)
    
    def _build_encoder(self, input_dim, hidden_dims, latent_dim):
        """Build encoder network."""
        layers = []
        in_channels = input_dim
        
        # Downsampling layers
        for hidden_dim in hidden_dims:
            layers.append(Linear(in_channels, hidden_dim))
            layers.append(LayerNorm(hidden_dim))
            in_channels = hidden_dim
        
        # Latent projection (mean and logvar)
        self.fc_mu = Linear(in_channels, latent_dim)
        self.fc_logvar = Linear(in_channels, latent_dim)
        
        return Sequential(*layers)
    
    def _build_decoder(self, latent_dim, hidden_dims, output_dim):
        """Build decoder network."""
        layers = []
        hidden_dims = hidden_dims[::-1]  # Reverse for decoder
        in_channels = latent_dim
        
        for hidden_dim in hidden_dims:
            layers.append(Linear(in_channels, hidden_dim))
            layers.append(LayerNorm(hidden_dim))
            in_channels = hidden_dim
        
        # Output projection
        layers.append(Linear(in_channels, output_dim))
        
        return Sequential(*layers)
    
    def encode(self, x: Tensor) -> Tuple[Tensor, Tensor, Tensor]:
        """
        Encode image to latent space.
        
        Returns:
            (z, mu, logvar) - latent, mean, log variance
        """
        # Encode
        h = self.encoder(x)
        
        # Get mean and log variance
        mu = self.fc_mu(h)
        logvar = self.fc_logvar(h)
        
        # Reparameterization trick
        std = (logvar * 0.5).exp()
        eps = Tensor(np.random.normal(0, 1, std.shape))
        z = mu + std * eps
        
        return z, mu, logvar
    
    def decode(self, z: Tensor) -> Tensor:
        """Decode latent to image."""
        return self.decoder(z)
    
    def forward(self, x: Tensor) -> Tuple[Tensor, Tensor, Tensor]:
        """Forward pass: encode and decode."""
        z, mu, logvar = self.encode(x)
        recon = self.decode(z)
        return recon, mu, logvar


class VariationalAutoencoder(VAE):
    """Alias for VAE."""
    pass
