"""
NAPLY Easy Fine-tuning API
===========================

Simple, one-liner API for fine-tuning AI models.

Features:
- One-liner fine-tuning
- Auto-handles LoRA, optimizer, scheduler
- All 10 naply training methods
- All dataset formats supported
- Stop and resume anytime
- CPU optimized

Usage:
    import naply
    
    # One-liner fine-tuning
    model = naply.finetune(base_model="small", dataset="my_data.jsonl", epochs=3)
    
    # Or step by step
    model = naply.load_for_finetune("small")
    naply.add_lora(model, rank=8)
    naply.train_lora(model, "my_data.jsonl", epochs=3)
    naply.save_finetuned(model, "my_model/")
"""

import os
import json
import csv
import gc
import numpy as np
from typing import Optional, Union, List, Dict, Any

from .tensor import Tensor
from .base_model_loader import load, load_pretrained, NaplyModel, MODEL_CONFIGS
from .finetune import (
    LoRAConfig, FineTuneConfig,
    apply_lora, merge_lora, save_lora_weights, load_lora_weights,
    count_parameters, print_trainable_parameters
)
from .finetune_trainer import FineTuneTrainer


# Special tokens
SYS_TOKEN = "<" + "|system|" + ">"
USR_TOKEN = "<" + "|user|" + ">"
AST_TOKEN = "<" + "|assistant|" + ">"
END_TOKEN = "<" + "|end|" + ">"


# =============================================================================
# SMART DATA LOADER FOR FINE-TUNING
# =============================================================================

class FineTuneDataLoader:
    """Smart data loader for fine-tuning datasets.
    
    Supports all formats: JSONL, JSON, CSV, TSV, Parquet, TXT, folders.
    """
    
    def __init__(self, path: str, max_samples: int = 50000):
        self.path = path
        self.max_samples = max_samples
        self.data = []
        
    def load(self) -> List[str]:
        """Load data from path."""
        print(f"   Loading data from: {self.path}")
        
        if not os.path.exists(self.path):
            print(f"   [WARNING] Path not found: {self.path}")
            return []
        
        if os.path.isfile(self.path):
            self._load_file(self.path)
        else:
            for root, dirs, files in os.walk(self.path):
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                for f in files:
                    if f.startswith('.'):
                        continue
                    self._load_file(os.path.join(root, f))
                    if len(self.data) >= self.max_samples:
                        break
        
        print(f"   Loaded {len(self.data):,} samples")
        return self.data
    
    def _load_file(self, filepath: str):
        """Load a single file."""
        ext = os.path.splitext(filepath)[1].lower()
        
        try:
            if ext == '.jsonl':
                self._load_jsonl(filepath)
            elif ext == '.json':
                self._load_json(filepath)
            elif ext == '.csv':
                self._load_csv(filepath)
            elif ext == '.tsv':
                self._load_tsv(filepath)
            elif ext == '.parquet':
                self._load_parquet(filepath)
            elif ext in ['.txt', '.md']:
                self._load_text(filepath)
        except Exception as e:
            print(f"   [WARN] {os.path.basename(filepath)}: {str(e)[:40]}")
    
    def _format_sample(self, text: str) -> str:
        """Format as instruction sample."""
        text = str(text)[:3000]
        return f"{SYS_TOKEN}\nAI Assistant.\n{USR_TOKEN}\n{text}\n{AST_TOKEN}\n"
    
    def _format_chat(self, user: str, assistant: str) -> str:
        """Format as chat sample."""
        return f"{SYS_TOKEN}\nYou are a helpful AI.\n{USR_TOKEN}\n{user}\n{AST_TOKEN}\n{assistant}\n{END_TOKEN}"
    
    def _load_jsonl(self, filepath: str):
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for i, line in enumerate(f):
                if i >= self.max_samples:
                    break
                if not line.strip():
                    continue
                try:
                    obj = json.loads(line)
                    text = self._extract_text(obj)
                    if text and len(text) > 20:
                        self.data.append(self._format_sample(text))
                except:
                    pass
    
    def _load_json(self, filepath: str):
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            data = json.load(f)
        
        if isinstance(data, list):
            for i, item in enumerate(data):
                if i >= self.max_samples:
                    break
                text = self._extract_text(item)
                if text and len(text) > 20:
                    self.data.append(self._format_sample(text))
        elif isinstance(data, dict):
            text = self._extract_text(data)
            if text:
                self.data.append(self._format_sample(text))
    
    def _load_csv(self, filepath: str):
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                if i >= self.max_samples:
                    break
                text = self._extract_text(row)
                if text and len(text) > 20:
                    self.data.append(self._format_sample(text))
    
    def _load_tsv(self, filepath: str):
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.DictReader(f, delimiter='\t')
            for i, row in enumerate(reader):
                if i >= self.max_samples:
                    break
                text = self._extract_text(row)
                if text and len(text) > 20:
                    self.data.append(self._format_sample(text))
    
    def _load_parquet(self, filepath: str):
        try:
            import pandas as pd
            df = pd.read_parquet(filepath)
            for i, row in df.iloc[:self.max_samples].iterrows():
                text = self._extract_text(row.to_dict())
                if text and len(text) > 20:
                    self.data.append(self._format_sample(text))
        except ImportError:
            print("   [NOTE] Install pandas for parquet support")
    
    def _load_text(self, filepath: str):
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        chunks = [content[i:i+2000] for i in range(0, min(len(content), 100000), 2000)]
        for chunk in chunks:
            if len(chunk) > 50:
                self.data.append(self._format_sample(chunk))
    
    def _extract_text(self, obj) -> str:
        """Extract text from various data formats."""
        if isinstance(obj, str):
            return obj
        
        if isinstance(obj, dict):
            # Instruction format
            if 'instruction' in obj and 'output' in obj:
                inp = obj.get('input', '')
                return f"Instruction: {obj['instruction']}\nInput: {inp}\nResponse: {obj['output']}"
            
            # Chat format
            if 'conversations' in obj:
                convs = []
                for msg in obj['conversations']:
                    if 'value' in msg:
                        convs.append(msg['value'])
                    elif 'content' in msg:
                        convs.append(msg['content'])
                return "\n".join(convs)
            
            # Common fields
            for key in ['text', 'content', 'body', 'question', 'answer', 'prompt', 'response']:
                if key in obj and obj[key]:
                    return str(obj[key])
            
            # Fallback
            return " ".join(str(v) for v in obj.values() if isinstance(v, str) and len(str(v)) > 10)
        
        return ""


