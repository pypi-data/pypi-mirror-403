"""
NAPLY Model - Main Interface
============================

The main Model class for building and training AI models.
This is the primary interface users interact with.
"""

import os
import json
import pickle
import time
import numpy as np
from typing import Optional, Union, Dict, List, Any
from tqdm import tqdm

from .tensor import Tensor
from .config import ModelConfig, TrainConfig, PRESETS, get_preset
from .transformer import GPT
from .tokenizer import BPETokenizer, CharTokenizer
from .optim import AdamW, CosineScheduler, clip_grad_norm
from .data import UniversalLoader, TextDataset, DataLoader
from .functional import cross_entropy


class Model:
    """
    NAPLY Model - Train AI from scratch with just a few lines of code.
    
    No limits on architecture. Any dataset format. Real learning.
    
    Args:
        config: ModelConfig or preset name ("tiny", "small", "medium", "large", "xl", etc.)
        layers: Number of transformer layers (if not using preset)
        heads: Number of attention heads (if not using preset)
        embedding: Embedding dimension (if not using preset)
        vocab_size: Vocabulary size (if not using preset)
        context: Maximum context length (if not using preset)
        
    Example:
        # Using preset
        model = Model("medium")
        
        # Custom architecture (no limits!)
        model = Model(layers=24, heads=16, embedding=1024, vocab_size=50000, context=4096)
        
        # Train on any data
        model.train("my_data/", epochs=10)
        
        # Chat
        model.chat("Hello!")
    """
    
    def __init__(
        self,
        config: Optional[Union[ModelConfig, str]] = None,
        layers: Optional[int] = None,
        heads: Optional[int] = None,
        embedding: Optional[int] = None,
        vocab_size: Optional[int] = None,
        context: Optional[int] = None,
        **kwargs
    ):
        # Handle config
        if isinstance(config, str):
            self.config = get_preset(config)
        elif isinstance(config, ModelConfig):
            self.config = config
        elif config is None and any([layers, heads, embedding]):
            # Custom architecture from parameters
            self.config = ModelConfig(
                n_layer=layers or 12,
                n_head=heads or 12,
                n_embd=embedding or 768,
                vocab_size=vocab_size or 50000,
                block_size=context or 2048,
                **kwargs
            )
        else:
            # Default to medium
            self.config = get_preset("medium")
        
        # Override individual parameters if provided
        if layers: self.config.n_layer = layers
        if heads: self.config.n_head = heads
        if embedding: self.config.n_embd = embedding
        if vocab_size: self.config.vocab_size = vocab_size
        if context: self.config.block_size = context
        
        # Initialize model
        self.model = GPT(
            vocab_size=self.config.vocab_size,
            n_layer=self.config.n_layer,
            n_head=self.config.n_head,
            n_embd=self.config.n_embd,
            block_size=self.config.block_size,
            dropout=self.config.dropout,
            bias=self.config.bias,
            use_swiglu=self.config.use_swiglu,
            use_rms_norm=self.config.use_rms_norm,
        )
        
        # Tokenizer
        self.tokenizer = None
        
        # Training state
        self.is_trained = False
        self.train_history = {'loss': [], 'lr': []}
    
    def count_params(self) -> int:
        """Count total trainable parameters."""
        return self.model.count_parameters()
    
    def summary(self) -> str:
        """Get model summary."""
        params = self.count_params()
        return (
            f"NAPLY Model Summary\n"
            f"{'='*40}\n"
            f"Layers:     {self.config.n_layer}\n"
            f"Heads:      {self.config.n_head}\n"
            f"Embedding:  {self.config.n_embd}\n"
            f"Vocab Size: {self.config.vocab_size:,}\n"
            f"Context:    {self.config.block_size:,}\n"
            f"Parameters: {params:,} ({params/1e6:.2f}M)\n"
            f"{'='*40}"
        )
    
    def train(
        self,
        data_path: str,
        epochs: int = 5,
        batch_size: int = 32,
        learning_rate: float = 1e-4,
        weight_decay: float = 0.01,
        warmup_steps: int = 100,
        max_grad_norm: float = 1.0,
        save_every: int = 1,
        output_dir: Optional[str] = None,
        verbose: bool = True
    ) -> Dict[str, List[float]]:
        """
        Train the model on your data.
        
        Supports any format: .txt, .json, .jsonl, .csv, or folder.
        
        Args:
            data_path: Path to data file or folder
            epochs: Number of training epochs
            batch_size: Training batch size
            learning_rate: Initial learning rate
            weight_decay: Weight decay for regularization
            warmup_steps: Number of warmup steps
            max_grad_norm: Maximum gradient norm for clipping
            save_every: Save checkpoint every N epochs
            output_dir: Directory to save checkpoints
            verbose: Whether to print progress
            
        Returns:
            Training history with losses
            
        Example:
            model.train("my_data/", epochs=10, batch_size=32)
        """
        if verbose:
            print(f"\n🚀 NAPLY Training Started")
            print(self.summary())
        
        # Load data
        if verbose:
            print(f"\n📂 Loading data from: {data_path}")
        
        loader = UniversalLoader(data_path)
        texts = loader.load()
        
        if len(texts) == 0:
            raise ValueError(f"No data found in {data_path}")
        
        if verbose:
            print(f"   Loaded {len(texts)} text samples")
        
        # Train tokenizer if needed
        if self.tokenizer is None:
            if verbose:
                print(f"\n🔤 Training tokenizer (vocab_size={self.config.vocab_size})...")
            
            if self.config.vocab_size < 500:
                self.tokenizer = CharTokenizer()
            else:
                self.tokenizer = BPETokenizer(vocab_size=self.config.vocab_size)
            
            self.tokenizer.train(texts, verbose=verbose)
            
            # Update model vocab size to match tokenizer
            if self.tokenizer.vocab_size != self.config.vocab_size:
                if verbose:
                    print(f"   Adjusting vocab size: {self.config.vocab_size} -> {self.tokenizer.vocab_size}")
                self.config.vocab_size = self.tokenizer.vocab_size
                
                # Rebuild the model weights for the new vocab size
                self.model = GPT(
                    vocab_size=self.config.vocab_size,
                    n_layer=self.config.n_layer,
                    n_head=self.config.n_head,
                    n_embd=self.config.n_embd,
                    block_size=self.config.block_size,
                    dropout=self.config.dropout,
                    bias=self.config.bias,
                    use_swiglu=self.config.use_swiglu,
                    use_rms_norm=self.config.use_rms_norm,
                )
        
        # Create dataset and dataloader
        if verbose:
            print(f"\n📊 Preparing dataset...")
        
        dataset = TextDataset(texts, self.tokenizer, max_length=self.config.block_size)
        dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
        
        if verbose:
            print(f"   {len(dataset)} samples, {len(dataloader)} batches per epoch")
        
        # Setup optimizer and scheduler
        optimizer = AdamW(
            self.model.parameters(),
            lr=learning_rate,
            weight_decay=weight_decay
        )
        
        total_steps = len(dataloader) * epochs
        scheduler = CosineScheduler(optimizer, total_steps, warmup_steps=warmup_steps)
        
        # Training loop
        if verbose:
            print(f"\n🏋️ Training for {epochs} epochs...")
        
        self.model.train()
        global_step = 0
        
        for epoch in range(epochs):
            epoch_loss = 0
            num_batches = 0
            
            pbar = tqdm(dataloader, desc=f"Epoch {epoch+1}/{epochs}", disable=not verbose)
            
            for batch_x, batch_y in pbar:
                # Forward pass
                logits, _ = self.model(batch_x)
                
                # Compute loss
                B, T, C = logits.shape
                logits_flat = logits.reshape(B * T, C)
                targets_flat = batch_y.reshape(B * T)
                loss = cross_entropy(logits_flat, targets_flat)
                
                # Backward pass
                optimizer.zero_grad()
                loss.backward()
                
                # Gradient clipping
                clip_grad_norm(self.model.parameters(), max_grad_norm)
                
                # Update
                optimizer.step()
                scheduler.step()
                
                # Track
                epoch_loss += loss.data
                num_batches += 1
                global_step += 1
                
                self.train_history['loss'].append(float(loss.data))
                self.train_history['lr'].append(optimizer.lr)
                
                pbar.set_postfix({
                    'loss': f"{loss.data:.4f}",
                    'lr': f"{optimizer.lr:.2e}"
                })
            
            avg_loss = epoch_loss / num_batches
            
            if verbose:
                print(f"   Epoch {epoch+1}: avg_loss={avg_loss:.4f}")
            
            # Save checkpoint
            if output_dir and (epoch + 1) % save_every == 0:
                ckpt_path = os.path.join(output_dir, f"checkpoint_epoch_{epoch+1}")
                self.save(ckpt_path)
                if verbose:
                    print(f"   💾 Saved checkpoint to {ckpt_path}")
        
        # Save final model to output_dir
        if output_dir:
            self.save(output_dir)
            if verbose:
                print(f"   💾 Saved final model to {output_dir}")
        
        self.is_trained = True
        
        if verbose:
            print(f"\n✅ Training complete! Final loss: {self.train_history['loss'][-1]:.4f}")
        
        return self.train_history
    
    def generate(
        self,
        prompt: str,
        max_tokens: int = 100,
        temperature: float = 0.8,
        top_k: int = 40,
        top_p: float = 0.9,
        stop_tokens: Optional[List[str]] = None
    ) -> str:
        """
        Generate text from a prompt.
        
        Args:
            prompt: Starting text
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (higher = more random)
            top_k: Top-K sampling (0 = disabled)
            top_p: Top-P (nucleus) sampling
            stop_tokens: Optional list of strings to stop generation
            
        Returns:
            Generated text
            
        Example:
            text = model.generate("Once upon a time", max_tokens=50)
        """
        if self.tokenizer is None:
            raise ValueError("Model not trained. Call train() first.")
        
        self.model.eval()
        
        # Encode prompt
        input_ids = self.tokenizer.encode(prompt)
        generated = list(input_ids)
        
        past_kv = None
        
        for i in range(max_tokens):
            # If we've reached the context limit, we must stop using past_kv
            # and slide the window instead.
            if len(generated) >= self.config.block_size:
                past_kv = None
                
            # If we use past_kv, we only need to pass the newest token.
            if past_kv is not None:
                # Use only the last token
                context = [generated[-1]]
            else:
                # pass the whole prompt (up to block_size)
                context = generated[-self.config.block_size:]
            
            x = Tensor(np.array([context], dtype=np.int32))
            
            # Forward pass
            logits, past_kv = self.model(x, past_key_values=past_kv)
            logits = logits.data[0, -1, :]  # Last position
            
            # Temperature
            logits = logits / temperature
            
            # Top-K
            if top_k > 0:
                indices_to_remove = logits < np.partition(logits, -top_k)[-top_k]
                logits[indices_to_remove] = -np.inf
            
            # Top-P (Nucleus)
            if top_p < 1.0:
                sorted_indices = np.argsort(logits)[::-1]
                sorted_logits = logits[sorted_indices]
                cumulative_probs = np.cumsum(np.exp(sorted_logits) / np.sum(np.exp(sorted_logits)))
                sorted_indices_to_remove = cumulative_probs > top_p
                sorted_indices_to_remove[1:] = sorted_indices_to_remove[:-1].copy()
                sorted_indices_to_remove[0] = False
                indices_to_remove = sorted_indices[sorted_indices_to_remove]
                logits[indices_to_remove] = -np.inf
            
            # Sample
            probs = np.exp(logits) / np.sum(np.exp(logits))
            next_token = np.random.choice(len(probs), p=probs)
            
            generated.append(next_token)
            
            # Check stop tokens
            if stop_tokens:
                current_text = self.tokenizer.decode(generated)
                for stop in stop_tokens:
                    if stop in current_text:
                        # Trim to stop token
                        idx = current_text.find(stop)
                        return current_text[:idx]
            
            # Check EOS
            if next_token == self.tokenizer.vocab.get(self.tokenizer.eos_token):
                break
        
        return self.tokenizer.decode(generated)
    
    def chat(self, prompt: str, max_tokens: int = 100) -> str:
        """
        Chat with the model.
        
        Args:
            prompt: User message
            max_tokens: Maximum tokens to generate
            
        Returns:
            Model response
            
        Example:
            response = model.chat("What is AI?")
        """
        return self.generate(prompt, max_tokens=max_tokens)
    
    def save(self, path: str):
        """
        Save the complete model.
        
        Saves model weights, tokenizer, and config.
        
        Args:
            path: Path to save (will create directory)
            
        Example:
            model.save("my_model/")
        """
        os.makedirs(path, exist_ok=True)
        
        # Save config
        config_path = os.path.join(path, "config.json")
        with open(config_path, 'w') as f:
            json.dump(self.config.to_dict(), f, indent=2)
        
        # Save model weights
        weights_path = os.path.join(path, "model.pkl")
        with open(weights_path, 'wb') as f:
            pickle.dump(self.model.state_dict(), f)
        
        # Save tokenizer
        if self.tokenizer:
            tokenizer_path = os.path.join(path, "tokenizer.json")
            self.tokenizer.save(tokenizer_path)
        
        # Save training history
        history_path = os.path.join(path, "history.json")
        with open(history_path, 'w') as f:
            json.dump(self.train_history, f)
        
        print(f"✅ Model saved to {path}")
    
    @classmethod
    def load(cls, path: str) -> 'Model':
        """
        Load a saved model.
        
        Args:
            path: Path to saved model
            
        Returns:
            Loaded Model instance
            
        Example:
            model = Model.load("my_model/")
        """
        # Load config
        config_path = os.path.join(path, "config.json")
        with open(config_path, 'r') as f:
            config_dict = json.load(f)
        config = ModelConfig.from_dict(config_dict)
        
        # Create model
        model = cls(config)
        
        # Load weights
        weights_path = os.path.join(path, "model.pkl")
        with open(weights_path, 'rb') as f:
            state_dict = pickle.load(f)
        model.model.load_state_dict(state_dict)
        
        # Load tokenizer
        tokenizer_path = os.path.join(path, "tokenizer.json")
        if os.path.exists(tokenizer_path):
            model.tokenizer = BPETokenizer.load(tokenizer_path)
        
        # Load history
        history_path = os.path.join(path, "history.json")
        if os.path.exists(history_path):
            with open(history_path, 'r') as f:
                model.train_history = json.load(f)
        
        model.is_trained = True
        print(f"✅ Model loaded from {path}")
        
        return model
    
    def __repr__(self) -> str:
        params = self.count_params()
        return f"Model(layers={self.config.n_layer}, heads={self.config.n_head}, embd={self.config.n_embd}, params={params:,})"
