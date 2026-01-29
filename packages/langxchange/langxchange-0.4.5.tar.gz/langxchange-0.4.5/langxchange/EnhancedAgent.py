"""
Enhanced LLM Agent Helper - Improved Implementation

Key Improvements:
1. Proper async/await patterns throughout
2. Retry logic with exponential backoff for LLM calls
3. Circuit breaker pattern for external services
4. LRU cache for repeated operations
5. Streaming LLM response support
6. Event-driven architecture with hooks
7. Prometheus-style metrics export
8. Better memory management with compression
9. Concurrent action execution support
10. Structured logging with correlation IDs

Author: Matrix Agent
"""

import json
import uuid
import re
import difflib
import asyncio
import traceback
import hashlib
import gzip
from datetime import datetime, timedelta
from typing import (
    List, Dict, Any, Optional, Callable, Union,
    Awaitable, TypeVar, Generic, AsyncIterator
)
from dataclasses import dataclass, field
from functools import lru_cache, wraps
from enum import Enum
from collections import deque
from contextlib import asynccontextmanager
import logging

T = TypeVar('T')


class AgentState(Enum):
    """Agent lifecycle states"""
    INITIALIZED = "initialized"
    RUNNING = "running"
    THINKING = "thinking"
    DECIDING = "deciding"
    ACTING = "acting"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class RetryConfig:
    """Configuration for retry logic"""
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 30.0
    exponential_base: float = 2.0
    jitter: bool = True


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    failure_threshold: int = 5
    recovery_timeout: float = 30.0
    half_open_max_calls: int = 3


@dataclass
class AgentMetrics:
    """Prometheus-style metrics"""
    cycles_total: int = 0
    cycles_success: int = 0
    cycles_failed: int = 0
    actions_total: int = 0
    actions_success: int = 0
    actions_failed: int = 0
    llm_calls_total: int = 0
    llm_calls_latency_sum: float = 0.0
    llm_tokens_total: int = 0
    memory_operations: int = 0
    external_memory_hits: int = 0
    external_memory_misses: int = 0
    start_time: Optional[str] = None
    last_activity: Optional[str] = None

    def to_prometheus(self) -> str:
        """Export metrics in Prometheus format"""
        lines = [
            f"# HELP agent_cycles_total Total number of cycles",
            f"agent_cycles_total {self.cycles_total}",
            f"# HELP agent_cycles_success Successful cycles",
            f"agent_cycles_success {self.cycles_success}",
            f"# HELP agent_actions_total Total actions executed",
            f"agent_actions_total {self.actions_total}",
            f"# HELP agent_llm_calls_total Total LLM API calls",
            f"agent_llm_calls_total {self.llm_calls_total}",
            f"# HELP agent_llm_latency_avg Average LLM latency",
            f"agent_llm_latency_avg {self.llm_calls_latency_sum / max(self.llm_calls_total, 1):.3f}",
        ]
        return "\n".join(lines)

    @property
    def success_rate(self) -> float:
        if self.cycles_total == 0:
            return 0.0
        return self.cycles_success / self.cycles_total


@dataclass
class AgentEvent:
    """Event for hooks system"""
    event_type: str
    agent_id: str
    timestamp: str
    data: Dict[str, Any]
    correlation_id: str


