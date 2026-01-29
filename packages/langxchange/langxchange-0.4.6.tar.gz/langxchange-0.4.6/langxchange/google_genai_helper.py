# langxchange/google_genai_helper.py

import os
from google import genai
from google.genai import types
"""
Enhanced Google GenAI Helper with vision, speech, context management, and usage tracking.
"""

import os
import logging
import io
import wave
import time
from datetime import datetime
from typing import List, Dict, Any, Optional, Union, Tuple
from dataclasses import dataclass, field
from google import genai
from google.genai import types


class GoogleGenAIError(Exception):
    """Custom exception for Google GenAI operations."""
    pass


@dataclass
class UsageStats:
    """Track API usage statistics."""
    chat_requests: int = 0
    vision_requests: int = 0
    tts_requests: int = 0
    stt_requests: int = 0
    embedding_requests: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_audio_seconds: float = 0.0
    total_images_processed: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    error_count: int = 0
    request_history: List[Dict[str, Any]] = field(default_factory=list)
    
    def add_request(self, request_type: str, input_tokens: int = 0, output_tokens: int = 0, 
                   audio_seconds: float = 0.0, images: int = 0, success: bool = True):
        """Add a request to usage statistics."""
        if request_type == "chat":
            self.chat_requests += 1
        elif request_type == "vision":
            self.vision_requests += 1
        elif request_type == "tts":
            self.tts_requests += 1
        elif request_type == "stt":
            self.stt_requests += 1
        elif request_type == "embedding":
            self.embedding_requests += 1
        
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.total_audio_seconds += audio_seconds
        self.total_images_processed += images
        
        if not success:
            self.error_count += 1
        
        self.request_history.append({
            "timestamp": datetime.now().isoformat(),
            "type": request_type,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "audio_seconds": audio_seconds,
            "images": images,
            "success": success
        })


@dataclass
class ContextCache:
    """Manage context caching for cost optimization."""
    cache_id: Optional[str] = None
    cached_content: Optional[str] = None
    cache_timestamp: Optional[datetime] = None
    cache_ttl_hours: int = 24
    
    def is_valid(self) -> bool:
        """Check if cache is still valid."""
        if not self.cache_timestamp:
            return False
        age_hours = (datetime.now() - self.cache_timestamp).total_seconds() / 3600
        return age_hours < self.cache_ttl_hours


