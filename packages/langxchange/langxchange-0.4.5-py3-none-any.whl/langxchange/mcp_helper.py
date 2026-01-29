import asyncio
import json
import os
import time
import logging
import sys
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Union
from contextlib import asynccontextmanager, AsyncExitStack
from functools import lru_cache
from collections import OrderedDict

# MCP SDK imports
from mcp import ClientSession, StdioServerParameters, stdio_client, types
from mcp.client.sse import sse_client


class MCPServiceManagerError(Exception):
    """Custom exception for MCP service manager errors."""
    pass


@dataclass
class ServerHealth:
    """Tracks health metrics for an MCP server."""
    last_success: float = 0.0
    last_failure: float = 0.0
    consecutive_failures: int = 0
    total_calls: int = 0
    total_errors: int = 0
    priority: int = 0  # Added priority field

    @property
    def is_healthy(self) -> bool:
        return self.consecutive_failures < 3

    @property
    def error_rate(self) -> float:
        if self.total_calls == 0:
            return 0.0
        return self.total_errors / self.total_calls


@dataclass
class CachedToolList:
    """TTL-cached tool list."""
    tools: Any
    cached_at: float
    ttl: float = 300.0  # 5 minutes default

    @property
    def is_valid(self) -> bool:
        return (time.monotonic() - self.cached_at) < self.ttl


@dataclass
class ManagedSession:
    """Wrapper for ClientSession with metadata."""
    session: ClientSession
    exit_stack: AsyncExitStack
    created_at: float = field(default_factory=time.monotonic)
    last_used: float = field(default_factory=time.monotonic)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    def touch(self):
        self.last_used = time.monotonic()


@dataclass
class ToolRegistryEntry:
    """Registry entry for an MCP tool with routing metadata."""
    server_name: str
    original_tool_name: str
    tool_description: str
    input_schema: Dict[str, Any]
    capabilities: List[str] = field(default_factory=list)
    
    @property
    def tool_id(self) -> str:
        """Unique identifier for this tool."""
        return f"{self.server_name}::{self.original_tool_name}"


@dataclass
class ToolMetadata:
    """Metadata about a tool for external consumers."""
    name: str
    description: str
    input_schema: Dict[str, Any]
    server_name: str
    namespace: str
    capabilities: List[str] = field(default_factory=list)