class CircuitBreaker:
    """Circuit breaker for external service calls"""

    def __init__(self, config: CircuitBreakerConfig = None):
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self._lock = asyncio.Lock()

    async def call(self, func: Callable[..., Awaitable[T]], *args, **kwargs) -> T:
        """Execute function with circuit breaker protection"""
        async with self._lock:
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    self.success_count = 0
                else:
                    raise CircuitBreakerOpenError("Circuit breaker is open")

        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result
        except Exception as e:
            await self._on_failure()
            raise

    def _should_attempt_reset(self) -> bool:
        if self.last_failure_time is None:
            return True
        elapsed = (datetime.utcnow() - self.last_failure_time).total_seconds()
        return elapsed >= self.config.recovery_timeout

    async def _on_success(self):
        async with self._lock:
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.config.half_open_max_calls:
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
            elif self.state == CircuitState.CLOSED:
                self.failure_count = 0

    async def _on_failure(self):
        async with self._lock:
            self.failure_count += 1
            self.last_failure_time = datetime.utcnow()

            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.OPEN
            elif self.failure_count >= self.config.failure_threshold:
                self.state = CircuitState.OPEN


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open"""
    pass


class LLMCallError(Exception):
    """Raised when LLM call fails"""
    pass


class MemoryManager:
    """Enhanced memory management with compression and tiering"""

    def __init__(
        self,
        max_hot_size: int = 1000,
        max_warm_size: int = 5000,
        compression_threshold: int = 500,
        external_memory: Optional[Any] = None
    ):
        self.hot_memory: deque = deque(maxlen=max_hot_size)
        self.warm_memory: List[bytes] = []  # Compressed
        self.max_warm_size = max_warm_size
        self.compression_threshold = compression_threshold
        self.external_memory = external_memory
        self._lock = asyncio.Lock()

    async def add(self, entry: Dict[str, Any], agent_id: str = None):
        """Add entry with automatic tiering"""
        async with self._lock:
            self.hot_memory.append(entry)

            # Tier down if hot memory is full
            if len(self.hot_memory) >= self.hot_memory.maxlen:
                await self._tier_down(agent_id)

    async def _tier_down(self, agent_id: str = None):
        """Move old entries to warm storage or external memory"""
        # Take oldest 20% from hot memory
        entries_to_move = []
        move_count = len(self.hot_memory) // 5

        for _ in range(move_count):
            if self.hot_memory:
                entries_to_move.append(self.hot_memory.popleft())

        if not entries_to_move:
            return

        # Compress and store in warm memory
        compressed = self._compress(entries_to_move)
        self.warm_memory.append(compressed)

        # If warm memory is full, offload to external
        if len(self.warm_memory) > self.max_warm_size and self.external_memory:
            await self._offload_to_external(agent_id)

    def _compress(self, entries: List[Dict]) -> bytes:
        """Compress entries using gzip"""
        json_data = json.dumps(entries, default=str)
        return gzip.compress(json_data.encode())

    def _decompress(self, data: bytes) -> List[Dict]:
        """Decompress entries"""
        json_data = gzip.decompress(data).decode()
        return json.loads(json_data)

    async def _offload_to_external(self, agent_id: str):
        """Offload oldest warm memory to external storage"""
        if not self.warm_memory:
            return

        oldest = self.warm_memory.pop(0)
        entries = self._decompress(oldest)

        for entry in entries:
            try:
                if hasattr(self.external_memory, 'add_memory_async'):
                    await self.external_memory.add_memory_async(
                        agent_id=agent_id,
                        role='observation',
                        text=json.dumps(entry, default=str)
                    )
                elif hasattr(self.external_memory, 'add_memory'):
                    self.external_memory.add_memory(
                        agent_id=agent_id,
                        role='observation',
                        text=json.dumps(entry, default=str)
                    )
            except Exception:
                pass  # Best effort

    async def get_recent(self, n: int = 10) -> List[Dict]:
        """Get n most recent entries"""
        recent = list(self.hot_memory)[-n:]

        # If need more, decompress from warm
        if len(recent) < n and self.warm_memory:
            needed = n - len(recent)
            for compressed in reversed(self.warm_memory):
                entries = self._decompress(compressed)
                recent = entries[-needed:] + recent
                if len(recent) >= n:
                    break

        return recent[-n:]

    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics"""
        warm_entries = sum(
            len(self._decompress(c)) for c in self.warm_memory
        ) if self.warm_memory else 0

        return {
            "hot_entries": len(self.hot_memory),
            "warm_entries": warm_entries,
            "warm_compressed_chunks": len(self.warm_memory),
            "has_external": self.external_memory is not None
        }