class EnhancedGoogleGenAIHelper:
    """
    Enhanced helper class for interacting with Google Gemini via the `google-genai` client.
    
    Features:
    - Multi-modal chat with vision
    - Text-to-speech generation
    - Speech-to-text transcription
    - Context length management
    - Usage statistics tracking
    """

    # Default models
    DEFAULT_CHAT_MODEL = "gemini-2.5-flash"
    DEFAULT_VISION_MODEL = "gemini-2.5-flash"
    DEFAULT_TTS_MODEL = "gemini-2.5-flash-preview-tts"
    DEFAULT_STT_MODEL = "gemini-2.5-flash"
    DEFAULT_EMBED_MODEL = "models/text-embedding-004"
    
    # Token estimation and limits
    TOKEN_WORD_RATIO = 0.75
    AUDIO_TOKENS_PER_SECOND = 32
    MAX_CONTEXT_TOKENS = 2_000_000  # Gemini 2.5 Pro context limit
    
    # Supported formats
    SUPPORTED_IMAGE_FORMATS = {"image/png", "image/jpeg", "image/webp", "image/heic", "image/heif"}
    SUPPORTED_AUDIO_FORMATS = {"audio/wav", "audio/mp3", "audio/aiff", "audio/aac", "audio/ogg", "audio/flac"}
    
    # Available TTS voices
    TTS_VOICES = [
        "Zephyr", "Puck", "Charon", "Kore", "Fenrir", "Leda", "Orus", "Aoede",
        "Callirrhoe", "Autonoe", "Enceladus", "Iapetus", "Umbriel", "Algieba",
        "Despina", "Erinome", "Algenib", "Rasalgethi", "Laomedeia", "Achernar",
        "Alnilam", "Schedar", "Gacrux", "Pulcherrima", "Achird", "Zubenelgenubi",
        "Vindemiatrix", "Sadachbia", "Sadaltager", "Sulafat"
    ]

    def __init__(
        self,
        api_key: Optional[str] = None,
        chat_model: Optional[str] = None,
        vision_model: Optional[str] = None,
        tts_model: Optional[str] = None,
        stt_model: Optional[str] = None,
        embed_model: Optional[str] = None,
        logger: Optional[logging.Logger] = None,
        enable_usage_tracking: bool = True,
        enable_context_caching: bool = True,
    ) -> None:
        """
        Initialize the Enhanced Google GenAI Helper.

        Args:
            api_key: Your Google API key (or use GOOGLE_API_KEY env var)
            chat_model: The Gemini chat model name
            vision_model: The Gemini vision model name
            tts_model: The text-to-speech model name
            stt_model: The speech-to-text model name
            embed_model: The embedding model name
            logger: Optional logger instance for debugging
            enable_usage_tracking: Track API usage statistics
            enable_context_caching: Enable context caching for cost optimization

        Raises:
            GoogleGenAIError: If API key is not provided or invalid
        """
        self.logger = logger or logging.getLogger(__name__)
        
        # Get API key from parameter or environment
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise GoogleGenAIError(
                "Google API key is required. Please provide it as a parameter "
                "or set the GOOGLE_API_KEY environment variable."
            )

        try:
            # Initialize the client
            self.client = genai.Client(api_key=self.api_key)
            self.logger.info("Google GenAI client initialized successfully")
        except Exception as e:
            raise GoogleGenAIError(f"Failed to initialize Google GenAI client: {str(e)}")
        
        # Set model names with fallbacks
        self.chat_model = chat_model or os.getenv("GOOGLE_CHAT_MODEL") or self.DEFAULT_CHAT_MODEL
        self.vision_model = vision_model or os.getenv("GOOGLE_VISION_MODEL") or self.DEFAULT_VISION_MODEL
        self.tts_model = tts_model or os.getenv("GOOGLE_TTS_MODEL") or self.DEFAULT_TTS_MODEL
        self.stt_model = stt_model or os.getenv("GOOGLE_STT_MODEL") or self.DEFAULT_STT_MODEL
        self.embed_model = embed_model or os.getenv("GOOGLE_EMBED_MODEL") or self.DEFAULT_EMBED_MODEL
        
        # Initialize tracking and caching
        self.usage_stats = UsageStats() if enable_usage_tracking else None
        self.context_cache = ContextCache() if enable_context_caching else None
        
        self.logger.info(f"Enhanced Google GenAI Helper initialized with models: "
                        f"chat={self.chat_model}, vision={self.vision_model}, "
                        f"tts={self.tts_model}, stt={self.stt_model}")

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        model: Optional[str] = None,
    ) -> str:
        """
        Perform a chat-style completion using Gemini.

        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens to generate
            model: Optional model override

        Returns:
            The assistant's reply text

        Raises:
            GoogleGenAIError: If the API call fails or returns invalid response
        """
        start_time = time.time()
        success = False
        input_tokens = 0
        output_tokens = 0
        
        try:
            if not messages:
                raise GoogleGenAIError("Messages list cannot be empty")
            
            # Validate parameters
            self._validate_temperature(temperature)
            self._validate_max_tokens(max_tokens)
            self._validate_messages(messages)
            
            # Estimate input tokens
            input_text = " ".join(msg["content"] for msg in messages)
            input_tokens = self.count_tokens(input_text)
            
            # Check context limits
            self._check_context_limits(input_tokens, max_tokens)
            
            # Build contents for the API
            contents = self._format_messages_for_api(messages)
            
            # Use provided model or default
            model_name = model or self.chat_model
            
            # Create configuration
            config = types.GenerateContentConfig(
                max_output_tokens=max_tokens,
                temperature=temperature,
            )
            
            self.logger.debug(f"Sending chat request to model: {model_name}")
            
            # Make API call
            response = self.client.models.generate_content(
                model=model_name,
                contents=contents,
                config=config,
            )
            
            if not hasattr(response, 'text') or not response.text:
                raise GoogleGenAIError("Received empty response from API")
            
            # Estimate output tokens
            output_tokens = self.count_tokens(response.text)
            success = True
            
            self.logger.debug("Chat completion successful")
            return response.text.strip()
            
        except Exception as e:
            if isinstance(e, GoogleGenAIError):
                raise
            raise GoogleGenAIError(f"Chat completion failed: {str(e)}")
        finally:
            # Track usage if enabled
            if self.usage_stats:
                self.usage_stats.add_request(
                    "chat", input_tokens, output_tokens, success=success
                )

    def chat_with_vision(
        self,
        text: str,
        images: List[Union[str, bytes]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        model: Optional[str] = None,
        image_detail: str = "auto",
    ) -> str:
        """
        Perform a chat completion with image understanding.

        Args:
            text: Text prompt/question about the images
            images: List of image paths (str) or image bytes
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens to generate
            model: Optional model override
            image_detail: Image processing detail level

        Returns:
            The assistant's reply text

        Raises:
            GoogleGenAIError: If the API call fails or returns invalid response
        """
        start_time = time.time()
        success = False
        input_tokens = 0
        output_tokens = 0
        image_count = len(images)
        
        try:
            if not text.strip():
                raise GoogleGenAIError("Text prompt cannot be empty")
            
            if not images:
                raise GoogleGenAIError("Images list cannot be empty")
            
            # Validate parameters
            self._validate_temperature(temperature)
            self._validate_max_tokens(max_tokens)
            
            # Process images
            image_parts = []
            for i, image in enumerate(images):
                if isinstance(image, str):
                    # Image path
                    if not os.path.exists(image):
                        raise GoogleGenAIError(f"Image file not found: {image}")
                    
                    mime_type = self._get_image_mime_type(image)
                    with open(image, 'rb') as f:
                        image_data = f.read()
                else:
                    # Image bytes
                    image_data = image
                    mime_type = "image/jpeg"  # Default, should ideally detect
                
                image_parts.append(types.Part.from_bytes(
                    data=image_data,
                    mime_type=mime_type
                ))
            
            # Estimate tokens (text + images)
            input_tokens = self.count_tokens(text)
            # Each image costs approximately 258 tokens minimum
            input_tokens += len(images) * 258
            
            # Check context limits
            self._check_context_limits(input_tokens, max_tokens)
            
            # Build contents
            contents = [text] + image_parts
            
            # Use provided model or default
            model_name = model or self.vision_model
            
            # Create configuration
            config = types.GenerateContentConfig(
                max_output_tokens=max_tokens,
                temperature=temperature,
            )
            
            self.logger.debug(f"Sending vision chat request to model: {model_name} with {len(images)} images")
            
            # Make API call
            response = self.client.models.generate_content(
                model=model_name,
                contents=contents,
                config=config,
            )
            
            if not hasattr(response, 'text') or not response.text:
                raise GoogleGenAIError("Received empty response from API")
            
            # Estimate output tokens
            output_tokens = self.count_tokens(response.text)
            success = True
            
            self.logger.debug("Vision chat completion successful")
            return response.text.strip()
            
        except Exception as e:
            if isinstance(e, GoogleGenAIError):
                raise
            raise GoogleGenAIError(f"Vision chat completion failed: {str(e)}")
        finally:
            # Track usage if enabled
            if self.usage_stats:
                self.usage_stats.add_request(
                    "vision", input_tokens, output_tokens, 
                    images=image_count, success=success
                )

    def text_to_speech(
        self,
        text: str,
        voice_name: str = "Kore",
        output_file: Optional[str] = None,
        model: Optional[str] = None,
        style_prompt: Optional[str] = None,
    ) -> Union[bytes, str]:
        """
        Convert text to speech using Gemini TTS.

        Args:
            text: Text to convert to speech
            voice_name: Voice to use (see TTS_VOICES for options)
            output_file: Optional file path to save audio (.wav)
            model: Optional model override
            style_prompt: Optional style instructions (e.g., "Say cheerfully:")

        Returns:
            Audio bytes if no output_file, otherwise path to saved file

        Raises:
            GoogleGenAIError: If the API call fails or returns invalid response
        """
        start_time = time.time()
        success = False
        input_tokens = 0
        audio_seconds = 0.0
        
        try:
            if not text.strip():
                raise GoogleGenAIError("Text cannot be empty")
            
            if voice_name not in self.TTS_VOICES:
                raise GoogleGenAIError(f"Voice '{voice_name}' not supported. "
                                     f"Available voices: {', '.join(self.TTS_VOICES)}")
            
            # Prepare content with optional style
            if style_prompt:
                content = f"{style_prompt} {text}"
            else:
                content = text
            
            # Estimate tokens
            input_tokens = self.count_tokens(content)
            
            # Use provided model or default
            model_name = model or self.tts_model
            
            # Create speech configuration
            config = types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=voice_name,
                        ),
                    ),
                ),
            )
            
            self.logger.debug(f"Generating speech with voice: {voice_name}")
            
            # Make API call
            response = self.client.models.generate_content(
                model=model_name,
                contents=content,
                config=config,
            )
            
            if not (hasattr(response, 'candidates') and response.candidates and
                   hasattr(response.candidates[0], 'content') and
                   response.candidates[0].content.parts):
                raise GoogleGenAIError("Received empty audio response from API")
            
            audio_data = response.candidates[0].content.parts[0].inline_data.data
            
            # Estimate audio duration (rough approximation: 150 words per minute)
            word_count = len(content.split())
            audio_seconds = (word_count / 150) * 60
            
            if output_file:
                # Save as WAV file
                self._save_wave_file(output_file, audio_data)
                success = True
                self.logger.debug(f"Audio saved to: {output_file}")
                return output_file
            else:
                success = True
                return audio_data
                
        except Exception as e:
            if isinstance(e, GoogleGenAIError):
                raise
            raise GoogleGenAIError(f"Text-to-speech failed: {str(e)}")
        finally:
            # Track usage if enabled
            if self.usage_stats:
                self.usage_stats.add_request(
                    "tts", input_tokens, 0, audio_seconds=audio_seconds, success=success
                )

    def speech_to_text(
        self,
        audio_file: Union[str, bytes],
        prompt: str = "Generate a transcript of the speech.",
        model: Optional[str] = None,
        timestamp_format: bool = False,
    ) -> str:
        """
        Convert speech to text using Gemini audio understanding.

        Args:
            audio_file: Path to audio file or audio bytes
            prompt: Instruction prompt for transcription
            model: Optional model override
            timestamp_format: Include timestamps in transcript

        Returns:
            Transcribed text

        Raises:
            GoogleGenAIError: If the API call fails or returns invalid response
        """
        start_time = time.time()
        success = False
        input_tokens = 0
        output_tokens = 0
        audio_seconds = 0.0
        
        try:
            if not prompt.strip():
                raise GoogleGenAIError("Prompt cannot be empty")
            
            # Process audio file
            if isinstance(audio_file, str):
                # Audio file path
                if not os.path.exists(audio_file):
                    raise GoogleGenAIError(f"Audio file not found: {audio_file}")
                
                # Upload file for processing
                uploaded_file = self.client.files.upload(file=audio_file)
                audio_part = uploaded_file
                
                # Estimate audio duration and tokens
                audio_seconds = self._estimate_audio_duration(audio_file)
                
            else:
                # Audio bytes - use inline data
                audio_part = types.Part.from_bytes(
                    data=audio_file,
                    mime_type="audio/wav"  # Default, should ideally detect
                )
                # Can't easily estimate duration from bytes
                audio_seconds = 60.0  # Default estimate
            
            # Calculate tokens (audio + prompt)
            input_tokens = self.count_tokens(prompt)
            input_tokens += int(audio_seconds * self.AUDIO_TOKENS_PER_SECOND)
            
            # Enhance prompt for timestamps if requested
            if timestamp_format:
                prompt = f"{prompt} Include timestamps in MM:SS format."
            
            # Use provided model or default
            model_name = model or self.stt_model
            
            self.logger.debug(f"Transcribing audio with model: {model_name}")
            
            # Make API call
            response = self.client.models.generate_content(
                model=model_name,
                contents=[prompt, audio_part],
            )
            
            if not hasattr(response, 'text') or not response.text:
                raise GoogleGenAIError("Received empty transcription response from API")
            
            # Estimate output tokens
            output_tokens = self.count_tokens(response.text)
            success = True
            
            self.logger.debug("Speech-to-text conversion successful")
            return response.text.strip()
            
        except Exception as e:
            if isinstance(e, GoogleGenAIError):
                raise
            raise GoogleGenAIError(f"Speech-to-text failed: {str(e)}")
        finally:
            # Track usage if enabled
            if self.usage_stats:
                self.usage_stats.add_request(
                    "stt", input_tokens, output_tokens, 
                    audio_seconds=audio_seconds, success=success
                )

    def manage_context_length(
        self,
        content: str,
        max_context_tokens: Optional[int] = None,
        strategy: str = "truncate",
        preserve_recent: bool = True,
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Manage content to fit within context length limits.

        Args:
            content: Content to manage
            max_context_tokens: Maximum tokens allowed (default: model limit)
            strategy: Management strategy ("truncate", "summarize", "cache")
            preserve_recent: Keep most recent content when truncating

        Returns:
            Tuple of (managed_content, management_info)

        Raises:
            GoogleGenAIError: If content management fails
        """
        try:
            max_tokens = max_context_tokens or self.MAX_CONTEXT_TOKENS
            current_tokens = self.count_tokens(content)
            
            management_info = {
                "original_tokens": current_tokens,
                "max_tokens": max_tokens,
                "strategy_used": strategy,
                "tokens_saved": 0,
                "cache_used": False
            }
            
            # Check if content fits within limits
            if current_tokens <= max_tokens:
                self.logger.debug(f"Content fits within limits: {current_tokens}/{max_tokens} tokens")
                return content, management_info
            
            self.logger.info(f"Content exceeds limit: {current_tokens}/{max_tokens} tokens. "
                           f"Applying strategy: {strategy}")
            
            if strategy == "cache" and self.context_cache:
                # Try to use cached content
                if self.context_cache.is_valid() and self.context_cache.cached_content:
                    if self.usage_stats:
                        self.usage_stats.cache_hits += 1
                    management_info["cache_used"] = True
                    self.logger.debug("Using cached content")
                    return self.context_cache.cached_content, management_info
                else:
                    if self.usage_stats:
                        self.usage_stats.cache_misses += 1
            
            if strategy == "truncate":
                # Truncate content to fit
                words = content.split()
                target_words = int(max_tokens * self.TOKEN_WORD_RATIO * 0.9)  # 90% safety margin
                
                if preserve_recent:
                    # Keep the last N words
                    managed_content = " ".join(words[-target_words:])
                else:
                    # Keep the first N words
                    managed_content = " ".join(words[:target_words])
                
                tokens_saved = current_tokens - self.count_tokens(managed_content)
                management_info["tokens_saved"] = tokens_saved
                
            elif strategy == "summarize":
                # Use the model to summarize content
                summary_prompt = f"Summarize the following content in approximately {max_tokens // 4} tokens:\n\n{content}"
                managed_content = self.chat([{"role": "user", "content": summary_prompt}])
                tokens_saved = current_tokens - self.count_tokens(managed_content)
                management_info["tokens_saved"] = tokens_saved
                
            else:
                raise GoogleGenAIError(f"Unknown strategy: {strategy}")
            
            # Update cache if enabled
            if strategy == "cache" and self.context_cache:
                self.context_cache.cached_content = managed_content
                self.context_cache.cache_timestamp = datetime.now()
            
            final_tokens = self.count_tokens(managed_content)
            self.logger.info(f"Context management complete: {current_tokens} -> {final_tokens} tokens")
            
            return managed_content, management_info
            
        except Exception as e:
            if isinstance(e, GoogleGenAIError):
                raise
            raise GoogleGenAIError(f"Context management failed: {str(e)}")

    def get_usage_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive usage statistics.

        Returns:
            Dictionary with usage statistics and insights

        Raises:
            GoogleGenAIError: If usage tracking is disabled
        """
        if not self.usage_stats:
            raise GoogleGenAIError("Usage tracking is disabled. Enable it during initialization.")
        
        stats = self.usage_stats
        total_requests = (stats.chat_requests + stats.vision_requests + 
                         stats.tts_requests + stats.stt_requests + stats.embedding_requests)
        
        # Calculate success rate
        success_rate = ((total_requests - stats.error_count) / total_requests * 100) if total_requests > 0 else 0
        
        # Estimate costs (approximate, based on token usage)
        estimated_cost = self._estimate_costs(stats)
        
        # Cache efficiency
        cache_efficiency = 0
        if stats.cache_hits + stats.cache_misses > 0:
            cache_efficiency = stats.cache_hits / (stats.cache_hits + stats.cache_misses) * 100
        
        return {
            "summary": {
                "total_requests": total_requests,
                "success_rate": round(success_rate, 2),
                "total_input_tokens": stats.total_input_tokens,
                "total_output_tokens": stats.total_output_tokens,
                "total_audio_seconds": round(stats.total_audio_seconds, 2),
                "total_images_processed": stats.total_images_processed,
                "estimated_cost_usd": round(estimated_cost, 4),
            },
            "by_feature": {
                "chat_requests": stats.chat_requests,
                "vision_requests": stats.vision_requests,
                "tts_requests": stats.tts_requests,
                "stt_requests": stats.stt_requests,
                "embedding_requests": stats.embedding_requests,
            },
            "performance": {
                "error_count": stats.error_count,
                "success_rate": f"{success_rate:.2f}%",
                "cache_hits": stats.cache_hits,
                "cache_misses": stats.cache_misses,
                "cache_efficiency": f"{cache_efficiency:.2f}%",
            },
            "recent_requests": stats.request_history[-10:],  # Last 10 requests
            "client_info": self.get_client_info()
        }

    def reset_usage_stats(self) -> None:
        """Reset usage statistics."""
        if self.usage_stats:
            self.usage_stats = UsageStats()
            self.logger.info("Usage statistics reset")

    def get_embedding(
        self, 
        text: str, 
        task_type: str = "retrieval_document",
        title: Optional[str] = None,
        model: Optional[str] = None,
    ) -> List[float]:
        """
        Generate an embedding vector for the given text.
        (Enhanced version of the original method with usage tracking)
        """
        start_time = time.time()
        success = False
        input_tokens = 0
        
        try:
            if not text.strip():
                raise GoogleGenAIError("Text cannot be empty")

            # Estimate tokens
            input_tokens = self.count_tokens(text)
            
            # Use provided model or default
            model_name = model or self.embed_model
            
            # Create configuration
            config_params = {"task_type": task_type}
            if title:
                config_params["title"] = title
            
            config = types.EmbedContentConfig(**config_params)
            
            self.logger.debug(f"Generating embedding with model: {model_name}")
            
            # Make API call
            result = self.client.models.embed_content(
                model=model_name,
                contents=text,
                config=config,
            )
            
            # Validate response
            if not hasattr(result, 'embeddings') or not result.embeddings:
                raise GoogleGenAIError("Received empty embeddings response")
            
            embedding = result.embeddings[0]
            if not hasattr(embedding, 'values') or not embedding.values:
                raise GoogleGenAIError("Invalid embedding format in response")
            
            success = True
            self.logger.debug("Embedding generation successful")
            return list(embedding.values)
            
        except Exception as e:
            if isinstance(e, GoogleGenAIError):
                raise
            raise GoogleGenAIError(f"Embedding generation failed: {str(e)}")
        finally:
            # Track usage if enabled
            if self.usage_stats:
                self.usage_stats.add_request(
                    "embedding", input_tokens, 0, success=success
                )

    # Helper methods
    def _validate_temperature(self, temperature: float) -> None:
        """Validate temperature parameter."""
        if not 0.0 <= temperature <= 2.0:
            raise GoogleGenAIError("Temperature must be between 0.0 and 2.0")

    def _validate_max_tokens(self, max_tokens: int) -> None:
        """Validate max_tokens parameter."""
        if max_tokens < 1:
            raise GoogleGenAIError("max_tokens must be positive")

    def _check_context_limits(self, input_tokens: int, output_tokens: int) -> None:
        """Check if the request fits within context limits."""
        total_tokens = input_tokens + output_tokens
        if total_tokens > self.MAX_CONTEXT_TOKENS:
            raise GoogleGenAIError(
                f"Request exceeds context limit: {total_tokens} > {self.MAX_CONTEXT_TOKENS} tokens. "
                f"Consider using context management."
            )

    def _get_image_mime_type(self, image_path: str) -> str:
        """Get MIME type for image file."""
        ext = os.path.splitext(image_path)[1].lower()
        mime_map = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.webp': 'image/webp',
            '.heic': 'image/heic',
            '.heif': 'image/heif',
        }
        return mime_map.get(ext, 'image/jpeg')

    def _save_wave_file(self, filename: str, audio_data: bytes, 
                       channels: int = 1, rate: int = 24000, sample_width: int = 2) -> None:
        """Save audio data as WAV file."""
        with wave.open(filename, "wb") as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(sample_width)
            wf.setframerate(rate)
            wf.writeframes(audio_data)

    def _estimate_audio_duration(self, audio_file: str) -> float:
        """Estimate audio duration in seconds."""
        try:
            # Try to read as WAV file
            with wave.open(audio_file, 'rb') as wf:
                frames = wf.getnframes()
                rate = wf.getframerate()
                return frames / rate
        except:
            # Fallback to file size estimation (very rough)
            file_size = os.path.getsize(audio_file)
            # Assume ~16kbps for compressed audio
            return file_size / (16000 / 8)

    def _estimate_costs(self, stats: UsageStats) -> float:
        """Estimate API costs based on usage (approximate)."""
        # These are rough estimates based on typical pricing
        # Actual costs may vary
        input_cost = stats.total_input_tokens * 0.000001  # $1 per 1M tokens
        output_cost = stats.total_output_tokens * 0.000002  # $2 per 1M tokens
        audio_cost = stats.total_audio_seconds * 0.0001  # Rough estimate
        return input_cost + output_cost + audio_cost

    def count_tokens(self, text: str) -> int:
        """Enhanced token counting with better accuracy."""
        if not text:
            return 0
        
        # Try to use actual API token counting if available
        try:
            result = self.client.models.count_tokens(
                model=self.chat_model,
                contents=[text]
            )
            if hasattr(result, 'total_tokens'):
                return result.total_tokens
        except:
            # Fallback to estimation
            pass
        
        # Fallback to word-based estimation
        word_count = len(text.split())
        estimated_tokens = int(word_count / self.TOKEN_WORD_RATIO)
        
        self.logger.debug(f"Estimated {estimated_tokens} tokens for {word_count} words")
        return estimated_tokens

    def list_models(self, model_type: str = "all") -> List[str]:
        """Enhanced model listing (same as original with usage tracking)."""
        try:
            if model_type in ("all", "chat"):
                chat_models = [m.name for m in self.client.models.list()]
                if model_type == "chat":
                    return chat_models
            
            if model_type in ("all", "embedding"):
                try:
                    embed_models = [m.name for m in self.client.embeddings.list()]
                    if model_type == "embedding":
                        return embed_models
                except AttributeError:
                    self.logger.warning("Embedding model listing not available")
                    if model_type == "embedding":
                        return []
            
            if model_type == "all":
                all_models = chat_models[:]
                try:
                    all_models.extend(embed_models)
                except NameError:
                    pass
                return all_models
            
            raise GoogleGenAIError(f"Invalid model_type: {model_type}")
            
        except Exception as e:
            if isinstance(e, GoogleGenAIError):
                raise
            raise GoogleGenAIError(f"Failed to list models: {str(e)}")

    def _validate_messages(self, messages: List[Dict[str, str]]) -> None:
        """Validate message format (same as original)."""
        valid_roles = {"system", "user", "assistant"}
        
        for i, message in enumerate(messages):
            if not isinstance(message, dict):
                raise GoogleGenAIError(f"Message {i} must be a dictionary")
            
            if "role" not in message or "content" not in message:
                raise GoogleGenAIError(f"Message {i} must have 'role' and 'content' keys")
            
            if message["role"] not in valid_roles:
                raise GoogleGenAIError(
                    f"Message {i} has invalid role '{message['role']}'. "
                    f"Valid roles: {valid_roles}"
                )
            
            if not isinstance(message["content"], str) or not message["content"].strip():
                raise GoogleGenAIError(f"Message {i} content must be a non-empty string")

    def _format_messages_for_api(self, messages: List[Dict[str, str]]) -> List[str]:
        """Format messages for the API (same as original)."""
        return [
            f"[{msg['role'].upper()}]\n{msg['content'].strip()}"
            for msg in messages
        ]

    def get_client_info(self) -> Dict[str, Any]:
        """Get enhanced client information."""
        info = {
            "chat_model": self.chat_model,
            "vision_model": self.vision_model,
            "tts_model": self.tts_model,
            "stt_model": self.stt_model,
            "embed_model": self.embed_model,
            "api_key_set": bool(self.api_key),
            "client_initialized": bool(self.client),
            "usage_tracking_enabled": bool(self.usage_stats),
            "context_caching_enabled": bool(self.context_cache),
            "supported_image_formats": list(self.SUPPORTED_IMAGE_FORMATS),
            "supported_audio_formats": list(self.SUPPORTED_AUDIO_FORMATS),
            "available_tts_voices": self.TTS_VOICES[:5],  # Show first 5
            "max_context_tokens": self.MAX_CONTEXT_TOKENS,
        }
        
        if self.context_cache and self.context_cache.cache_id:
            info["cache_status"] = {
                "cache_id": self.context_cache.cache_id,
                "is_valid": self.context_cache.is_valid(),
                "cache_age_hours": ((datetime.now() - self.context_cache.cache_timestamp).total_seconds() / 3600
                                  if self.context_cache.cache_timestamp else 0)
            }
        
        return info

    def __repr__(self) -> str:
        """Enhanced string representation."""
        return (
            f"GoogleGenAIHelper("
            f"chat='{self.chat_model}', "
            f"vision='{self.vision_model}', "
            f"tts='{self.tts_model}', "
            f"stt='{self.stt_model}', "
            f"tracking={'ON' if self.usage_stats else 'OFF'}"
            f")"
        )





