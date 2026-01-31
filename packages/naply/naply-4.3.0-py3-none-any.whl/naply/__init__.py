"""
NAPLY - Production-Ready AI Training Library
=============================================

Build powerful AI models from scratch with just a few lines of code.
Lightweight, CPU-optimized, PyTorch-like API.

Quick Start:
    import naply
    
    model = naply.Model(layers=12, heads=12, embedding=768)
    model.train("my_data/", epochs=10)
    model.chat("Hello!")
"""

__version__ = "4.3.0"
__author__ = "NAPLY Team"

from typing import Optional

# =============================================================================
# Core Tensor & Autograd
# =============================================================================
from .tensor import Tensor

# =============================================================================
# Functional Operations
# =============================================================================
from .functional import (
    # Loss functions
    cross_entropy, mse_loss, kl_divergence, focal_loss,
    # Activations
    relu, gelu, silu, swish, sigmoid, tanh, softmax, log_softmax,
    leaky_relu, elu,
    # Normalization
    layer_norm, rms_norm, batch_norm,
    # Regularization
    dropout,
    # Utilities
    clip_grad_norm, masked_fill,
    one_hot, sinusoidal_position_encoding, rotary_position_embedding,
)

# =============================================================================
# Neural Network Layers
# =============================================================================
from .layers import (
    Module, Linear, Embedding, LayerNorm, RMSNorm,
    Dropout, Sequential, ModuleList, Adapter,
    GELU, SiLU, ReLU, Softmax,
)

# =============================================================================
# Attention Mechanisms
# =============================================================================
from .attention import (
    MultiHeadAttention,
    GroupedQueryAttention,
    FlashAttention,
    SlidingWindowAttention,
)

# =============================================================================
# Transformer Architecture
# =============================================================================
from .transformer import (
    FeedForward, SwiGLU, TransformerBlock, GPT, LLaMA,
)

# =============================================================================
# Main Model Interface
# =============================================================================
from .model import Model


class AI(Model):
    """
    NAPLY AI - Backwards-compatible alias around `Model`.

    This matches the older README style:

        import naply
        model = naply.AI(size="small")
        model.train("my_data.txt", epochs=5)
        print(model.chat("Hello"))

    Internally it just maps common `size` presets to the existing Model presets.
    """

    _SIZE_TO_PRESET = {
        "tiny": "tiny",
        "small": "small",
        "medium": "medium",
        "large": "large",
        "xl": "xl",
        "xxl": "xxl",
    }

    def __init__(
        self,
        size: str = "small",
        layers: Optional[int] = None,
        heads: Optional[int] = None,
        embedding: Optional[int] = None,
        vocab_size: Optional[int] = None,
        context: Optional[int] = None,
        **kwargs,
    ):
        # Map size -> preset name used by ModelConfig presets
        preset = self._SIZE_TO_PRESET.get(size.lower(), "small")
        super().__init__(
            config=preset,
            layers=layers,
            heads=heads,
            embedding=embedding,
            vocab_size=vocab_size,
            context=context,
            **kwargs,
        )

# =============================================================================
# Configuration
# =============================================================================
from .config import ModelConfig, TrainConfig, PRESETS, get_preset

# =============================================================================
# Tokenizers
# =============================================================================
from .tokenizer import (
    Tokenizer, BPETokenizer, WordPieceTokenizer, CharTokenizer, SimpleTokenizer,
)

# =============================================================================
# Data Loading
# =============================================================================
from .data import (
    Dataset, TextDataset, DataLoader, UniversalLoader,
    load_data, prepare_training_data,
)

# =============================================================================
# Optimizers & Schedulers
# =============================================================================
from .optim import (
    Optimizer, SGD, Adam, AdamW, RMSprop, AdaGrad,
    LRScheduler, CosineScheduler, WarmupScheduler, LinearScheduler,
    StepScheduler, ReduceOnPlateau,
    clip_grad_norm, clip_grad_value,
)

