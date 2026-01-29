import os
import asyncio
import json
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Union, Callable, Any, AsyncGenerator
from dataclasses import dataclass, field
from pathlib import Path
import hashlib

try:
    from openai import OpenAI, AsyncOpenAI
    from openai import APIConnectionError, RateLimitError, APIStatusError
except ImportError:
    raise ImportError("Please install openai: pip install openai")

try:
    import tiktoken
except ImportError:
    tiktoken = None


@dataclass
class OpenAIConfig:
    """Configuration class for OpenAI helper."""
    api_key: Optional[str] = None
    chat_model: str = "gpt-4o-mini"            # modern default for quality+cost
    embedding_model: str = "text-embedding-3-large"
    image_model: str = "gpt-image-1"
    vision_model: str = "gpt-4o-mini"          # handles text+vision in chat
    tts_model: str = "tts-1"
    whisper_model: str = "whisper-1"
    base_url: Optional[str] = None
    organization: Optional[str] = None
    project: Optional[str] = None
    max_retries: int = 3
    timeout: float = 60.0
    enable_caching: bool = True
    cache_ttl: int = 3600  # 1 hour
    enable_cost_tracking: bool = True
    log_level: str = "INFO"

    def __post_init__(self):
        if not self.api_key:
            self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise EnvironmentError("OPENAI_API_KEY not set in environment or config.")

        # Env overrides
        self.chat_model = os.getenv("OPENAI_CHAT_MODEL", self.chat_model)
        self.embedding_model = os.getenv("OPENAI_EMBED_MODEL", self.embedding_model)
        self.organization = os.getenv("OPENAI_ORG", self.organization)
        self.project = os.getenv("OPENAI_PROJECT", self.project)


@dataclass
class CacheEntry:
    data: Any
    created_at: datetime
    ttl: int
    def is_expired(self) -> bool:
        return datetime.now() > self.created_at + timedelta(seconds=self.ttl)


@dataclass
class UsageStats:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    requests: int = 0
    estimated_cost: float = 0.0

    # Central pricing table: approximate, easy to extend.
    # Values are USD per 1K tokens. Update as needed.
    PRICE = {
        # Chat/completion (input/output)
        "gpt-4o":            {"input": 0.005,  "output": 0.015},
        "gpt-4o-mini":       {"input": 0.0005, "output": 0.0015},
        "gpt-4.1":           {"input": 0.01,   "output": 0.03},
        "gpt-4.1-mini":      {"input": 0.002,  "output": 0.006},
        "o4-mini":           {"input": 0.003,  "output": 0.012},
        "gpt-3.5-turbo":     {"input": 0.001,  "output": 0.002},
        # Embeddings (input only)
        "text-embedding-3-small": {"input": 0.00002, "output": 0.0},
        "text-embedding-3-large": {"input": 0.00013, "output": 0.0},
    }

    @staticmethod
    def _model_family(model: str) -> Optional[str]:
        """Map a specific model name to a pricing family key."""
        if not model:
            return None
        model = model.lower()
        for family in UsageStats.PRICE.keys():
            if model.startswith(family):
                return family
        return None

    def add_usage(self, prompt_tokens: int = 0, completion_tokens: int = 0, model: str = ""):
        self.prompt_tokens += prompt_tokens
        self.completion_tokens += completion_tokens
        self.total_tokens += prompt_tokens + completion_tokens
        self.requests += 1

        family = self._model_family(model)
        if not family:
            return  # unknown model; skip cost estimate

        rates = self.PRICE[family]
        self.estimated_cost += (prompt_tokens / 1000.0) * rates.get("input", 0.0)
        self.estimated_cost += (completion_tokens / 1000.0) * rates.get("output", 0.0)


