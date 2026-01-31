"""
Voice Dataset
=============

Dataset loading and preprocessing for voice models.
"""

import os
import numpy as np
from typing import List, Tuple, Optional
from pathlib import Path
from ..tensor import Tensor
from .spectrogram import SpectrogramProcessor


class VoiceDataset:
    """
    Dataset for voice training.
    
    Loads audio files and converts to mel spectrograms.
    """
    
    def __init__(
        self,
        data_path: str,
        sample_rate: int = 22050,
        n_mels: int = 80,
        max_length: Optional[int] = None
    ):
        self.data_path = Path(data_path)
        self.sample_rate = sample_rate
        self.n_mels = n_mels
        self.max_length = max_length
        
        # Initialize processor
        self.processor = SpectrogramProcessor(
            sample_rate=sample_rate,
            n_mels=n_mels
        )
        
        # Load audio files
        self.audio_files = self._load_audio_files()
        
        if len(self.audio_files) == 0:
            raise ValueError(f"No audio files found in {data_path}")
        
        # Fit normalization
        self._fit_normalization()
    
    def _load_audio_files(self) -> List[Tuple[str, np.ndarray]]:
        """Load all audio files from directory."""
        audio_files = []
        
        # Supported formats
        extensions = ['.wav', '.mp3', '.flac', '.ogg']
        
        for ext in extensions:
            for file_path in self.data_path.rglob(f'*{ext}'):
                try:
                    audio = self._load_audio(str(file_path))
                    if audio is not None:
                        audio_files.append((str(file_path), audio))
                except Exception as e:
                    print(f"Warning: Could not load {file_path}: {e}")
        
        return audio_files
    
    def _load_audio(self, path: str) -> Optional[np.ndarray]:
        """Load audio file."""
        try:
            import soundfile as sf
            audio, sr = sf.read(path)
        except ImportError:
            try:
                from scipy.io import wavfile
                sr, audio = wavfile.read(path)
            except ImportError:
                raise ImportError("Need soundfile or scipy to load audio")
        
        # Resample if needed
        if sr != self.sample_rate:
            try:
                import librosa
                audio = librosa.resample(audio, orig_sr=sr, target_sr=self.sample_rate)
            except ImportError:
                # Simple resampling (not ideal)
                ratio = self.sample_rate / sr
                indices = np.round(np.arange(0, len(audio), 1/ratio)).astype(int)
                audio = audio[indices]
        
        # Convert to mono
        if len(audio.shape) > 1:
            audio = np.mean(audio, axis=1)
        
        # Normalize
        audio = audio / (np.abs(audio).max() + 1e-8)
        
        return audio
    
    def _fit_normalization(self):
        """Fit normalization parameters."""
        print("Fitting normalization parameters...")
        audio_samples = [audio for _, audio in self.audio_files[:100]]  # Sample first 100
        self.processor.fit(audio_samples)
        print("Normalization fitted!")
    
    def __len__(self) -> int:
        return len(self.audio_files)
    
    def __getitem__(self, idx: int) -> Tuple[Tensor, Tensor]:
        """Get a sample."""
        file_path, audio = self.audio_files[idx]
        
        # Convert to mel spectrogram
        mel_spec = self.processor.process(audio, normalize=True)
        
        # Truncate if needed
        if self.max_length and mel_spec.shape[1] > self.max_length:
            mel_spec = mel_spec[:, :self.max_length]
        
        # For autoencoder training, input = target
        return mel_spec, mel_spec


class VoiceDataLoader:
    """
    Data loader for voice datasets.
    """
    
    def __init__(
        self,
        dataset: VoiceDataset,
        batch_size: int = 1,
        shuffle: bool = True
    ):
        self.dataset = dataset
        self.batch_size = batch_size
        self.shuffle = shuffle
        self.indices = list(range(len(dataset)))
    
    def __len__(self) -> int:
        return (len(self.dataset) + self.batch_size - 1) // self.batch_size
    
    def __iter__(self):
        """Iterate over batches."""
        if self.shuffle:
            np.random.shuffle(self.indices)
        
        for i in range(0, len(self.indices), self.batch_size):
            batch_indices = self.indices[i:i + self.batch_size]
            batch = [self.dataset[idx] for idx in batch_indices]
            
            # Pad to same length
            max_len = max(x[0].shape[1] for x in batch)
            
            batch_x = []
            batch_y = []
            
            for x, y in batch:
                # Pad
                pad_len = max_len - x.shape[1]
                if pad_len > 0:
                    x = self._pad_tensor(x, pad_len)
                    y = self._pad_tensor(y, pad_len)
                
                batch_x.append(x)
                batch_y.append(y)
            
            # Stack
            batch_x = Tensor(np.stack([x.data for x in batch_x]))
            batch_y = Tensor(np.stack([y.data for y in batch_y]))
            
            yield batch_x, batch_y
    
    def _pad_tensor(self, tensor: Tensor, pad_len: int) -> Tensor:
        """Pad tensor."""
        pad_shape = list(tensor.shape)
        pad_shape[1] = pad_len
        pad = Tensor(np.zeros(pad_shape))
        return Tensor(np.concatenate([tensor.data, pad.data], axis=1))
