import os
import json
import time
import base64
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Callable

try:
    import anthropic
except ImportError:
    raise ImportError("Please install anthropic: pip install anthropic")

try:
    import tiktoken  # optional, we fallback for Claude
except ImportError:
    tiktoken = None

# ---------------- Config & bookkeeping ----------------

@dataclass
class AnthropicConfig:
    """Configuration for EnhancedAnthropicHelper."""
    api_key: Optional[str] = None
    model: str = "claude-3-7-sonnet-2025-06-25"  # choose your preferred Claude 3.x/3.5/3.7 model
    max_retries: int = 3
    timeout: float = 60.0
    enable_caching: bool = True
    cache_ttl: int = 3600
    enable_cost_tracking: bool = True
    log_level: str = "INFO"

    def __post_init__(self):
        if not self.api_key:
            self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise EnvironmentError("ANTHROPIC_API_KEY not set in environment or config.")


class CacheEntry:
    def __init__(self, data: Any, ttl: int):
        self.data = data
        self.created_at = datetime.now()
        self.ttl = ttl
    def is_expired(self) -> bool:
        return datetime.now() > self.created_at + timedelta(seconds=self.ttl)


class UsageStats:
    """
    Best-effort usage+cost tracker. Anthropic returns token usage in responses.
    Pricing here is APPROXIMATE; update per your contract/pricing.
    Values are USD per 1K tokens.
    """
    def __init__(self):
        self.input_tokens = 0
        self.output_tokens = 0
        self.total_tokens = 0
        self.requests = 0
        self.estimated_cost = 0.0

    PRICE = {
        # Update these numbers to match Anthropic’s current pricing/tier.
        # Keys are model family prefixes for rough matching.
        "claude-3-7": {"input": 0.003, "output": 0.015},
        "claude-3-5": {"input": 0.003, "output": 0.015},
        "claude-3-opus": {"input": 0.015, "output": 0.075},
        "claude-3-sonnet": {"input": 0.003, "output": 0.015},
        "claude-3-haiku": {"input": 0.0008, "output": 0.004},
    }

    @staticmethod
    def _family(model: str) -> Optional[str]:
        m = (model or "").lower()
        for fam in UsageStats.PRICE:
            if m.startswith(fam):
                return fam
        # fuzzy: map older names
        if m.startswith("claude-3"):
            return "claude-3-sonnet"
        return None

    def add_usage(self, input_tokens: int = 0, output_tokens: int = 0, model: str = ""):
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        self.total_tokens += input_tokens + output_tokens
        self.requests += 1
        fam = self._family(model)
        if not fam:
            return
        rate = self.PRICE[fam]
        self.estimated_cost += (input_tokens / 1000.0) * rate.get("input", 0.0)
        self.estimated_cost += (output_tokens / 1000.0) * rate.get("output", 0.0)


# ---------------- Helper ----------------

