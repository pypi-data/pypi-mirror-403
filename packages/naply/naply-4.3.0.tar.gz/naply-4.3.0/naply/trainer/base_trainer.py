"""
Base Trainer - Unified Training Engine
=======================================

Complete training infrastructure that works for text, voice, and image models.
"""

import os
import time
import numpy as np
from typing import Optional, Dict, List, Callable, Any
from tqdm import tqdm

from .gpu_manager import DeviceManager, GPUManager
from .checkpoint import CheckpointManager
from .logger import TrainingLogger, MetricsLogger
from ..tensor import Tensor
from ..layers import Module
from ..optim import Optimizer, AdamW, CosineScheduler, clip_grad_norm
from ..data import DataLoader
from ..functional import cross_entropy


class BaseTrainer:
    """
    Base trainer class with all production features.
    
    Features:
    - Auto device detection (GPU/CPU)
    - Mixed precision training
    - Gradient accumulation
    - Checkpointing and resume
    - Crash recovery
    - Progress tracking
    - Early stopping
    """
    
    def __init__(
        self,
        model: Module,
        optimizer: Optional[Optimizer] = None,
        device_manager: Optional[DeviceManager] = None,
        checkpoint_dir: Optional[str] = None,
        log_dir: Optional[str] = None,
        learning_rate: float = 1e-4,
        weight_decay: float = 0.01,
        max_grad_norm: float = 1.0,
        gradient_accumulation_steps: int = 1,
        use_amp: bool = False,
        verbose: bool = True,
    ):
        self.model = model
        self.device_manager = device_manager or DeviceManager()
        self.gpu_manager = GPUManager(self.device_manager)
        
        # Optimizer
        self.optimizer = optimizer or AdamW(
            model.parameters(),
            lr=learning_rate,
            weight_decay=weight_decay
        )
        
        # Training config
        self.max_grad_norm = max_grad_norm
        self.gradient_accumulation_steps = gradient_accumulation_steps
        self.verbose = verbose
        
        # Enable AMP if GPU available
        if use_amp:
            self.gpu_manager.enable_amp(True)
        
        # CPU optimizations
        if self.device_manager.is_cpu():
            self.gpu_manager.optimize_for_cpu()
        
        # Checkpointing
        self.checkpoint_manager = None
        if checkpoint_dir:
            self.checkpoint_manager = CheckpointManager(checkpoint_dir)
        
        # Logging
        self.logger = TrainingLogger(log_dir, verbose=verbose)
        self.metrics = MetricsLogger()
        
        # Training state
        self.global_step = 0
        self.current_epoch = 0
        self.best_loss = float('inf')
    
    def train(
        self,
        train_dataloader: DataLoader,
        epochs: int = 5,
        val_dataloader: Optional[DataLoader] = None,
        warmup_steps: int = 100,
        save_every: int = 1,
        eval_every: int = 100,
        resume: bool = True,
        **kwargs
    ) -> Dict[str, List[float]]:
        """
        Train the model.
        
        Args:
            train_dataloader: Training data loader
            epochs: Number of epochs
            val_dataloader: Optional validation data loader
            warmup_steps: Warmup steps for learning rate
            save_every: Save checkpoint every N epochs
            eval_every: Evaluate every N steps
            resume: Whether to resume from checkpoint if available
        """
        # Resume from checkpoint
        if resume and self.checkpoint_manager:
            try:
                metadata = self.checkpoint_manager.resume_training(
                    self.model,
                    self.optimizer
                )
                self.current_epoch = metadata.get('epoch', 0)
                self.global_step = metadata.get('step', 0)
                if self.verbose:
                    print(f"📂 Resumed from epoch {self.current_epoch}, step {self.global_step}")
            except FileNotFoundError:
                if self.verbose:
                    print("Starting fresh training")
        
        # Setup scheduler
        total_steps = len(train_dataloader) * epochs
        scheduler = CosineScheduler(
            self.optimizer,
            total_steps,
            warmup_steps=warmup_steps
        )
        
        # Start logging
        self.logger.start()
        
        if self.verbose:
            print(f"\n{'='*60}")
            print(f"Training Configuration")
            print(f"{'='*60}")
            print(f"Device:        {self.device_manager.get_device()}")
            print(f"Epochs:        {epochs}")
            print(f"Steps/Epoch:   {len(train_dataloader)}")
            print(f"Total Steps:   {total_steps:,}")
            print(f"Batch Size:    {train_dataloader.batch_size}")
            print(f"Grad Accum:   {self.gradient_accumulation_steps}")
            print(f"Mixed Prec:    {self.gpu_manager.mixed_precision}")
            print(f"{'='*60}\n")
        
        history = {'train_loss': [], 'val_loss': [], 'lr': []}
        
        for epoch in range(self.current_epoch, epochs):
            self.current_epoch = epoch
            
            # Train epoch
            train_loss = self._train_epoch(
                train_dataloader,
                scheduler,
                epoch,
                eval_every=eval_every,
                val_dataloader=val_dataloader
            )
            history['train_loss'].append(train_loss)
            history['lr'].append(self.optimizer.lr)
            
            # Validation
            if val_dataloader:
                val_loss = self._validate(val_dataloader)
                history['val_loss'].append(val_loss)
                self.logger.log_epoch(epoch + 1, train_loss, val_loss)
                
                # Update best loss
                if val_loss < self.best_loss:
                    self.best_loss = val_loss
            else:
                self.logger.log_epoch(epoch + 1, train_loss)
            
            # Save checkpoint
            if self.checkpoint_manager and (epoch + 1) % save_every == 0:
                self.checkpoint_manager.save_checkpoint(
                    self.model,
                    self.optimizer,
                    scheduler,
                    epoch=epoch,
                    step=self.global_step,
                    loss=train_loss,
                    metrics=self.metrics.to_dict()
                )
        
        # Final save
        if self.checkpoint_manager:
            self.checkpoint_manager.save_checkpoint(
                self.model,
                self.optimizer,
                scheduler,
                epoch=epochs - 1,
                step=self.global_step,
                loss=history['train_loss'][-1],
                metrics=self.metrics.to_dict()
            )
        
        # Save metrics
        self.logger.save_metrics()
        
        if self.verbose:
            print(self.logger.summary())
        
        return history
    
    def _train_epoch(
        self,
        dataloader: DataLoader,
        scheduler,
        epoch: int,
        eval_every: int = 100,
        val_dataloader: Optional[DataLoader] = None
    ) -> float:
        """Train for one epoch."""
        self.model.train()
        
        total_loss = 0
        num_batches = 0
        accumulated_loss = 0
        
        pbar = tqdm(dataloader, desc=f"Epoch {epoch+1}", disable=not self.verbose)
        
        for batch_idx, (x, y) in enumerate(pbar):
            # Forward pass
            loss = self._forward_pass(x, y)
            
            # Scale for accumulation
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
                
                # Logging
                self.logger.log(
                    step=self.global_step,
                    loss=accumulated_loss,
                    lr=self.optimizer.lr,
                    epoch=epoch
                )
                self.metrics.log(
                    loss=accumulated_loss,
                    lr=self.optimizer.lr
                )
                
                accumulated_loss = 0
                
                # Update progress bar
                pbar.set_postfix({
                    'loss': f"{loss.data:.4f}",
                    'lr': f"{self.optimizer.lr:.2e}"
                })
                
                # Validation
                if val_dataloader and self.global_step % eval_every == 0:
                    val_loss = self._validate(val_dataloader)
                    self.metrics.log(val_loss=val_loss)
        
        return total_loss / max(num_batches, 1)
    
    def _forward_pass(self, x: Tensor, y: Tensor) -> Tensor:
        """Forward pass - override in subclasses for different model types."""
        logits, _ = self.model(x)
        B, T, C = logits.shape
        return cross_entropy(logits.reshape(B * T, C), y.reshape(B * T))
    
    def _validate(self, dataloader: DataLoader) -> float:
        """Validate the model."""
        self.model.eval()
        
        total_loss = 0
        num_batches = 0
        
        for x, y in dataloader:
            loss = self._forward_pass(x, y)
            total_loss += loss.data
            num_batches += 1
        
        return total_loss / max(num_batches, 1)


