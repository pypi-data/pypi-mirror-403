import os
import sqlite3
import uuid
import asyncio
import json
from datetime import datetime
from typing import List, Tuple, Optional, Dict, Any

class AgentMemoryHelper:
    """
    Manages per-agent conversational memory using SQLite and optional Vector Store:
      - Stores every turn in SQLite (agent_id, timestamp, role, text)
      - Provides retrieval and basic search functionality
      - Supports pluggable semantic search via vector_helper
      - Async-compatible methods using asyncio.to_thread
    """

    def __init__(
        self,
        llm_helper=None,
        sqlite_path: str = "agent_memory.db",
        vector_helper: Optional[Any] = None
    ):
        # llm_helper is optional if vector_helper is provided or semantic search is not used
        self.llm = llm_helper
        self.vector_helper = vector_helper

        # --- SQLite setup ---
        self.conn = sqlite3.connect(sqlite_path, check_same_thread=False)
        self._init_sqlite()

    def _init_sqlite(self):
        c = self.conn.cursor()
        c.execute("""
        CREATE TABLE IF NOT EXISTS memory (
            agent_id TEXT,
            timestamp TEXT,
            role      TEXT,
            text      TEXT,
            metadata  TEXT
        )""")
        self.conn.commit()

    def add_memory(self, agent_id: str, role: str, text: str, metadata: Optional[Dict] = None):
        """Add a new message turn to SQLite for this agent."""
        timestamp = datetime.utcnow().isoformat()
        meta_json = json.dumps(metadata) if metadata else None
        # Insert into SQLite
        self.conn.execute(
            "INSERT INTO memory (agent_id,timestamp,role,text,metadata) VALUES (?,?,?,?,?)",
            (agent_id, timestamp, role, text, meta_json)
        )
        self.conn.commit()

        # Add to vector store if available
        if self.vector_helper:
            try:
                # Check if vector_helper has add_memory or similar
                if hasattr(self.vector_helper, "add_memory"):
                    self.vector_helper.add_memory(
                        agent_id=agent_id,
                        role=role,
                        text=text,
                        metadata=metadata
                    )
            except Exception as e:
                print(f"Warning: Failed to add to vector store: {e}")

    async def add_memory_async(self, agent_id: str, role: str, text: str, metadata: Optional[Dict] = None):
        """Async version of add_memory."""
        await asyncio.to_thread(self.add_memory, agent_id, role, text, metadata)

    def get_recent(
        self,
        agent_id: str,
        n: int = 10
    ) -> List[Tuple[str, str, str]]:
        """
        Return the last n turns as a list of tuples:
          [(timestamp, role, text), ...], most recent last.
        """
        c = self.conn.cursor()
        c.execute("""
            SELECT timestamp, role, text
              FROM memory
             WHERE agent_id = ?
          ORDER BY timestamp DESC
             LIMIT ?
        """, (agent_id, n))
        rows = c.fetchall()
        return list(reversed(rows))

    async def get_recent_async(self, agent_id: str, n: int = 10) -> List[Tuple[str, str, str]]:
        """Async version of get_recent."""
        return await asyncio.to_thread(self.get_recent, agent_id, n)

    def search_memory(
        self,
        agent_id: str,
        query: str,
        top_k: int = 5
    ) -> List[Tuple[str, str, str]]:
        """
        Perform a basic substring search over this agent's memory text.
        Returns up to top_k matching turns as (timestamp, role, text).
        """
        pattern = f"%{query}%"
        c = self.conn.cursor()
        c.execute("""
            SELECT timestamp, role, text
              FROM memory
             WHERE agent_id = ? AND text LIKE ?
          ORDER BY timestamp DESC
             LIMIT ?
        """, (agent_id, pattern, top_k))
        rows = c.fetchall()
        return list(reversed(rows))

    async def search_memory_async(self, agent_id: str, query: str, top_k: int = 5) -> List[Tuple[str, str, str]]:
        """Async version of search_memory."""
        return await asyncio.to_thread(self.search_memory, agent_id, query, top_k)

    async def search_semantic_async(
        self,
        agent_id: str,
        query: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search using the pluggable vector_helper.
        """
        if not self.vector_helper:
            return []

        try:
            # Most langxchange vector helpers have a search or query method
            if hasattr(self.vector_helper, "search"):
                results = await self.vector_helper.search(
                    query=query,
                    limit=top_k,
                    filter={"agent_id": agent_id}
                )
                return results
            elif hasattr(self.vector_helper, "query"):
                results = self.vector_helper.query(
                    query_texts=[query],
                    n_results=top_k,
                    where={"agent_id": agent_id}
                )
                return results
        except Exception as e:
            print(f"Warning: Semantic search failed: {e}")
            return []
        
        return []

    def clear_memory(self, agent_id: str):
        """Delete all history for the given agent."""
        self.conn.execute("DELETE FROM memory WHERE agent_id = ?", (agent_id,))
        self.conn.commit()
        
        if self.vector_helper and hasattr(self.vector_helper, "delete_memory"):
            try:
                self.vector_helper.delete_memory(agent_id=agent_id)
            except:
                pass

    async def clear_memory_async(self, agent_id: str):
        """Async version of clear_memory."""
        await asyncio.to_thread(self.clear_memory, agent_id)
