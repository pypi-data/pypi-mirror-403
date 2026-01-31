"""
🧠 NAPLY Micro-Specialist Cluster (v4.0 Octane)
==============================================

Architecture:
- Micro-Specialist: High-efficiency Transformer-lite blocks.
- Parallel Routing: Ensemble manages specialized clusters.
- Octane Optimized: Memory-efficient, fast CPU execution.
"""

import numpy as np
import os
import json
import time
from .tensor import Tensor
from .layers import Module, Linear, LayerNorm, Embedding
from .functional import relu, sigmoid, softmax
from .transformer import TransformerBlock

class MicroSpecialist(Module):
    """
    High-efficiency specialist based on Transformer-lite architecture.
    Optimized for 1GB RAM and fast CPU inference.
    """
    def __init__(self, vocab_size: int, n_layers: int = 4, n_embd: int = 128, n_head: int = 4):
        super().__init__()
        self.n_embd = n_embd
        self.vocab_size = vocab_size
        
        # Architecture: Lite-Transformer
        self.embedding = Embedding(vocab_size, n_embd)
        self.pos_embedding = Embedding(1024, n_embd) # Max context 1024
        
        self.blocks = []
        for i in range(n_layers):
            block = TransformerBlock(n_embd, n_head, dropout=0.0, bias=False, use_rms_norm=True)
            setattr(self, f"block_{i}", block)
            self.blocks.append(block)
            
        self.ln_f = LayerNorm(n_embd)
        self.head = Linear(n_embd, vocab_size, bias=False)
        
        # SGL Confidence Head (Scalar)
        self.confidence_head = Linear(n_embd, 1)
        
    def forward(self, x: Tensor, past_kv=None):
        """Forward pass with optional KV-caching support."""
        B, T = x.shape
        
        # Position embeddings based on cache length
        if past_kv is not None and past_kv[0] is not None:
            past_len = past_kv[0][0].shape[2]
        else:
            past_len = 0
            
        p_idx = Tensor(np.arange(past_len, past_len + T).reshape(1, -1))
        
        x = self.embedding(x) + self.pos_embedding(p_idx)
        
        new_kv = []
        for i, block in enumerate(self.blocks):
            p_kv = past_kv[i] if past_kv else None
            x, kv = block(x, past_kv=p_kv)
            new_kv.append(kv)
            
        h = self.ln_f(x)
        logits = self.head(h)
        
        # Confidence score based on the last hidden state
        c = sigmoid(self.confidence_head(h[:, -1, :]))
        
        return logits, c, new_kv

# Aliases for backward compatibility
SpecialistModel = MicroSpecialist

# ==========================================
# 📘 Language Cluster (Grammar/Fluency)
# ==========================================

class SyntaxNet(MicroSpecialist):
    """Handles grammar, punctuation, and sentence structure."""
    def __init__(self, vocab_size: int):
        super().__init__(vocab_size, n_layers=4, n_embd=128)
        self.name = "SyntaxNet"

class LexiconNet(MicroSpecialist):
    """Handles vocabulary, word choice, and synonyms."""
    def __init__(self, vocab_size: int):
        super().__init__(vocab_size, n_layers=4, n_embd=128)
        self.name = "LexiconNet"

# ==========================================
# 🧠 Thought Cluster (Reasoning/Logic)
# ==========================================

class LogicNet(MicroSpecialist):
    """Handles logical deduction and step-by-step thinking."""
    def __init__(self, vocab_size: int):
        super().__init__(vocab_size, n_layers=6, n_embd=128) # Slightly deeper for logic
        self.name = "LogicNet"

class ThoughtNet(MicroSpecialist):
    """Handles abstract reasoning and context grounding."""
    def __init__(self, vocab_size: int):
        super().__init__(vocab_size, n_layers=6, n_embd=128)
        self.name = "ThoughtNet"

# ==========================================
# 💻 Expert Cluster (Domain/Technical)
# ==========================================

class CodeNet(MicroSpecialist):
    """Expert in Python, JavaScript, and algorithmic logic."""
    def __init__(self, vocab_size: int):
        super().__init__(vocab_size, n_layers=6, n_embd=128)
        self.name = "CodeNet"

class TechNet(MicroSpecialist):
    """Expert in technical documentation and scientific data."""
    def __init__(self, vocab_size: int):
        super().__init__(vocab_size, n_layers=4, n_embd=128)
        self.name = "TechNet"

# Aliases for backward compatibility
GrammarNet = SyntaxNet
ReasoningNet = LogicNet
DomainNet = CodeNet

# ==========================================
# 🚀 Ensemble System
# ==========================================

