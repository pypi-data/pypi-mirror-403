"""
Voice Encoder
=============

Extract speaker embeddings and voice identity features.
"""

import numpy as np
from typing import Optional, Tuple
from ..tensor import Tensor
from ..layers import Module, Linear, LayerNorm, Sequential
from ..attention import MultiHeadAttention


class VoiceEncoder(Module):
    """
    Voice encoder for extracting speaker embeddings.
    
    Processes mel spectrograms to extract speaker identity.
    """
    
    def __init__(
        self,
        input_dim: int = 80,  # n_mels
        hidden_dim: int = 256,
        embedding_dim: int = 128,
        n_layers: int = 3
    ):
        super().__init__()
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.embedding_dim = embedding_dim
        
        # Convolutional layers for spectrogram processing
        self.conv_layers = Sequential(
            Linear(input_dim, hidden_dim),
            Linear(hidden_dim, hidden_dim),
            Linear(hidden_dim, hidden_dim)
        )
        
        # Attention for temporal modeling
        self.attention = MultiHeadAttention(
            n_embd=hidden_dim,
            n_head=4
        )
        
        # Final embedding projection
        self.embedding_proj = Linear(hidden_dim, embedding_dim)
        self.norm = LayerNorm(embedding_dim)
    
    def forward(self, x: Tensor) -> Tensor:
        """
        Encode voice to speaker embedding.
        
        Args:
            x: Mel spectrogram (batch, time, n_mels)
            
        Returns:
            Speaker embedding (batch, embedding_dim)
        """
        # Process through conv layers
        x = self.conv_layers(x)
        
        # Temporal attention
        x, _ = self.attention(x)
        
        # Global average pooling
        x = x.mean(dim=1)  # (batch, hidden_dim)
        
        # Project to embedding
        x = self.embedding_proj(x)
        x = self.norm(x)
        
        return x


class SpeakerEncoder(VoiceEncoder):
    """
    Specialized speaker encoder for voice cloning.
    
    Extracts speaker identity from 3-10 minutes of clean audio.
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.speaker_embeddings = {}  # Cache for known speakers
    
    def encode_speaker(self, audio_samples: list) -> Tensor:
        """
        Encode speaker from multiple audio samples.
        
        Args:
            audio_samples: List of mel spectrograms
            
        Returns:
            Speaker embedding
        """
        # Encode each sample
        embeddings = []
        for sample in audio_samples:
            if isinstance(sample, np.ndarray):
                sample = Tensor(sample)
            emb = self.forward(sample)
            embeddings.append(emb)
        
        # Average embeddings
        if embeddings:
            avg_emb = sum(embeddings) / len(embeddings)
            return avg_emb
        return Tensor(np.zeros(self.embedding_dim))
    
    def register_speaker(self, name: str, audio_samples: list):
        """Register a speaker for voice cloning."""
        embedding = self.encode_speaker(audio_samples)
        self.speaker_embeddings[name] = embedding
        return embedding
    
    def get_speaker_embedding(self, name: str) -> Optional[Tensor]:
        """Get registered speaker embedding."""
        return self.speaker_embeddings.get(name)
