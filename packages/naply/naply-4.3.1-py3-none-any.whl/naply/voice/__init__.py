"""
NAPLY Voice Generation & Cloning
==================================

Build voice generation and cloning models from scratch.

Core Pipeline:
    Audio → Mel Spectrogram → Encoder → Decoder → Waveform

Example:
    from naply.voice import VoiceTrainer
    
    trainer = VoiceTrainer(
        data_path="my_voice/",
        speaker_name="lakshmi"
    )
    trainer.train(epochs=200)
    trainer.save("lakshmi_voice.pt")
"""

from .trainer import VoiceTrainer
from .inference import VoiceInference, clone_voice, generate_speech
from .spectrogram import MelSpectrogram, SpectrogramProcessor
from .encoder import VoiceEncoder, SpeakerEncoder
from .decoder import VoiceDecoder, AcousticModel
from .vocoder import Vocoder, WaveformGenerator
from .dataset import VoiceDataset, VoiceDataLoader

__all__ = [
    'VoiceTrainer',
    'VoiceInference',
    'clone_voice',
    'generate_speech',
    'MelSpectrogram',
    'SpectrogramProcessor',
    'VoiceEncoder',
    'SpeakerEncoder',
    'VoiceDecoder',
    'AcousticModel',
    'Vocoder',
    'WaveformGenerator',
    'VoiceDataset',
    'VoiceDataLoader',
]
