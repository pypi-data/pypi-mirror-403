import asyncio
import json
import unittest
from unittest.mock import MagicMock, AsyncMock
from langxchange.EnhancedAgent import EnhancedLLMAgentHelper, AgentState

class MockLLM:
    async def chat(self, messages):
        last_msg = messages[-1]["content"]
        if "Analyze" in last_msg:
            return "Thinking about using the MCP tool."
        if "Select next action" in last_msg:
            # The tool name should be namespaced: server::tool
            return json.dumps({"action": "test_server::echo", "parameters": {"message": "hello"}, "reasoning": "Testing MCP"})
        if "Generate complete parameters" in last_msg:
            return json.dumps({"message": "hello"})
        return "Default response"

class TestAgentMCPDirect(unittest.IsolatedAsyncioTestCase):
    async def test_direct_mcp_integration(self):
        # 1. Setup Mock MCP Config
        mcp_config = {
            "servers": [
                {
                    "name": "test_server",
                    "transport": "stdio",
                    "command": "python3",
                    "args": ["mock_mcp_server.py"]
                }
            ]
        }

        # 2. Initialize Agent with MCP Config
        llm = MockLLM()
        agent = EnhancedLLMAgentHelper(
            llm=llm,
            action_space=[],
            mcp_config=mcp_config,
            debug=True
        )

        # 3. Mock MCP Manager to avoid actual server startup in this unit test
        # We want to test the integration logic
        agent.mcp_manager = AsyncMock()
        agent.mcp_manager.initialize = AsyncMock()
        agent.mcp_manager.shutdown = AsyncMock()
        
        # Mock tool discovery
        mock_metadata = MagicMock()
        mock_metadata.name = "echo"
        mock_metadata.description = "Echo a message"
        mock_metadata.input_schema = {"type": "object", "properties": {"message": {"type": "string"}}}
        mock_metadata.server_name = "test_server"
        
        agent.mcp_manager.get_all_tools_with_metadata = AsyncMock(return_value={
            "test_server::echo": mock_metadata
        })
        
        # Mock tool execution
        agent.mcp_manager.call_tool = AsyncMock(return_value="Echo: hello")

        # 4. Run Cycle
        agent.set_goal("Test MCP integration")
        result = await agent.run_cycle()

        # 5. Verify
        if result.get("status") == "error":
            import sys
            print(f"Error: {result.get('error')}", file=sys.stderr)
            print(f"Traceback: {result.get('traceback')}", file=sys.stderr)

        self.assertEqual(len(agent.action_space), 1)
        self.assertEqual(agent.action_space[0]["action"], "test_server::echo")
        self.assertEqual(result["outcome"]["status"], "success")
        self.assertEqual(result["outcome"]["result"], "Echo: hello")
        
        agent.mcp_manager.call_tool.assert_called_once_with(
            server_name="test_server",
            tool_name="echo",
            arguments={"message": "hello"}
        )

if __name__ == "__main__":
    unittest.main()
