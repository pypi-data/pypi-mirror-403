# langxchange/llama_helper.py

import os
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from sentence_transformers import SentenceTransformer
"""
Enhanced LLaMA Helper with improved error handling, modern API usage, and additional features.
Author: Langxchange
"""

import os
import logging
import torch
from typing import List, Dict, Union, Optional, Any
from dataclasses import dataclass
from pathlib import Path

from transformers import (
    AutoTokenizer, 
    AutoModelForCausalLM, 
    pipeline,
    GenerationConfig
)
from sentence_transformers import SentenceTransformer


@dataclass
class LLaMAConfig:
    """Configuration class for LLaMA Helper settings."""
    chat_model: str = "meta-llama/Llama-2-7b-chat-hf"
    embed_model: str = "all-MiniLM-L6-v2"
    hf_token: Optional[str] = None
    device: Optional[str] = None
    max_memory_per_gpu: Optional[str] = "8GB"
    load_in_8bit: bool = False
    load_in_4bit: bool = False
    cache_dir: Optional[str] = None
    trust_remote_code: bool = False


class EnhancedLLaMAHelper:
    """
    Enhanced helper class for interacting with LLaMA models via Hugging Face.
    
    Features:
    - Modern HuggingFace API usage
    - Comprehensive error handling and logging
    - Memory management options
    - Batch processing capabilities
    - Flexible configuration
    - Proper cleanup methods
    """

    def __init__(self, config: Optional[LLaMAConfig] = None, **kwargs):
        """
        Initialize LLaMAHelper with enhanced configuration options.
        
        Args:
            config: LLaMAConfig object with settings
            **kwargs: Override config parameters
        """
        # Setup logging
        self._setup_logging()
        
        # Merge config with kwargs
        self.config = config or LLaMAConfig()
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        
        # Apply environment variable defaults
        self._apply_env_defaults()
        
        # Validate configuration
        self._validate_config()
        
        # Initialize device
        self.device = self._detect_device()
        
        # Initialize components
        self.tokenizer = None
        self.model = None
        self.generator = None
        self.embedder = None
        
        # Load models
        self._load_models()
        
        self.logger.info(f"LLaMAHelper initialized successfully on device: {self.device}")

    def _setup_logging(self) -> None:
        """Setup logging configuration."""
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def _apply_env_defaults(self) -> None:
        """Apply environment variable defaults to configuration."""
        if not self.config.chat_model:
            self.config.chat_model = os.getenv("LLAMA_CHAT_MODEL", "meta-llama/Llama-2-7b-chat-hf")
        
        if not self.config.embed_model:
            self.config.embed_model = os.getenv("LLAMA_EMBED_MODEL", "all-MiniLM-L6-v2")
        
        if not self.config.hf_token:
            self.config.hf_token = os.getenv("HUGGINGFACE_TOKEN") or os.getenv("HF_TOKEN")
        
        if not self.config.cache_dir:
            self.config.cache_dir = os.getenv("HF_CACHE_DIR")

    def _validate_config(self) -> None:
        """Validate configuration parameters."""
        if not self.config.hf_token:
            raise EnvironmentError(
                "Hugging Face token required to access gated models. "
                "Set HUGGINGFACE_TOKEN or HF_TOKEN env var or pass hf_token in config."
            )
        
        if self.config.load_in_8bit and self.config.load_in_4bit:
            raise ValueError("Cannot use both 8-bit and 4-bit quantization simultaneously.")

    def _detect_device(self) -> str:
        """Intelligently detect the best available device."""
        if self.config.device:
            return self.config.device
        
        if torch.cuda.is_available():
            device_count = torch.cuda.device_count()
            self.logger.info(f"CUDA available with {device_count} GPU(s)")
            return f"cuda:{torch.cuda.current_device()}"
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            self.logger.info("MPS (Apple Silicon) available")
            return "mps"
        else:
            self.logger.info("Using CPU")
            return "cpu"

    def _get_model_kwargs(self) -> Dict[str, Any]:
        """Get model loading arguments based on configuration."""
        kwargs = {
            "token": self.config.hf_token,  # Updated from deprecated use_auth_token
            "trust_remote_code": self.config.trust_remote_code,
        }
        
        if self.config.cache_dir:
            kwargs["cache_dir"] = self.config.cache_dir
        
        # Memory and quantization settings
        if self.device.startswith("cuda"):
            if self.config.load_in_8bit:
                kwargs["load_in_8bit"] = True
            elif self.config.load_in_4bit:
                kwargs["load_in_4bit"] = True
            else:
                kwargs["device_map"] = "auto"
                if self.config.max_memory_per_gpu:
                    kwargs["max_memory"] = {i: self.config.max_memory_per_gpu 
                                          for i in range(torch.cuda.device_count())}
        
        return kwargs

    def _load_models(self) -> None:
        """Load tokenizer, model, and embedder with enhanced error handling."""
        try:
            self.logger.info(f"Loading chat model: {self.config.chat_model}")
            
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.config.chat_model,
                token=self.config.hf_token,
                cache_dir=self.config.cache_dir
            )
            
            # Add padding token if missing
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            # Load model
            model_kwargs = self._get_model_kwargs()
            self.model = AutoModelForCausalLM.from_pretrained(
                self.config.chat_model,
                **model_kwargs
            )
            
            # Create pipeline
            self.generator = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if self.device.startswith("cuda") else -1,
                token=self.config.hf_token
            )
            
            # Load embedding model
            self.logger.info(f"Loading embedding model: {self.config.embed_model}")
            self.embedder = SentenceTransformer(
                self.config.embed_model,
                device=self.device,
                cache_folder=self.config.cache_dir
            )
            
        except Exception as e:
            self.logger.error(f"Failed to load models: {e}")
            raise RuntimeError(f"Model loading failed: {e}")

    def generate_text(
        self,
        prompt: str,
        max_length: int = 256,
        max_new_tokens: Optional[int] = None,
        temperature: float = 0.7,
        do_sample: bool = True,
        top_p: float = 0.9,
        top_k: int = 50,
        repetition_penalty: float = 1.1,
        pad_token_id: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Generate text with enhanced parameters and error handling.
        
        Args:
            prompt: Input text prompt
            max_length: Maximum total length (deprecated, use max_new_tokens)
            max_new_tokens: Maximum new tokens to generate
            temperature: Sampling temperature
            do_sample: Whether to use sampling
            top_p: Top-p sampling parameter
            top_k: Top-k sampling parameter
            repetition_penalty: Repetition penalty
            pad_token_id: Padding token ID
            **kwargs: Additional generation parameters
            
        Returns:
            Generated text string
        """
        if not self.generator:
            raise RuntimeError("Model not loaded. Call _load_models() first.")
        
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("Prompt must be a non-empty string.")
        
        try:
            # Use max_new_tokens if provided, otherwise fallback to max_length
            generation_kwargs = {
                "do_sample": do_sample,
                "temperature": temperature if do_sample else None,
                "top_p": top_p if do_sample else None,
                "top_k": top_k if do_sample else None,
                "repetition_penalty": repetition_penalty,
                "return_full_text": False,
                "pad_token_id": pad_token_id or self.tokenizer.pad_token_id,
                **kwargs
            }
            
            if max_new_tokens is not None:
                generation_kwargs["max_new_tokens"] = max_new_tokens
            else:
                generation_kwargs["max_length"] = max_length
            
            # Remove None values
            generation_kwargs = {k: v for k, v in generation_kwargs.items() if v is not None}
            
            results = self.generator(prompt, **generation_kwargs)
            return results[0]["generated_text"].strip()
            
        except Exception as e:
            self.logger.error(f"Text generation failed: {e}")
            raise RuntimeError(f"Failed to generate text: {e}")

    def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        max_new_tokens: int = 256,
        temperature: float = 0.7,
        do_sample: bool = True,
        **kwargs
    ) -> str:
        """
        Enhanced chat functionality with proper message formatting.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            system_prompt: Optional system prompt to prepend
            max_new_tokens: Maximum new tokens to generate
            temperature: Sampling temperature
            do_sample: Whether to use sampling
            **kwargs: Additional generation parameters
            
        Returns:
            Assistant response string
        """
        if not isinstance(messages, list) or not messages:
            raise ValueError("Messages must be a non-empty list of dictionaries.")
        
        try:
            # Build conversation prompt
            prompt_parts = []
            
            # Add system prompt if provided
            if system_prompt:
                prompt_parts.append(f"<s>[INST] <<SYS>>\n{system_prompt}\n<</SYS>>")
            
            # Format messages for LLaMA chat format
            for i, msg in enumerate(messages):
                if not isinstance(msg, dict) or 'role' not in msg or 'content' not in msg:
                    raise ValueError(f"Message {i} must have 'role' and 'content' keys.")
                
                role = msg["role"].lower()
                content = msg["content"].strip()
                
                if not content:
                    continue
                
                if role == "user":
                    if i == 0 and not system_prompt:
                        prompt_parts.append(f"<s>[INST] {content} [/INST]")
                    else:
                        prompt_parts.append(f"<s>[INST] {content} [/INST]")
                elif role == "assistant":
                    prompt_parts.append(f" {content} </s>")
                elif role == "system":
                    # System messages are handled separately
                    continue
            
            # Ensure proper format
            if not prompt_parts[-1].endswith("[/INST]"):
                prompt_parts.append("")  # Prepare for assistant response
            
            prompt = "".join(prompt_parts)
            
            return self.generate_text(
                prompt=prompt,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                do_sample=do_sample,
                **kwargs
            )
            
        except Exception as e:
            self.logger.error(f"Chat generation failed: {e}")
            raise RuntimeError(f"Failed to generate chat response: {e}")

    def get_embedding(self, text: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """
        Generate embeddings for text(s) with batch support.
        
        Args:
            text: Single text string or list of texts
            
        Returns:
            Single embedding list or list of embedding lists
        """
        if not self.embedder:
            raise RuntimeError("Embedding model not loaded.")
        
        if isinstance(text, str):
            if not text.strip():
                raise ValueError("Text cannot be empty.")
        elif isinstance(text, list):
            if not text or not all(isinstance(t, str) and t.strip() for t in text):
                raise ValueError("All texts must be non-empty strings.")
        else:
            raise ValueError("Text must be a string or list of strings.")
        
        try:
            embeddings = self.embedder.encode(text, convert_to_tensor=False)
            
            if isinstance(text, str):
                return embeddings.tolist() if hasattr(embeddings, "tolist") else list(embeddings)
            else:
                return [emb.tolist() if hasattr(emb, "tolist") else list(emb) for emb in embeddings]
                
        except Exception as e:
            self.logger.error(f"Embedding generation failed: {e}")
            raise RuntimeError(f"Failed to generate embeddings: {e}")

    def count_tokens(self, text: Union[str, List[str]]) -> Union[int, List[int]]:
        """
        Count tokens in text(s) with batch support.
        
        Args:
            text: Single text string or list of texts
            
        Returns:
            Token count(s)
        """
        if not self.tokenizer:
            raise RuntimeError("Tokenizer not loaded.")
        
        if isinstance(text, str):
            if not text.strip():
                return 0
            return len(self.tokenizer.encode(text, add_special_tokens=True))
        elif isinstance(text, list):
            return [len(self.tokenizer.encode(t, add_special_tokens=True)) if t.strip() else 0 for t in text]
        else:
            raise ValueError("Text must be a string or list of strings.")

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about loaded models."""
        return {
            "chat_model": self.config.chat_model,
            "embed_model": self.config.embed_model,
            "device": self.device,
            "vocab_size": self.tokenizer.vocab_size if self.tokenizer else None,
            "model_parameters": sum(p.numel() for p in self.model.parameters()) if self.model else None,
            "model_dtype": str(next(self.model.parameters()).dtype) if self.model else None,
        }

    def clear_cache(self) -> None:
        """Clear GPU memory cache if using CUDA."""
        if self.device.startswith("cuda"):
            torch.cuda.empty_cache()
            self.logger.info("GPU cache cleared")

    def cleanup(self) -> None:
        """Clean up resources and free memory."""
        try:
            if hasattr(self, 'model') and self.model:
                del self.model
            if hasattr(self, 'generator') and self.generator:
                del self.generator
            if hasattr(self, 'embedder') and self.embedder:
                del self.embedder
            if hasattr(self, 'tokenizer') and self.tokenizer:
                del self.tokenizer
            
            self.clear_cache()
            self.logger.info("Resources cleaned up successfully")
            
        except Exception as e:
            self.logger.error(f"Cleanup failed: {e}")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.cleanup()

    def __del__(self):
        """Destructor with cleanup."""
        try:
            self.cleanup()
        except:
            pass  # Ignore errors during destruction


# Example usage and factory functions
def create_llama_helper(
    model_size: str = "7b",
    quantization: Optional[str] = None,
    **kwargs
) -> EnhancedLLaMAHelper:
    """
    Factory function to create LLaMAHelper with common configurations.
    
    Args:
        model_size: "7b", "13b", or "70b"
        quantization: "8bit", "4bit", or None
        **kwargs: Additional configuration parameters
        
    Returns:
        Configured LLaMAHelper instance
    """
    model_map = {
        "7b": "meta-llama/Llama-2-7b-chat-hf",
        "13b": "meta-llama/Llama-2-13b-chat-hf",
        "70b": "meta-llama/Llama-2-70b-chat-hf",
    }
    
    config = LLaMAConfig(
        chat_model=model_map.get(model_size, model_map["7b"]),
        load_in_8bit=quantization == "8bit",
        load_in_4bit=quantization == "4bit",
        **kwargs
    )
    
    return EnhancedLLaMAHelper(config)


# if __name__ == "__main__":
#     # Example usage
#     try:
#         # Create helper with context manager for automatic cleanup
#         with create_llama_helper(model_size="7b", quantization="8bit") as helper:
            
#             # Simple text generation
#             response = helper.generate_text("What is artificial intelligence?", max_new_tokens=100)
#             print("Generated text:", response)
            
#             # Chat conversation
#             messages = [
#                 {"role": "user", "content": "Hello, how are you?"},
#                 {"role": "assistant", "content": "I'm doing well, thank you! How can I help you today?"},
#                 {"role": "user", "content": "Can you explain quantum computing?"}
#             ]
            
#             chat_response = helper.chat(messages, max_new_tokens=150)
#             print("Chat response:", chat_response)
            
#             # Embeddings
#             embeddings = helper.get_embedding(["Hello world", "Goodbye world"])
#             print("Embedding dimensions:", len(embeddings[0]))
            
#             # Token counting
#             token_count = helper.count_tokens("This is a test sentence.")
#             print("Token count:", token_count)
            
#             # Model info
#             info = helper.get_model_info()
#             print("Model info:", info)
            
#     except Exception as e:
#         print(f"Error: {e}")


#Existing LLamaHelper Class
class LLaMAHelper:
    """
    Helper class for interacting with LLaMA chat and embeddings via Hugging Face.
    """

    def __init__(
        self,
        chat_model: str = None,
        embed_model: str = None,
        hf_token: str = None,
        device: str = None
    ):
        """
        chat_model: HF model name for chat (e.g. "meta-llama/Llama-2-7b-chat-hf")
        embed_model: SentenceTransformer model name for embeddings
        hf_token: Hugging Face access token (or set HUGGINGFACE_TOKEN env var)
        device: "cpu" or "cuda" (auto-detected if None)
        """
        self.chat_model_name = chat_model or os.getenv(
            "LLAMA_CHAT_MODEL",
            "meta-llama/Llama-2-7b-chat-hf"
        )
        self.embed_model_name = embed_model or os.getenv(
            "LLAMA_EMBED_MODEL",
            "all-MiniLM-L6-v2"
        )

        # pick up token from param or env
        self.hf_token = hf_token or os.getenv("HUGGINGFACE_TOKEN")
        if not self.hf_token:
            raise EnvironmentError(
                "Hugging Face token required to access gated models. "
                "Set HUGGINGFACE_TOKEN env var or pass hf_token."
            )

        # Determine device
        self.device = device or ("cuda" if os.getenv("CUDA_VISIBLE_DEVICES") else "cpu")

        # Load tokenizer and model with the access token
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.chat_model_name,
            use_auth_token=self.hf_token
        )
        self.model = AutoModelForCausalLM.from_pretrained(
            self.chat_model_name,
            use_auth_token=self.hf_token,
            device_map="auto" if self.device.startswith("cuda") else None
        )
        self.generator = pipeline(
            "text-generation",
            model=self.model,
            tokenizer=self.tokenizer,
            device=0 if self.device.startswith("cuda") else -1,
            use_auth_token=self.hf_token
        )

        # Embedding model (public)
        self.embedder = SentenceTransformer(
            self.embed_model_name,
            device=self.device
        )

    def generate_text(
        self,
        prompt: str,
        max_length: int = 256,
        temperature: float = 0.7,
        do_sample: bool = True,
    ) -> str:
        try:
            results = self.generator(
                prompt,
                max_length=max_length,
                do_sample=do_sample,
                temperature=temperature,
                return_full_text=False
            )
            return results[0]["generated_text"]
        except Exception as e:
            raise RuntimeError(f"[❌ ERROR] Failed to generate text: {e}")

    def chat(
        self,
        messages: list,
        max_length: int = 256,
        temperature: float = 0.7,
        do_sample: bool = True,
    ) -> str:
        prompt_parts = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            tag = role.upper()
            prompt_parts.append(f"[{tag}]\n{content}\n")
        prompt = "\n".join(prompt_parts) + "[ASSISTANT]\n"

        return self.generate_text(
            prompt=prompt,
            max_length=max_length,
            temperature=temperature,
            do_sample=do_sample
        )

    def get_embedding(self, text: str) -> list:
        try:
            emb = self.embedder.encode(text)
            return emb.tolist() if hasattr(emb, "tolist") else list(emb)
        except Exception as e:
            raise RuntimeError(f"[❌ ERROR] Failed to generate embedding: {e}")

    def count_tokens(self, prompt: str) -> int:
        return len(self.tokenizer.tokenize(prompt))