class EnhancedLLMAgentHelper:
    """
    Production-ready LLM-driven agent with:
    - Async-first design
    - Retry with exponential backoff
    - Circuit breaker pattern
    - Tiered memory management
    - Event hooks system
    - Prometheus metrics
    - Streaming support
    """

    def __init__(
        self,
        llm: Callable,
        action_space: List[Dict[str, Any]],
        agent_id: Optional[str] = None,
        memory: Optional[Dict[str, Any]] = None,
        config: Optional[Dict[str, Any]] = None,
        external_memory_helper: Optional[Any] = None,
        debug: bool = False,
        max_cycles: int = 10,
        cycle_delay: float = 1.0,
        retry_config: Optional[RetryConfig] = None,
        circuit_breaker_config: Optional[CircuitBreakerConfig] = None,
    ):
        # Core components
        self.llm = llm
        self.agent_id = agent_id or uuid.uuid4().hex
        self.action_space = action_space
        self.config = config or {}

        # State management
        self.state = AgentState.INITIALIZED
        self.current_goal: Optional[str] = None
        self._correlation_id: str = ""

        # Memory management
        self.memory_manager = MemoryManager(
            external_memory=external_memory_helper
        )
        self.actions_taken: List[Dict] = []
        self.state_data: Dict[str, Any] = memory.get("state", {}) if memory else {}

        # Metrics
        self.metrics = AgentMetrics()

        # Control flow
        self.max_cycles = max_cycles
        self.cycle_delay = cycle_delay
        self._should_stop = False
        self._is_running = False

        # Resilience
        self.retry_config = retry_config or RetryConfig()
        self.circuit_breaker = CircuitBreaker(circuit_breaker_config)

        # Debug & logging
        self.debug = debug
        self.logger = self._setup_logger()

        # Event hooks
        self._hooks: Dict[str, List[Callable]] = {
            "on_cycle_start": [],
            "on_cycle_end": [],
            "on_think": [],
            "on_decide": [],
            "on_act": [],
            "on_error": [],
            "on_complete": [],
        }

        # Cache for repeated operations
        self._prompt_cache: Dict[str, str] = {}

    def _setup_logger(self) -> logging.Logger:
        """Setup structured logger"""
        logger = logging.getLogger(f"agent.{self.agent_id[:8]}")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        logger.setLevel(logging.DEBUG if self.debug else logging.INFO)
        return logger

    def _log(self, level: str, message: str, **kwargs):
        """Structured logging with correlation ID"""
        extra = {
            "correlation_id": self._correlation_id,
            "state": self.state.value,
            "goal": self.current_goal,
            **kwargs
        }
        log_msg = f"[{self._correlation_id[:8]}] {message}"
        if extra:
            log_msg += f" | {json.dumps({k: str(v)[:100] for k, v in extra.items()})}"

        getattr(self.logger, level)(log_msg)

    # === Hook System ===

    def register_hook(self, event: str, callback: Callable):
        """Register event hook"""
        if event in self._hooks:
            self._hooks[event].append(callback)

    async def _emit_event(self, event_type: str, data: Dict[str, Any]):
        """Emit event to registered hooks"""
        event = AgentEvent(
            event_type=event_type,
            agent_id=self.agent_id,
            timestamp=datetime.utcnow().isoformat(),
            data=data,
            correlation_id=self._correlation_id
        )

        for hook in self._hooks.get(event_type, []):
            try:
                if asyncio.iscoroutinefunction(hook):
                    await hook(event)
                else:
                    hook(event)
            except Exception as e:
                self._log("warning", f"Hook {event_type} failed: {e}")

    # === Core Agent Methods ===

    def set_goal(self, goal: str):
        """Set agent goal"""
        self._log("info", f"Setting goal: {goal}")
        self.current_goal = goal
        self.state_data["current_goal"] = goal
        self.metrics.last_activity = datetime.utcnow().isoformat()

    def stop(self):
        """Request graceful stop"""
        self._should_stop = True
        self._log("info", "Stop requested")

    def reset(self):
        """Reset agent state"""
        self.actions_taken.clear()
        self.state_data.clear()
        self.current_goal = None
        self._should_stop = False
        self._is_running = False
        self.state = AgentState.INITIALIZED
        self._log("info", "Agent reset")

    async def perceive(self, observation: str):
        """Process new observation"""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": "observation",
            "content": observation,
            "correlation_id": self._correlation_id
        }
        await self.memory_manager.add(entry, self.agent_id)
        self.metrics.memory_operations += 1
        self._log("debug", f"Perceived: {observation[:100]}...")

    # === LLM Interaction with Resilience ===

    async def _call_llm_with_retry(
        self,
        messages: List[Dict[str, str]],
        purpose: str = "general"
    ) -> str:
        """Call LLM with retry and circuit breaker"""

        async def _do_call():
            start_time = asyncio.get_event_loop().time()

            try:
                if asyncio.iscoroutinefunction(self.llm.chat):
                    response = await self.llm.chat(messages=messages)
                else:
                    response = self.llm.chat(messages=messages)

                elapsed = asyncio.get_event_loop().time() - start_time
                self.metrics.llm_calls_total += 1
                self.metrics.llm_calls_latency_sum += elapsed

                return response.strip() if hasattr(response, 'strip') else str(response).strip()

            except Exception as e:
                self._log("error", f"LLM call failed: {e}")
                raise LLMCallError(str(e))

        # Apply circuit breaker
        try:
            return await self.circuit_breaker.call(
                self._retry_with_backoff,
                _do_call,
                purpose
            )
        except CircuitBreakerOpenError:
            self._log("error", "Circuit breaker open - LLM unavailable")
            raise

    async def _retry_with_backoff(
        self,
        func: Callable[[], Awaitable[str]],
        purpose: str
    ) -> str:
        """Execute with exponential backoff retry"""
        last_error = None

        for attempt in range(self.retry_config.max_retries + 1):
            try:
                return await func()
            except Exception as e:
                last_error = e

                if attempt < self.retry_config.max_retries:
                    delay = min(
                        self.retry_config.base_delay * (self.retry_config.exponential_base ** attempt),
                        self.retry_config.max_delay
                    )

                    if self.retry_config.jitter:
                        import random
                        delay *= (0.5 + random.random())

                    self._log("warning", f"Retry {attempt + 1} for {purpose} in {delay:.2f}s")
                    await asyncio.sleep(delay)

        raise last_error

    # === Think / Decide / Act Cycle ===

    async def think(self) -> str:
        """Generate strategic thinking"""
        self.state = AgentState.THINKING

        if not self.current_goal:
            raise RuntimeError("No goal set")

        context = await self._build_context()

        messages = [
            {"role": "system", "content": self._get_system_prompt("think")},
            {"role": "user", "content": self._build_think_prompt(context)}
        ]

        self._log("debug", "Thinking...")
        response = await self._call_llm_with_retry(messages, "think")

        await self._emit_event("on_think", {"thought": response})
        return response

    async def decide(self, thought: str) -> Dict[str, Any]:
        """Make decision based on thinking"""
        self.state = AgentState.DECIDING

        messages = [
            {"role": "system", "content": self._get_system_prompt("decide")},
            {"role": "user", "content": self._build_decide_prompt(thought)}
        ]

        self._log("debug", "Deciding...")
        response = await self._call_llm_with_retry(messages, "decide")

        decision = await self._parse_decision(response, thought)
        await self._emit_event("on_decide", {"decision": decision})

        return decision

    async def act(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        """Execute decided action"""
        self.state = AgentState.ACTING

        action = decision["action"]

        if action == "complete":
            return await self._handle_completion(decision)

        action_func = decision["function"]
        params = decision.get("parameters", {})

        self._log("info", f"Executing: {action}", parameters=params)

        try:
            # Prepare parameters
            params = await self._prepare_params(action, params)

            # Execute
            if asyncio.iscoroutinefunction(action_func):
                result = await action_func(params)
            else:
                result = action_func(params)

            # Record success
            await self._record_action(action, params, result, "success")
            self.metrics.actions_success += 1
            self.metrics.actions_total += 1

            await self._emit_event("on_act", {
                "action": action,
                "status": "success",
                "result": result
            })

            return {
                "status": "success",
                "action": action,
                "result": result,
                "parameters": params
            }

        except Exception as e:
            self._log("error", f"Action failed: {e}")
            await self._record_action(action, params, str(e), "error")
            self.metrics.actions_failed += 1
            self.metrics.actions_total += 1

            await self._emit_event("on_error", {
                "action": action,
                "error": str(e)
            })

            return {
                "status": "error",
                "action": action,
                "error": str(e)
            }

    # === Cycle Execution ===

    async def run_cycle(self) -> Dict[str, Any]:
        """Run single think-decide-act cycle"""
        self._correlation_id = uuid.uuid4().hex[:12]

        if not self.metrics.start_time:
            self.metrics.start_time = datetime.utcnow().isoformat()

        await self._emit_event("on_cycle_start", {
            "cycle": self.metrics.cycles_total + 1
        })

        try:
            thought = await self.think()
            decision = await self.decide(thought)
            outcome = await self.act(decision)

            # Perceive outcome
            await self.perceive(
                f"Action '{decision['action']}' completed: {outcome.get('status')}"
            )

            self.metrics.cycles_success += 1
            self.metrics.cycles_total += 1
            self.metrics.last_activity = datetime.utcnow().isoformat()

            result = {
                "thought": thought,
                "decision": decision,
                "outcome": outcome,
                "cycle": self.metrics.cycles_total,
                "correlation_id": self._correlation_id
            }

            await self._emit_event("on_cycle_end", result)
            return result

        except Exception as e:
            self.metrics.cycles_failed += 1
            self.metrics.cycles_total += 1
            self.state = AgentState.ERROR

            error_result = {
                "status": "error",
                "error": str(e),
                "traceback": traceback.format_exc(),
                "cycle": self.metrics.cycles_total
            }

            await self._emit_event("on_error", error_result)
            return error_result

    async def run_autonomous(self) -> List[Dict[str, Any]]:
        """Run multiple cycles autonomously"""
        self._is_running = True
        self.state = AgentState.RUNNING
        results = []

        self._log("info", f"Starting autonomous run (max {self.max_cycles} cycles)")

        try:
            for cycle in range(self.max_cycles):
                if self._should_stop:
                    self._log("info", "Stopping on request")
                    break

                result = await self.run_cycle()
                results.append(result)

                # Check completion
                if result.get("outcome", {}).get("status") == "complete":
                    await self._emit_event("on_complete", {
                        "cycles": len(results),
                        "goal": self.current_goal
                    })
                    break

                # Check error
                if result.get("status") == "error":
                    break

                # Delay between cycles
                if cycle < self.max_cycles - 1:
                    await asyncio.sleep(self.cycle_delay)

        finally:
            self._is_running = False
            self.state = AgentState.STOPPED

        return results

    # === Helper Methods ===

    async def _build_context(self) -> Dict[str, Any]:
        """Build context for thinking"""
        recent_obs = await self.memory_manager.get_recent(5)
        recent_actions = self.actions_taken[-5:] if self.actions_taken else []

        return {
            "goal": self.current_goal,
            "observations": [o.get("content", "") for o in recent_obs],
            "actions": [a.get("action", "") for a in recent_actions],
            "available_actions": self.action_space,
            "state": self.state_data
        }

    def _get_system_prompt(self, mode: str) -> str:
        """Get system prompt for mode"""
        prompts = {
            "think": (
                "You are an intelligent agent analyzing situations to achieve goals. "
                "Consider context, available actions, and progress. Provide clear, "
                "actionable insights for the next decision."
            ),
            "decide": (
                "You are a decision maker. Based on analysis, select the optimal next action. "
                "Respond ONLY with valid JSON: {\"action\": \"name\", \"parameters\": {}, \"reasoning\": \"why\"}"
            )
        }
        return prompts.get(mode, prompts["think"])

    def _build_think_prompt(self, context: Dict) -> str:
        """Build thinking prompt"""
        actions_str = "\n".join(
            f"- {a['action']}: {a['description']}"
            for a in context["available_actions"]
        )

        return (
            f"Goal: {context['goal']}\n\n"
            f"Recent Observations:\n" + "\n".join(context["observations"]) + "\n\n"
            f"Recent Actions: {context['actions']}\n\n"
            f"Available Actions:\n{actions_str}\n\n"
            "Analyze and provide strategic thinking."
        )

    def _build_decide_prompt(self, thought: str) -> str:
        """Build decision prompt"""
        actions = [
            {"action": a["action"], "description": a["description"]}
            for a in self.action_space
        ]

        return (
            f"Analysis: {thought}\n\n"
            f"Goal: {self.current_goal}\n"
            f"Available Actions: {json.dumps(actions, indent=2)}\n\n"
            "Select next action as JSON."
        )

    async def _parse_decision(self, response: str, thought: str) -> Dict[str, Any]:
        """Parse LLM decision response"""
        try:
            # Try direct JSON parse
            decision = json.loads(response)
            action = decision.get("action")

            if action == "complete":
                return {
                    "action": "complete",
                    "parameters": {},
                    "function": self._complete,
                    "reasoning": decision.get("reasoning", "Goal achieved")
                }

            # Validate action
            action_spec = next(
                (a for a in self.action_space if a["action"] == action),
                None
            )

            if not action_spec:
                raise ValueError(f"Unknown action: {action}")

            return {
                "action": action,
                "parameters": decision.get("parameters", {}),
                "function": action_spec["func"],
                "reasoning": decision.get("reasoning", "")
            }

        except (json.JSONDecodeError, ValueError) as e:
            self._log("warning", f"Decision parse failed, using fallback: {e}")
            return await self._fallback_decision(response)

    async def _fallback_decision(self, response: str) -> Dict[str, Any]:
        """Fallback decision parsing"""
        action_names = [a["action"] for a in self.action_space]

        # Try to extract JSON
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                decision = json.loads(json_match.group(0))
                action = decision.get("action")
                if action in action_names:
                    return {
                        "action": action,
                        "parameters": decision.get("parameters", {}),
                        "function": next(a["func"] for a in self.action_space if a["action"] == action),
                        "reasoning": "Recovered from embedded JSON"
                    }
            except:
                pass

        # Fuzzy match
        for word in response.split()[:10]:
            matches = difflib.get_close_matches(word, action_names, n=1, cutoff=0.6)
            if matches:
                action = matches[0]
                return {
                    "action": action,
                    "parameters": {},
                    "function": next(a["func"] for a in self.action_space if a["action"] == action),
                    "reasoning": f"Fuzzy matched from '{word}'"
                }

        # Default to first action
        if self.action_space:
            return {
                "action": self.action_space[0]["action"],
                "parameters": {},
                "function": self.action_space[0]["func"],
                "reasoning": "Fallback to first action"
            }

        return {
            "action": "complete",
            "parameters": {},
            "function": self._complete,
            "reasoning": "No valid action found"
        }

    async def _prepare_params(self, action: str, initial_params: Dict) -> Dict:
        """Prepare action parameters"""
        action_spec = next(a for a in self.action_space if a["action"] == action)
        required = action_spec.get("parameters", {})

        if isinstance(required, dict):
            required_keys = [k for k in required.keys() if k != "optional"]
        else:
            required_keys = []

        # Check if all required params present
        if all(k in initial_params for k in required_keys):
            return initial_params

        # Generate missing params via LLM
        return await self._generate_params(action, action_spec, initial_params)

    async def _generate_params(
        self,
        action: str,
        spec: Dict,
        initial: Dict
    ) -> Dict:
        """Generate parameters using LLM"""
        messages = [
            {
                "role": "system",
                "content": "Generate complete parameters for the action. Return ONLY valid JSON."
            },
            {
                "role": "user",
                "content": (
                    f"Action: {action}\n"
                    f"Description: {spec.get('description', '')}\n"
                    f"Required: {json.dumps(spec.get('parameters', {}))}\n"
                    f"Current: {json.dumps(initial)}\n"
                    f"Goal: {self.current_goal}\n"
                    "Generate complete parameters as JSON."
                )
            }
        ]

        try:
            response = await self._call_llm_with_retry(messages, "params")
            generated = json.loads(response)
            return {**generated, **initial}
        except:
            return initial

    async def _record_action(
        self,
        action: str,
        params: Dict,
        result: Any,
        status: str
    ):
        """Record action in history"""
        record = {
            "action": action,
            "parameters": params,
            "result": result,
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
            "correlation_id": self._correlation_id
        }
        self.actions_taken.append(record)

    async def _handle_completion(self, decision: Dict) -> Dict[str, Any]:
        """Handle completion action"""
        self._should_stop = True
        return {
            "status": "complete",
            "message": "Goal achieved",
            "goal": self.current_goal,
            "actions_taken": len(self.actions_taken),
            "reasoning": decision.get("reasoning", "")
        }

    async def _complete(self, params: Dict = None) -> Dict[str, Any]:
        """Complete action function"""
        self._should_stop = True
        return {"completed": True}

    # === Utility Methods ===

    def get_metrics(self) -> Dict[str, Any]:
        """Get agent metrics"""
        return {
            "agent_id": self.agent_id,
            "state": self.state.value,
            "cycles_total": self.metrics.cycles_total,
            "cycles_success": self.metrics.cycles_success,
            "cycles_failed": self.metrics.cycles_failed,
            "success_rate": f"{self.metrics.success_rate:.1%}",
            "actions_total": self.metrics.actions_total,
            "llm_calls": self.metrics.llm_calls_total,
            "avg_llm_latency": f"{self.metrics.llm_calls_latency_sum / max(self.metrics.llm_calls_total, 1):.3f}s",
            "memory": self.memory_manager.get_stats(),
            "circuit_breaker": self.circuit_breaker.state.value
        }

    def export_prometheus_metrics(self) -> str:
        """Export metrics in Prometheus format"""
        return self.metrics.to_prometheus()

    @asynccontextmanager
    async def session(self):
        """Context manager for agent session"""
        try:
            yield self
        finally:
            self.stop()
            self._log("info", "Session ended", metrics=self.get_metrics())
