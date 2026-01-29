"""
Improved LocalLLM with enhanced functionality, error handling, and performance optimizations.
"""

import logging
from typing import Union, List, Optional, Dict, Any
from pathlib import Path
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
except ImportError as e:
    raise ImportError(
        "sentence-transformers package is required. Install with: pip install sentence-transformers"
    ) from e


class LocalLLM:
    """
    Enhanced wrapper for SentenceTransformer with improved functionality.
    
    Features:
    - Flexible input handling (single string or list of strings)
    - Configurable encoding parameters
    - Device selection (CPU/GPU)
    - Better error handling and validation
    - Optional caching
    - Performance optimizations
    - Comprehensive logging
    
    Args:
        model_name: HuggingFace model name or local path
        device: Device to use ('cpu', 'cuda', 'auto')
        cache_folder: Optional folder to cache models
        trust_remote_code: Whether to trust remote code in models
        **model_kwargs: Additional arguments for SentenceTransformer
    """
    
    def __init__(
        self,
        model_name: str,
        device: str = "auto",
        cache_folder: Optional[str] = None,
        trust_remote_code: bool = False,
        **model_kwargs: Any
    ):
        self.model_name = model_name
        self.device = device
        self.cache_folder = cache_folder
        self.logger = self._setup_logger()
        
        self.model: Optional[SentenceTransformer] = None
        self._load_model(trust_remote_code, **model_kwargs)
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logger for the embedder."""
        logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def _load_model(self, trust_remote_code: bool, **model_kwargs: Any) -> None:
        """Load the SentenceTransformer model with error handling."""
        try:
            self.logger.info(f"Loading model: {self.model_name}")
            
            # Prepare model arguments
            load_kwargs = {
                'device': self.device,
                'trust_remote_code': trust_remote_code,
                **model_kwargs
            }
            
            if self.cache_folder:
                load_kwargs['cache_folder'] = self.cache_folder
            
            self.model = SentenceTransformer(self.model_name, **load_kwargs)
            self.logger.info(f"Model loaded successfully on device: {self.model.device}")
            
        except Exception as e:
            error_msg = f"Failed to load model '{self.model_name}': {str(e)}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg) from e
    
    def _validate_inputs(self, texts: Union[str, List[str]]) -> List[str]:
        """Validate and normalize input texts."""
        if not texts:
            raise ValueError("Input texts cannot be empty")
        
        # Convert single string to list
        if isinstance(texts, str):
            if not texts.strip():
                raise ValueError("Input text cannot be empty or whitespace only")
            return [texts]
        
        # Validate list of strings
        if not isinstance(texts, list):
            raise TypeError(f"Expected str or list[str], got {type(texts)}")
        
        if not all(isinstance(text, str) for text in texts):
            raise TypeError("All items in texts list must be strings")
        
        # Filter out empty strings and log warning
        valid_texts = [text for text in texts if text.strip()]
        if len(valid_texts) != len(texts):
            self.logger.warning(
                f"Filtered out {len(texts) - len(valid_texts)} empty/whitespace-only texts"
            )
        
        if not valid_texts:
            raise ValueError("No valid (non-empty) texts provided")
        
        return valid_texts
    
    def embed(
        self,
        texts: Union[str, List[str]],
        batch_size: int = 32,
        show_progress_bar: bool = True,
        convert_to_numpy: bool = True,
        normalize_embeddings: bool = False,
        return_as_list: bool = True,
        **encode_kwargs: Any
    ) -> Union[List[List[float]], np.ndarray]:
        """
        Generate embeddings for input texts.
        
        Args:
            texts: Single string or list of strings to embed
            batch_size: Batch size for encoding (default: 32)
            show_progress_bar: Whether to show progress bar (default: True)
            convert_to_numpy: Whether to convert to numpy arrays (default: True)
            normalize_embeddings: Whether to normalize embeddings (default: False)
            return_as_list: Whether to return as list of lists (default: True)
            **encode_kwargs: Additional arguments for model.encode()
        
        Returns:
            Embeddings as list of lists or numpy array
        
        Raises:
            ValueError: If inputs are invalid
            RuntimeError: If model is not loaded or encoding fails
        """
        if self.model is None:
            raise RuntimeError("Model not loaded. Cannot generate embeddings.")
        
        # Validate and normalize inputs
        valid_texts = self._validate_inputs(texts)
        
        try:
            self.logger.info(f"Generating embeddings for {len(valid_texts)} texts")
            
            # Prepare encoding arguments
            encoding_args = {
                'batch_size': batch_size,
                'show_progress_bar': show_progress_bar,
                'convert_to_numpy': convert_to_numpy,
                'normalize_embeddings': normalize_embeddings,
                **encode_kwargs
            }
            
            # Generate embeddings
            embeddings = self.model.encode(valid_texts, **encoding_args)
            
            self.logger.info(f"Successfully generated embeddings with shape: {embeddings.shape}")
            
            # Return format based on preference
            if return_as_list and convert_to_numpy:
                return [vec.tolist() for vec in embeddings]
            else:
                return embeddings
                
        except Exception as e:
            error_msg = f"Failed to generate embeddings: {str(e)}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg) from e
    
    def get_embedding(
        self,
        texts: Union[str, List[str]],
        normalize: bool = True,
        as_numpy: bool = False,
        batch_size: int = 32,
        show_progress: bool = False,
        include_metadata: bool = False,
        **kwargs: Any
    ) -> Union[List[List[float]], np.ndarray, Dict[str, Any]]:
        """
        Get embeddings for input texts with convenient defaults and optional metadata.
        
        This method provides a more user-friendly interface compared to embed() with:
        - Normalized embeddings by default for better similarity computations
        - Optional metadata including model information and processing stats
        - Simplified parameter names for common use cases
        - Less verbose progress reporting by default
        
        Args:
            texts: Single string or list of strings to embed
            normalize: Whether to normalize embeddings (default: True)
            as_numpy: Whether to return numpy arrays instead of lists (default: False)
            batch_size: Batch size for encoding (default: 32)
            show_progress: Whether to show progress bar (default: False)
            include_metadata: Whether to include metadata in the response (default: False)
            **kwargs: Additional arguments passed to the underlying model.encode()
        
        Returns:
            If include_metadata=False:
                Embeddings as list of lists (default) or numpy array
            If include_metadata=True:
                Dictionary containing:
                - 'embeddings': The embedding vectors
                - 'metadata': Dictionary with processing information
        
        Raises:
            ValueError: If inputs are invalid
            RuntimeError: If model is not loaded or encoding fails
        
        Examples:
            # Basic usage with normalized embeddings
            embeddings = embedder.get_embeddings("Hello world")
            
            # Multiple texts with numpy output
            embeddings = embedder.get_embeddings(["text1", "text2"], as_numpy=True)
            
            # With metadata for analysis
            result = embedder.get_embeddings(
                ["text1", "text2"], 
                include_metadata=True
            )
            embeddings = result['embeddings']
            info = result['metadata']
        """
        if self.model is None:
            raise RuntimeError("Model not loaded. Cannot generate embeddings.")
        
        # Store original inputs for metadata
        original_texts = texts
        is_single_text = isinstance(texts, str)
        
        # Validate and normalize inputs
        valid_texts = self._validate_inputs(texts)
        
        try:
            self.logger.info(f"Getting embeddings for {len(valid_texts)} texts")
            
            # Import time for metadata timing
            import time
            start_time = time.time()
            
            # Prepare encoding arguments
            encoding_args = {
                'batch_size': batch_size,
                'show_progress_bar': show_progress,
                'convert_to_numpy': True,  # Always convert to numpy first
                'normalize_embeddings': normalize,
                **kwargs
            }
            
            # Generate embeddings
            embeddings = self.model.encode(valid_texts, **encoding_args)
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            self.logger.info(f"Successfully generated embeddings with shape: {embeddings.shape}")
            
            # Format output based on preferences
            if not as_numpy:
                embeddings = [vec.tolist() for vec in embeddings]
            
            # Handle single text input - return single embedding vector if original was single text
            if is_single_text and not include_metadata:
                if as_numpy:
                    embeddings = embeddings[0]  # Return single numpy array
                else:
                    embeddings = embeddings[0]  # Return single list
            
            # Prepare metadata if requested
            if include_metadata:
                metadata = {
                    'input_count': len(valid_texts),
                    'original_input_count': len(original_texts) if isinstance(original_texts, list) else 1,
                    'filtered_count': len(original_texts) - len(valid_texts) if isinstance(original_texts, list) else 0,
                    'embedding_dimension': embeddings.shape[-1] if hasattr(embeddings, 'shape') else len(embeddings[0]) if embeddings else 0,
                    'processing_time_seconds': processing_time,
                    'texts_per_second': len(valid_texts) / processing_time if processing_time > 0 else float('inf'),
                    'model_name': self.model_name,
                    'device': str(self.model.device),
                    'normalized': normalize,
                    'batch_size': batch_size,
                    'output_format': 'numpy' if as_numpy else 'list'
                }
                
                return {
                    'embeddings': embeddings,
                    'metadata': metadata
                }
            
            return embeddings
                
        except Exception as e:
            error_msg = f"Failed to get embeddings: {str(e)}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg) from e
    
    def embed_batch(
        self,
        texts_batches: List[List[str]],
        **embed_kwargs: Any
    ) -> List[Union[List[List[float]], np.ndarray]]:
        """
        Generate embeddings for multiple batches of texts.
        
        Args:
            texts_batches: List of text batches
            **embed_kwargs: Arguments to pass to embed method
        
        Returns:
            List of embedding results for each batch
        """
        results = []
        for i, batch in enumerate(texts_batches):
            self.logger.info(f"Processing batch {i+1}/{len(texts_batches)}")
            embeddings = self.embed(batch, **embed_kwargs)
            results.append(embeddings)
        return results
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model."""
        if self.model is None:
            return {"status": "Model not loaded"}
        
        return {
            "model_name": self.model_name,
            "device": str(self.model.device),
            "max_seq_length": getattr(self.model, 'max_seq_length', 'Unknown'),
            "embedding_dimension": self.get_embedding_dimension(),
            "tokenizer": type(self.model.tokenizer).__name__ if hasattr(self.model, 'tokenizer') else 'Unknown'
        }
    
    def get_embedding_dimension(self) -> Optional[int]:
        """Get the embedding dimension of the model."""
        if self.model is None:
            return None
        
        try:
            # Get dimension from model
            return self.model.get_sentence_embedding_dimension()
        except Exception as e:
            self.logger.warning(f"Could not determine embedding dimension: {e}")
            return None
    
    def benchmark(
        self,
        sample_texts: Optional[List[str]] = None,
        num_samples: int = 100,
        num_runs: int = 3
    ) -> Dict[str, float]:
        """
        Benchmark the embedding performance.
        
        Args:
            sample_texts: Optional list of texts to use for benchmarking
            num_samples: Number of samples to generate if sample_texts not provided
            num_runs: Number of benchmark runs to average
        
        Returns:
            Dictionary with benchmark results
        """
        import time
        
        if sample_texts is None:
            sample_texts = [f"This is sample text number {i}" for i in range(num_samples)]
        
        times = []
        for run in range(num_runs):
            start_time = time.time()
            self.embed(sample_texts, show_progress_bar=False)
            end_time = time.time()
            times.append(end_time - start_time)
        
        avg_time = sum(times) / len(times)
        texts_per_second = len(sample_texts) / avg_time
        
        return {
            "average_time_seconds": avg_time,
            "texts_per_second": texts_per_second,
            "total_texts": len(sample_texts),
            "num_runs": num_runs
        }
    
    def __str__(self) -> str:
        return f"LocalLLM(model={self.model_name}, device={self.device})"
    
    def __repr__(self) -> str:
        return self.__str__()


