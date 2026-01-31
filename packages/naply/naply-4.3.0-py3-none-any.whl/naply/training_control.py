"""
NAPLY Training Control
======================

Advanced training control: pause, resume, checkpointing, and progress tracking.
"""

import os
import json
import time
import signal
import pickle
import threading
from typing import Dict, Optional, Callable, Any
from enum import Enum


class TrainingState(Enum):
    """Training state enumeration."""
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    COMPLETED = "completed"


class TrainingController:
    """
    Advanced training controller with pause/resume/stop functionality.
    
    Features:
    - Pause training anytime (Ctrl+C or programmatic)
    - Resume from exact point
    - Auto-save checkpoints
    - Progress tracking
    - State management
    
    Example:
        controller = TrainingController(checkpoint_dir="checkpoints/")
        
        for epoch in range(epochs):
            for step in range(steps):
                # Check if paused
                if controller.is_paused():
                    controller.wait_for_resume()
                
                # Check if stopped
                if controller.is_stopped():
                    break
                
                # Train step
                loss = train_step()
                controller.update(epoch, step, loss)
    """
    
    def __init__(
        self,
        checkpoint_dir: str = "checkpoints/",
        auto_save_interval: int = 100,  # Save every N steps
        max_checkpoints: int = 5
    ):
        self.checkpoint_dir = checkpoint_dir
        self.auto_save_interval = auto_save_interval
        self.max_checkpoints = max_checkpoints
        
        os.makedirs(checkpoint_dir, exist_ok=True)
        
        # State
        self.state = TrainingState.RUNNING
        self.current_epoch = 0
        self.current_step = 0
        self.current_loss = 0.0
        
        # Progress tracking
        self.epoch_losses = []
        self.step_losses = []
        self.start_time = None
        
        # Pause/resume lock
        self.pause_lock = threading.Lock()
        self.pause_event = threading.Event()
        self.pause_event.set()  # Start as running
        
        # Setup signal handlers
        self._setup_signal_handlers()
        
        # Checkpoint metadata
        self.metadata = {
            'total_epochs': 0,
            'total_steps': 0,
            'best_loss': float('inf'),
            'training_history': []
        }
    
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful interruption."""
        def signal_handler(sig, frame):
            if self.state == TrainingState.RUNNING:
                print("\n\n⏸️  Training paused! Press Ctrl+C again to stop, or resume programmatically.")
                self.pause()
            elif self.state == TrainingState.PAUSED:
                print("\n\n⏹️  Training stopped! Saving checkpoint...")
                self.stop()
        
        signal.signal(signal.SIGINT, signal_handler)
    
    def pause(self):
        """Pause training."""
        with self.pause_lock:
            if self.state == TrainingState.RUNNING:
                self.state = TrainingState.PAUSED
                self.pause_event.clear()
                self.save_checkpoint()
                print(f"✅ Training paused at Epoch {self.current_epoch}, Step {self.current_step}")
    
    def resume(self):
        """Resume training."""
        with self.pause_lock:
            if self.state == TrainingState.PAUSED:
                self.state = TrainingState.RUNNING
                self.pause_event.set()
                print(f"▶️  Training resumed from Epoch {self.current_epoch}, Step {self.current_step}")
    
    def stop(self):
        """Stop training."""
        with self.pause_lock:
            self.state = TrainingState.STOPPED
            self.pause_event.set()  # Unblock any waiting threads
            self.save_checkpoint()
            print(f"⏹️  Training stopped at Epoch {self.current_epoch}, Step {self.current_step}")
    
    def is_paused(self) -> bool:
        """Check if training is paused."""
        return self.state == TrainingState.PAUSED
    
    def is_stopped(self) -> bool:
        """Check if training is stopped."""
        return self.state == TrainingState.STOPPED
    
    def is_running(self) -> bool:
        """Check if training is running."""
        return self.state == TrainingState.RUNNING
    
    def wait_for_resume(self):
        """Wait until training is resumed."""
        self.pause_event.wait()
    
    def update(self, epoch: int, step: int, loss: float, **kwargs):
        """Update training progress."""
        self.current_epoch = epoch
        self.current_step = step
        self.current_loss = loss
        
        if self.start_time is None:
            self.start_time = time.time()
        
        # Track losses
        self.step_losses.append(loss)
        # Detect new epoch
        is_new_epoch = False
        if not self.epoch_losses:
            is_new_epoch = True
        elif step == 0:
            is_new_epoch = True
        elif step == 1 and len(self.epoch_losses[-1]) > 0:
            is_new_epoch = True
            
        if is_new_epoch:
            if self.epoch_losses:
                # Record previous epoch summary
                self.metadata['training_history'].append({
                    'epoch': self.current_epoch - 1,
                    'avg_loss': sum(self.step_losses[-100:]) / min(100, len(self.step_losses)) if self.step_losses else 0.0,
                    'steps': len(self.step_losses)
                })
            self.epoch_losses.append([])
        
        self.epoch_losses[-1].append(loss)
        
        # Update best loss
        if loss < self.metadata['best_loss']:
            self.metadata['best_loss'] = loss
        
        # Auto-save checkpoint
        if step > 0 and step % self.auto_save_interval == 0:
            self.save_checkpoint(auto=True)
    
    def save_checkpoint(self, auto: bool = False):
        """Save training checkpoint."""
        checkpoint = {
            'epoch': self.current_epoch,
            'step': self.current_step,
            'loss': self.current_loss,
            'state': self.state.value,
            'metadata': self.metadata,
            'timestamp': time.time()
        }
        
        # Save checkpoint file
        if auto:
            filename = f"checkpoint_auto_epoch{self.current_epoch}_step{self.current_step}.json"
        else:
            filename = f"checkpoint_epoch{self.current_epoch}_step{self.current_step}.json"
        
        filepath = os.path.join(self.checkpoint_dir, filename)
        
        with open(filepath, 'w') as f:
            json.dump(checkpoint, f, indent=2)
        
        # Update latest checkpoint
        latest_path = os.path.join(self.checkpoint_dir, "latest_checkpoint.json")
        with open(latest_path, 'w') as f:
            json.dump(checkpoint, f, indent=2)
        
        # Cleanup old checkpoints
        self._cleanup_checkpoints()
        
        if not auto:
            print(f"💾 Checkpoint saved: {filename}")
    
    def load_checkpoint(self) -> Optional[Dict]:
        """Load latest checkpoint."""
        latest_path = os.path.join(self.checkpoint_dir, "latest_checkpoint.json")
        
        if not os.path.exists(latest_path):
            return None
        
        with open(latest_path, 'r') as f:
            checkpoint = json.load(f)
        
        # Restore state
        self.current_epoch = checkpoint['epoch']
        self.current_step = checkpoint['step']
        self.current_loss = checkpoint['loss']
        self.state = TrainingState(checkpoint['state'])
        self.metadata = checkpoint.get('metadata', {})
        
        print(f"📂 Loaded checkpoint: Epoch {self.current_epoch}, Step {self.current_step}")
        
        return checkpoint
    
    def _cleanup_checkpoints(self):
        """Remove old checkpoints."""
        checkpoints = []
        for filename in os.listdir(self.checkpoint_dir):
            if filename.startswith("checkpoint_") and filename.endswith(".json"):
                filepath = os.path.join(self.checkpoint_dir, filename)
                mtime = os.path.getmtime(filepath)
                checkpoints.append((mtime, filename, filepath))
        
        # Sort by modification time (newest first)
        checkpoints.sort(reverse=True)
        
        # Keep only the most recent N checkpoints
        for mtime, filename, filepath in checkpoints[self.max_checkpoints:]:
            if "auto" in filename:  # Only delete auto checkpoints
                os.remove(filepath)
    
    def get_progress(self) -> Dict[str, Any]:
        """Get training progress information."""
        elapsed = time.time() - self.start_time if self.start_time else 0
        
        return {
            'epoch': self.current_epoch,
            'step': self.current_step,
            'loss': self.current_loss,
            'state': self.state.value,
            'elapsed_time': elapsed,
            'avg_loss': sum(self.step_losses[-100:]) / min(100, len(self.step_losses)) if self.step_losses else 0.0,
            'best_loss': self.metadata['best_loss'],
            'total_steps': len(self.step_losses)
        }
    
    def print_progress(self):
        """Print current training progress."""
        progress = self.get_progress()
        print(f"\n📊 Training Progress:")
        print(f"   Epoch: {progress['epoch']}")
        print(f"   Step: {progress['step']}")
        print(f"   Loss: {progress['loss']:.4f}")
        print(f"   Avg Loss (last 100): {progress['avg_loss']:.4f}")
        print(f"   Best Loss: {progress['best_loss']:.4f}")
        print(f"   State: {progress['state']}")
        print(f"   Elapsed: {progress['elapsed_time']:.1f}s")