# =============================================================================
# Training Methods (10 Advanced Methods)
# =============================================================================
from .methods import (
    BaseTrainer,
    CRCTrainer,   # Consistency-Retention Compression
    DCLTrainer,   # Domain-Constrained Learning
    ILCTrainer,   # Incremental Learning Consolidation
    MCUTrainer,   # Memory Consolidation Unit
    P3Engine,     # Parallel Pipelined Processing
    PPLTrainer,   # Progressive Prompt Learning
    PTLTrainer,   # Parallel Training and Learning (Multi-threaded CPU)
    RDLTrainer,   # Recursive Data Learning
    S3LTrainer,   # Structured Selective Stabilized Learning
    SGLTrainer,   # Sparse Gradient Learning
    GradientAccumulator,
    EMAModel,
)

# =============================================================================
# Specialist Models
# =============================================================================
from .specialists import (
    PowerAIEnsemble,
    SyntaxNet, LexiconNet,
    LogicNet, ThoughtNet,
    CodeNet, TechNet,
    GrammarNet, ReasoningNet, DomainNet,
    SpecialistModel,
)

# =============================================================================
# Advanced Features (Huge Datasets & Training Control)
# =============================================================================
try:
    from .large_dataset import StreamingDataset, HugeDatasetLoader, create_huge_dataset_loader
    from .training_control import TrainingController, TrainingState
except ImportError:
    # Optional features - may not be available in all installations
    StreamingDataset = None
    HugeDatasetLoader = None
    create_huge_dataset_loader = None
    TrainingController = None
    TrainingState = None

# =============================================================================
# Easy API (Simplest Way to Use NAPLY)
# =============================================================================
try:
    from .easy import train, chat, build, quick_start
except ImportError:
    train = None
    chat = None
    build = None
    quick_start = None

# =============================================================================
# Unified Training Engine
# =============================================================================
try:
    from .trainer import (
        BaseTrainer, UnifiedTrainer,
        GPUManager, DeviceManager,
        AdvancedCheckpoint, CheckpointManager,
        TrainingLogger, MetricsLogger,
    )
except ImportError:
    BaseTrainer = None
    UnifiedTrainer = None
    GPUManager = None
    DeviceManager = None
    AdvancedCheckpoint = None
    CheckpointManager = None
    TrainingLogger = None
    MetricsLogger = None

# =============================================================================
# Voice Generation & Cloning
# =============================================================================
try:
    from .voice import (
        VoiceTrainer, VoiceInference,
        clone_voice, generate_speech,
        MelSpectrogram, SpectrogramProcessor,
        VoiceEncoder, SpeakerEncoder,
        VoiceDecoder, AcousticModel,
        Vocoder, WaveformGenerator,
        VoiceDataset, VoiceDataLoader,
    )
except ImportError:
    VoiceTrainer = None
    VoiceInference = None
    clone_voice = None
    generate_speech = None

# =============================================================================
# Image Generation (Diffusion Models)
# =============================================================================
try:
    from .image import (
        ImageTrainer, ImageInference,
        generate_image, generate_images,
        VAE, VariationalAutoencoder,
        UNet, DiffusionUNet,
        DiffusionModel, DiffusionScheduler,
        ImageDataset, ImageDataLoader,
    )
except ImportError:
    ImageTrainer = None
    ImageInference = None
    generate_image = None
    generate_images = None

# =============================================================================
# Enhanced Text Generation
# =============================================================================
try:
    from .text_enhanced import EnhancedTextModel
    from .powerful_text_model import PowerfulTextModel
except ImportError:
    EnhancedTextModel = None
    PowerfulTextModel = None

# =============================================================================
# CPU Optimizations
# =============================================================================
try:
    from .cpu_optimize import CPUOptimizer, optimize_for_cpu, get_cpu_optimizer
except ImportError:
    CPUOptimizer = None
    optimize_for_cpu = lambda: None
    get_cpu_optimizer = lambda: None

# Auto-optimize on import
try:
    optimize_for_cpu()
except:
    pass