class UnifiedTrainer(BaseTrainer):
    """
    Unified trainer that works for any model type (text, voice, image).
    
    Automatically handles different data types and model architectures.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model_type = self._detect_model_type()
    
    def _detect_model_type(self) -> str:
        """Detect model type from architecture."""
        model_name = self.model.__class__.__name__.lower()
        
        if 'voice' in model_name or 'audio' in model_name:
            return 'voice'
        elif 'image' in model_name or 'diffusion' in model_name or 'vae' in model_name:
            return 'image'
        else:
            return 'text'
    
    def _forward_pass(self, x: Tensor, y: Tensor) -> Tensor:
        """Forward pass with model type detection."""
        if self.model_type == 'voice':
            return self._voice_forward(x, y)
        elif self.model_type == 'image':
            return self._image_forward(x, y)
        else:
            return super()._forward_pass(x, y)
    
    def _voice_forward(self, x: Tensor, y: Tensor) -> Tensor:
        """Forward pass for voice models."""
        # Voice models typically output spectrograms
        output = self.model(x)
        # Use MSE for spectrogram reconstruction
        from ..functional import mse_loss
        return mse_loss(output, y)
    
    def _image_forward(self, x: Tensor, y: Tensor) -> Tensor:
        """Forward pass for image models."""
        # Image models (diffusion) predict noise
        output = self.model(x)
        # Use MSE for noise prediction
        from ..functional import mse_loss
        return mse_loss(output, y)
