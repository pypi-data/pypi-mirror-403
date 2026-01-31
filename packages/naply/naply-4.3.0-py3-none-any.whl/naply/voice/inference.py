"""
Voice Inference
===============

Generate speech and clone voices.
"""

import numpy as np
from typing import Optional
from pathlib import Path

from .encoder import SpeakerEncoder
from .decoder import AcousticModel
from .vocoder import Vocoder, WaveformGenerator
from .spectrogram import SpectrogramProcessor
from ..tensor import Tensor


class VoiceInference:
    """
    Voice inference for TTS and voice cloning.
    """
    
    def __init__(
        self,
        encoder: Optional[SpeakerEncoder] = None,
        decoder: Optional[AcousticModel] = None,
        vocoder: Optional[Vocoder] = None,
        sample_rate: int = 22050
    ):
        self.encoder = encoder
        self.decoder = decoder or AcousticModel()
        self.vocoder = vocoder or Vocoder(sample_rate=sample_rate)
        self.waveform_gen = WaveformGenerator(self.vocoder, sample_rate)
        self.sample_rate = sample_rate
    
    def generate_speech(
        self,
        text: str,
        speaker_embedding: Optional[Tensor] = None
    ) -> np.ndarray:
        """
        Generate speech from text.
        
        Args:
            text: Input text
            speaker_embedding: Optional speaker embedding for voice cloning
            
        Returns:
            Audio waveform
        """
        # Tokenize text (simplified - use proper tokenizer in production)
        text_ids = self._text_to_ids(text)
        text_ids = Tensor(np.array([text_ids]))
        
        # Generate mel spectrogram
        mel_spec = self.decoder(text_ids, speaker_embedding=speaker_embedding)
        
        # Convert to waveform
        audio = self.waveform_gen.generate(mel_spec)
        
        return audio[0]  # Remove batch dimension
    
    def _text_to_ids(self, text: str) -> list:
        """Convert text to token IDs (simplified)."""
        # In production, use proper tokenizer
        return [ord(c) % 1000 for c in text[:100]]  # Simple char-based
    
    def clone_voice(
        self,
        text: str,
        reference_audio: np.ndarray
    ) -> np.ndarray:
        """
        Clone voice from reference audio.
        
        Args:
            text: Text to speak
            reference_audio: Reference audio for voice cloning
            
        Returns:
            Generated audio with cloned voice
        """
        # Extract speaker embedding from reference
        processor = SpectrogramProcessor(sample_rate=self.sample_rate)
        mel_spec = processor.process(reference_audio)
        
        if self.encoder:
            speaker_emb = self.encoder(Tensor(mel_spec.data))
        else:
            # Fallback: use average of mel spectrogram
            speaker_emb = Tensor(mel_spec.data.mean(axis=1))
        
        # Generate speech with cloned voice
        return self.generate_speech(text, speaker_embedding=speaker_emb)
    
    def save_audio(self, audio: np.ndarray, path: str):
        """Save generated audio."""
        self.waveform_gen.save(audio, path)


def clone_voice(
    text: str,
    reference_audio_path: str,
    model_path: Optional[str] = None
) -> np.ndarray:
    """
    Quick voice cloning function.
    
    Args:
        text: Text to generate
        reference_audio_path: Path to reference audio
        model_path: Optional path to trained model
        
    Returns:
        Generated audio
    """
    # Load reference audio
    try:
        import soundfile as sf
        audio, sr = sf.read(reference_audio_path)
    except ImportError:
        from scipy.io import wavfile
        sr, audio = wavfile.read(reference_audio_path)
    
    # Create inference
    inference = VoiceInference(sample_rate=sr)
    
    # Clone voice
    generated = inference.clone_voice(text, audio)
    
    return generated


def generate_speech(
    text: str,
    speaker_name: Optional[str] = None,
    model_path: Optional[str] = None
) -> np.ndarray:
    """
    Quick speech generation function.
    
    Args:
        text: Text to generate
        speaker_name: Optional speaker name for voice cloning
        model_path: Optional path to trained model
        
    Returns:
        Generated audio
    """
    inference = VoiceInference()
    
    # Load speaker embedding if provided
    speaker_emb = None
    if speaker_name and model_path:
        # Load from model
        import pickle
        emb_path = Path(model_path) / "speaker_embedding.pkl"
        if emb_path.exists():
            with open(emb_path, 'rb') as f:
                emb_data = pickle.load(f)
                speaker_emb = Tensor(emb_data)
    
    return inference.generate_speech(text, speaker_embedding=speaker_emb)