class GoogleGenAIHelper:
    """
    Helper class for interacting with Google Gemini via the `google-genai` client.
    """

    def __init__(
        self,
        api_key: str = None,
        chat_model: str = None,
        embed_model: str = None,
    ):
        """
        api_key: Your Google API key (or use GOOGLE_API_KEY env var)
        chat_model: The Gemini chat model name (e.g., "gemini-2.0-flash")
        embed_model: The embedding model name (e.g., "models/embedding-gecko-001")
        """
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise EnvironmentError("GOOGLE_API_KEY not set in environment.")

        # Initialize the client
        self.client = genai.Client(api_key=self.api_key)
        
        # print( self.client)
        self.chat_model = chat_model or os.getenv("GOOGLE_CHAT_MODEL", "gemini-2.0-flash")
        self.embed_model = embed_model or os.getenv("GOOGLE_EMBED_MODEL", "models/text-embedding-004")

    def chat(
        self,
        messages: list,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        """
        Perform a chat-style completion using Gemini.

        messages: list of dicts, e.g.:
          [
            {"role": "system",  "content": "You are a helpful assistant."},
            {"role": "user",    "content": "Explain quantum computing."}
          ]

        max_tokens: maximum tokens to generate.

        Returns the assistant's reply text.
        """
        # Build a list of plain strings to pass as 'contents'
        # Each message becomes "[ROLE]\n<content>"
        contents = [
            f"[{msg['role'].upper()}]\n{msg['content'].strip()}"
            for msg in messages
        ]

        config = types.GenerateContentConfig(
            max_output_tokens=max_tokens,
            temperature=temperature,
        )
        response = self.client.models.generate_content(
            model=self.chat_model,
            contents=contents,
            config=config,
        )
        print(response.text)
        return response.text

    def get_embedding(self, text: str) -> list:
        """
        Generate an embedding vector for the given text.
        """
        title = "Custom query"
        result = self.client.models.embed_content(
            model=self.embed_model,
            contents=text,
            # config=types.EmbedContentConfig(task_type="SEMANTIC_SIMILARITY")
            config=types.EmbedContentConfig(
                task_type="retrieval_document",
                title=title
                        )
            )
        # request = types.EmbedTextRequest(
        #     model=self.embed_model,
        #     text=[text],
        # )
        # resp = self.client.embeddings.embed_text(request=request)
        return result.embeddings[0].values

    # def get_embedding(self, text: str) -> list:
    #     """
    #     Generate an embedding vector for the given text.
    #     Raises RuntimeError if the API returns no embedding.
    #     """
    #     request = types.EmbedTextRequest(
    #         model=self.embed_model,
    #         text=[text],
    #     )
    #     resp = self.client.embeddings.embed_text(request=request)

    #     # resp.embeddings should be a list of lists
    #     if not hasattr(resp, "embeddings") or not resp.embeddings:
    #         raise RuntimeError(f"[❌ ERROR] Empty embeddings response: {resp!r}")

    #     embedding = resp.embeddings[0]
    #     if embedding is None or not isinstance(embedding, (list, tuple)):
    #         raise RuntimeError(f"[❌ ERROR] Invalid embedding returned: {embedding!r}")

    #     return embedding
    

    def count_tokens(self, prompt: str) -> int:
        """
        Rough token count: approximate 1 token ≈ 0.75 words.
        """
        return int(len(prompt.split()) / 0.75)

    def list_chat_models(self) -> list:
        """
        List available chat models.
        """
        return [m.name for m in self.client.models.list()]

    def list_embed_models(self) -> list:
        """
        List available embedding models.
        """
        return [m.name for m in self.client.embeddings.list()]
