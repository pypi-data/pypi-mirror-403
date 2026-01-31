"""
Voice Decoder & Acoustic Model
===============================

Generate mel spectrograms from text or embeddings.
"""

import numpy as np
from typing import Optional
from ..tensor import Tensor
from ..layers import Module, Linear, LayerNorm, Sequential, Embedding
from ..transformer import TransformerBlock


class AcousticModel(Module):
    """
    Acoustic model that generates mel spectrograms.
    
    Can be conditioned on:
    - Text (for TTS)
    - Speaker embeddings (for voice cloning)
    """
    
    def __init__(
        self,
        vocab_size: int = 1000,
        embedding_dim: int = 256,
        hidden_dim: int = 512,
        n_layers: int = 6,
        n_mels: int = 80,
        speaker_dim: int = 128
    ):
        super().__init__()
        self.vocab_size = vocab_size
        self.embedding_dim = embedding_dim
        self.hidden_dim = hidden_dim
        self.n_mels = n_mels
        
        # Text embedding
        self.text_embedding = Embedding(vocab_size, embedding_dim)
        
        # Speaker conditioning
        self.speaker_proj = Linear(speaker_dim, hidden_dim)
        
        # Transformer decoder
        self.blocks = Sequential(*[
            TransformerBlock(
                n_embd=hidden_dim,
                n_head=8,
                dropout=0.1
            )
            for _ in range(n_layers)
        ])
        
        # Output projection to mel spectrogram
        self.mel_proj = Linear(hidden_dim, n_mels)
        self.norm = LayerNorm(hidden_dim)
    
    def forward(
        self,
        text_ids: Tensor,
        speaker_embedding: Optional[Tensor] = None
    ) -> Tensor:
        """
        Generate mel spectrogram from text.
        
        Args:
            text_ids: Text token IDs (batch, seq_len)
            speaker_embedding: Optional speaker embedding (batch, speaker_dim)
            
        Returns:
            Mel spectrogram (batch, seq_len, n_mels)
        """
        # Text embeddings
        x = self.text_embedding(text_ids)
        
        # Add speaker conditioning
        if speaker_embedding is not None:
            speaker_feat = self.speaker_proj(speaker_embedding)
            # Broadcast and add
            x = x + speaker_feat.unsqueeze(1)
        
        # Process through transformer
        x = self.blocks(x)
        x = self.norm(x)
        
        # Generate mel spectrogram
        mel = self.mel_proj(x)
        
        return mel


class VoiceDecoder(AcousticModel):
    """
    Voice decoder for TTS and voice cloning.
    
    Alias for AcousticModel with voice-specific defaults.
    """
    pass
