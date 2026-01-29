import asyncio
import json
import os
import sys
import logging
from typing import Dict, Any, List

# Add the parent directory to sys.path to import langxchange
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from langxchange.mcp_helper import MCPServiceManager, ServerHealth, ToolRegistryEntry

async def test_mcp_registry_and_routing():
    print("Testing MCP Registry and Routing...")
    
    # Mock config
    config = {
        "servers": [
            {
                "name": "server1",
                "transport": "stdio",
                "command": "echo",
                "args": ["server1"]
            },
            {
                "name": "server2",
                "transport": "stdio",
                "command": "echo",
                "args": ["server2"]
            }
        ]
    }
    
    # Initialize manager
    manager = MCPServiceManager(config_dict=config)
    
    # 1. Test Capability Registration with Priority
    print("\n1. Testing Capability Registration with Priority...")
    manager.register_server_capabilities("server1", ["files", "read"], priority=10)
    manager.register_server_capabilities("server2", ["files", "write"], priority=5)
    
    servers = manager.get_servers_by_capability("files")
    print(f"Servers with 'files' capability: {servers}")
    assert "server1" in servers and "server2" in servers
    
    servers = manager.get_servers_by_capability("read")
    print(f"Servers with 'read' capability: {servers}")
    assert "server1" in servers
    assert "server2" not in servers
    
    # Check priority storage
    assert manager._server_priorities["server1"] == 10
    assert manager._server_priorities["server2"] == 5

    # 2. Test Tool Registry (Mocking tools)
    print("\n2. Testing Tool Registry...")
    
    # Manually populate registry since we don't want to actually start servers in this unit test
    manager._tool_registry["server1::read_file"] = ToolRegistryEntry(
        server_name="server1",
        original_tool_name="read_file",
        tool_description="Read a file",
        input_schema={},
        capabilities=["files", "read"]
    )
    manager._tool_registry["server2::write_file"] = ToolRegistryEntry(
        server_name="server2",
        original_tool_name="write_file",
        tool_description="Write a file",
        input_schema={},
        capabilities=["files", "write"]
    )
    manager._tool_registry["server2::read_file"] = ToolRegistryEntry(
        server_name="server2",
        original_tool_name="read_file",
        tool_description="Read a file (server2 version)",
        input_schema={},
        capabilities=["files", "read"]
    )
    
    # 3. Test Server Resolution
    print("\n3. Testing Server Resolution...")
    
    # Test direct resolution with namespace
    server = manager.resolve_tool_server("server1::read_file")
    print(f"Resolved 'server1::read_file': {server}")
    assert server == "server1"
    
    # Test resolution by name (multiple matches)
    server = manager.resolve_tool_server("read_file")
    print(f"Resolved 'read_file' (multiple matches): {server}")
    assert server in ["server1", "server2"]
    
    # Test new intelligent routing method
    server_int = await manager.select_best_server_for_tool("read_file")
    print(f"Resolved 'read_file' (Intelligent): {server_int}")
    # server1 has priority 10, server2 has priority 5
    assert server_int == "server1"
    
    # Test resolution with context (capability hint)
    context = {"preferred_capability": "read"}
    server = manager.resolve_tool_server("read_file", context=context)
    print(f"Resolved 'read_file' with 'read' capability hint: {server}")
    # Both have 'read' capability in my mock above, let's adjust mock to differentiate
    manager._tool_registry["server1::read_file"].capabilities = ["read"]
    manager._tool_registry["server2::read_file"].capabilities = ["write"] # server2 can't read now
    
    server = manager.resolve_tool_server("read_file", context=context)
    print(f"Resolved 'read_file' with 'read' capability hint (after adjustment): {server}")
    assert server == "server1"

    # 4. Test Health & Priority Based Selection
    print("\n4. Testing Health & Priority Based Selection...")
    
    # Mock health states
    manager._health["server1"] = ServerHealth(consecutive_failures=5, priority=10) # Unhealthy but high priority
    manager._health["server2"] = ServerHealth(consecutive_failures=0, priority=5)  # Healthy but low priority
    
    # Should pick server2 because server1 is unhealthy
    server = await manager.select_best_server_for_tool("read_file")
    print(f"Resolved 'read_file' with server1 unhealthy: {server}")
    assert server == "server2"
    
    # Test with both healthy but different priorities
    manager._health["server1"] = ServerHealth(total_calls=100, total_errors=0, priority=10)
    manager._health["server2"] = ServerHealth(total_calls=100, total_errors=0, priority=5)
    
    server = manager.select_best_server(["server1", "server2"])
    print(f"Best server (Priority 10 vs 5): {server}")
    assert server == "server1"

    print("\nAll Phase 1 unit tests passed!")

if __name__ == "__main__":
    asyncio.run(test_mcp_registry_and_routing())
