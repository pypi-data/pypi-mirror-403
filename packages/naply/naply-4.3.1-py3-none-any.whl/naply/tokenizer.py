"""
NAPLY Tokenizers
================

Tokenization for converting text to/from token IDs.
Supports BPE, WordPiece, and character-level tokenization.
"""

import os
import json
import re
from typing import List, Dict, Optional, Tuple, Union
from collections import Counter


class Tokenizer:
    """
    Base tokenizer class.
    
    Provides common tokenization interface.
    """
    
    def __init__(self, vocab: Optional[Dict[str, int]] = None):
        self.vocab = vocab or {}
        self.id_to_token = {v: k for k, v in self.vocab.items()}
        
        # Special tokens
        self.pad_token = "<|pad|>"
        self.unk_token = "<|unk|>"
        self.bos_token = "<|bos|>"
        self.eos_token = "<|eos|>"
        
        # Chat Special Tokens (Added for Naply v4.1 Intelligence)
        self.system_token = "<|system|>"
        self.user_token = "<|user|>"
        self.assistant_token = "<|assistant|>"
        self.end_token = "<|end|>"
        
    @property
    def vocab_size(self) -> int:
        return len(self.vocab)
    
    def encode(self, text: str) -> List[int]:
        """Convert text to token IDs."""
        raise NotImplementedError
    
    def decode(self, ids: List[int]) -> str:
        """Convert token IDs back to text."""
        raise NotImplementedError
    
    def save(self, path: str):
        """Save tokenizer to file."""
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else '.', exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump({
                'vocab': self.vocab,
                'merges': self.merges if hasattr(self, 'merges') else [],
                'type': self.__class__.__name__,
            }, f, ensure_ascii=False, indent=2)
    
    @classmethod
    def load(cls, path: str) -> 'Tokenizer':
        """Load tokenizer from file."""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        tokenizer = cls(vocab=data['vocab'])
        if 'merges' in data:
            tokenizer.merges = [tuple(m) for m in data['merges']]
            tokenizer.merge_ranks = {merge: i for i, merge in enumerate(tokenizer.merges)}
        return tokenizer