class EnhancedOpenAIHelper:
    """Enhanced OpenAI helper with advanced features."""

    def __init__(self, config: Optional[OpenAIConfig] = None):
        self.config = config or OpenAIConfig()
        self._setup_logging()
        self._setup_clients()
        self._setup_cache()
        self._setup_usage_tracking()

    def _setup_logging(self):
        logging.basicConfig(
            level=getattr(logging, self.config.log_level.upper(), logging.INFO),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        self.logger = logging.getLogger(self.__class__.__name__)

    def _setup_clients(self):
        client_kwargs = {
            "api_key": self.config.api_key,
            "max_retries": self.config.max_retries,
            "timeout": self.config.timeout,
        }
        if self.config.base_url:
            client_kwargs["base_url"] = self.config.base_url
        if self.config.organization:
            client_kwargs["organization"] = self.config.organization
        if self.config.project:
            client_kwargs["project"] = self.config.project

        self.client = OpenAI(**client_kwargs)
        self.async_client = AsyncOpenAI(**client_kwargs)

    def _setup_cache(self):
        self._cache: Dict[str, CacheEntry] = {}

    def _setup_usage_tracking(self):
        self.usage_stats = UsageStats()

    # ---------------- Cache helpers ----------------
    def _cache_key(self, *args, **kwargs) -> str:
        key_data = {"args": args, "kwargs": kwargs}
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_str.encode()).hexdigest()

    def _get_from_cache(self, key: str) -> Optional[Any]:
        if not self.config.enable_caching:
            return None
        entry = self._cache.get(key)
        if entry and not entry.is_expired():
            self.logger.debug(f"Cache hit for key: {key}")
            return entry.data
        if entry:
            self._cache.pop(key, None)
        return None

    def _set_cache(self, key: str, data: Any, ttl: Optional[int] = None):
        if not self.config.enable_caching:
            return
        ttl = ttl or self.config.cache_ttl
        self._cache[key] = CacheEntry(data=data, created_at=datetime.now(), ttl=ttl)
        self.logger.debug(f"Cache set for key: {key}")

    # ---------------- Retry helper ----------------
    def _retry_with_backoff(self, func: Callable, *args, **kwargs):
        max_retries = self.config.max_retries
        base_delay = 1.0
        for attempt in range(max_retries + 1):
            try:
                return func(*args, **kwargs)
            except RateLimitError as e:
                if attempt == max_retries:
                    raise
                delay = base_delay * (2 ** attempt)
                self.logger.warning(f"Rate limit hit, retrying in {delay:.1f}s (attempt {attempt + 1})")
                time.sleep(delay)
            except (APIConnectionError, APIStatusError) as e:
                if attempt == max_retries:
                    raise
                delay = base_delay * (2 ** attempt)
                self.logger.warning(f"API error, retrying in {delay:.1f}s (attempt {attempt + 1}): {e}")
                time.sleep(delay)

    # ---------------- Chat ----------------
    def chat(
        self,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        functions: Optional[List[Dict]] = None,
        function_call: Optional[Union[str, Dict]] = None,
        tools: Optional[List[Dict]] = None,
        tool_choice: Optional[Union[str, Dict]] = None,
        response_format: Optional[Dict] = None,
        seed: Optional[int] = None,
        **kwargs,
    ) -> Union[str, Dict, AsyncGenerator[str, None]]:
        """Chat completion with function/tool calling support."""
        model = model or self.config.chat_model
        if not (0 <= temperature <= 2):
            raise ValueError("Temperature must be between 0 and 2")

        request_params = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": stream,
            **kwargs,
        }
        if max_tokens is not None:
            request_params["max_tokens"] = max_tokens
        if functions:
            request_params["functions"] = functions
        if function_call:
            request_params["function_call"] = function_call
        if tools:
            request_params["tools"] = tools
        if tool_choice:
            request_params["tool_choice"] = tool_choice
        if response_format:
            request_params["response_format"] = response_format
        if seed is not None:
            request_params["seed"] = seed

        cache_key = None
        if not stream and self.config.enable_caching:
            cache_key = self._cache_key("chat", **request_params)
            cached = self._get_from_cache(cache_key)
            if cached is not None:
                return cached

        def _make_request():
            resp = self.client.chat.completions.create(**request_params)

            # Track usage if available (non-stream)
            if hasattr(resp, "usage") and resp.usage:
                self.usage_stats.add_usage(
                    prompt_tokens=getattr(resp.usage, "prompt_tokens", 0) or 0,
                    completion_tokens=getattr(resp.usage, "completion_tokens", 0) or 0,
                    model=model,
                )

            if stream:
                def stream_generator():
                    chunks: List[str] = []
                    for chunk in resp:
                        delta = chunk.choices[0].delta
                        piece = getattr(delta, "content", None)
                        if piece:
                            chunks.append(piece)
                            yield piece
                    if cache_key:
                        self._set_cache(cache_key, "".join(chunks))
                return stream_generator()
            else:
                choice = resp.choices[0]
                if getattr(choice.message, "tool_calls", None) or getattr(choice.message, "function_call", None):
                    out = {
                        "content": choice.message.content,
                        "tool_calls": choice.message.tool_calls,
                        "function_call": choice.message.function_call,
                        "finish_reason": choice.finish_reason,
                    }
                else:
                    out = choice.message.content

                if cache_key:
                    self._set_cache(cache_key, out)
                return out

        return self._retry_with_backoff(_make_request)

    async def achat(self, messages: List[Dict[str, Any]], model: Optional[str] = None, **kwargs) -> Union[str, Dict]:
        model = model or self.config.chat_model

        cache_key = None
        if self.config.enable_caching and not kwargs.get("stream", False):
            cache_key = self._cache_key("achat", model=model, messages=messages, **kwargs)
            cached = self._get_from_cache(cache_key)
            if cached is not None:
                return cached

        resp = await self.async_client.chat.completions.create(model=model, messages=messages, **kwargs)

        if hasattr(resp, "usage") and resp.usage:
            self.usage_stats.add_usage(
                prompt_tokens=getattr(resp.usage, "prompt_tokens", 0) or 0,
                completion_tokens=getattr(resp.usage, "completion_tokens", 0) or 0,
                model=model,
            )

        choice = resp.choices[0]
        if getattr(choice.message, "tool_calls", None) or getattr(choice.message, "function_call", None):
            out = {
                "content": choice.message.content,
                "tool_calls": choice.message.tool_calls,
                "function_call": choice.message.function_call,
                "finish_reason": choice.finish_reason,
            }
        else:
            out = choice.message.content

        if cache_key:
            self._set_cache(cache_key, out)
        return out

    # ---------------- Vision in chat ----------------
    def chat_with_vision(self, text: str, images: List[Union[str, Path]], model: Optional[str] = None, **kwargs) -> str:
        model = model or self.config.vision_model
        content: List[Dict[str, Any]] = [{"type": "text", "text": text}]

        for img in images:
            if isinstance(img, (str, Path)):
                s = str(img)
                if s.startswith(("http://", "https://")):
                    content.append({"type": "image_url", "image_url": {"url": s}})
                else:
                    import base64
                    with open(s, "rb") as f:
                        b64 = base64.b64encode(f.read()).decode()
                    # Keep generic MIME; change if you know the exact type
                    content.append({"type": "image_url", "image_url": {"url": f"data:image/*;base64,{b64}"}})
        messages = [{"role": "user", "content": content}]
        return self.chat(messages, model=model, **kwargs)

    # ---------------- Embeddings ----------------
    def get_embedding(self, text: str, model: Optional[str] = None, dimensions: Optional[int] = None) -> List[float]:
        model = model or self.config.embedding_model
        cache_key = self._cache_key("embedding", text=text, model=model, dimensions=dimensions)
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        def _make_request():
            req = {"input": [text], "model": model}
            if dimensions:
                req["dimensions"] = dimensions
            resp = self.client.embeddings.create(**req)
            # Some SDKs do not populate usage for embeddings; guard it
            usage = getattr(resp, "usage", None)
            if usage and self.config.enable_cost_tracking:
                self.usage_stats.add_usage(prompt_tokens=getattr(usage, "prompt_tokens", 0) or 0, model=model)
            vec = resp.data[0].embedding
            self._set_cache(cache_key, vec)
            return vec

        return self._retry_with_backoff(_make_request)

    def get_embeddings(
        self, texts: List[str], model: Optional[str] = None, dimensions: Optional[int] = None, batch_size: int = 100
    ) -> List[List[float]]:
        model = model or self.config.embedding_model
        all_vecs: List[List[float]] = []
        total_batches = (len(texts) + batch_size - 1) // batch_size

        for idx in range(0, len(texts), batch_size):
            batch = texts[idx : idx + batch_size]

            def _make_request():
                req = {"input": batch, "model": model}
                if dimensions:
                    req["dimensions"] = dimensions
                resp = self.client.embeddings.create(**req)
                usage = getattr(resp, "usage", None)
                if usage and self.config.enable_cost_tracking:
                    self.usage_stats.add_usage(prompt_tokens=getattr(usage, "prompt_tokens", 0) or 0, model=model)
                return [item.embedding for item in resp.data]

            vecs = self._retry_with_backoff(_make_request)
            all_vecs.extend(vecs)
            self.logger.info(f"Processed batch {idx // batch_size + 1}/{total_batches}")

        return all_vecs

    # ---------------- Images ----------------
    def generate_image(
        self,
        prompt: str,
        model: Optional[str] = None,
        size: str = "1024x1024",
        quality: str = "standard",
        n: int = 1,
        response_format: str = "url",
    ) -> List[str]:
        """Generate images with gpt-image-1. response_format: 'url' or 'b64_json'."""
        model = model or self.config.image_model

        def _make_request():
            resp = self.client.images.generate(
                model=model,
                prompt=prompt,
                size=size,
                quality=quality,
                n=n,
                response_format=response_format,
            )
            self.usage_stats.requests += 1
            if response_format == "url":
                return [d.url for d in resp.data]
            return [d.b64_json for d in resp.data]

        return self._retry_with_backoff(_make_request)

    # ---------------- Audio ----------------
    def text_to_speech(
        self,
        text: str,
        voice: str = "alloy",
        model: Optional[str] = None,
        response_format: str = "mp3",
        speed: float = 1.0,
    ) -> bytes:
        model = model or self.config.tts_model

        def _make_request():
            resp = self.client.audio.speech.create(
                model=model, voice=voice, input=text, response_format=response_format, speed=speed
            )
            self.usage_stats.requests += 1
            return resp.content

        return self._retry_with_backoff(_make_request)

    def speech_to_text(
        self,
        audio_file: Union[str, Path],
        model: Optional[str] = None,
        language: Optional[str] = None,
        prompt: Optional[str] = None,
        response_format: str = "json",
        temperature: float = 0,
    ) -> Union[str, Dict]:
        model = model or self.config.whisper_model

        def _make_request():
            with open(audio_file, "rb") as f:
                resp = self.client.audio.transcriptions.create(
                    model=model,
                    file=f,
                    language=language,
                    prompt=prompt,
                    response_format=response_format,
                    temperature=temperature,
                )
            self.usage_stats.requests += 1
            # SDK returns a rich object; 'text' for JSON
            return getattr(resp, "text", resp)

        return self._retry_with_backoff(_make_request)

    # ---------------- Tokens & context ----------------
    def count_tokens(self, text: str, model: Optional[str] = None) -> int:
        if not tiktoken:
            raise ImportError("Please install tiktoken: pip install tiktoken")
        model = model or self.config.chat_model

        cache_key = self._cache_key("tokens", text=text, model=model)
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        try:
            enc = tiktoken.encoding_for_model(model)
        except Exception:
            # Fallback for unknown/new models
            enc = tiktoken.get_encoding("cl100k_base")
        tokens = len(enc.encode(text))
        self._set_cache(cache_key, tokens)
        return tokens

    def manage_context_length(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 4000,
        preserve_system: bool = True,
    ) -> List[Dict[str, str]]:
        """Trim oldest messages to fit max_tokens. Keeps system message if requested."""
        if not tiktoken:
            self.logger.warning("tiktoken not available; cannot manage context length accurately.")
            return messages

        def msg_tokens(m: Dict[str, str]) -> int:
            return self.count_tokens(m.get("content", ""))

        total = sum(msg_tokens(m) for m in messages)
        if total <= max_tokens:
            return messages

        kept: List[Dict[str, str]] = []
        work = messages[:]

        if preserve_system and work and work[0].get("role") == "system":
            kept.append(work.pop(0))
            # do not subtract twice; we'll recalc as we mutate
            total = sum(msg_tokens(m) for m in kept + work)

        while work and total > max_tokens:
            removed = work.pop(0)
            total = sum(msg_tokens(m) for m in kept + work)

        result = kept + work
        self.logger.info(f"Context management: kept {len(result)} messages (~{total} tokens)")
        return result

    # ---------------- Safety / Moderation ----------------
    def moderate(self, text: str) -> Dict[str, Any]:
        """Content moderation with omni-moderation-latest and caching."""
        cache_key = self._cache_key("moderate", text=text)
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        def _make_request():
            resp = self.client.moderations.create(model="omni-moderation-latest", input=text)
            result = resp.results[0].model_dump()
            self._set_cache(cache_key, result)
            return result

        return self._retry_with_backoff(_make_request)

    # ---------------- Models ----------------
    def list_models(self) -> List[str]:
        """List available model IDs (cached 24h)."""
        cache_key = "models_list"
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        def _make_request():
            models = self.client.models.list()
            ids = [m.id for m in models.data]
            self._set_cache(cache_key, ids, ttl=86400)
            return ids

        return self._retry_with_backoff(_make_request)

    # ---------------- Introspection & utilities ----------------
    def get_usage_stats(self) -> Dict[str, Any]:
        return {
            "prompt_tokens": self.usage_stats.prompt_tokens,
            "completion_tokens": self.usage_stats.completion_tokens,
            "total_tokens": self.usage_stats.total_tokens,
            "requests": self.usage_stats.requests,
            "estimated_cost": round(self.usage_stats.estimated_cost, 6),
            "cache_size": len(self._cache),
        }

    def clear_cache(self):
        self._cache.clear()
        self.logger.info("Cache cleared")

    def reset_usage_stats(self):
        self.usage_stats = UsageStats()
        self.logger.info("Usage statistics reset")

    def batch_process(
        self,
        items: List[Any],
        processor: Callable[[Any], Any],
        batch_size: int = 10,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> List[Any]:
        results: List[Any] = []
        total_batches = (len(items) + batch_size - 1) // batch_size
        for i in range(0, len(items), batch_size):
            batch = items[i : i + batch_size]
            batch_results: List[Any] = []
            for item in batch:
                try:
                    batch_results.append(processor(item))
                except Exception as e:
                    self.logger.error(f"Error processing item {item}: {e}")
                    batch_results.append(None)
            results.extend(batch_results)
            if progress_callback:
                progress_callback(i // batch_size + 1, total_batches)
            self.logger.info(f"Processed batch {i // batch_size + 1}/{total_batches}")
        return results

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        stats = self.get_usage_stats()
        self.logger.info(f"Session complete. Usage: {stats}")

    # ---------------- Responses API (optional path) ----------------
    def _to_responses_input(self, messages_or_text: Union[str, List[Dict[str, Any]]]) -> Any:
        """
        Convert either:
          - a simple text prompt (str), or
          - OpenAI chat-style messages: [{"role":"user","content":"..."}]
        into a Responses API-compatible 'input'.

        Returns either a string (for simple text) or a list of message dicts.
        """
        if isinstance(messages_or_text, str):
            return messages_or_text

        if isinstance(messages_or_text, list):
            # Responses API accepts the same message structure:
            # [{"role":"user","content":[{"type":"text","text":"..."}]}] OR content as str.
            normalized = []
            for m in messages_or_text:
                role = m.get("role", "user")
                content = m.get("content", "")
                if isinstance(content, str):
                    normalized.append({"role": role, "content": content})
                elif isinstance(content, list):
                    # already typed parts (text/image_url objects). Pass through.
                    normalized.append({"role": role, "content": content})
                else:
                    # fallback: stringify
                    normalized.append({"role": role, "content": str(content)})
            return normalized

        # Fallback
        return str(messages_or_text)

    def _responses_text_from(self, resp: Any) -> str:
        """
        Extract plain text from a Responses API result.
        Handles common SDK shapes defensively.
        """
        # Newer SDKs often expose response.output_text
        text = getattr(resp, "output_text", None)
        if isinstance(text, str) and text.strip():
            return text

        # Otherwise, walk output content
        output = getattr(resp, "output", None)
        if isinstance(output, list) and output:
            # output -> [ { "content": [ { "type":"output_text", "text":"..." }, ... ] }, ... ]
            try:
                parts = output[0].get("content", [])
                for p in parts:
                    if isinstance(p, dict) and p.get("type") in ("output_text", "text"):
                        if "text" in p and isinstance(p["text"], str):
                            return p["text"]
            except Exception:
                pass

        # Older shapes: choices[0].message.content (rare for responses)
        choices = getattr(resp, "choices", None)
        if isinstance(choices, list) and choices:
            msg = getattr(choices[0], "message", None)
            if msg and isinstance(getattr(msg, "content", None), str):
                return msg.content

        # Give up to string
        return str(resp)

    def responses(
        self,
        messages_or_text: Union[str, List[Dict[str, Any]]],
        model: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Text-first convenience wrapper around the Responses API.
        Returns plain text (extracted), not the raw object.
        """
        model = model or self.config.chat_model
        payload = {
            "model": model,
            "input": self._to_responses_input(messages_or_text),
            **kwargs
        }

        cache_key = self._cache_key("responses", **payload)
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        def _make_request():
            resp = self.client.responses.create(**payload)
            # Track usage if present
            usage = getattr(resp, "usage", None)
            if usage and self.config.enable_cost_tracking:
                self.usage_stats.add_usage(
                    prompt_tokens=getattr(usage, "input_tokens", 0) or 0,
                    completion_tokens=getattr(usage, "output_tokens", 0) or 0,
                    model=model,
                )
            text = self._responses_text_from(resp)
            self._set_cache(cache_key, text)
            return text

        return self._retry_with_backoff(_make_request)

    async def aresponses(
        self,
        messages_or_text: Union[str, List[Dict[str, Any]]],
        model: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Async twin of responses(). Returns extracted text.
        """
        model = model or self.config.chat_model
        payload = {
            "model": model,
            "input": self._to_responses_input(messages_or_text),
            **kwargs
        }

        cache_key = self._cache_key("aresponses", **payload)
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        resp = await self.async_client.responses.create(**payload)
        usage = getattr(resp, "usage", None)
        if usage and self.config.enable_cost_tracking:
            self.usage_stats.add_usage(
                prompt_tokens=getattr(usage, "input_tokens", 0) or 0,
                completion_tokens=getattr(usage, "output_tokens", 0) or 0,
                model=model,
            )
        text = self._responses_text_from(resp)
        self._set_cache(cache_key, text)
        return text

    # ---------------- JSON helpers for Responses API ----------------
    def responses_json_object(
        self,
        messages_or_text: Union[str, List[Dict[str, Any]]],
        model: Optional[str] = None,
        strict: bool = False,
        **kwargs
    ) -> Any:
        """
        Ask the model to return JSON. If strict=False, uses lightweight JSON mode.
        If strict=True, you should pass a schema via responses_json_schema(...) instead.
        """
        model = model or self.config.chat_model
        payload = {
            "model": model,
            "input": self._to_responses_input(messages_or_text),
            # Lightweight JSON mode (let model return a single JSON object)
            "response_format": {"type": "json_object"} if not strict else None,
            **{k: v for k, v in kwargs.items() if v is not None},
        }
        cache_key = self._cache_key("responses_json_object", **payload)
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        def _make_request():
            resp = self.client.responses.create(**payload)
            usage = getattr(resp, "usage", None)
            if usage and self.config.enable_cost_tracking:
                self.usage_stats.add_usage(
                    prompt_tokens=getattr(usage, "input_tokens", 0) or 0,
                    completion_tokens=getattr(usage, "output_tokens", 0) or 0,
                    model=model,
                )
            text = self._responses_text_from(resp)
            try:
                data = json.loads(text)
            except Exception:
                # Fallback: try to extract JSON substring
                import re
                m = re.search(r"\{.*\}", text, re.DOTALL)
                data = json.loads(m.group(0)) if m else {"_raw": text}
            self._set_cache(cache_key, data)
            return data

        return self._retry_with_backoff(_make_request)

    def responses_json_schema(
        self,
        messages_or_text: Union[str, List[Dict[str, Any]]],
        schema_name: str,
        schema: Dict[str, Any],
        model: Optional[str] = None,
        **kwargs
    ) -> Any:
        """
        Enforce a strict JSON Schema using Responses API structured outputs.
        'schema' must be a valid JSON Schema object (draft-07+).
        """
        model = model or self.config.chat_model
        payload = {
            "model": model,
            "input": self._to_responses_input(messages_or_text),
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": schema_name,
                    "schema": schema,
                    "strict": True
                }
            },
            **kwargs
        }

        cache_key = self._cache_key("responses_json_schema", **payload)
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        def _make_request():
            resp = self.client.responses.create(**payload)
            usage = getattr(resp, "usage", None)
            if usage and self.config.enable_cost_tracking:
                self.usage_stats.add_usage(
                    prompt_tokens=getattr(usage, "input_tokens", 0) or 0,
                    completion_tokens=getattr(usage, "output_tokens", 0) or 0,
                    model=model,
                )
            # With structured outputs, SDKs typically expose JSON directly:
            # Prefer response.output[0].content[0].parsed if available.
            try:
                output = getattr(resp, "output", None)
                if isinstance(output, list) and output:
                    parts = output[0].get("content", [])
                    for p in parts:
                        # Some SDKs: {"type":"output_json","parsed":{...}}
                        if isinstance(p, dict) and "parsed" in p:
                            data = p["parsed"]
                            self._set_cache(cache_key, data)
                            return data
            except Exception:
                pass

            # Fallback to parse from text
            text = self._responses_text_from(resp)
            data = json.loads(text)
            self._set_cache(cache_key, data)
            return data

        return self._retry_with_backoff(_make_request)

