"""
Voice Trainer
=============

High-level API for training voice models.
"""

import os
from typing import Optional, Dict
from pathlib import Path

from ..trainer import UnifiedTrainer
from ..optim import AdamW, CosineScheduler
from .encoder import SpeakerEncoder
from .decoder import AcousticModel
from .vocoder import Vocoder
from .dataset import VoiceDataset, VoiceDataLoader
from .spectrogram import SpectrogramProcessor


class VoiceTrainer:
    """
    Voice trainer for building voice generation and cloning models.
    
    Example:
        trainer = VoiceTrainer(
            data_path="my_voice/",
            speaker_name="lakshmi"
        )
        trainer.train(epochs=200)
        trainer.save("lakshmi_voice.pt")
    """
    
    def __init__(
        self,
        data_path: str,
        speaker_name: Optional[str] = None,
        sample_rate: int = 22050,
        n_mels: int = 80,
        embedding_dim: int = 128,
        hidden_dim: int = 256,
        checkpoint_dir: Optional[str] = None,
        log_dir: Optional[str] = None
    ):
        self.data_path = data_path
        self.speaker_name = speaker_name
        self.sample_rate = sample_rate
        self.n_mels = n_mels
        
        # Initialize components
        print("🔊 Initializing Voice Trainer...")
        
        # Load dataset
        self.dataset = VoiceDataset(
            data_path=data_path,
            sample_rate=sample_rate,
            n_mels=n_mels
        )
        
        print(f"   Loaded {len(self.dataset)} audio samples")
        
        # Build models
        self.encoder = SpeakerEncoder(
            input_dim=n_mels,
            hidden_dim=hidden_dim,
            embedding_dim=embedding_dim
        )
        
        self.decoder = AcousticModel(
            vocab_size=1000,  # Placeholder - adjust based on text if needed
            embedding_dim=256,
            hidden_dim=hidden_dim,
            n_mels=n_mels,
            speaker_dim=embedding_dim
        )
        
        self.vocoder = Vocoder(
            n_mels=n_mels,
            sample_rate=sample_rate
        )
        
        # Extract speaker embedding if name provided
        self.speaker_embedding = None
        if speaker_name:
            self._extract_speaker_embedding()
        
        # Setup trainer
        checkpoint_dir = checkpoint_dir or os.path.join(data_path, "checkpoints")
        self.trainer = UnifiedTrainer(
            model=self.decoder,  # Train decoder first
            checkpoint_dir=checkpoint_dir,
            log_dir=log_dir,
            learning_rate=1e-4
        )
        
        print("✅ Voice Trainer initialized!")
    
    def _extract_speaker_embedding(self):
        """Extract speaker embedding from data."""
        print(f"🎤 Extracting speaker embedding for '{self.speaker_name}'...")
        
        # Get audio samples
        audio_samples = []
        for i in range(min(10, len(self.dataset))):
            mel_spec, _ = self.dataset[i]
            audio_samples.append(mel_spec)
        
        # Encode speaker
        self.speaker_embedding = self.encoder.encode_speaker(audio_samples)
        self.encoder.register_speaker(self.speaker_name, audio_samples)
        
        print(f"✅ Speaker embedding extracted!")
    
    def train(
        self,
        epochs: int = 200,
        batch_size: int = 1,
        learning_rate: float = 1e-4,
        **kwargs
    ) -> Dict:
        """
        Train the voice model.
        
        Args:
            epochs: Number of training epochs
            batch_size: Batch size
            learning_rate: Learning rate
        """
        print(f"\n🎵 Training Voice Model")
        print(f"   Epochs: {epochs}")
        print(f"   Batch Size: {batch_size}")
        print(f"   Learning Rate: {learning_rate}\n")
        
        # Create data loader
        dataloader = VoiceDataLoader(
            self.dataset,
            batch_size=batch_size,
            shuffle=True
        )
        
        # Train
        history = self.trainer.train(
            train_dataloader=dataloader,
            epochs=epochs,
            learning_rate=learning_rate,
            **kwargs
        )
        
        print("\n✅ Training complete!")
        return history
    
    def save(self, path: str):
        """Save trained models."""
        save_path = Path(path)
        save_path.mkdir(parents=True, exist_ok=True)
        
        # Save models
        import pickle
        
        # Encoder
        with open(save_path / "encoder.pkl", 'wb') as f:
            pickle.dump(self.encoder.state_dict(), f)
        
        # Decoder
        with open(save_path / "decoder.pkl", 'wb') as f:
            pickle.dump(self.decoder.state_dict(), f)
        
        # Vocoder
        with open(save_path / "vocoder.pkl", 'wb') as f:
            pickle.dump(self.vocoder.state_dict(), f)
        
        # Speaker embedding
        if self.speaker_embedding is not None:
            with open(save_path / "speaker_embedding.pkl", 'wb') as f:
                pickle.dump(self.speaker_embedding.data, f)
        
        # Config
        config = {
            'sample_rate': self.sample_rate,
            'n_mels': self.n_mels,
            'speaker_name': self.speaker_name
        }
        import json
        with open(save_path / "config.json", 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"✅ Models saved to {path}")
    
    @classmethod
    def load(cls, path: str) -> 'VoiceTrainer':
        """Load trained models."""
        # Implementation for loading
        raise NotImplementedError("Loading not yet implemented")