# =============================================================================
# Fine-tuning (LoRA, QLoRA, PEFT)
# =============================================================================
try:
    from .finetune import (
        LoRAConfig, QLoRAConfig, FineTuneConfig,
        LoRALayer, QLoRALayer, LinearWithLoRA,
        apply_lora, merge_lora, unmerge_lora,
        get_trainable_params, save_lora_weights, load_lora_weights,
        count_parameters, print_trainable_parameters,
    )
    from .base_model_loader import (
        NaplyModel, ModelConfig as BaseModelConfig, MODEL_CONFIGS,
        load as load_base_model, load_pretrained, from_naply,
        load_safetensors, load_pytorch, load_gguf,
    )
    from .finetune_trainer import (
        FineTuneTrainer, TrainingState as FineTuneState,
        CosineWarmupScheduler, CheckpointManager as FineTuneCheckpointManager,
    )
    from .easy_finetune import (
        finetune, load_for_finetune, add_lora, train_lora,
        save_finetuned, load_finetuned, merge_and_save,
        FineTuneDataLoader,
    )
except ImportError as e:
    # Fine-tuning module not available
    LoRAConfig = None
    QLoRAConfig = None
    LoRALayer = None
    apply_lora = None
    finetune = None
    FineTuneTrainer = None

# =============================================================================
# Quick API Functions
# =============================================================================

def build(
    preset: str = None,
    layers: int = 12,
    heads: int = 12,
    embedding: int = 768,
    vocab_size: int = 50000,
    context: int = 2048,
    **kwargs
) -> Model:
    """
    Build a new AI model.
    
    Args:
        preset: Use a preset ("tiny", "small", "medium", "large", "xl")
        layers: Number of transformer layers
        heads: Number of attention heads
        embedding: Embedding dimension
        vocab_size: Vocabulary size
        context: Maximum context length
        
    Returns:
        Model ready for training
        
    Example:
        model = naply.build("medium")
        model = naply.build(layers=24, heads=16, embedding=1024)
    """
    if preset:
        return Model(preset)
    return Model(
        layers=layers,
        heads=heads,
        embedding=embedding,
        vocab_size=vocab_size,
        context=context,
        **kwargs
    )


def train(
    data_path: str,
    preset: str = "medium",
    epochs: int = 5,
    batch_size: int = 32,
    learning_rate: float = 1e-4,
    output_path: str = None,
    **kwargs
) -> Model:
    """
    Train a model on your data in one line.
    
    Args:
        data_path: Path to data (txt, json, jsonl, csv, or folder)
        preset: Model preset to use
        epochs: Number of training epochs
        batch_size: Training batch size
        learning_rate: Learning rate
        output_path: Path to save trained model
        
    Returns:
        Trained model
        
    Example:
        model = naply.train("my_data/", epochs=10)
    """
    model = Model(preset)
    model.train(
        data_path,
        epochs=epochs,
        batch_size=batch_size,
        learning_rate=learning_rate,
        **kwargs
    )
    if output_path:
        model.save(output_path)
    return model


def load(path: str) -> Model:
    """
    Load a saved model.
    
    Args:
        path: Path to saved model
        
    Returns:
        Loaded model
        
    Example:
        model = naply.load("my_model/")
    """
    return Model.load(path)


def chat(model_or_path, prompt: str = None):
    """
    Chat with a model.
    
    Args:
        model_or_path: Model instance or path to saved model
        prompt: Optional prompt (starts interactive mode if None)
        
    Example:
        naply.chat("my_model/")
        response = naply.chat(model, "Hello!")
    """
    if isinstance(model_or_path, str):
        model = load(model_or_path)
    else:
        model = model_or_path
    
    if prompt:
        return model.chat(prompt)
    
    # Interactive mode
    print("🤖 NAPLY Chat (type 'quit' to exit)")
    print("-" * 40)
    while True:
        try:
            user_input = input("You: ").strip()
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("Goodbye! 👋")
                break
            if not user_input:
                continue
            response = model.chat(user_input)
            print(f"AI: {response}\n")
        except KeyboardInterrupt:
            print("\nGoodbye! 👋")
            break