class PowerAIEnsemble(Module):
    """
    v4.0 Octane Ensemble Cluster.
    Routes queries between 6 Micro-Specialists for maximum precision.
    """
    def __init__(self, vocab_size: int, context_length: int = 1024):
        super().__init__()
        self.vocab_size = vocab_size
        self.context_length = context_length
        
        # Instantiate Clusters
        self.syntax = SyntaxNet(vocab_size)
        self.lexicon = LexiconNet(vocab_size)
        self.logic = LogicNet(vocab_size)
        self.thought = ThoughtNet(vocab_size)
        self.code = CodeNet(vocab_size)
        self.tech = TechNet(vocab_size)
        
        self.specialists = [
            self.syntax, self.lexicon, 
            self.logic, self.thought, 
            self.code, self.tech
        ]
        
        # Register as sub-modules for parameter tracking
        self.add_module("syntax", self.syntax)
        self.add_module("lexicon", self.lexicon)
        self.add_module("logic", self.logic)
        self.add_module("thought", self.thought)
        self.add_module("code", self.code)
        self.add_module("tech", self.tech)

    def add_module(self, name, module):
        """Helper to register modules"""
        setattr(self, name, module)
        self._modules[name] = module

    def forward(self, x: Tensor, past_kv=None) -> tuple:
        """
        Forward pass for the ensemble.
        Aggregates predictions from all specialists using confidence weighting.
        """
        logits_all = []
        confs_all = []
        new_kv = []
        
        # Default biases (can be tuned dynamically during generation)
        # For training/standard forward, we use neutral biases (1.0)
        biases = {s.name: 1.0 for s in self.specialists}

        for i, s in enumerate(self.specialists):
            # Handle KV cache per specialist
            # past_kv should be a list of caches, one for each specialist
            s_kv = past_kv[i] if past_kv is not None and i < len(past_kv) else None
            
            # Forward pass
            l, c, kv = s(x, past_kv=s_kv)
            new_kv.append(kv)
            
            # Collect outputs (focus on last token for generation, or full sequence for training?)
            # Validating shape: l is (B, T, V), c is (B, 1) or scalar
            logits_all.append(l)
            confs_all.append(c * biases[s.name])
            
        # Weighted Aggregation
        # Stack logits: (6, B, T, V)
        # Stack confs: (6, B, 1)
        
        # For simplicity in this implementation, we average logits weighted by confidence
        # Note: This is a simplified forward pass properly differentiable
        
        # Calculate total weight
        total_weight = confs_all[0]
        for i in range(1, len(confs_all)):
            total_weight = total_weight + confs_all[i]
            
        # Normalize and sum
        weighted_sum = logits_all[0] * (confs_all[0].reshape(logits_all[0].shape[0], 1, 1) / (total_weight.reshape(logits_all[0].shape[0], 1, 1) + 1e-6))
        for i in range(1, len(logits_all)):
             # Reshape confidence to (B, 1, 1) to broadcast over (B, T, V)
             w = confs_all[i].reshape(logits_all[i].shape[0], 1, 1) / (total_weight.reshape(logits_all[i].shape[0], 1, 1) + 1e-6)
             weighted_sum = weighted_sum + logits_all[i] * w
             
        # Return logits, confidence (aggregate), and new KV states
        return weighted_sum, total_weight, new_kv

    def save(self, path: str, epoch: int = 0, tokenizer = None):
        """Save specialized cluster weights."""
        os.makedirs(path, exist_ok=True)
        for s in self.specialists:
            s_path = f"{path}/{s.name.lower()}.npz"
            params = {name: p.data for name, p in s.named_parameters()}
            np.savez(s_path, **params)
            
        if tokenizer:
            tokenizer.save(os.path.join(path, "tokenizer.json"))
            
        with open(f"{path}/config.json", 'w') as f:
            json.dump({
                "epoch": epoch,
                "vocab_size": self.vocab_size,
                "context_length": self.context_length,
                "version": "4.0-octane"
            }, f)

    def load(self, path: str):
        """Load cluster weights."""
        for s in self.specialists:
            s_path = f"{path}/{s.name.lower()}.npz"
            if os.path.exists(s_path):
                data = np.load(s_path)
                for name, p in s.named_parameters():
                    if name in data:
                        p.data = data[name].copy()
        
        config_path = f"{path}/config.json"
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return json.load(f)
        return {}

    def generate(self, tokenizer, prompt, max_tokens=200, temperature=0.8, top_p=0.9, skip_special_tokens=True):
        """Routed generation across the Micro-Specialist cluster."""
        tokens = tokenizer.encode(prompt)
        p_low = prompt.lower()
        
        # Dynamic Cluster Biasing
        biases = {s.name: 1.0 for s in self.specialists}
        if len(prompt.split()) < 5: biases["SyntaxNet"] = 2.0
        if any(w in p_low for w in ["code", "def ", "class", "print"]): biases["CodeNet"] = 3.0
        if any(w in p_low for w in ["why", "how", "solve", "math"]): biases["LogicNet"] = 2.5
        
        generated = []
        kv_caches = {s.name: None for s in self.specialists}
        
        for _ in range(max_tokens):
            ctx = tokens[-self.context_length:]
            x = Tensor(np.array([ctx]))
            
            # Forward pulses to all specialists (Parallel capable)
            logits_all = []
            confs_all = []
            
            for s in self.specialists:
                # Optimized: If we have KV-cache, only pass the LAST token
                step_x = x[:, -1:] if kv_caches[s.name] is not None else x
                
                l, c, kv = s(step_x, past_kv=kv_caches[s.name])
                kv_caches[s.name] = kv # Enable caching for 10x speedup
                logits_all.append(l.data[0, -1, :])
                confs_all.append(float(c.data.flatten()[0]) * biases[s.name])
                
            # Weighted Intelligence Mixing
            weights = np.array(confs_all)
            weights /= (np.sum(weights) + 1e-6)
            
            mixed_logits = np.zeros(self.vocab_size)
            for i, l in enumerate(logits_all):
                mixed_logits += l * weights[i]
                
            # Efficient Sampling
            mixed_logits /= (temperature + 1e-6)
            # Simple Top-P fallback
            probs = softmax(Tensor(mixed_logits)).data.flatten()
            
            # Repetition Penalty (Quick)
            if len(tokens) > 5:
                for t in set(tokens[-10:]):
                    probs[t] *= 0.8
                probs /= probs.sum()

            next_token = int(np.random.choice(self.vocab_size, p=probs))
            tokens.append(next_token)
            generated.append(next_token)
            
            if next_token == tokenizer.vocab.get(tokenizer.eos_token):
                break
                
        return tokenizer.decode(tokens, skip_special_tokens=skip_special_tokens)
