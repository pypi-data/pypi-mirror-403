"""
Vocoder - Waveform Generation
==============================

Convert mel spectrograms to audio waveforms.
"""

import numpy as np
from typing import Optional
from ..tensor import Tensor
from ..layers import Module, Linear, Sequential


class Vocoder(Module):
    """
    Vocoder for converting mel spectrograms to waveforms.
    
    Uses neural vocoder architecture (simplified WaveNet-style).
    """
    
    def __init__(
        self,
        n_mels: int = 80,
        hidden_dim: int = 512,
        n_layers: int = 4,
        sample_rate: int = 22050
    ):
        super().__init__()
        self.n_mels = n_mels
        self.hidden_dim = hidden_dim
        self.sample_rate = sample_rate
        
        # Upsampling layers
        self.upsample = Sequential(
            Linear(n_mels, hidden_dim),
            Linear(hidden_dim, hidden_dim * 2),
            Linear(hidden_dim * 2, hidden_dim * 4)
        )
        
        # Waveform generation layers
        self.waveform_layers = Sequential(*[
            Linear(hidden_dim * 4, hidden_dim * 4)
            for _ in range(n_layers)
        ])
        
        # Output projection (single sample per timestep)
        self.output_proj = Linear(hidden_dim * 4, 1)
    
    def forward(self, mel_spec: Tensor) -> Tensor:
        """
        Generate waveform from mel spectrogram.
        
        Args:
            mel_spec: Mel spectrogram (batch, time, n_mels)
            
        Returns:
            Waveform (batch, time * hop_length)
        """
        # Upsample mel spectrogram
        x = self.upsample(mel_spec)
        
        # Generate waveform
        x = self.waveform_layers(x)
        waveform = self.output_proj(x)
        
        # Reshape to 1D
        waveform = waveform.squeeze(-1)
        
        return waveform


class WaveformGenerator:
    """
    High-level waveform generator.
    
    Wraps vocoder with post-processing.
    """
    
    def __init__(self, vocoder: Optional[Vocoder] = None, sample_rate: int = 22050):
        self.vocoder = vocoder or Vocoder(sample_rate=sample_rate)
        self.sample_rate = sample_rate
    
    def generate(self, mel_spec: Tensor) -> np.ndarray:
        """
        Generate audio waveform from mel spectrogram.
        
        Args:
            mel_spec: Mel spectrogram
            
        Returns:
            Audio waveform as numpy array
        """
        waveform = self.vocoder(mel_spec)
        
        # Convert to numpy
        audio = waveform.data
        
        # Normalize
        audio = audio / (np.abs(audio).max() + 1e-8)
        
        # Clip to valid range
        audio = np.clip(audio, -1.0, 1.0)
        
        return audio
    
    def save(self, audio: np.ndarray, path: str):
        """Save audio to file."""
        try:
            import soundfile as sf
            sf.write(path, audio, self.sample_rate)
        except ImportError:
            # Fallback: save as WAV using scipy
            try:
                from scipy.io import wavfile
                # Convert to int16
                audio_int16 = (audio * 32767).astype(np.int16)
                wavfile.write(path, self.sample_rate, audio_int16)
            except ImportError:
                raise ImportError("Need soundfile or scipy to save audio")