class MCPServiceManager:
    """
    High-performance MCP server lifecycle and session manager.
    
    Features:
    - Async-first design for non-blocking I/O
    - Per-server locks to minimize contention
    - Connection pooling with health monitoring
    - TTL-based caching for tool metadata
    - Automatic reconnection on failure
    - Graceful shutdown handling
    """

    def __init__(
        self,
        config_path: Optional[str] = None,
        config_dict: Optional[Dict[str, Any]] = None,
        logger: Optional[logging.Logger] = None,
        max_concurrent_calls: int = 10,
        session_idle_timeout: float = 300.0,
        tool_cache_ttl: float = 300.0,
        roots: Optional[List[Dict[str, Any]]] = None,
    ):
        self.config_path = config_path
        self.config_dict = config_dict
        self.logger = logger or self._setup_logger()
        self.max_concurrent_calls = max_concurrent_calls
        self.session_idle_timeout = session_idle_timeout
        self.tool_cache_ttl = tool_cache_ttl
        self.roots = roots or []

        # Server state
        self._server_configs: Dict[str, Dict[str, Any]] = {}
        self._sessions: Dict[str, ManagedSession] = {}
        self._health: Dict[str, ServerHealth] = {}
        self._tool_cache: Dict[str, CachedToolList] = {}

        # Tool registry and capabilities (NEW)
        self._tool_registry: Dict[str, ToolRegistryEntry] = {}
        self._server_capabilities: Dict[str, List[str]] = {}
        self._server_priorities: Dict[str, int] = {} # Added priorities map

        # Concurrency control
        self._server_locks: Dict[str, asyncio.Lock] = {}
        self._global_semaphore: Optional[asyncio.Semaphore] = None
        self._shutdown_event = asyncio.Event()

        # Background tasks
        self._cleanup_task: Optional[asyncio.Task] = None

        self._load_config()

    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger("langxchange.mcp")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(levelname)s - [%(name)s] %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

    def _load_config(self):
        """Load and validate MCP server configurations."""
        if self.config_dict:
            config = self.config_dict
        elif self.config_path:
            if not os.path.exists(self.config_path):
                raise MCPServiceManagerError(
                    f"MCP config not found: {self.config_path}"
                )

            with open(self.config_path, "r") as f:
                config = json.load(f)
        else:
            raise MCPServiceManagerError(
                "No MCP configuration provided (path or dict)"
            )

        servers = config.get("servers")
        if not servers:
            # Fallback for older config format if needed, but sticking to 'servers' list
            servers = config.get("mcpServers")
            if isinstance(servers, dict):
                # Convert dict format to list format
                servers = [{"name": k, **v} for k, v in servers.items()]

        if not servers:
            raise MCPServiceManagerError("No MCP servers defined in config")

        for server in servers:
            name = server.get("name")
            if not name:
                raise MCPServiceManagerError("MCP server missing 'name'")

            # Validate required fields based on transport
            transport = server.get("transport", "stdio")
            if transport == "stdio" and "command" not in server:
                raise MCPServiceManagerError(
                    f"Server '{name}' missing 'command' for stdio transport"
                )
            if transport == "sse" and "url" not in server:
                raise MCPServiceManagerError(
                    f"Server '{name}' missing 'url' for SSE transport"
                )

            self._server_configs[name] = server
            self._server_locks[name] = asyncio.Lock()
            self._health[name] = ServerHealth()

        self.logger.info(
            f"Loaded {len(self._server_configs)} MCP server definitions"
        )

    async def initialize(self):
        """Initialize async resources. Call after event loop is running."""
        self._global_semaphore = asyncio.Semaphore(self.max_concurrent_calls)
        self._cleanup_task = asyncio.create_task(self._cleanup_idle_sessions())
        self.logger.info("MCPServiceManager initialized")

    async def _cleanup_idle_sessions(self):
        """Background task to clean up idle sessions."""
        while not self._shutdown_event.is_set():
            try:
                await asyncio.sleep(60)  # Check every minute
                await self._evict_idle_sessions()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Cleanup task error: {e}")

    async def _evict_idle_sessions(self):
        """Remove sessions that have been idle too long."""
        now = time.monotonic()
        to_evict = []

        for name, managed in self._sessions.items():
            idle_time = now - managed.last_used
            if idle_time > self.session_idle_timeout:
                to_evict.append(name)

        for name in to_evict:
            self.logger.info(f"Evicting idle session: {name}")
            await self.stop_server(name)

    async def _start_stdio_server(
        self,
        name: str,
        config: Dict[str, Any]
    ) -> ManagedSession:
        """Start a stdio-based MCP server."""
        server_params = StdioServerParameters(
            command=config["command"],
            args=config.get("args", []),
            env={**os.environ, **config.get("env", {})},
            cwd=config.get("cwd"),
        )

        self.logger.debug(f"Starting stdio server '{name}': {server_params.command} {server_params.args}")

        exit_stack = AsyncExitStack()
        try:
            read, write = await exit_stack.enter_async_context(stdio_client(server_params))
            session = await exit_stack.enter_async_context(
                ClientSession(
                    read, 
                    write,
                    list_roots_callback=self._list_roots_callback
                )
            )
            
            self.logger.info(f"MCP: Initializing stdio session for '{name}'...")
            start_time = time.monotonic()
            await session.initialize()
            self.logger.info(f"MCP: Stdio session for '{name}' initialized in {time.monotonic() - start_time:.2f}s")
            
            return ManagedSession(
                session=session,
                exit_stack=exit_stack,
            )
        except Exception:
            await exit_stack.aclose()
            raise

    async def _start_sse_server(
        self,
        name: str,
        config: Dict[str, Any]
    ) -> ManagedSession:
        """Start an SSE-based MCP server connection."""
        url = config["url"]
        headers = config.get("headers", {})

        self.logger.debug(f"Connecting to SSE server '{name}': {url}")

        exit_stack = AsyncExitStack()
        try:
            read, write = await exit_stack.enter_async_context(sse_client(url=url, headers=headers))
            session = await exit_stack.enter_async_context(
                ClientSession(
                    read, 
                    write,
                    list_roots_callback=self._list_roots_callback
                )
            )
            
            await session.initialize()
            
            return ManagedSession(
                session=session,
                exit_stack=exit_stack,
            )
        except Exception:
            await exit_stack.aclose()
            raise

    async def _get_or_create_session(self, name: str) -> ManagedSession:
        """Get existing session or create new one with proper locking."""
        # Fast path: check without lock
        if name in self._sessions:
            managed = self._sessions[name]
            managed.touch()
            return managed

        # Slow path: acquire per-server lock
        lock = self._server_locks.get(name)
        if not lock:
            raise MCPServiceManagerError(f"Unknown MCP server: {name}")

        async with lock:
            # Double-check after acquiring lock
            if name in self._sessions:
                managed = self._sessions[name]
                managed.touch()
                return managed

            config = self._server_configs[name]
            transport_type = config.get("transport", "stdio")

            try:
                if transport_type == "stdio":
                    managed = await self._start_stdio_server(name, config)
                elif transport_type == "sse":
                    managed = await self._start_sse_server(name, config)
                else:
                    raise MCPServiceManagerError(
                        f"Unsupported transport: {transport_type}"
                    )

                self._sessions[name] = managed
                self._health[name].last_success = time.monotonic()
                self._health[name].consecutive_failures = 0
                self.logger.info(f"Started MCP server '{name}'")
                return managed

            except Exception as e:
                health = self._health[name]
                health.last_failure = time.monotonic()
                health.consecutive_failures += 1
                health.total_errors += 1
                raise MCPServiceManagerError(
                    f"Failed to start server '{name}': {e}"
                ) from e

    async def _list_roots_callback(self, params: Any = None) -> types.ListRootsResult:
        """Callback to provide roots to MCP servers."""
        self.logger.info(f"MCP: Server requested roots list. Providing {len(self.roots)} roots.")
        roots = [
            types.Root(
                uri=root.get("uri"),
                name=root.get("name")
            )
            for root in self.roots
            if root.get("uri")
        ]
        return types.ListRootsResult(roots=roots)

    async def start_server(self, name: str) -> ClientSession:
        """Start or get existing server session."""
        managed = await self._get_or_create_session(name)
        return managed.session

    async def stop_server(self, name: str):
        """Stop a running MCP server."""
        lock = self._server_locks.get(name)
        if not lock:
            return

        async with lock:
            managed = self._sessions.pop(name, None)
            if not managed:
                return

            # Clear cached tools
            self._tool_cache.pop(name, None)

            try:
                await managed.exit_stack.aclose()
            except Exception as e:
                self.logger.warning(f"Error closing session '{name}': {e}")

            self.logger.info(f"Stopped MCP server '{name}'")

    async def list_tools(
        self,
        server_name: str,
        force_refresh: bool = False
    ) -> Any:
        """
        List available tools from server with caching.
        
        Args:
            server_name: Name of the MCP server
            force_refresh: Bypass cache and fetch fresh data
        """
        # Check cache first
        if not force_refresh and server_name in self._tool_cache:
            cached = self._tool_cache[server_name]
            if cached.is_valid:
                return cached.tools

        session = await self.start_server(server_name)
        tools = await session.list_tools()

        # Update cache
        self._tool_cache[server_name] = CachedToolList(
            tools=tools,
            cached_at=time.monotonic(),
            ttl=self.tool_cache_ttl,
        )

        return tools

    def register_server_capabilities(
        self,
        server_name: str,
        capabilities: List[str],
        priority: int = 0
    ) -> None:
        """
        Register capabilities for a server.
        
        Args:
            server_name: Name of the MCP server
            capabilities: List of capability tags (e.g., ["file_operations", "web_scraping"])
        """
        if server_name not in self._server_configs:
            raise MCPServiceManagerError(f"Unknown server: {server_name}")
        
        self._server_capabilities[server_name] = capabilities
        self._server_priorities[server_name] = priority
        
        # Also update health object if it exists
        if server_name in self._health:
            self._health[server_name].priority = priority
            
        self.logger.info(f"Registered capabilities for '{server_name}': {capabilities} (priority: {priority})")

    def get_servers_by_capability(self, capability: str) -> List[str]:
        """
        Get all servers that have a specific capability.
        
        Args:
            capability: Capability tag to search for
            
        Returns:
            List of server names with this capability
        """
        return [
            server_name
            for server_name, caps in self._server_capabilities.items()
            if capability in caps
        ]

    async def get_all_tools_with_metadata(self) -> Dict[str, ToolMetadata]:
        """
        Fetch all tools from all servers with routing metadata.
        
        Returns:
            Dictionary mapping tool IDs to ToolMetadata objects
        """
        all_tools = {}
        
        for server_name in self._server_configs.keys():
            try:
                tools_result = await self.list_tools(server_name)
                server_caps = self._server_capabilities.get(server_name, [])
                
                for tool in tools_result.tools:
                    tool_id = f"{server_name}::{tool.name}"
                    
                    # Create registry entry
                    registry_entry = ToolRegistryEntry(
                        server_name=server_name,
                        original_tool_name=tool.name,
                        tool_description=tool.description,
                        input_schema=tool.inputSchema,
                        capabilities=server_caps.copy()
                    )
                    
                    # Store in registry
                    self._tool_registry[tool_id] = registry_entry
                    
                    # Create metadata for external use
                    all_tools[tool_id] = ToolMetadata(
                        name=tool.name,
                        description=tool.description,
                        input_schema=tool.inputSchema,
                        server_name=server_name,
                        namespace=server_name,
                        capabilities=server_caps.copy()
                    )
                    
            except Exception as e:
                self.logger.error(f"Failed to fetch tools from '{server_name}': {e}")
        
        self.logger.info(f"Built tool registry with {len(all_tools)} tools from {len(self._server_configs)} servers")
        return all_tools

    def select_best_server(
        self,
        candidates: List[str],
        prefer_healthy: bool = True
    ) -> Optional[str]:
        """
        Select the best server from candidates based on health metrics.
        
        Args:
            candidates: List of server names to choose from
            prefer_healthy: Prioritize healthy servers
            
        Returns:
            Best server name or None if no valid candidates
        """
        if not candidates:
            return None
        
        if len(candidates) == 1:
            return candidates[0]
        
        # Filter to healthy servers if requested
        if prefer_healthy:
            healthy = [s for s in candidates if self._health.get(s, ServerHealth()).is_healthy]
            if healthy:
                candidates = healthy
        
        # Sort by priority (higher is better), error rate (lower is better), and last success time (more recent is better)
        def score_server(server_name: str) -> tuple:
            health = self._health.get(server_name, ServerHealth())
            priority = self._server_priorities.get(server_name, health.priority)
            # Return tuple: (-priority, error_rate, -last_success) for sorting
            # Negative priority so higher priority is better (sorted ascending)
            return (-priority, health.error_rate, -health.last_success)
        
        candidates.sort(key=score_server)
        return candidates[0]

    async def select_best_server_for_tool(self, tool_name: str) -> Optional[str]:
        """
        Intelligently select the best server that provides the given tool.
        
        Args:
            tool_name: Original name of the tool
            
        Returns:
            Best server name or None if tool not found
        """
        # Find all servers that provide this tool
        providing_servers = []
        
        # Check registry first
        for tool_id, entry in self._tool_registry.items():
            if entry.original_tool_name == tool_name:
                providing_servers.append(entry.server_name)
        
        # If not in registry, try to find by listing tools (fallback)
        if not providing_servers:
            for server_name in self._server_configs.keys():
                try:
                    tools_result = await self.list_tools(server_name)
                    if any(t.name == tool_name for t in tools_result.tools):
                        providing_servers.append(server_name)
                except Exception:
                    continue
                    
        if not providing_servers:
            return None
            
        # Use health and priority aware selection
        return self.select_best_server(providing_servers)

    def resolve_tool_server(
        self,
        tool_name: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Resolve which server should handle a tool call.
        
        Args:
            tool_name: Name of the tool (may include namespace prefix)
            context: Optional context for intelligent routing
            
        Returns:
            Server name or None if tool not found
        """
        # Check if tool_name includes namespace (server::tool format)
        if "::" in tool_name:
            namespace, actual_tool = tool_name.split("::", 1)
            # Direct lookup in registry
            if tool_name in self._tool_registry:
                return self._tool_registry[tool_name].server_name
            # Try with just the namespace
            if namespace in self._server_configs:
                return namespace
        
        # Search registry for matching tool name
        matching_servers = []
        for tool_id, entry in self._tool_registry.items():
            if entry.original_tool_name == tool_name:
                matching_servers.append(entry.server_name)
        
        if not matching_servers:
            self.logger.warning(f"Tool '{tool_name}' not found in registry")
            return None
        
        # Use context hints if provided
        if context and "preferred_capability" in context:
            capability = context["preferred_capability"]
            capable_servers = [
                s for s in matching_servers
                if capability in self._server_capabilities.get(s, [])
            ]
            if capable_servers:
                matching_servers = capable_servers
        
        # Select best server from matches
        return self.select_best_server(matching_servers)


    async def call_tool(
        self,
        server_name: str,
        tool_name: str,
        arguments: Dict[str, Any],
        timeout: float = 30.0,
    ) -> Any:
        """
        Call a tool on an MCP server with concurrency control.
        
        Args:
            server_name: Name of the MCP server
            tool_name: Name of the tool to call
            arguments: Tool arguments
            timeout: Maximum time to wait for response
        """
        if self._global_semaphore is None:
            raise MCPServiceManagerError(
                "Manager not initialized. Call initialize() first."
            )

        health = self._health[server_name]
        health.total_calls += 1

        async with self._global_semaphore:
            managed = await self._get_or_create_session(server_name)

            try:
                async with managed.lock:  # Serialize calls per session
                    managed.touch()
                    result = await asyncio.wait_for(
                        managed.session.call_tool(
                            name=tool_name,
                            arguments=arguments,
                        ),
                        timeout=timeout,
                    )

                health.last_success = time.monotonic()
                health.consecutive_failures = 0
                return result

            except asyncio.TimeoutError:
                health.last_failure = time.monotonic()
                health.consecutive_failures += 1
                health.total_errors += 1
                raise MCPServiceManagerError(
                    f"Tool call timed out ({server_name}.{tool_name})"
                )
            except Exception as e:
                health.last_failure = time.monotonic()
                health.consecutive_failures += 1
                health.total_errors += 1

                # Auto-reconnect on connection errors
                if health.consecutive_failures >= 2:
                    self.logger.warning(
                        f"Consecutive failures for '{server_name}', "
                        "attempting reconnect"
                    )
                    await self.stop_server(server_name)

                raise MCPServiceManagerError(
                    f"Tool call failed ({server_name}.{tool_name}): {e}"
                ) from e

    async def call_tools_parallel(
        self,
        calls: List[Dict[str, Any]],
        timeout: float = 30.0,
    ) -> List[Any]:
        """
        Execute multiple tool calls in parallel.
        
        Args:
            calls: List of dicts with 'server_name', 'tool_name', 'arguments'
            timeout: Maximum time per call
            
        Returns:
            List of results in same order as input calls
        """
        tasks = [
            self.call_tool(
                server_name=call["server_name"],
                tool_name=call["tool_name"],
                arguments=call.get("arguments", {}),
                timeout=timeout,
            )
            for call in calls
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert exceptions to MCPServiceManagerError for consistency
        processed = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                call = calls[i]
                self.logger.error(
                    f"Parallel call failed: {call['server_name']}."
                    f"{call['tool_name']}: {result}"
                )
            processed.append(result)

        return processed

    def get_health(self, server_name: str) -> ServerHealth:
        """Get health metrics for a server."""
        return self._health.get(server_name, ServerHealth())

    def get_all_health(self) -> Dict[str, ServerHealth]:
        """Get health metrics for all servers."""
        return dict(self._health)

    @asynccontextmanager
    async def session_context(self, server_name: str):
        """Context manager for session lifecycle."""
        session = await self.start_server(server_name)
        try:
            yield session
        finally:
            # Session stays alive for reuse, just update last_used
            if server_name in self._sessions:
                self._sessions[server_name].touch()

    async def shutdown(self):
        """Gracefully shutdown all servers and cleanup resources."""
        self._shutdown_event.set()

        # Cancel cleanup task
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        # Stop all servers concurrently
        stop_tasks = [
            self.stop_server(name)
            for name in list(self._sessions.keys())
        ]
        if stop_tasks:
            await asyncio.gather(*stop_tasks, return_exceptions=True)

        self._tool_cache.clear()
        self.logger.info("MCPServiceManager shutdown complete")

    async def __aenter__(self):
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.shutdown()