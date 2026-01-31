"""
NAPLY Production Trainer
========================

Complete training loop with all production features:
- Gradient accumulation
- Mixed precision (simulated for CPU)
- Checkpointing
- Early stopping
- Learning rate scheduling
- Progress bars
- Logging
"""

import os
import time
import json
import numpy as np
from typing import Optional, Dict, List, Callable, Any
from tqdm import tqdm

from .tensor import Tensor
from .layers import Module
from .optim import Optimizer, AdamW, CosineScheduler, clip_grad_norm
from .data import DataLoader
from .functional import cross_entropy
from .utils import Checkpoint, EarlyStopping, ProgressTracker


class Trainer:
    """
    Production-grade trainer for NAPLY models.
    
    Includes all features for training large models efficiently:
    - Gradient accumulation
    - Learning rate scheduling with warmup
    - Gradient clipping
    - Checkpointing
    - Early stopping
    - Progress tracking and logging
    
    Example:
        trainer = Trainer(
            model=model,
            optimizer=AdamW(model.parameters(), lr=1e-4),
            epochs=10,
            gradient_accumulation_steps=4,
            checkpoint_dir="checkpoints/"
        )
        trainer.train(train_dataloader, val_dataloader)
    """
    
    def __init__(
        self,
        model: Module,
        optimizer: Optional[Optimizer] = None,
        epochs: int = 5,
        learning_rate: float = 1e-4,
        weight_decay: float = 0.01,
        warmup_steps: int = 100,
        max_grad_norm: float = 1.0,
        gradient_accumulation_steps: int = 1,
        checkpoint_dir: Optional[str] = None,
        checkpoint_every: int = 1,
        early_stopping_patience: int = 0,
        log_every: int = 10,
        eval_every: int = 100,
        callbacks: Optional[List[Callable]] = None,
    ):
        self.model = model
        self.optimizer = optimizer or AdamW(
            model.parameters(), 
            lr=learning_rate, 
            weight_decay=weight_decay
        )
        self.epochs = epochs
        self.warmup_steps = warmup_steps
        self.max_grad_norm = max_grad_norm
        self.gradient_accumulation_steps = gradient_accumulation_steps
        self.checkpoint_dir = checkpoint_dir
        self.checkpoint_every = checkpoint_every
        self.log_every = log_every
        self.eval_every = eval_every
        self.callbacks = callbacks or []
        
        # Setup checkpointing
        self.checkpoint = Checkpoint(checkpoint_dir) if checkpoint_dir else None
        
        # Setup early stopping
        self.early_stopping = EarlyStopping(patience=early_stopping_patience) if early_stopping_patience > 0 else None
        
        # Progress tracking
        self.tracker = ProgressTracker()
        
        # Training state
        self.global_step = 0
        self.current_epoch = 0
        self.best_loss = float('inf')
    
    def train(
        self,
        train_dataloader: DataLoader,
        val_dataloader: Optional[DataLoader] = None,
        resume_from: Optional[str] = None
    ) -> Dict[str, List[float]]:
        """
        Train the model.
        
        Args:
            train_dataloader: Training data loader
            val_dataloader: Optional validation data loader
            resume_from: Optional checkpoint to resume from
            
        Returns:
            Training history
        """
        # Resume from checkpoint if specified
        if resume_from and self.checkpoint:
            metadata = self.checkpoint.load(resume_from, self.model, self.optimizer)
            self.current_epoch = metadata['epoch']
            self.global_step = metadata['step']
            print(f"Resumed from epoch {self.current_epoch}, step {self.global_step}")
        
        # Setup scheduler
        total_steps = len(train_dataloader) * self.epochs
        scheduler = CosineScheduler(
            self.optimizer, 
            total_steps, 
            warmup_steps=self.warmup_steps
        )
        
        # Start tracking
        self.tracker.start()
        
        print(f"\n🚀 Training Started")
        print(f"   Epochs: {self.epochs}")
        print(f"   Steps per epoch: {len(train_dataloader)}")
        print(f"   Gradient accumulation: {self.gradient_accumulation_steps}")
        print(f"   Effective batch size: {train_dataloader.batch_size * self.gradient_accumulation_steps}")
        print()
        
        history = {'train_loss': [], 'val_loss': [], 'lr': []}
        
        for epoch in range(self.current_epoch, self.epochs):
            self.current_epoch = epoch
            
            # Training epoch
            train_loss = self._train_epoch(train_dataloader, scheduler, epoch)
            history['train_loss'].append(train_loss)
            history['lr'].append(self.optimizer.lr)
            
            # Validation
            if val_dataloader:
                val_loss = self._validate(val_dataloader)
                history['val_loss'].append(val_loss)
                print(f"Epoch {epoch+1}/{self.epochs} | Train Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f}")
                
                # Early stopping check
                if self.early_stopping:
                    if self.early_stopping.should_stop(val_loss):
                        print(f"Early stopping triggered at epoch {epoch+1}")
                        break
                
                # Best model tracking
                if val_loss < self.best_loss:
                    self.best_loss = val_loss
                    if self.checkpoint:
                        self.checkpoint.save(
                            self.model, self.optimizer,
                            epoch=epoch, step=self.global_step,
                            loss=val_loss, is_best=True
                        )
            else:
                print(f"Epoch {epoch+1}/{self.epochs} | Train Loss: {train_loss:.4f}")
            
            # Checkpoint
            if self.checkpoint and (epoch + 1) % self.checkpoint_every == 0:
                self.checkpoint.save(
                    self.model, self.optimizer,
                    epoch=epoch, step=self.global_step,
                    loss=train_loss
                )
            
            # Callbacks
            for callback in self.callbacks:
                callback(epoch=epoch, train_loss=train_loss, model=self.model)
        
        print(f"\n✅ Training Complete!")
        print(self.tracker.summary())
        
        return history
    
    def _train_epoch(
        self, 
        dataloader: DataLoader, 
        scheduler,
        epoch: int
    ) -> float:
        """Train for one epoch."""
        self.model.train()
        
        total_loss = 0
        num_batches = 0
        accumulated_loss = 0
        
        pbar = tqdm(dataloader, desc=f"Epoch {epoch+1}", leave=True)
        
        for batch_idx, (x, y) in enumerate(pbar):
            # Forward pass
            logits, _ = self.model(x)
            
            B, T, C = logits.shape
            loss = cross_entropy(logits.reshape(B * T, C), y.reshape(B * T))
            
            # Scale loss for accumulation
            scaled_loss = loss.data / self.gradient_accumulation_steps
            accumulated_loss += scaled_loss
            
            # Backward pass
            loss.backward()
            
            # Update weights
            if (batch_idx + 1) % self.gradient_accumulation_steps == 0:
                # Gradient clipping
                clip_grad_norm(self.model.parameters(), self.max_grad_norm)
                
                # Optimizer step
                self.optimizer.step()
                scheduler.step()
                self.optimizer.zero_grad()
                
                # Track
                total_loss += accumulated_loss
                num_batches += 1
                self.global_step += 1
                
                self.tracker.log(
                    self.global_step,
                    loss=accumulated_loss,
                    lr=self.optimizer.lr
                )
                
                accumulated_loss = 0
                
                # Update progress bar
                pbar.set_postfix({
                    'loss': f"{loss.data:.4f}",
                    'lr': f"{self.optimizer.lr:.2e}"
                })
        
        return total_loss / max(num_batches, 1)
    
    def _validate(self, dataloader: DataLoader) -> float:
        """Validate the model."""
        self.model.eval()
        
        total_loss = 0
        num_batches = 0
        
        for x, y in dataloader:
            logits, _ = self.model(x)
            
            B, T, C = logits.shape
            loss = cross_entropy(logits.reshape(B * T, C), y.reshape(B * T))
            
            total_loss += loss.data
            num_batches += 1
        
        return total_loss / max(num_batches, 1)
    
    def save(self, path: str):
        """Save trainer state."""
        state = {
            'global_step': self.global_step,
            'current_epoch': self.current_epoch,
            'best_loss': self.best_loss,
            'history': self.tracker.metrics,
        }
        with open(os.path.join(path, 'trainer_state.json'), 'w') as f:
            json.dump(state, f, indent=2)
    
    def load(self, path: str):
        """Load trainer state."""
        with open(os.path.join(path, 'trainer_state.json'), 'r') as f:
            state = json.load(f)
        self.global_step = state['global_step']
        self.current_epoch = state['current_epoch']
        self.best_loss = state['best_loss']


class SimpleTrainer:
    """
    Simple trainer for quick experiments.
    
    Minimal setup, maximum productivity.
    
    Example:
        trainer = SimpleTrainer(model)
        trainer.fit(dataloader, epochs=5)
    """
    
    def __init__(self, model: Module, lr: float = 1e-4):
        self.model = model
        self.optimizer = AdamW(model.parameters(), lr=lr)
    
    def fit(self, dataloader: DataLoader, epochs: int = 5) -> Dict:
        """Train the model."""
        history = {'loss': []}
        
        for epoch in range(epochs):
            epoch_loss = 0
            steps = 0
            
            for x, y in tqdm(dataloader, desc=f"Epoch {epoch+1}/{epochs}"):
                self.optimizer.zero_grad()
                
                logits, _ = self.model(x)
                B, T, C = logits.shape
                loss = cross_entropy(logits.reshape(B*T, C), y.reshape(B*T))
                
                loss.backward()
                clip_grad_norm(self.model.parameters(), 1.0)
                self.optimizer.step()
                
                epoch_loss += loss.data
                steps += 1
            
            avg_loss = epoch_loss / steps
            history['loss'].append(avg_loss)
            print(f"Epoch {epoch+1}: loss={avg_loss:.4f}")
        
        return history
