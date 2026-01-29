import asyncio
import json
import unittest
from unittest.mock import MagicMock, AsyncMock
from langxchange.EnhancedAgent import EnhancedLLMAgentHelper, AgentState, CircuitState
from langxchange.agent_memory_helper import AgentMemoryHelper

class MockLLM:
    async def chat(self, messages):
        # Simple mock response logic
        last_msg = messages[-1]["content"]
        if "Analyze" in last_msg:
            return "Thinking about the goal."
        if "Select next action" in last_msg:
            return json.dumps({"action": "test_tool", "parameters": {"value": 42}, "reasoning": "Testing tool"})
        if "Generate complete parameters" in last_msg:
            return json.dumps({"value": 42})
        if "Condense" in last_msg:
            return "Summarized content"
        return "Default response"

class TestAgentImprovements(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.llm = MockLLM()
        self.memory_db = "test_memory.db"
        if os.path.exists(self.memory_db):
            os.remove(self.memory_db)
        
        self.mock_vector_helper = MagicMock()
        self.mock_vector_helper.search = AsyncMock(return_value=[{"text": "semantic match"}])
        
        self.memory_helper = AgentMemoryHelper(
            sqlite_path=self.memory_db,
            vector_helper=self.mock_vector_helper
        )

    async def test_memory_async_and_semantic(self):
        # Test async add
        await self.memory_helper.add_memory_async("agent1", "user", "hello world", {"key": "val"})
        
        # Test async get
        recent = await self.memory_helper.get_recent_async("agent1", 1)
        self.assertEqual(len(recent), 1)
        self.assertEqual(recent[0][2], "hello world")
        
        # Test semantic search
        results = await self.memory_helper.search_semantic_async("agent1", "hello", top_k=1)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["text"], "semantic match")
        self.mock_vector_helper.search.assert_called_once()

    async def test_agent_dynamic_discovery(self):
        async def discovery():
            return [{"action": "test_tool", "description": "A test tool", "func": AsyncMock(return_value="success")}]
        
        agent = EnhancedLLMAgentHelper(
            llm=self.llm,
            action_space=[],
            discovery_callback=discovery,
            external_memory_helper=self.memory_helper
        )
        agent.set_goal("Test dynamic discovery")
        
        # Run one cycle
        result = await agent.run_cycle()
        self.assertEqual(len(agent.action_space), 1)
        self.assertEqual(agent.action_space[0]["action"], "test_tool")

    async def test_agent_per_tool_circuit_breaker(self):
        fail_tool = AsyncMock(side_effect=Exception("Tool failed"))
        action_space = [{"action": "fail_tool", "description": "Failing tool", "func": fail_tool}]
        
        agent = EnhancedLLMAgentHelper(
            llm=self.llm,
            action_space=action_space,
            circuit_breaker_config=MagicMock(failure_threshold=1, recovery_timeout=30)
        )
        
        # Force failure
        decision = {"action": "fail_tool", "function": fail_tool, "parameters": {}}
        await agent.act(decision)
        
        # Check if circuit breaker is open for this tool
        cb = agent._get_circuit_breaker("fail_tool")
        self.assertEqual(cb.state, CircuitState.OPEN)
        
        # Global circuit breaker should still be closed
        self.assertEqual(agent._global_circuit_breaker.state, CircuitState.CLOSED)

    async def test_agent_summarization(self):
        agent = EnhancedLLMAgentHelper(
            llm=self.llm,
            action_space=[],
            external_memory_helper=self.memory_helper
        )
        
        large_obs = "A" * 2000
        await agent.perceive(large_obs)
        
        recent = await self.memory_helper.get_recent_async(agent.agent_id, 1)
        self.assertTrue(recent[0][2].startswith("[Summarized]"))

    async def test_correlation_id_propagation(self):
        hook_data = {}
        async def on_act(event):
            hook_data["correlation_id"] = event.correlation_id

        agent = EnhancedLLMAgentHelper(
            llm=self.llm,
            action_space=[{"action": "test_tool", "description": "test", "func": AsyncMock(return_value="ok")}],
            external_memory_helper=self.memory_helper
        )
        agent.register_hook("on_act", on_act)
        agent.set_goal("Test correlation")
        
        result = await agent.run_cycle()
        self.assertEqual(hook_data["correlation_id"], result["correlation_id"])

if __name__ == "__main__":
    import os
    unittest.main()
