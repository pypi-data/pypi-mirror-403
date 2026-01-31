"""
NAPLY Data Loading
==================

Universal data loader supporting all popular formats.
- .txt (plain text)
- .json (JSON)
- .jsonl (JSON Lines)
- .csv (CSV)
- Folders with mixed formats
"""

import os
import json
import csv
import zipfile
import io
import random
import numpy as np
from typing import List, Dict, Optional, Iterator, Union, Tuple, Any
from .tensor import Tensor


class Dataset:
    """
    Base dataset class.
    
    All datasets should inherit from this class.
    """
    
    def __len__(self) -> int:
        raise NotImplementedError
    
    def __getitem__(self, idx: int) -> Any:
        raise NotImplementedError


class TextDataset(Dataset):
    """
    Simple text dataset for language modeling.
    
    Args:
        texts: List of text strings
        tokenizer: Tokenizer instance
        max_length: Maximum sequence length
    """
    
    def __init__(
        self, 
        texts: List[str], 
        tokenizer,
        max_length: int = 512
    ):
        self.texts = texts
        self.tokenizer = tokenizer
        self.max_length = max_length
        
        # Tokenize all texts and chunk them
        self.tokens = []
        for text in texts:
            ids = tokenizer.encode(text)
            if len(ids) > self.max_length:
                # Chunk into multiple samples
                for i in range(0, len(ids) - self.max_length, self.max_length):
                    self.tokens.append(ids[i:i + self.max_length + 1])
            elif len(ids) > 1:
                self.tokens.append(ids)
    
    def __len__(self) -> int:
        return len(self.tokens)
    
    def __getitem__(self, idx: int) -> Tuple[np.ndarray, np.ndarray]:
        """
        Returns:
            x: Input token IDs (context)
            y: Target token IDs (shifted by 1)
        """
        tokens = self.tokens[idx]
        
        # Truncate or pad
        if len(tokens) > self.max_length + 1:
            tokens = tokens[:self.max_length + 1]
        
        # Input and target (next token prediction)
        x = np.array(tokens[:-1], dtype=np.int32)
        y = np.array(tokens[1:], dtype=np.int32)
        
        return x, y


class DataLoader:
    """
    Data loader for batching and shuffling.
    
    Args:
        dataset: Dataset instance
        batch_size: Batch size
        shuffle: Whether to shuffle data
        drop_last: Whether to drop incomplete batches
    """
    
    def __init__(
        self, 
        dataset: Dataset,
        batch_size: int = 32,
        shuffle: bool = True,
        drop_last: bool = False
    ):
        self.dataset = dataset
        self.batch_size = batch_size
        self.shuffle = shuffle
        self.drop_last = drop_last
    
    def __len__(self) -> int:
        n = len(self.dataset) // self.batch_size
        if not self.drop_last and len(self.dataset) % self.batch_size != 0:
            n += 1
        return n
    
    def __iter__(self) -> Iterator[Tuple[Tensor, Tensor]]:
        indices = list(range(len(self.dataset)))
        if self.shuffle:
            random.shuffle(indices)
        
        for i in range(0, len(indices), self.batch_size):
            batch_indices = indices[i:i + self.batch_size]
            if self.drop_last and len(batch_indices) < self.batch_size:
                break
            
            batch_x = []
            batch_y = []
            max_len = 0
            
            for idx in batch_indices:
                x, y = self.dataset[idx]
                batch_x.append(x)
                batch_y.append(y)
                max_len = max(max_len, len(x))
            
            # Pad to max length in batch
            padded_x = np.zeros((len(batch_x), max_len), dtype=np.int32)
            padded_y = np.zeros((len(batch_y), max_len), dtype=np.int32)
            
            for j, (x, y) in enumerate(zip(batch_x, batch_y)):
                padded_x[j, :len(x)] = x
                padded_y[j, :len(y)] = y
            
            yield Tensor(padded_x), Tensor(padded_y)