class EnhancedAnthropicHelper:
    """
    Anthropic version that mirrors your OpenAI helper’s public API:

    - chat(messages, ...)
    - achat(messages, ...)           (async not provided by official SDK; emulate via thread if needed)
    - chat_with_vision(text, images, ...)
    - responses(...), aresponses(...)
    - responses_json_object(...)
    - responses_json_schema(...)
    - get_embedding(s)/generate_image/text_to_speech/speech_to_text -> NotImplemented on Anthropic
    - moderate(text) -> lightweight classifier using the model (costs tokens)
    - list_models() -> static list (no public listing endpoint)
    - manage_context_length(), count_tokens() -> approximate
    - caching, retries, usage stats
    """

    def __init__(self, config: Optional[AnthropicConfig] = None):
        self.config = config or AnthropicConfig()
        self._setup_logging()
        self._setup_client()
        self._cache: Dict[str, CacheEntry] = {}
        self.usage = UsageStats()

    def _setup_logging(self):
        logging.basicConfig(
            level=getattr(logging, self.config.log_level.upper(), logging.INFO),
            format="%(asctime)s - AnthropicHelper - %(levelname)s - %(message)s",
        )
        self.logger = logging.getLogger("AnthropicHelper")

    def _setup_client(self):
        self.client = anthropic.Anthropic(
            api_key=self.config.api_key,
            timeout=self.config.timeout,
        )

    # --------- Utilities ---------

    @staticmethod
    def _cache_key(payload: Dict[str, Any]) -> str:
        s = json.dumps(payload, sort_keys=True, default=str)
        import hashlib
        return hashlib.md5(s.encode()).hexdigest()

    def _cache_get(self, key: str):
        if not self.config.enable_caching:
            return None
        it = self._cache.get(key)
        if it and not it.is_expired():
            return it.data
        if it:
            self._cache.pop(key, None)
        return None

    def _cache_set(self, key: str, data: Any, ttl: Optional[int] = None):
        if not self.config.enable_caching:
            return
        self._cache[key] = CacheEntry(data, ttl or self.config.cache_ttl)

    def _retry(self, fn: Callable, *args, **kwargs):
        delay = 1.0
        for attempt in range(self.config.max_retries + 1):
            try:
                return fn(*args, **kwargs)
            except anthropic.RateLimitError as e:
                if attempt == self.config.max_retries:
                    raise
                self.logger.warning(f"Rate limited. Retrying in {delay:.1f}s...")
                time.sleep(delay)
                delay *= 2
            except anthropic.APIStatusError as e:
                if attempt == self.config.max_retries:
                    raise
                self.logger.warning(f"API error: {e}. Retrying in {delay:.1f}s...")
                time.sleep(delay)
                delay *= 2

    # Token counting (approx for Claude). If you need exact, integrate the official tokenizer when available.
    def count_tokens(self, text: str) -> int:
        if tiktoken:
            # Generic fallback tokenizer
            enc = tiktoken.get_encoding("cl100k_base")
            return len(enc.encode(text))
        # Rough heuristic: ~4 chars per token
        return max(1, len(text) // 4)

    def manage_context_length(self, messages: List[Dict[str, Any]], max_tokens: int = 4000,
                              preserve_system: bool = True) -> List[Dict[str, Any]]:
        def msg_tokens(m: Dict[str, Any]) -> int:
            content = m.get("content", "")
            if isinstance(content, list):
                # count text parts only (very rough)
                return sum(self.count_tokens(p.get("text", "")) for p in content if isinstance(p, dict))
            return self.count_tokens(str(content))

        total = sum(msg_tokens(m) for m in messages)
        if total <= max_tokens:
            return messages

        kept: List[Dict[str, Any]] = []
        work = messages[:]
        if preserve_system and work and work[0].get("role") == "system":
            kept.append(work.pop(0))
            total = sum(msg_tokens(m) for m in kept + work)

        while work and total > max_tokens:
            work.pop(0)
            total = sum(msg_tokens(m) for m in kept + work)

        return kept + work

    # --------- Messages / Chat ---------

    @staticmethod
    def _normalize_messages(messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Convert OpenAI-style messages to Anthropic messages:
        - Anthropic uses system + messages(list of {role: "user"|"assistant"|"tool", content:[{type:"text"...}]})
        - We'll extract the first 'system' as system, pass the rest to messages.
        """
        system = None
        out_msgs: List[Dict[str, Any]] = []
        for m in messages:
            role = m.get("role", "user")
            content = m.get("content", "")
            if role == "system":
                # Anthropic supports 'system' string at top-level
                if isinstance(content, list):
                    # concatenate text parts
                    txt = " ".join(
                        p["text"] for p in content if isinstance(p, dict) and p.get("type") == "text"
                    )
                    system = (system + "\n" + txt) if system else txt
                else:
                    system = (system + "\n" + str(content)) if system else str(content)
                continue

            if isinstance(content, str):
                out_msgs.append({"role": role, "content": [{"type": "text", "text": content}]})
            elif isinstance(content, list):
                # pass through typed parts (text/image)
                normalized_parts = []
                for p in content:
                    if isinstance(p, dict) and p.get("type") == "image_url":
                        url = p.get("image_url", {}).get("url")
                        if url and url.startswith("data:image/"):
                            # already base64 data URI
                            b64 = url.split(",")[-1]
                            normalized_parts.append({
                                "type": "image",
                                "source": {"type": "base64", "media_type": "image/*", "data": b64}
                            })
                        elif url and url.startswith(("http://", "https://")):
                            # Anthropic prefers base64; fetch yourself if needed
                            normalized_parts.append({
                                "type": "text",
                                "text": f"[Image URL provided: {url}]"
                            })
                        else:
                            normalized_parts.append({"type": "text", "text": str(p)})
                    elif isinstance(p, dict) and p.get("type") == "text":
                        normalized_parts.append({"type": "text", "text": p["text"]})
                    else:
                        normalized_parts.append({"type": "text", "text": str(p)})
                out_msgs.append({"role": role, "content": normalized_parts})
            else:
                out_msgs.append({"role": role, "content": [{"type": "text", "text": str(content)}]})

        return {"system": system, "messages": out_msgs}

    def _record_usage(self, resp: Any, model: str):
        usage = getattr(resp, "usage", None)
        if not usage:
            return
        in_tok = getattr(usage, "input_tokens", 0) or 0
        out_tok = getattr(usage, "output_tokens", 0) or 0
        self.usage.add_usage(in_tok, out_tok, model=model)

    def chat(self,
             messages: List[Dict[str, Any]],
             model: Optional[str] = None,
             temperature: float = 0.7,
             max_tokens: Optional[int] = None,
             stream: bool = False,
             tools: Optional[List[Dict[str, Any]]] = None,
             tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
             response_format: Optional[Dict[str, Any]] = None,
             **kwargs) -> Union[str, Any]:
        """
        Anthropic messages.create wrapper. Returns assistant text by default,
        or the raw response when tool calls / structured outputs are present.
        """
        mdl = model or self.config.model
        packed = self._normalize_messages(messages)
        payload = {
            "model": mdl,
            "messages": packed["messages"],
            "system": packed["system"],
            "temperature": temperature,
            **kwargs
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if tools:
            payload["tools"] = tools
        if tool_choice:
            payload["tool_choice"] = tool_choice
        if response_format:
            payload["response_format"] = response_format

        cache_key = self._cache_key({"fn": "chat", **payload})
        cached = self._cache_get(cache_key)
        if cached is not None and not stream:
            return cached

        def _create():
            if stream:
                # Streaming: yield chunks of text
                # NOTE: Anthropic SDK streaming yields events; we concatenate "content_block_delta" text.
                with self.client.messages.stream(**payload) as s:
                    full_text = []
                    for event in s:
                        if event.type == "content_block_delta" and getattr(event.delta, "type", "") == "text_delta":
                            piece = event.delta.text
                            if piece:
                                full_text.append(piece)
                                yield piece
                    # cache the whole text
                    self._cache_set(cache_key, "".join(full_text))
            else:
                resp = self.client.messages.create(**payload)
                self._record_usage(resp, mdl)
                # If tool use / structured outputs present, return raw response
                has_tool_use = any(
                    (p.get("type") == "tool_use") for p in (resp.content or []) if isinstance(p, dict)
                )
                if has_tool_use or response_format:
                    self._cache_set(cache_key, resp)
                    return resp
                # Otherwise extract assistant text
                text = "".join(
                    p.get("text", "") for p in (resp.content or []) if isinstance(p, dict) and p.get("type") == "text"
                )
                self._cache_set(cache_key, text)
                return text

        return self._retry(_create)

    # -------- Vision convenience (wraps chat) --------
    def chat_with_vision(self, text: str, images: List[Union[str, Path]],
                         model: Optional[str] = None, **kwargs) -> str:
        parts: List[Dict[str, Any]] = [{"type": "text", "text": text}]
        for img in images:
            s = str(img)
            if s.startswith(("http://", "https://")):
                parts.append({"type": "text", "text": f"[Image URL provided: {s}]"})
            else:
                with open(s, "rb") as f:
                    b64 = base64.b64encode(f.read()).decode()
                # Try to infer media type (lightweight)
                media = "image/png" if s.lower().endswith(".png") else "image/jpeg"
                parts.append({"type": "image", "source": {"type": "base64", "media_type": media, "data": b64}})
        messages = [{"role": "user", "content": parts}]
        return self.chat(messages, model=model, **kwargs)

    # -------- Responses-like helpers (aliases) --------
    # Anthropic does not have a separate "Responses API"—we just proxy to messages.create.

    def responses(self, messages_or_text: Union[str, List[Dict[str, Any]]],
                  model: Optional[str] = None, **kwargs) -> str:
        if isinstance(messages_or_text, str):
            messages = [{"role": "user", "content": messages_or_text}]
        else:
            messages = messages_or_text
        out = self.chat(messages, model=model, **kwargs)
        # If raw response returned (e.g., tool use), coerce to text
        if isinstance(out, str):
            return out
        text = "".join(p.get("text", "") for p in (out.content or []) if isinstance(p, dict) and p.get("type") == "text")
        return text

    def aresponses(self, *args, **kwargs):
        raise NotImplementedError("Anthropic official SDK is sync-only. Use threads/async executor if needed.")

    # -------- JSON helpers (structured outputs) --------

    def responses_json_object(self, messages_or_text: Union[str, List[Dict[str, Any]]],
                              model: Optional[str] = None, **kwargs) -> Any:
        """
        Lightweight JSON mode. Anthropic supports strict schemas; for loose JSON
        we request text and parse, with a fallback to substring extraction.
        """
        text = self.responses(messages_or_text, model=model, **kwargs)
        try:
            return json.loads(text)
        except Exception:
            import re
            m = re.search(r"\{.*\}", text, re.DOTALL)
            return json.loads(m.group(0)) if m else {"_raw": text}

    def responses_json_schema(self, messages_or_text: Union[str, List[Dict[str, Any]]],
                              schema_name: str, schema: Dict[str, Any],
                              model: Optional[str] = None, **kwargs) -> Any:
        """
        Strict JSON schema via Anthropic structured outputs.
        """
        mdl = model or self.config.model
        if isinstance(messages_or_text, str):
            messages = [{"role": "user", "content": messages_or_text}]
        else:
            messages = messages_or_text

        packed = self._normalize_messages(messages)
        payload = {
            "model": mdl,
            "messages": packed["messages"],
            "system": packed["system"],
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

        cache_key = self._cache_key({"fn": "responses_json_schema", **payload})
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached

        def _create():
            resp = self.client.messages.create(**payload)
            self._record_usage(resp, mdl)
            # Anthropic returns parsed JSON in content items of type "tool_result" or "output_json" (SDK evolves).
            # Best-effort: prefer "parsed" if present, else parse text.
            # Current SDK typically includes 'content[0].type=="output_json"' with .parsed
            try:
                for p in (resp.content or []):
                    if isinstance(p, dict) and "parsed" in p:
                        data = p["parsed"]
                        self._cache_set(cache_key, data)
                        return data
            except Exception:
                pass
            # Fallback: concatenate text and parse
            text = "".join(
                p.get("text", "") for p in (resp.content or []) if isinstance(p, dict) and p.get("type") == "text"
            )
            data = json.loads(text)
            self._cache_set(cache_key, data)
            return data

        return self._retry(_create)

    # -------- Moderation (LLM-powered) --------
    def moderate(self, text: str) -> Dict[str, Any]:
        """
        Anthropic doesn't expose a standalone moderation endpoint.
        We implement a small classifier prompt (costs tokens).
        """
        sys = (
            "You are a safety classifier. Return a compact JSON object with fields:\n"
            "allowed (boolean), categories (array of strings), reason (string)."
        )
        prompt = (
            "Classify the following content for safety policy violations.\n"
            "Return only JSON.\n\nCONTENT:\n" + text
        )
        data = self.responses_json_schema(
            messages_or_text=[{"role": "system", "content": sys},
                              {"role": "user", "content": prompt}],
            schema_name="SafetyResult",
            schema={
                "type": "object",
                "properties": {
                    "allowed": {"type": "boolean"},
                    "categories": {"type": "array", "items": {"type": "string"}},
                    "reason": {"type": "string"}
                },
                "required": ["allowed", "categories", "reason"],
                "additionalProperties": False
            },
            model=self.config.model
        )
        return data

    # -------- Unsupported in Anthropic (stubs to keep API symmetry) --------
    def get_embedding(self, *args, **kwargs):
        raise NotImplementedError("Embeddings API is not available in Anthropic. Use OpenAI/HF or your own service.")

    def get_embeddings(self, *args, **kwargs):
        raise NotImplementedError("Embeddings API is not available in Anthropic. Use OpenAI/HF or your own service.")

    def generate_image(self, *args, **kwargs):
        raise NotImplementedError("Image generation is not provided by Anthropic. Use an image model provider.")

    def text_to_speech(self, *args, **kwargs):
        raise NotImplementedError("TTS is not provided by Anthropic. Use a TTS provider.")

    def speech_to_text(self, *args, **kwargs):
        raise NotImplementedError("Whisper/STT is not provided by Anthropic. Use a speech provider.")

    def list_models(self) -> List[str]:
        # No public listing endpoint; keep a curated list
        return [
            "claude-3-7-sonnet-2025-06-25",
            "claude-3-5-sonnet-2024-10-22",
            "claude-3-5-haiku-2024-10-22",
            "claude-3-opus-2024-04-xx",
            "claude-3-sonnet-2024-xx-xx",
            "claude-3-haiku-2024-xx-xx",
        ]

    # -------- Introspection --------
    def get_usage_stats(self) -> Dict[str, Any]:
        return {
            "input_tokens": self.usage.input_tokens,
            "output_tokens": self.usage.output_tokens,
            "total_tokens": self.usage.total_tokens,
            "requests": self.usage.requests,
            "estimated_cost": round(self.usage.estimated_cost, 6),
            "cache_size": len(self._cache),
        }

    def clear_cache(self):
        self._cache.clear()
        self.logger.info("Cache cleared")

    def reset_usage_stats(self):
        self.usage = UsageStats()
        self.logger.info("Usage statistics reset")
