"""
Enhanced Text Generation
========================

Advanced text generation with:
- Extended context windows
- Better token prediction
- Pattern learning
- Advanced sampling strategies
"""

import numpy as np
from typing import Optional, List, Dict, Tuple
from .tensor import Tensor
from .model import Model
from .transformer import GPT


class EnhancedTextModel(Model):
    """
    Enhanced text model with advanced features.
    
    Features:
    - Extended context windows (up to 32K tokens)
    - Advanced pattern learning
    - Better next token prediction
    - Multiple sampling strategies
    """
    
    def __init__(
        self,
        config=None,
        layers: Optional[int] = None,
        heads: Optional[int] = None,
        embedding: Optional[int] = None,
        vocab_size: Optional[int] = None,
        context: Optional[int] = None,
        **kwargs
    ):
        # Support extended context windows
        if context is None:
            context = 8192  # Default to 8K
        elif context > 32768:
            context = 32768  # Cap at 32K
        
        super().__init__(
            config=config,
            layers=layers,
            heads=heads,
            embedding=embedding,
            vocab_size=vocab_size,
            context=context,
            **kwargs
        )
        
        # Enhanced features
        self.use_rope = kwargs.get('use_rope', True)  # Rotary Position Embedding
        self.use_flash_attention = kwargs.get('use_flash_attention', False)
        self.pattern_memory = {}  # Store learned patterns
    
    def generate_advanced(
        self,
        prompt: str,
        max_tokens: int = 200,
        temperature: float = 0.8,
        top_k: int = 40,
        top_p: float = 0.9,
        repetition_penalty: float = 1.1,
        length_penalty: float = 1.0,
        stop_tokens: Optional[List[str]] = None,
        use_pattern_memory: bool = True
    ) -> str:
        """
        Advanced text generation with multiple strategies.
        
        Args:
            prompt: Starting text
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_k: Top-K sampling
            top_p: Top-P (nucleus) sampling
            repetition_penalty: Penalty for repetition
            length_penalty: Length penalty
            stop_tokens: Stop generation tokens
            use_pattern_memory: Use learned patterns
        """
        if self.tokenizer is None:
            raise ValueError("Model not trained. Call train() first.")
        
        self.model.eval()
        
        # Encode prompt
        input_ids = self.tokenizer.encode(prompt)
        generated = list(input_ids)
        
        past_kv = None
        
        for i in range(max_tokens):
            # Check context limit
            if len(generated) >= self.config.block_size:
                # Use sliding window
                window_start = len(generated) - self.config.block_size + 1
                context = generated[window_start:]
                past_kv = None  # Reset cache
            else:
                context = generated[-self.config.block_size:]
            
            x = Tensor(np.array([context], dtype=np.int32))
            
            # Forward pass
            logits, past_kv = self.model(x, past_key_values=past_kv)
            logits = logits.data[0, -1, :]  # Last position
            
            # Apply pattern memory (if enabled)
            if use_pattern_memory and len(generated) > 10:
                logits = self._apply_pattern_memory(logits, generated)
            
            # Temperature
            logits = logits / temperature
            
            # Repetition penalty
            if repetition_penalty != 1.0:
                logits = self._apply_repetition_penalty(logits, generated, repetition_penalty)
            
            # Top-K
            if top_k > 0:
                indices_to_remove = logits < np.partition(logits, -top_k)[-top_k]
                logits[indices_to_remove] = -np.inf
            
            # Top-P (Nucleus)
            if top_p < 1.0:
                sorted_indices = np.argsort(logits)[::-1]
                sorted_logits = logits[sorted_indices]
                probs = np.exp(sorted_logits) / np.sum(np.exp(sorted_logits))
                cumulative_probs = np.cumsum(probs)
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
                        idx = current_text.find(stop)
                        return current_text[:idx]
            
            # Check EOS
            if next_token == self.tokenizer.vocab.get(self.tokenizer.eos_token, -1):
                break
        
        return self.tokenizer.decode(generated)
    
    def _apply_repetition_penalty(
        self,
        logits: np.ndarray,
        generated: List[int],
        penalty: float
    ) -> np.ndarray:
        """Apply repetition penalty to logits."""
        # Get recent tokens
        recent_tokens = generated[-20:] if len(generated) > 20 else generated
        
        # Apply penalty
        for token_id in set(recent_tokens):
            if token_id < len(logits):
                if logits[token_id] > 0:
                    logits[token_id] /= penalty
                else:
                    logits[token_id] *= penalty
        
        return logits
    
    def _apply_pattern_memory(
        self,
        logits: np.ndarray,
        generated: List[int]
    ) -> np.ndarray:
        """Apply learned patterns to boost likely continuations."""
        # Simple pattern matching: look for common n-grams
        if len(generated) < 3:
            return logits
        
        # Get last 3 tokens
        last_3 = tuple(generated[-3:])
        
        # Check if we've seen this pattern before
        if last_3 in self.pattern_memory:
            # Boost tokens that commonly follow this pattern
            pattern_data = self.pattern_memory[last_3]
            for token_id, boost in pattern_data.items():
                if token_id < len(logits):
                    logits[token_id] += boost * 0.1  # Small boost
        
        return logits
    
    def learn_patterns(self, texts: List[str], n: int = 3):
        """
        Learn patterns from texts for better generation.
        
        Args:
            texts: Training texts
            n: N-gram size
        """
        print("🧠 Learning patterns...")
        
        for text in texts:
            tokens = self.tokenizer.encode(text)
            
            # Extract n-grams
            for i in range(len(tokens) - n):
                ngram = tuple(tokens[i:i+n])
                next_token = tokens[i+n] if i+n < len(tokens) else None
                
                if next_token is not None:
                    if ngram not in self.pattern_memory:
                        self.pattern_memory[ngram] = {}
                    
                    if next_token not in self.pattern_memory[ngram]:
                        self.pattern_memory[ngram][next_token] = 0
                    
                    self.pattern_memory[ngram][next_token] += 1
        
        # Normalize
        for ngram in self.pattern_memory:
            total = sum(self.pattern_memory[ngram].values())
            for token in self.pattern_memory[ngram]:
                self.pattern_memory[ngram][token] /= total
        
        print(f"✅ Learned {len(self.pattern_memory)} patterns")
    
    def chat_advanced(
        self,
        prompt: str,
        max_tokens: int = 200,
        **kwargs
    ) -> str:
        """Advanced chat with better responses."""
        return self.generate_advanced(
            prompt=prompt,
            max_tokens=max_tokens,
            **kwargs
        )