class UniversalLoader:
    """
    Universal data loader supporting all formats.
    
    Automatically detects and loads:
    - .txt files (plain text)
    - .json files (JSON format)
    - .jsonl files (JSON Lines)
    - .csv files (CSV format)
    - Directories (loads all files recursively)
    
    Example:
        loader = UniversalLoader("my_data/")
        texts = loader.load()  # Returns list of texts
    """
    
    SUPPORTED_EXTENSIONS = {'.txt', '.json', '.jsonl', '.csv', '.md', '.py', '.zip', '.js', '.ts', '.java', '.c', '.cpp', '.go', '.rs', '.rb', '.php', '.html', '.css'}
    
    def __init__(self, path: str):
        self.path = path
    
    def load(self) -> List[str]:
        """
        Load data from path.
        
        Returns:
            List of text strings
        """
        if os.path.isfile(self.path):
            return self._load_file(self.path)
        elif os.path.isdir(self.path):
            return self._load_directory(self.path)
        else:
            raise FileNotFoundError(f"Path not found: {self.path}")
    
    def _load_directory(self, dir_path: str) -> List[str]:
        """Load all files from a directory."""
        texts = []
        
        for root, dirs, files in os.walk(dir_path):
            for file in files:
                filepath = os.path.join(root, file)
                ext = os.path.splitext(file)[1].lower()
                
                if ext in self.SUPPORTED_EXTENSIONS:
                    try:
                        file_texts = self._load_file(filepath)
                        texts.extend(file_texts)
                    except Exception as e:
                        print(f"Warning: Could not load {filepath}: {e}")
        
        print(f"Loaded {len(texts)} texts from {dir_path}")
        return texts
    
    def _load_file(self, filepath: str) -> List[str]:
        """Load a single file."""
        ext = os.path.splitext(filepath)[1].lower()
        
        if ext == '.txt' or ext == '.md' or ext == '.py':
            return self._load_txt(filepath)
        elif ext == '.json':
            return self._load_json(filepath)
        elif ext == '.jsonl':
            return self._load_jsonl(filepath)
        elif ext == '.csv':
            return self._load_csv(filepath)
        elif ext == '.zip':
            return self._load_zip(filepath)
        else:
            # Try as text
            return self._load_txt(filepath)
    
    def _load_txt(self, filepath: str) -> List[str]:
        """Load plain text file."""
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Split into paragraphs or return as single text
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        if len(paragraphs) == 0:
            return [content] if content.strip() else []
        return paragraphs
    
    def _load_json(self, filepath: str) -> List[str]:
        """Load JSON file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return self._extract_texts_from_json(data)
    
    def _load_jsonl(self, filepath: str) -> List[str]:
        """Load JSON Lines file (used in many ML datasets)."""
        texts = []
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        data = json.loads(line)
                        texts.extend(self._extract_texts_from_json(data))
                    except json.JSONDecodeError:
                        continue
        return texts
    
    def _load_csv(self, filepath: str) -> List[str]:
        """Load CSV file."""
        texts = []
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.reader(f)
            header = next(reader, None)
            
            # Find text columns
            text_columns = []
            if header:
                for i, col in enumerate(header):
                    col_lower = col.lower()
                    if any(name in col_lower for name in ['text', 'content', 'message', 'body', 'input', 'output']):
                        text_columns.append(i)
                
                if not text_columns:
                    text_columns = list(range(len(header)))
            
            for row in reader:
                for col_idx in text_columns:
                    if col_idx < len(row) and row[col_idx].strip():
                        texts.append(row[col_idx].strip())
        
        return texts
    
    def _extract_texts_from_json(self, data: Union[Dict, List]) -> List[str]:
        """Extract text from JSON data (handles various formats)."""
        texts = []
        
        if isinstance(data, str):
            if data.strip():
                texts.append(data.strip())
        
        elif isinstance(data, list):
            for item in data:
                texts.extend(self._extract_texts_from_json(item))
        
        elif isinstance(data, dict):
            # Common formats
            text_keys = ['text', 'content', 'message', 'input', 'output', 'prompt', 'response', 'body']
            
            for key in text_keys:
                if key in data:
                    texts.extend(self._extract_texts_from_json(data[key]))
            
            # Chat format (messages array)
            if 'messages' in data:
                for msg in data['messages']:
                    if isinstance(msg, dict) and 'content' in msg:
                        if msg['content'].strip():
                            texts.append(msg['content'].strip())
            
            # Instruction format
            if 'instruction' in data and 'output' in data:
                instruction = data.get('instruction', '')
                input_text = data.get('input', '')
                output_text = data.get('output', '')
                combined = f"{instruction}\n{input_text}\n{output_text}".strip()
                if combined:
                    texts.append(combined)
        
        return texts


    def _load_zip(self, filepath: str) -> List[str]:
        """Load data from a ZIP file."""
        texts = []
        try:
            with zipfile.ZipFile(filepath, 'r') as zf:
                for filename in zf.namelist():
                    # Skip directories and hidden files
                    if filename.endswith('/') or filename.startswith('.') or '/.' in filename:
                        continue
                        
                    ext = os.path.splitext(filename)[1].lower()
                    if ext in self.SUPPORTED_EXTENSIONS and ext != '.zip':
                        try:
                            # Read file content from zip (safely)
                            with zf.open(filename) as f:
                                content = f.read().decode('utf-8', errors='ignore')
                                
                                # Process based on extension
                                if ext in ['.txt', '.md', '.py']:
                                    paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
                                    if not paragraphs and content.strip():
                                        texts.append(content.strip())
                                    else:
                                        texts.extend(paragraphs)
                                        
                                elif ext == '.json':
                                    data = json.loads(content)
                                    texts.extend(self._extract_texts_from_json(data))
                                    
                                elif ext == '.jsonl':
                                    for line in content.splitlines():
                                        if line.strip():
                                            try:
                                                data = json.loads(line)
                                                texts.extend(self._extract_texts_from_json(data))
                                            except:
                                                pass
                                                
                                elif ext == '.csv':
                                    f_io = io.StringIO(content)
                                    reader = csv.reader(f_io)
                                    header = next(reader, None)
                                    text_columns = []
                                    if header:
                                        for i, col in enumerate(header):
                                            if any(n in col.lower() for n in ['text', 'content', 'message', 'body']):
                                                text_columns.append(i)
                                        if not text_columns:
                                            text_columns = list(range(len(header)))
                                            
                                    for row in reader:
                                        for col_idx in text_columns:
                                            if col_idx < len(row) and row[col_idx].strip():
                                                texts.append(row[col_idx].strip())

                        except Exception as e:
                            print(f"Warning: Could not read {filename} in zip: {e}")
                            
        except Exception as e:
            print(f"Warning: Could not open zip file {filepath}: {e}")
            
        return texts


def load_data(path: str) -> List[str]:
    """
    Convenience function to load data from any format.
    
    Args:
        path: Path to file or directory
        
    Returns:
        List of text strings
        
    Example:
        texts = load_data("my_data/")
        texts = load_data("data.jsonl")
    """
    loader = UniversalLoader(path)
    return loader.load()


def prepare_training_data(
    texts: List[str],
    tokenizer,
    max_length: int = 512,
    batch_size: int = 32,
    shuffle: bool = True
) -> DataLoader:
    """
    Prepare training data from texts.
    
    Args:
        texts: List of text strings
        tokenizer: Tokenizer instance
        max_length: Maximum sequence length
        batch_size: Batch size
        shuffle: Whether to shuffle
        
    Returns:
        DataLoader ready for training
    """
    dataset = TextDataset(texts, tokenizer, max_length)
    return DataLoader(dataset, batch_size=batch_size, shuffle=shuffle)