# =============================================================================
# MAIN FINE-TUNING FUNCTION
# =============================================================================

def finetune(
    base_model: Union[str, NaplyModel] = "small",
    dataset: Optional[str] = None,
    epochs: int = 3,
    steps_per_epoch: int = 500,
    batch_size: int = 4,
    learning_rate: float = 2e-4,
    lora_rank: int = 8,
    lora_alpha: int = 16,
    output_dir: str = "finetune_output",
    resume: bool = True,
    **kwargs
) -> NaplyModel:
    """Fine-tune a base model with your data.
    
    This is the main one-liner API for fine-tuning.
    
    Args:
        base_model: Base model name ("tiny", "small", "medium") or path or NaplyModel
        dataset: Path to dataset (any format)
        epochs: Number of training epochs
        steps_per_epoch: Steps per epoch
        batch_size: Training batch size
        learning_rate: Learning rate
        lora_rank: LoRA rank (lower = fewer params, higher = more capacity)
        lora_alpha: LoRA scaling (typically 2x rank)
        output_dir: Output directory for checkpoints
        resume: Whether to resume from checkpoint
        
    Returns:
        Fine-tuned model
        
    Example:
        model = naply.finetune("small", "my_data.jsonl", epochs=3)
    """
    print("\n" + "="*60)
    print("NAPLY FINE-TUNING")
    print("="*60)
    
    # Load base model
    if isinstance(base_model, str):
        if base_model in MODEL_CONFIGS:
            print(f"   Creating {base_model} model...")
            model = load_pretrained(base_model)
        elif os.path.exists(base_model):
            print(f"   Loading model from: {base_model}")
            model = load(base_model)
        else:
            print(f"   Unknown model '{base_model}', using 'small'")
            model = load_pretrained("small")
    else:
        model = base_model
    
    # Apply LoRA
    print(f"\n   Applying LoRA (rank={lora_rank}, alpha={lora_alpha})...")
    lora_config = LoRAConfig(rank=lora_rank, alpha=lora_alpha)
    model = apply_lora(model, lora_config)
    
    # Load data
    if dataset:
        loader = FineTuneDataLoader(dataset)
        data = loader.load()
    else:
        print("   [WARNING] No dataset provided!")
        data = []
    
    if not data:
        print("   [ERROR] No data to train on!")
        return model
    
    # Create trainer config
    train_config = FineTuneConfig(
        learning_rate=learning_rate,
        batch_size=batch_size,
        epochs=epochs,
        output_dir=output_dir
    )
    
    # Create trainer
    trainer = FineTuneTrainer(model, train_config)
    
    # Train
    history = trainer.train(
        data,
        epochs=epochs,
        steps_per_epoch=steps_per_epoch,
        resume=resume
    )
    
    # Save final model
    trainer.save(output_dir)
    
    return model