class BPETokenizer(Tokenizer):
    """
    Byte-Pair Encoding (BPE) Tokenizer.
    
    The standard tokenization algorithm used in GPT models.
    
    Args:
        vocab_size: Target vocabulary size
        min_frequency: Minimum frequency for a merge
        
    Example:
        tokenizer = BPETokenizer(vocab_size=10000)
        tokenizer.train(["Hello world!", "How are you?"])
        ids = tokenizer.encode("Hello!")
        text = tokenizer.decode(ids)
    """
    
    def __init__(
        self, 
        vocab: Optional[Dict[str, int]] = None,
        vocab_size: int = 10000,
        min_frequency: int = 2
    ):
        super().__init__(vocab)
        self.target_vocab_size = vocab_size if vocab is None else len(vocab)
        self.min_frequency = min_frequency
        self.merges: List[Tuple[str, str]] = []
        self.merge_ranks: Dict[Tuple[str, str], int] = {}
        self.cache: Dict[str, List[int]] = {}
    
    def train(self, texts: List[str], verbose: bool = True):
        """
        Train BPE on a corpus of texts.
        
        Args:
            texts: List of training texts
            verbose: Whether to print progress
        """
        # Initialize with character vocabulary
        word_freqs = Counter()
        for text in texts:
            words = text.split()
            for word in words:
                word_freqs[' '.join(list(word)) + ' </w>'] += 1
        
        # Add special tokens
        self.vocab = {
            self.pad_token: 0,
            self.unk_token: 1,
            self.bos_token: 2,
            self.eos_token: 3,
            self.system_token: 4,
            self.user_token: 5,
            self.assistant_token: 6,
            self.end_token: 7,
        }
        
        # Add all characters
        chars = set()
        for word in word_freqs:
            for char in word.split():
                chars.add(char)
        
        for i, char in enumerate(sorted(chars)):
            self.vocab[char] = len(self.vocab)
        
        if verbose:
            print(f"Starting BPE training with {len(self.vocab)} initial tokens...")
        
        # Learn merges
        self.merges = []
        while len(self.vocab) < self.target_vocab_size:
            # Count pairs
            pairs = Counter()
            for word, freq in word_freqs.items():
                symbols = word.split()
                for i in range(len(symbols) - 1):
                    pairs[(symbols[i], symbols[i + 1])] += freq
            
            if not pairs:
                break
            
            # Find best pair
            best = max(pairs, key=pairs.get)
            if pairs[best] < self.min_frequency:
                break
            
            # Merge
            self.merges.append(best)
            new_token = best[0] + best[1]
            self.vocab[new_token] = len(self.vocab)
            
            # Update word frequencies
            new_word_freqs = Counter()
            pattern = re.escape(best[0]) + r'\s+' + re.escape(best[1])
            replacement = new_token
            for word, freq in word_freqs.items():
                new_word = re.sub(pattern, lambda m: new_token, word)
                new_word_freqs[new_word] = freq
            word_freqs = new_word_freqs
            
            if verbose and len(self.merges) % 500 == 0:
                print(f"  Learned {len(self.merges)} merges, vocab size: {len(self.vocab)}")
        
        self.id_to_token = {v: k for k, v in self.vocab.items()}
        self.merge_ranks = {merge: i for i, merge in enumerate(self.merges)}
        self.cache = {}
        
        if verbose:
            print(f"BPE training complete! Final vocab size: {len(self.vocab)}")
    
    def encode(self, text: str) -> List[int]:
        """Encode text to token IDs."""
        if not self.vocab:
            raise ValueError("Tokenizer not trained. Call train() first.")
        
        ids = []
        words = text.split()
        
        for word in words:
            # Check cache
            if word in self.cache:
                ids.extend(self.cache[word])
                continue
                
            # Convert to characters
            word_tokens = list(word) + ['</w>']
            
            # Apply merges using priority (merge_ranks)
            while len(word_tokens) > 1:
                pairs = [(word_tokens[i], word_tokens[i + 1]) for i in range(len(word_tokens) - 1)]
                
                # Find the pair with the best (lowest) rank
                best_pair = None
                min_rank = float('inf')
                
                for pair in pairs:
                    rank = self.merge_ranks.get(pair, float('inf'))
                    if rank < min_rank:
                        best_pair = pair
                        min_rank = rank
                
                if best_pair is None or min_rank == float('inf'):
                    break
                
                # Apply the best merge
                new_word_tokens = []
                i = 0
                while i < len(word_tokens):
                    if i < len(word_tokens) - 1 and (word_tokens[i], word_tokens[i+1]) == best_pair:
                        new_word_tokens.append(best_pair[0] + best_pair[1])
                        i += 2
                    else:
                        new_word_tokens.append(word_tokens[i])
                        i += 1
                word_tokens = new_word_tokens
            
            # Convert to IDs
            word_ids = []
            for token in word_tokens:
                if token in self.vocab:
                    word_ids.append(self.vocab[token])
                else:
                    word_ids.append(self.vocab.get(self.unk_token, 1))
            
            # Cache and update total
            self.cache[word] = word_ids
            ids.extend(word_ids)
        
        return ids
    
    def decode(self, ids: List[int], skip_special_tokens: bool = True) -> str:
        """Decode token IDs back to text with proper spacing."""
        if not ids:
            return ""
        
        tokens = []
        for i in ids:
            if i in self.id_to_token:
                token = self.id_to_token[i]
                if skip_special_tokens:
                    if token not in [self.pad_token, self.bos_token, self.eos_token, self.unk_token, self.system_token, self.user_token, self.assistant_token, self.end_token]:
                        tokens.append(token)
                else:
                    tokens.append(token)
        
        if not tokens:
            return ""
        
        # Join tokens and clean up
        text = ''.join(tokens)
        
        # Replace word boundary markers with spaces
        text = text.replace('</w>', ' ')
        
        if skip_special_tokens:
            text = text.replace('<|pad|>', '')
            text = text.replace('<|bos|>', '')
            text = text.replace('<|eos|>', '')
            text = text.replace('<|unk|>', '')
            text = text.replace('<|system|>', '')
            text = text.replace('<|user|>', '')
            text = text.replace('<|assistant|>', '')
            text = text.replace('<|end|>', '')
        
        # Fix spacing around punctuation
        text = re.sub(r'\s+([.,!?;:])', r'\1', text)
        text = re.sub(r'([.,!?;:])\s*([.,!?;:])', r'\1 \2', text)
        
        # Normalize whitespace
        if skip_special_tokens:
             text = re.sub(r'\s+', ' ', text)
        
        return text.strip()


