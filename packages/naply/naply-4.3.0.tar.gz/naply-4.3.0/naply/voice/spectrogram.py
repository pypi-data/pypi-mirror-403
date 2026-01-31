"""
Mel Spectrogram Processing
===========================

Convert audio to mel spectrograms for voice models.
"""

import numpy as np
from typing import Optional, Tuple
from ..tensor import Tensor


class MelSpectrogram:
    """
    Mel Spectrogram converter.
    
    Converts audio waveforms to mel spectrograms for training.
    """
    
    def __init__(
        self,
        sample_rate: int = 22050,
        n_fft: int = 2048,
        hop_length: int = 512,
        n_mels: int = 80,
        fmin: float = 0.0,
        fmax: Optional[float] = None
    ):
        self.sample_rate = sample_rate
        self.n_fft = n_fft
        self.hop_length = hop_length
        self.n_mels = n_mels
        self.fmin = fmin
        self.fmax = fmax or (sample_rate / 2)
        
        # Build mel filter bank
        self.mel_filters = self._build_mel_filter_bank()
    
    def _build_mel_filter_bank(self) -> np.ndarray:
        """Build mel filter bank."""
        # Simplified mel filter bank
        # In production, use librosa or similar
        n_fft_bins = self.n_fft // 2 + 1
        mel_filters = np.zeros((self.n_mels, n_fft_bins))
        
        # Linear spacing in mel scale
        mel_points = np.linspace(
            self._hz_to_mel(self.fmin),
            self._hz_to_mel(self.fmax),
            self.n_mels + 2
        )
        hz_points = self._mel_to_hz(mel_points)
        
        # Create triangular filters
        for i in range(self.n_mels):
            for j in range(n_fft_bins):
                freq = j * self.sample_rate / self.n_fft
                if hz_points[i] <= freq <= hz_points[i + 1]:
                    mel_filters[i, j] = (freq - hz_points[i]) / (hz_points[i + 1] - hz_points[i])
                elif hz_points[i + 1] <= freq <= hz_points[i + 2]:
                    mel_filters[i, j] = (hz_points[i + 2] - freq) / (hz_points[i + 2] - hz_points[i + 1])
        
        return mel_filters
    
    def _hz_to_mel(self, hz: float) -> float:
        """Convert Hz to mel scale."""
        return 2595 * np.log10(1 + hz / 700)
    
    def _mel_to_hz(self, mel: float) -> float:
        """Convert mel to Hz."""
        return 700 * (10 ** (mel / 2595) - 1)
    
    def __call__(self, audio: np.ndarray) -> np.ndarray:
        """
        Convert audio to mel spectrogram.
        
        Args:
            audio: Audio waveform (1D array)
            
        Returns:
            Mel spectrogram (n_mels, time)
        """
        # Pad audio
        audio = np.pad(audio, (self.n_fft // 2, self.n_fft // 2), mode='reflect')
        
        # Compute STFT
        stft = self._stft(audio)
        
        # Magnitude spectrogram
        magnitude = np.abs(stft)
        
        # Apply mel filter bank
        mel_spec = np.dot(self.mel_filters, magnitude)
        
        # Convert to log scale
        mel_spec = np.log(mel_spec + 1e-8)
        
        return mel_spec
    
    def _stft(self, audio: np.ndarray) -> np.ndarray:
        """Compute Short-Time Fourier Transform."""
        # Simplified STFT
        # In production, use librosa.stft or scipy.signal.stft
        n_frames = (len(audio) - self.n_fft) // self.hop_length + 1
        stft = np.zeros((self.n_fft // 2 + 1, n_frames), dtype=np.complex64)
        
        window = np.hanning(self.n_fft)
        
        for i in range(n_frames):
            start = i * self.hop_length
            frame = audio[start:start + self.n_fft]
            if len(frame) < self.n_fft:
                frame = np.pad(frame, (0, self.n_fft - len(frame)))
            frame = frame * window
            fft = np.fft.rfft(frame, n=self.n_fft)
            stft[:, i] = fft
        
        return stft
    
    def inverse(self, mel_spec: np.ndarray) -> np.ndarray:
        """
        Convert mel spectrogram back to audio (approximate).
        
        Note: This is a simplified inverse. For high quality,
        use a proper vocoder.
        """
        # Inverse mel filter bank (pseudo-inverse)
        magnitude = np.dot(self.mel_filters.T, np.exp(mel_spec))
        
        # Reconstruct phase (simplified - use Griffin-Lim in production)
        phase = np.random.random(magnitude.shape) * 2 * np.pi
        stft = magnitude * np.exp(1j * phase)
        
        # Inverse STFT
        audio = self._istft(stft)
        
        return audio
    
    def _istft(self, stft: np.ndarray) -> np.ndarray:
        """Inverse STFT."""
        n_frames = stft.shape[1]
        audio_length = (n_frames - 1) * self.hop_length + self.n_fft
        audio = np.zeros(audio_length)
        
        window = np.hanning(self.n_fft)
        
        for i in range(n_frames):
            start = i * self.hop_length
            frame = np.fft.irfft(stft[:, i], n=self.n_fft)
            frame = frame * window
            audio[start:start + self.n_fft] += frame
        
        # Remove padding
        audio = audio[self.n_fft // 2:-self.n_fft // 2]
        
        return audio


class SpectrogramProcessor:
    """
    High-level spectrogram processor with normalization.
    """
    
    def __init__(self, **kwargs):
        self.mel_spec = MelSpectrogram(**kwargs)
        self.mean = None
        self.std = None
    
    def fit(self, audio_files: list):
        """Fit normalization parameters."""
        all_specs = []
        for audio in audio_files:
            spec = self.mel_spec(audio)
            all_specs.append(spec)
        
        # Compute statistics
        all_specs = np.concatenate(all_specs, axis=1)
        self.mean = np.mean(all_specs)
        self.std = np.std(all_specs)
    
    def process(self, audio: np.ndarray, normalize: bool = True) -> Tensor:
        """Process audio to normalized mel spectrogram."""
        spec = self.mel_spec(audio)
        
        if normalize and self.mean is not None:
            spec = (spec - self.mean) / (self.std + 1e-8)
        
        return Tensor(spec)
    
    def unprocess(self, spec: Tensor, denormalize: bool = True) -> np.ndarray:
        """Convert spectrogram back to audio."""
        spec_data = spec.data
        
        if denormalize and self.mean is not None:
            spec_data = spec_data * self.std + self.mean
        
        return self.mel_spec.inverse(spec_data)
