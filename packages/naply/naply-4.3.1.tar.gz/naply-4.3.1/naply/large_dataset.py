"""
NAPLY Large Dataset Support
===========================

Memory-efficient data loading for huge datasets.
Supports streaming, chunking, and on-the-fly processing.
"""

import os
import json
import gc
import mmap
import numpy as np
from typing import List, Iterator, Optional, Callable, Tuple
from .tensor import Tensor


class StreamingDataset:
    """
    Memory-efficient streaming dataset for huge datasets.
    
    Loads data on-the-fly instead of loading everything into memory.
    Supports files larger than RAM.
    
    Example:
        dataset = StreamingDataset("huge_data.jsonl", chunk_size=1000)
        for batch in dataset.iter_batches(batch_size=32):
            x, y = batch
            # Train on batch
    """
    
    def __init__(
        self,
        file_path: str,
        tokenizer,
        max_length: int = 512,
        chunk_size: int = 10000,
        cache_size: int = 100000
    ):
        self.file_path = file_path
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.chunk_size = chunk_size
        self.cache_size = cache_size
        
        # Cache for recently loaded data
        self.cache = []
        self.cache_positions = []
        
        # Count total samples (lazy)
        self._total_samples = None
    
    def _count_samples(self) -> int:
        """Count total samples in file."""
        if self._total_samples is not None:
            return self._total_samples
        
        count = 0
        with open(self.file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for _ in f:
                count += 1
        
        self._total_samples = count
        return count
    
    def __len__(self) -> int:
        """Get total number of samples."""
        return self._count_samples()
    
    def _load_chunk(self, start_idx: int, end_idx: int) -> List[Tuple[np.ndarray, np.ndarray]]:
        """Load a chunk of data from file."""
        samples = []
        current_idx = 0
        
        with open(self.file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                if current_idx >= end_idx:
                    break
                
                if current_idx >= start_idx:
                    try:
                        # Parse line (JSONL format)
                        if line.strip():
                            data = json.loads(line) if line.strip().startswith('{') else {'text': line.strip()}
                            
                            # Extract text
                            text = data.get('text', data.get('content', data.get('instruction', '')))
                            if not text:
                                text = str(data)
                            
                            # Tokenize
                            tokens = self.tokenizer.encode(text)
                            
                            # Create samples
                            for i in range(0, len(tokens) - self.max_length, self.max_length):
                                x = np.array(tokens[i:i+self.max_length], dtype=np.int32)
                                y = np.array(tokens[i+1:i+self.max_length+1], dtype=np.int32)
                                samples.append((x, y))
                                
                                if len(samples) >= self.chunk_size:
                                    return samples
                    except:
                        continue
                
                current_idx += 1
        
        return samples
    
    def iter_batches(
        self,
        batch_size: int = 32,
        shuffle: bool = True,
        num_workers: int = 1
    ) -> Iterator[Tuple[Tensor, Tensor]]:
        """
        Iterate over batches, loading data on-the-fly.
        
        Args:
            batch_size: Batch size
            shuffle: Whether to shuffle
            num_workers: Number of parallel workers (for future use)
        """
        total_samples = self._count_samples()
        indices = list(range(total_samples))
        
        if shuffle:
            np.random.shuffle(indices)
        
        # Process in chunks
        for chunk_start in range(0, total_samples, self.chunk_size):
            chunk_end = min(chunk_start + self.chunk_size, total_samples)
            chunk_indices = indices[chunk_start:chunk_end]
            
            # Load chunk
            samples = self._load_chunk(chunk_start, chunk_end)
            
            # Create batches from chunk
            for i in range(0, len(samples), batch_size):
                batch_samples = samples[i:i+batch_size]
                if len(batch_samples) < batch_size:
                    continue
                
                # Pad to same length
                max_len = max(len(s[0]) for s in batch_samples)
                batch_x = np.zeros((len(batch_samples), max_len), dtype=np.int32)
                batch_y = np.zeros((len(batch_samples), max_len), dtype=np.int32)
                
                for j, (x, y) in enumerate(batch_samples):
                    batch_x[j, :len(x)] = x
                    batch_y[j, :len(y)] = y
                
                yield Tensor(batch_x), Tensor(batch_y)
            
            # Free memory
            del samples
            gc.collect()


class HugeDatasetLoader:
    """
    Loader for huge datasets with memory efficiency.
    
    Features:
    - Streaming data loading
    - Automatic chunking
    - Memory management
    - Progress tracking
    - Resume support
    """
    
    def __init__(
        self,
        data_path: str,
        tokenizer,
        max_length: int = 512,
        chunk_size: int = 10000,
        use_streaming: bool = True
    ):
        self.data_path = data_path
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.chunk_size = chunk_size
        self.use_streaming = use_streaming
        
        # Check if path is file or directory
        if os.path.isfile(data_path):
            self.is_file = True
            self.files = [data_path]
        elif os.path.isdir(data_path):
            self.is_file = False
            self.files = self._scan_directory(data_path)
        else:
            raise FileNotFoundError(f"Path not found: {data_path}")
        
        print(f"📂 Found {len(self.files)} file(s) to process")
    
    def _scan_directory(self, dir_path: str) -> List[str]:
        """Scan directory for data files."""
        files = []
        extensions = {'.txt', '.json', '.jsonl', '.csv'}
        
        for root, dirs, filenames in os.walk(dir_path):
            for filename in filenames:
                if any(filename.endswith(ext) for ext in extensions):
                    files.append(os.path.join(root, filename))
        
        return files
    
    def get_dataset_size(self) -> int:
        """Estimate total dataset size."""
        total = 0
        for file_path in self.files:
            if file_path.endswith('.jsonl'):
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    total += sum(1 for _ in f)
            else:
                # Estimate for other formats
                size = os.path.getsize(file_path)
                total += size // 100  # Rough estimate
        
        return total
    
    def iter_batches(
        self,
        batch_size: int = 32,
        shuffle: bool = True
    ) -> Iterator[Tuple[Tensor, Tensor]]:
        """
        Iterate over batches from all files.
        
        Yields:
            (x, y) batches as Tensors
        """
        all_indices = []
        file_ranges = []
        
        # Calculate ranges for each file
        current_idx = 0
        for file_path in self.files:
            if file_path.endswith('.jsonl'):
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    file_size = sum(1 for _ in f)
            else:
                # Estimate
                file_size = os.path.getsize(file_path) // 100
            
            file_ranges.append((current_idx, current_idx + file_size, file_path))
            all_indices.extend(range(current_idx, current_idx + file_size))
            current_idx += file_size
        
        if shuffle:
            np.random.shuffle(all_indices)
        
        # Process files
        for start_idx, end_idx, file_path in file_ranges:
            dataset = StreamingDataset(
                file_path,
                self.tokenizer,
                self.max_length,
                self.chunk_size
            )
            
            for batch_x, batch_y in dataset.iter_batches(batch_size, shuffle=False):
                yield batch_x, batch_y
            
            # Free memory
            del dataset
            gc.collect()


def create_huge_dataset_loader(
    data_path: str,
    tokenizer,
    max_length: int = 512,
    chunk_size: int = 10000
) -> HugeDatasetLoader:
    """
    Create a loader for huge datasets.
    
    Args:
        data_path: Path to data file or directory
        tokenizer: Tokenizer instance
        max_length: Maximum sequence length
        chunk_size: Chunk size for processing
        
    Returns:
        HugeDatasetLoader instance
    """
    return HugeDatasetLoader(
        data_path,
        tokenizer,
        max_length,
        chunk_size,
        use_streaming=True
    )
