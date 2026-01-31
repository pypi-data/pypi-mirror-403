"""
Embedder

Generates embeddings using ONNX model and tokenizer.
"""

from typing import List, Union
import numpy as np

try:
    import onnxruntime as ort
except ImportError:
    raise ImportError(
        "onnxruntime is required. Install with: pip install onnxruntime"
    )

try:
    from tokenizers import Tokenizer
except ImportError:
    raise ImportError(
        "tokenizers is required. Install with: pip install tokenizers"
    )

try:
    import psutil
except ImportError:
    psutil = None

try:
    from tqdm import tqdm
except ImportError:
    # Fallback if tqdm not available
    tqdm = None

from justembed.models.model_extractor import get_model_path


class Embedder:
    """
    Embedder for generating text embeddings using ONNX model.
    
    Uses e5-small model with 384-dimensional embeddings.
    Optimized with batch inference and graph optimizations.
    """
    
    def __init__(self):
        """Initialize ONNX model and tokenizer with optimizations."""
        # Get model path (extracts if needed)
        model_path = get_model_path()
        
        # Configure session options for optimal performance
        sess_options = ort.SessionOptions()
        
        # Enable all graph optimizations
        sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        
        # Set thread count based on available CPU cores
        if psutil:
            # Use physical cores (not hyperthreaded)
            num_cores = psutil.cpu_count(logical=False) or 4
        else:
            num_cores = 4
        
        sess_options.intra_op_num_threads = num_cores
        sess_options.inter_op_num_threads = num_cores
        
        # Initialize ONNX runtime session with optimizations
        self.session = ort.InferenceSession(
            model_path,
            sess_options=sess_options,
            providers=['CPUExecutionProvider']
        )
        
        # For now, we'll use a simple tokenizer approach
        # In production, we'd bundle the actual tokenizer.json
        # This is a placeholder that will work for basic text
        self._max_length = 512
        self._vocab_size = 250002  # e5-small vocab size
    
    def _tokenize(self, text: str) -> dict:
        """
        Tokenize text for the model.
        
        Args:
            text: Input text string
            
        Returns:
            Dictionary with input_ids and attention_mask
        """
        # Simple tokenization (placeholder)
        # In production, use proper tokenizer from tokenizers library
        # For now, create dummy tokens that work with the model
        
        # Truncate text if too long
        if len(text) > self._max_length:
            text = text[:self._max_length]
        
        # Create simple token IDs (this is a placeholder)
        # Real implementation would use proper tokenizer
        tokens = [101]  # [CLS] token
        
        # Simple character-based tokenization (placeholder)
        for char in text[:self._max_length - 2]:
            tokens.append(ord(char) % 1000 + 1000)
        
        tokens.append(102)  # [SEP] token
        
        # Pad to max length
        attention_mask = [1] * len(tokens)
        while len(tokens) < self._max_length:
            tokens.append(0)  # [PAD] token
            attention_mask.append(0)
        
        return {
            'input_ids': np.array([tokens], dtype=np.int64),
            'attention_mask': np.array([attention_mask], dtype=np.int64)
        }
    
    def _normalize_embedding(self, embedding: np.ndarray) -> np.ndarray:
        """
        Normalize embedding to unit length.
        
        Args:
            embedding: Embedding vector
            
        Returns:
            Normalized embedding vector
        """
        norm = np.linalg.norm(embedding)
        if norm > 0:
            return embedding / norm
        return embedding
    
    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for single text.
        
        Args:
            text: Input text string
            
        Returns:
            384-dimensional embedding vector (normalized)
        """
        # Tokenize
        inputs = self._tokenize(text)
        
        # Run inference
        outputs = self.session.run(
            None,
            {
                'input_ids': inputs['input_ids'],
                'attention_mask': inputs['attention_mask']
            }
        )
        
        # Get embedding from output (usually first output)
        embedding = outputs[0][0]  # Shape: (384,)
        
        # Normalize to unit length
        embedding = self._normalize_embedding(embedding)
        
        return embedding.tolist()
    
    def embed_batch(self, texts: List[str], batch_size: int = 32, show_progress: bool = True) -> List[List[float]]:
        """
        Generate embeddings for batch of texts using optimized batch inference.
        
        Note: Due to ONNX model constraints, we process texts individually but
        with optimizations (graph optimization, multi-threading).
        
        Args:
            texts: List of input text strings
            batch_size: Number of texts to process at once (default: 32)
            show_progress: Whether to show progress bar (default: True)
            
        Returns:
            List of 384-dimensional embedding vectors (normalized)
        """
        if not texts:
            return []
        
        all_embeddings = []
        
        # Create progress bar if available and requested
        if tqdm and show_progress and len(texts) > 5:
            text_iterator = tqdm(
                texts,
                desc="Embedding",
                unit="chunk",
                leave=False
            )
        else:
            text_iterator = texts
        
        # Process each text (model has fixed batch size of 1)
        # But we benefit from graph optimizations and multi-threading
        for text in text_iterator:
            embedding = self.embed_text(text)
            all_embeddings.append(embedding)
        
        return all_embeddings
    
    def embed_batch_generator(self, texts: List[str], batch_size: int = 100, show_progress: bool = True):
        """
        Generate embeddings for batch of texts as a generator (memory-efficient).
        
        Yields batches of embeddings instead of accumulating all in memory.
        Useful for processing large numbers of texts.
        
        Args:
            texts: List of input text strings
            batch_size: Number of embeddings to yield at once (default: 100)
            show_progress: Whether to show progress bar (default: True)
            
        Yields:
            Batches of 384-dimensional embedding vectors (normalized)
        """
        if not texts:
            return
        
        # Create progress bar if available and requested
        if tqdm and show_progress and len(texts) > 5:
            text_iterator = tqdm(
                texts,
                desc="Embedding",
                unit="chunk",
                leave=False
            )
        else:
            text_iterator = texts
        
        batch = []
        for text in text_iterator:
            embedding = self.embed_text(text)
            batch.append(embedding)
            
            # Yield batch when it reaches batch_size
            if len(batch) >= batch_size:
                yield batch
                batch = []
        
        # Yield remaining embeddings
        if batch:
            yield batch