# Example usage and factory functions
class EmbedderFactory:
    """Factory class for creating common embedder configurations."""
    
    @staticmethod
    def create_fast_embedder(cache_folder: Optional[str] = None) -> LocalLLM:
        """Create a fast, lightweight embedder."""
        return LocalLLM(
            model_name="all-MiniLM-L6-v2",
            device="auto",
            cache_folder=cache_folder
        )
    
    @staticmethod
    def create_multilingual_embedder(cache_folder: Optional[str] = None) -> LocalLLM:
        """Create a multilingual embedder."""
        return LocalLLM(
            model_name="distiluse-base-multilingual-cased",
            device="auto",
            cache_folder=cache_folder
        )
    
    @staticmethod
    def create_high_quality_embedder(cache_folder: Optional[str] = None) -> LocalLLM:
        """Create a high-quality embedder (larger model)."""
        return LocalLLM(
            model_name="all-mpnet-base-v2",
            device="auto",
            cache_folder=cache_folder
        )


# Utility functions
def compare_embedders(
    embedders: List[LocalLLM],
    test_texts: List[str],
    names: Optional[List[str]] = None
) -> Dict[str, Dict[str, Any]]:
    """
    Compare multiple embedders on the same texts.
    
    Args:
        embedders: List of LocalLLM instances
        test_texts: Texts to use for comparison
        names: Optional names for the embedders
    
    Returns:
        Comparison results
    """
    if names is None:
        names = [f"Embedder_{i}" for i in range(len(embedders))]
    
    results = {}
    for embedder, name in zip(embedders, names):
        try:
            benchmark = embedder.benchmark(test_texts)
            info = embedder.get_model_info()
            results[name] = {
                "model_info": info,
                "benchmark": benchmark
            }
        except Exception as e:
            results[name] = {"error": str(e)}
    
    return results


# if __name__ == "__main__":
#     # Example usage
#     embedder = LocalLLM("all-MiniLM-L6-v2")
    
#     # Single text
#     embedding = embedder.embed("Hello, world!")
#     print(f"Single text embedding shape: {len(embedding[0])}")
    
#     # Multiple texts
#     texts = ["Hello, world!", "How are you?", "This is a test."]
#     embeddings = embedder.embed(texts)
#     print(f"Multiple texts embeddings shape: {len(embeddings)} x {len(embeddings[0])}")
    
#     # Model info
#     print("Model info:", embedder.get_model_info())
    
#     # Benchmark
#     benchmark = embedder.benchmark(texts)
#     print("Benchmark results:", benchmark)
