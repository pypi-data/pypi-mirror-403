import asyncio
import json
import os
import sys
from typing import Dict, Any, List
from dataclasses import dataclass

# Add the parent directory to sys.path to import langxchange
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from langxchange.mcp_helper import MCPServiceManager, ToolRegistryEntry, ToolMetadata

# Mock Tool class to simulate MCP tools
@dataclass
class MockTool:
    name: str
    description: str
    inputSchema: Dict[str, Any]

async def test_real_world_scenario():
    print("Testing Real-World Scenario Routing...")
    
    # User-provided JSON config
    config_json = [
      {
        "name": "filesystem",
        "description": "Read files from Downloads",
        "transport": "stdio",
        "command": "mcp-server-filesystem",
        "args": [
          "/home/ikolilu-backend/Downloads"
        ],
        "env": {
          "LOG_LEVEL": "info"
        }
      },
      {
        "name": "web_search",
        "description": "Brave Web Search",
        "transport": "stdio",
        "command": "brave-search-mcp-server",
        "args": [],
        "env": {
          "BRAVE_API_KEY": "e0ff8f42bce9a8f289dbd501c8180a3f8c86cc3e9faae940656b359038e69ff1"
        }
      },
      {
        "name": "email",
        "description": "Gmail Service",
        "transport": "stdio",
        "command": "mcp-server-gmail",
        "args": [],
        "env": {
          "GMAIL_API_KEY": "AIzaSyBXt94PcVyh29ASwFR19Xwtq3C_YZJtOEY"
        }
      }
    ]
    
    # Initialize manager with the list format (our manager handles list or dict)
    manager = MCPServiceManager(config_dict={"servers": config_json})
    
    # 1. Register Capabilities with Priorities
    print("\n1. Registering Capabilities with Priorities...")
    manager.register_server_capabilities("filesystem", ["files", "pdf", "local"], priority=10)
    manager.register_server_capabilities("web_search", ["search", "web", "brave"], priority=5)
    manager.register_server_capabilities("email", ["email", "gmail", "send"], priority=8)
    
    # 2. Mock Tool Discovery
    # Since we can't run the actual binaries, we'll manually populate the registry
    # to simulate what get_all_tools_with_metadata would do if servers were running.
    print("\n2. Simulating Tool Discovery...")
    
    # Filesystem tools
    manager._tool_registry["filesystem::read_file"] = ToolRegistryEntry(
        server_name="filesystem",
        original_tool_name="read_file",
        tool_description="Read content of a file",
        input_schema={"path": "string"},
        capabilities=["files", "pdf", "local"]
    )
    
    # Web search tools
    manager._tool_registry["web_search::brave_search"] = ToolRegistryEntry(
        server_name="web_search",
        original_tool_name="brave_search",
        tool_description="Search the web using Brave",
        input_schema={"query": "string"},
        capabilities=["search", "web", "brave"]
    )
    
    # Email tools
    manager._tool_registry["email::send_email"] = ToolRegistryEntry(
        server_name="email",
        original_tool_name="send_email",
        tool_description="Send an email via Gmail",
        input_schema={"to": "string", "subject": "string", "body": "string"},
        capabilities=["email", "gmail", "send"]
    )

    # 3. Test Routing for the requested tasks
    print("\n3. Testing Routing for Tasks...")
    
    tasks = [
        {"task": "Read sms.pdf", "tool": "read_file", "expected": "filesystem"},
        {"task": "Search for Timothy Owusu", "tool": "brave_search", "expected": "web_search"},
        {"task": "Send apology letter", "tool": "send_email", "expected": "email"}
    ]
    
    for t in tasks:
        # Test new intelligent routing method
        resolved_server = await manager.select_best_server_for_tool(t["tool"])
        print(f"Task: '{t['task']}' -> Tool: '{t['tool']}' -> Resolved Server (Intelligent): {resolved_server}")
        assert resolved_server == t["expected"], f"Failed to resolve {t['tool']} to {t['expected']}"
        
        # Test legacy method
        resolved_server_legacy = manager.resolve_tool_server(t["tool"])
        assert resolved_server_legacy == t["expected"]

    # 4. Test Capability-based Routing (Intelligent Selection)
    print("\n4. Testing Capability-based Routing...")
    
    # If we had multiple search servers, we could use capability hints
    context = {"preferred_capability": "gmail"}
    resolved_server = manager.resolve_tool_server("send_email", context=context)
    print(f"Resolved 'send_email' with 'gmail' hint: {resolved_server}")
    assert resolved_server == "email"
    
    # 5. Test Priority-based Selection
    print("\n5. Testing Priority-based Selection...")
    # Add another search server with lower priority
    manager._server_configs["secondary_search"] = {"name": "secondary_search"}
    manager.register_server_capabilities("secondary_search", ["search", "web"], priority=1)
    manager._tool_registry["secondary_search::brave_search"] = ToolRegistryEntry(
        server_name="secondary_search",
        original_tool_name="brave_search",
        tool_description="Secondary Search",
        input_schema={"query": "string"},
        capabilities=["search", "web"]
    )
    
    # Should still pick web_search because it has higher priority (5 vs 1)
    best_search = await manager.select_best_server_for_tool("brave_search")
    print(f"Best search server (Priority 5 vs 1): {best_search}")
    assert best_search == "web_search"

    print("\nReal-world scenario routing test passed!")

if __name__ == "__main__":
    asyncio.run(test_real_world_scenario())