class WordPieceTokenizer(Tokenizer):
    """
    WordPiece Tokenizer (used in BERT).
    
    Similar to BPE but uses a greedy longest-match-first algorithm.
    """
    
    def __init__(
        self, 
        vocab: Optional[Dict[str, int]] = None,
        vocab_size: int = 10000
    ):
        super().__init__(vocab)
        self.target_vocab_size = vocab_size if vocab is None else len(vocab)
        self.unk_token = "[UNK]"
        self.prefix = "##"
    
    def train(self, texts: List[str], verbose: bool = True):
        """Train WordPiece tokenizer."""
        # Count words
        word_freq = Counter()
        for text in texts:
            for word in text.lower().split():
                word_freq[word] += 1
        
        # Initialize vocab with characters
        self.vocab = {
            "[PAD]": 0,
            "[UNK]": 1,
            "[CLS]": 2,
            "[SEP]": 3,
            "[MASK]": 4,
        }
        
        chars = set()
        for word in word_freq:
            for i, char in enumerate(word):
                if i > 0:
                    chars.add(self.prefix + char)
                else:
                    chars.add(char)
        
        for char in sorted(chars):
            self.vocab[char] = len(self.vocab)
        
        # Learn subwords (simplified)
        for word, freq in word_freq.most_common(self.vocab_size - len(self.vocab)):
            if word not in self.vocab:
                self.vocab[word] = len(self.vocab)
        
        self.id_to_token = {v: k for k, v in self.vocab.items()}
        
        if verbose:
            print(f"WordPiece training complete! Vocab size: {len(self.vocab)}")
    
    def encode(self, text: str) -> List[int]:
        """Encode text using WordPiece."""
        ids = []
        
        for word in text.lower().split():
            if word in self.vocab:
                ids.append(self.vocab[word])
            else:
                # Subword tokenization
                tokens = []
                start = 0
                while start < len(word):
                    end = len(word)
                    found = False
                    while start < end:
                        substr = word[start:end]
                        if start > 0:
                            substr = self.prefix + substr
                        if substr in self.vocab:
                            tokens.append(self.vocab[substr])
                            found = True
                            break
                        end -= 1
                    if not found:
                        tokens.append(self.vocab.get(self.unk_token, 1))
                        start += 1
                    else:
                        start = end
                ids.extend(tokens)
        
        return ids
    
    def decode(self, ids: List[int]) -> str:
        """Decode WordPiece tokens."""
        tokens = [self.id_to_token.get(i, self.unk_token) for i in ids]
        text = ' '.join(tokens)
        text = text.replace(' ' + self.prefix, '')
        text = text.replace('[PAD]', '').replace('[UNK]', '').replace('[CLS]', '').replace('[SEP]', '')
        return text.strip()


class CharTokenizer(Tokenizer):
    """
    Character-level tokenizer.
    
    Simple but works well for small datasets.
    """
    
    def __init__(self, vocab: Optional[Dict[str, int]] = None):
        super().__init__(vocab)
    
    def train(self, texts: List[str], verbose: bool = True):
        """Build character vocabulary from texts."""
        chars = set()
        for text in texts:
            chars.update(text)
        
        self.vocab = {
            self.pad_token: 0,
            self.unk_token: 1,
            self.bos_token: 2,
            self.eos_token: 3,
        }
        
        for i, char in enumerate(sorted(chars)):
            self.vocab[char] = len(self.vocab)
        
        self.id_to_token = {v: k for k, v in self.vocab.items()}
        
        if verbose:
            print(f"Character tokenizer built! Vocab size: {len(self.vocab)}")
    
    def encode(self, text: str) -> List[int]:
        """Encode text to character IDs."""
        return [self.vocab.get(c, self.vocab[self.unk_token]) for c in text]
    
    def decode(self, ids: List[int]) -> str:
        """Decode character IDs to text."""
        tokens = [self.id_to_token.get(i, '') for i in ids]
        text = ''.join(tokens)
        text = text.replace(self.pad_token, '').replace(self.unk_token, '').replace(self.bos_token, '').replace(self.eos_token, '')
        return text


class SimpleTokenizer(Tokenizer):
    """
    Simple word-based tokenizer.
    
    For quick prototyping and small datasets.
    """
    
    def __init__(self, vocab: Optional[Dict[str, int]] = None, max_vocab: int = 50000):
        super().__init__(vocab)
        self.max_vocab = max_vocab
    
    def train(self, texts: List[str], verbose: bool = True):
        """Build word vocabulary."""
        word_freq = Counter()
        for text in texts:
            words = text.lower().split()
            word_freq.update(words)
        
        self.vocab = {
            self.pad_token: 0,
            self.unk_token: 1,
            self.bos_token: 2,
            self.eos_token: 3,
        }
        
        for word, _ in word_freq.most_common(self.max_vocab - len(self.vocab)):
            self.vocab[word] = len(self.vocab)
        
        self.id_to_token = {v: k for k, v in self.vocab.items()}
        
        if verbose:
            print(f"Simple tokenizer built! Vocab size: {len(self.vocab)}")
    
    def encode(self, text: str) -> List[int]:
        """Encode text to word IDs."""
        return [self.vocab.get(w.lower(), self.vocab[self.unk_token]) for w in text.split()]
    
    def decode(self, ids: List[int]) -> str:
        """Decode word IDs to text."""
        tokens = [self.id_to_token.get(i, '') for i in ids]
        tokens = [t for t in tokens if t not in [self.pad_token, self.unk_token, self.bos_token, self.eos_token]]
        return ' '.join(tokens)