# =============================================================================
# Exports
# =============================================================================
__all__ = [
    # Version
    "__version__", "__author__",
    # Advanced features
    "StreamingDataset", "HugeDatasetLoader", "create_huge_dataset_loader",
    "TrainingController", "TrainingState",
    
    # Main API
    "Model", "build", "train", "load", "chat",
    
    # Enhanced Text
    "EnhancedTextModel",
    "PowerfulTextModel",
    
    # Unified Training Engine
    "BaseTrainer", "UnifiedTrainer",
    "GPUManager", "DeviceManager",
    "AdvancedCheckpoint", "CheckpointManager",
    "TrainingLogger", "MetricsLogger",
    
    # Voice Generation
    "VoiceTrainer", "VoiceInference",
    "clone_voice", "generate_speech",
    "MelSpectrogram", "SpectrogramProcessor",
    "VoiceEncoder", "SpeakerEncoder",
    "VoiceDecoder", "AcousticModel",
    "Vocoder", "WaveformGenerator",
    "VoiceDataset", "VoiceDataLoader",
    
    # Image Generation
    "ImageTrainer", "ImageInference",
    "generate_image", "generate_images",
    "VAE", "VariationalAutoencoder",
    "UNet", "DiffusionUNet",
    "DiffusionModel", "DiffusionScheduler",
    "ImageDataset", "ImageDataLoader",
    
    # Easy API (Simplest Way)
    "train", "chat", "build", "quick_start",
    
    # Fine-tuning (New)
    "finetune", "load_for_finetune", "add_lora", "train_lora",
    "save_finetuned", "load_finetuned", "merge_and_save",
    "FineTuneDataLoader",
    "LoRAConfig", "QLoRAConfig", "FineTuneConfig",
    "LoRALayer", "QLoRALayer", "LinearWithLoRA",
    "FineTuneTrainer", "NaplyModel",
    
    # Core
    "Tensor",
    
    # Functional
    "cross_entropy", "mse_loss", "kl_divergence", "focal_loss",
    "relu", "gelu", "silu", "swish", "sigmoid", "tanh", "softmax",
    "log_softmax", "leaky_relu", "elu",
    "layer_norm", "rms_norm", "batch_norm", "dropout",
    "clip_grad_norm", "masked_fill",
    
    # Layers
    "Module", "Linear", "Embedding", "LayerNorm", "RMSNorm",
    "Dropout", "Sequential", "ModuleList", "Adapter",
    "GELU", "SiLU", "ReLU", "Softmax",
    
    # Attention
    "MultiHeadAttention", "GroupedQueryAttention",
    "FlashAttention", "SlidingWindowAttention",
    
    # Transformer
    "FeedForward", "SwiGLU", "TransformerBlock", "GPT", "LLaMA",
    
    # Config
    "ModelConfig", "TrainConfig", "PRESETS", "get_preset",
    
    # Tokenizers
    "Tokenizer", "BPETokenizer", "WordPieceTokenizer",
    "CharTokenizer", "SimpleTokenizer",
    
    # Data
    "Dataset", "TextDataset", "DataLoader", "UniversalLoader",
    "load_data", "prepare_training_data",
    
    # Optimizers
    "Optimizer", "SGD", "Adam", "AdamW", "RMSprop", "AdaGrad",
    "LRScheduler", "CosineScheduler", "WarmupScheduler",
    "LinearScheduler", "StepScheduler", "ReduceOnPlateau",
    
    # Training Methods (10 Methods)
    "BaseTrainer", "CRCTrainer", "DCLTrainer", "ILCTrainer",
    "MCUTrainer", "P3Engine", "PPLTrainer", "PTLTrainer",
    "RDLTrainer", "S3LTrainer", "SGLTrainer", "GradientAccumulator", "EMAModel",
    
    # Specialist Models
    "SyntaxNet", "LexiconNet", "LogicNet", "ThoughtNet",
    "CodeNet", "TechNet",
    "GrammarNet", "ReasoningNet", "DomainNet",
    "SpecialistModel",
    "PowerAIEnsemble",
    
    # Optimizers & Schedulers
    "OneCycleScheduler",
]