# =============================================================================
# STEP-BY-STEP API
# =============================================================================

def load_for_finetune(model_name: str = "small") -> NaplyModel:
    """Load a base model for fine-tuning.
    
    Args:
        model_name: Model name or path
        
    Returns:
        NaplyModel ready for fine-tuning
    """
    if model_name in MODEL_CONFIGS:
        return load_pretrained(model_name)
    elif os.path.exists(model_name):
        return load(model_name)
    else:
        print(f"   Unknown model '{model_name}', using 'small'")
        return load_pretrained("small")


def add_lora(
    model: NaplyModel,
    rank: int = 8,
    alpha: int = 16,
    target_modules: Optional[List[str]] = None
) -> NaplyModel:
    """Add LoRA adapters to model.
    
    Args:
        model: Base model
        rank: LoRA rank
        alpha: LoRA scaling
        target_modules: Which modules to target
        
    Returns:
        Model with LoRA adapters
    """
    config = LoRAConfig(rank=rank, alpha=alpha, target_modules=target_modules)
    return apply_lora(model, config)


def train_lora(
    model: NaplyModel,
    dataset: str,
    epochs: int = 3,
    batch_size: int = 4,
    learning_rate: float = 2e-4,
    output_dir: str = "finetune_output"
) -> Dict[str, Any]:
    """Train LoRA adapters on dataset.
    
    Args:
        model: Model with LoRA adapters
        dataset: Path to dataset
        epochs: Training epochs
        batch_size: Batch size
        learning_rate: Learning rate
        output_dir: Output directory
        
    Returns:
        Training history
    """
    # Load data
    loader = FineTuneDataLoader(dataset)
    data = loader.load()
    
    if not data:
        print("   [ERROR] No data!")
        return {}
    
    # Create trainer
    config = FineTuneConfig(
        learning_rate=learning_rate,
        batch_size=batch_size,
        epochs=epochs,
        output_dir=output_dir
    )
    trainer = FineTuneTrainer(model, config)
    
    # Train
    history = trainer.train(data, epochs=epochs)
    trainer.save(output_dir)
    return history


def save_finetuned(model: NaplyModel, path: str):
    """Save fine-tuned model.
    
    Args:
        model: Fine-tuned model
        path: Path to save
    """
    os.makedirs(path, exist_ok=True)
    save_lora_weights(model, path)
    print(f"   Saved to: {path}")


def load_finetuned(model: NaplyModel, path: str) -> NaplyModel:
    """Load fine-tuned LoRA weights into model.
    
    Args:
        model: Base model with LoRA
        path: Path to load from
        
    Returns:
        Model with loaded weights
    """
    load_lora_weights(model, path)
    return model


def merge_and_save(model: NaplyModel, path: str):
    """Merge LoRA weights and save complete model.
    
    After merging, the model can run without LoRA overhead.
    
    Args:
        model: Model with LoRA
        path: Path to save
    """
    merged = merge_lora(model)
    os.makedirs(path, exist_ok=True)
    
    # Save full model state
    import pickle
    state = merged.state_dict()
    with open(os.path.join(path, "model.pkl"), "wb") as f:
        pickle.dump(state, f)
    
    print(f"   Merged model saved to: {path}")


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Main API
    "finetune",
    # Step-by-step API
    "load_for_finetune",
    "add_lora",
    "train_lora",
    "save_finetuned",
    "load_finetuned",
    "merge_and_save",
    # Data loader
    "FineTuneDataLoader",
]
