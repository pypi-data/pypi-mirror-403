"""
Training Logger
===============

Progress tracking, metrics logging, and visualization.
"""

import os
import json
import time
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime


class TrainingLogger:
    """
    Comprehensive training logger.
    
    Features:
    - Real-time metrics tracking
    - JSON logging
    - Progress summaries
    - Training history
    """
    
    def __init__(self, log_dir: Optional[str] = None, verbose: bool = True):
        self.log_dir = Path(log_dir) if log_dir else None
        self.verbose = verbose
        
        if self.log_dir:
            self.log_dir.mkdir(parents=True, exist_ok=True)
            self.log_file = self.log_dir / "training.log"
            self.metrics_file = self.log_dir / "metrics.json"
        else:
            self.log_file = None
            self.metrics_file = None
        
        self.metrics: Dict[str, List[float]] = {}
        self.start_time = None
        self.step_count = 0
    
    def start(self):
        """Start logging session."""
        self.start_time = time.time()
        self.step_count = 0
        self.metrics = {
            'loss': [],
            'lr': [],
            'epoch': [],
            'step': [],
            'time': []
        }
        
        if self.verbose:
            print(f"\n🚀 Training Started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    def log(
        self,
        step: int,
        loss: float,
        lr: float = 0.0,
        epoch: int = 0,
        **kwargs
    ):
        """Log training step."""
        self.step_count = step
        elapsed = time.time() - self.start_time if self.start_time else 0
        
        # Update metrics
        self.metrics['loss'].append(loss)
        self.metrics['lr'].append(lr)
        self.metrics['epoch'].append(epoch)
        self.metrics['step'].append(step)
        self.metrics['time'].append(elapsed)
        
        # Add custom metrics
        for key, value in kwargs.items():
            if key not in self.metrics:
                self.metrics[key] = []
            self.metrics[key].append(value)
        
        # Write to file
        if self.log_file:
            self._write_log(step, loss, lr, epoch, **kwargs)
        
        # Save metrics periodically
        if self.metrics_file and step % 100 == 0:
            self.save_metrics()
    
    def _write_log(self, step: int, loss: float, lr: float, epoch: int, **kwargs):
        """Write log entry to file."""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'step': step,
            'epoch': epoch,
            'loss': loss,
            'lr': lr,
            **kwargs
        }
        
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(entry) + '\n')
    
    def log_epoch(
        self,
        epoch: int,
        train_loss: float,
        val_loss: Optional[float] = None,
        **kwargs
    ):
        """Log epoch summary."""
        elapsed = time.time() - self.start_time if self.start_time else 0
        
        if self.verbose:
            msg = f"Epoch {epoch} | Train Loss: {train_loss:.4f}"
            if val_loss is not None:
                msg += f" | Val Loss: {val_loss:.4f}"
            msg += f" | Time: {elapsed:.1f}s"
            print(msg)
        
        if self.log_file:
            entry = {
                'timestamp': datetime.now().isoformat(),
                'epoch': epoch,
                'train_loss': train_loss,
                'val_loss': val_loss,
                'elapsed_time': elapsed,
                **kwargs
            }
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(entry) + '\n')
    
    def save_metrics(self):
        """Save metrics to JSON file."""
        if self.metrics_file:
            with open(self.metrics_file, 'w') as f:
                json.dump(self.metrics, f, indent=2)
    
    def summary(self) -> str:
        """Get training summary."""
        if not self.metrics.get('loss'):
            return "No training data recorded"
        
        total_steps = len(self.metrics['loss'])
        final_loss = self.metrics['loss'][-1]
        best_loss = min(self.metrics['loss'])
        total_time = self.metrics['time'][-1] if self.metrics['time'] else 0
        
        return (
            f"\n{'='*50}\n"
            f"Training Summary\n"
            f"{'='*50}\n"
            f"Total Steps:    {total_steps:,}\n"
            f"Final Loss:     {final_loss:.4f}\n"
            f"Best Loss:      {best_loss:.4f}\n"
            f"Total Time:     {total_time:.1f}s ({total_time/60:.1f} min)\n"
            f"Avg Time/Step:  {total_time/total_steps:.3f}s\n"
            f"{'='*50}\n"
        )
    
    def get_metrics(self) -> Dict[str, List[float]]:
        """Get all logged metrics."""
        return self.metrics.copy()


class MetricsLogger:
    """
    Lightweight metrics logger for specific metrics.
    """
    
    def __init__(self):
        self.metrics: Dict[str, List[Any]] = {}
    
    def log(self, **kwargs):
        """Log metrics."""
        for key, value in kwargs.items():
            if key not in self.metrics:
                self.metrics[key] = []
            self.metrics[key].append(value)
    
    def get(self, key: str) -> List[Any]:
        """Get metric values."""
        return self.metrics.get(key, [])
    
    def latest(self, key: str) -> Any:
        """Get latest value for a metric."""
        values = self.get(key)
        return values[-1] if values else None
    
    def clear(self):
        """Clear all metrics."""
        self.metrics = {}
    
    def to_dict(self) -> Dict[str, List[Any]]:
        """Export metrics as dictionary."""
        return self.metrics.copy()
