"""
Advanced Checkpointing System
==============================

Resume training, crash recovery, and model state management.
"""

import os
import json
import time
import pickle
import shutil
from typing import Optional, Dict, Any, List
from pathlib import Path


class AdvancedCheckpoint:
    """
    Advanced checkpointing with crash recovery.
    
    Features:
    - Automatic checkpointing
    - Crash recovery
    - Best model tracking
    - Metadata storage
    """
    
    def __init__(
        self,
        save_dir: str,
        max_checkpoints: int = 5,
        save_best: bool = True,
        monitor: str = "loss"
    ):
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(parents=True, exist_ok=True)
        self.max_checkpoints = max_checkpoints
        self.save_best = save_best
        self.monitor = monitor
        self.best_score = float('inf') if monitor == "loss" else float('-inf')
        self.checkpoints: List[Dict] = []
        self._load_index()
    
    def _load_index(self):
        """Load checkpoint index."""
        index_path = self.save_dir / "checkpoints.json"
        if index_path.exists():
            try:
                with open(index_path, 'r') as f:
                    data = json.load(f)
                    self.checkpoints = data.get('checkpoints', [])
                    best = data.get('best', {})
                    if best:
                        self.best_score = best.get('score', self.best_score)
            except:
                self.checkpoints = []
    
    def _save_index(self):
        """Save checkpoint index."""
        index_path = self.save_dir / "checkpoints.json"
        data = {
            'checkpoints': self.checkpoints,
            'best': {
                'score': self.best_score,
                'path': str(self.save_dir / "best.pkl") if self.save_best else None
            }
        }
        with open(index_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def save(
        self,
        model,
        optimizer=None,
        scheduler=None,
        epoch: int = 0,
        step: int = 0,
        loss: float = 0.0,
        metrics: Optional[Dict] = None,
        is_best: bool = False,
        **kwargs
    ) -> str:
        """
        Save a checkpoint.
        
        Returns:
            Path to saved checkpoint
        """
        timestamp = int(time.time())
        filename = f"checkpoint_epoch{epoch}_step{step}_{timestamp}.pkl"
        filepath = self.save_dir / filename
        
        checkpoint = {
            'model_state': model.state_dict() if hasattr(model, 'state_dict') else model,
            'epoch': epoch,
            'step': step,
            'loss': loss,
            'metrics': metrics or {},
            'timestamp': timestamp,
            **kwargs
        }
        
        if optimizer:
            checkpoint['optimizer_state'] = self._get_optimizer_state(optimizer)
        
        if scheduler:
            checkpoint['scheduler_state'] = self._get_scheduler_state(scheduler)
        
        # Save checkpoint
        with open(filepath, 'wb') as f:
            pickle.dump(checkpoint, f)
        
        # Update index
        self.checkpoints.append({
            'filename': filename,
            'epoch': epoch,
            'step': step,
            'loss': loss,
            'timestamp': timestamp,
            'metrics': metrics or {}
        })
        
        # Save best model
        if self.save_best and is_best:
            best_path = self.save_dir / "best.pkl"
            shutil.copy(filepath, best_path)
            self.best_score = loss
        
        # Save latest
        latest_path = self.save_dir / "latest.pkl"
        shutil.copy(filepath, latest_path)
        
        # Cleanup old checkpoints
        self._cleanup()
        self._save_index()
        
        return str(filepath)
    
    def _get_optimizer_state(self, optimizer) -> Dict:
        """Extract optimizer state."""
        if hasattr(optimizer, 'state_dict'):
            return optimizer.state_dict()
        return {
            'lr': getattr(optimizer, 'lr', 0),
            't': getattr(optimizer, 't', 0),
        }
    
    def _get_scheduler_state(self, scheduler) -> Dict:
        """Extract scheduler state."""
        if hasattr(scheduler, 'state_dict'):
            return scheduler.state_dict()
        return {
            'last_lr': getattr(scheduler, 'last_lr', 0),
        }
    
    def load(
        self,
        path: str,
        model,
        optimizer=None,
        scheduler=None
    ) -> Dict[str, Any]:
        """
        Load a checkpoint.
        
        Returns:
            Metadata dictionary
        """
        filepath = Path(path)
        if not filepath.exists():
            raise FileNotFoundError(f"Checkpoint not found: {path}")
        
        with open(filepath, 'rb') as f:
            checkpoint = pickle.load(f)
        
        # Load model
        if hasattr(model, 'load_state_dict'):
            model.load_state_dict(checkpoint['model_state'])
        else:
            # Assume it's a dict we can update
            if isinstance(model, dict):
                model.update(checkpoint['model_state'])
        
        # Load optimizer
        if optimizer and 'optimizer_state' in checkpoint:
            self._load_optimizer_state(optimizer, checkpoint['optimizer_state'])
        
        # Load scheduler
        if scheduler and 'scheduler_state' in checkpoint:
            self._load_scheduler_state(scheduler, checkpoint['scheduler_state'])
        
        return {
            'epoch': checkpoint.get('epoch', 0),
            'step': checkpoint.get('step', 0),
            'loss': checkpoint.get('loss', 0.0),
            'metrics': checkpoint.get('metrics', {}),
        }
    
    def _load_optimizer_state(self, optimizer, state: Dict):
        """Restore optimizer state."""
        if hasattr(optimizer, 'load_state_dict'):
            optimizer.load_state_dict(state)
        else:
            if 'lr' in state:
                optimizer.lr = state['lr']
            if 't' in state:
                optimizer.t = state['t']
    
    def _load_scheduler_state(self, scheduler, state: Dict):
        """Restore scheduler state."""
        if hasattr(scheduler, 'load_state_dict'):
            scheduler.load_state_dict(state)
    
    def load_latest(self, model, optimizer=None, scheduler=None) -> Dict[str, Any]:
        """Load the latest checkpoint."""
        latest_path = self.save_dir / "latest.pkl"
        if not latest_path.exists():
            raise FileNotFoundError("No latest checkpoint found")
        return self.load(str(latest_path), model, optimizer, scheduler)
    
    def load_best(self, model, optimizer=None, scheduler=None) -> Dict[str, Any]:
        """Load the best checkpoint."""
        best_path = self.save_dir / "best.pkl"
        if not best_path.exists():
            raise FileNotFoundError("No best checkpoint found")
        return self.load(str(best_path), model, optimizer, scheduler)
    
    def _cleanup(self):
        """Remove old checkpoints."""
        if len(self.checkpoints) <= self.max_checkpoints:
            return
        
        # Sort by timestamp
        self.checkpoints.sort(key=lambda x: x['timestamp'])
        
        # Remove oldest
        to_remove = self.checkpoints[:-self.max_checkpoints]
        for ckpt in to_remove:
            filepath = self.save_dir / ckpt['filename']
            if filepath.exists():
                filepath.unlink()
        
        # Update list
        self.checkpoints = self.checkpoints[-self.max_checkpoints:]


class CheckpointManager:
    """
    High-level checkpoint manager with automatic recovery.
    """
    
    def __init__(self, save_dir: str, **kwargs):
        self.checkpoint = AdvancedCheckpoint(save_dir, **kwargs)
        self.save_dir = Path(save_dir)
    
    def save_checkpoint(
        self,
        model,
        optimizer=None,
        scheduler=None,
        epoch: int = 0,
        step: int = 0,
        loss: float = 0.0,
        metrics: Optional[Dict] = None,
        **kwargs
    ):
        """Save checkpoint with automatic best model tracking."""
        is_best = loss < self.checkpoint.best_score if self.checkpoint.monitor == "loss" else loss > self.checkpoint.best_score
        
        return self.checkpoint.save(
            model=model,
            optimizer=optimizer,
            scheduler=scheduler,
            epoch=epoch,
            step=step,
            loss=loss,
            metrics=metrics,
            is_best=is_best,
            **kwargs
        )
    
    def resume_training(
        self,
        model,
        optimizer=None,
        scheduler=None,
        use_best: bool = False
    ) -> Dict[str, Any]:
        """
        Resume training from checkpoint.
        
        Args:
            use_best: If True, load best model instead of latest
        """
        try:
            if use_best:
                return self.checkpoint.load_best(model, optimizer, scheduler)
            else:
                return self.checkpoint.load_latest(model, optimizer, scheduler)
        except FileNotFoundError:
            print("No checkpoint found, starting from scratch")
            return {'epoch': 0, 'step': 0, 'loss': 0.0}
