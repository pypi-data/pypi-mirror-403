# langxchange/prompt_helper.py

from typing import Any, Dict, List, Optional

from typing import Any, Dict, List, Optional, Callable, Union
from enum import Enum
import json


class PromptMode(Enum):
    """Enumeration for different prompt building modes."""
    BASIC = "basic"
    AUGMENTED = "augmented"
    CONTEXTUAL = "contextual"
    SUMMARIZED = "summarized"


class PromptBuilder:
    """
    Handles different strategies for building prompts from retrieval results.
    """
    
    @staticmethod
    def basic_prompt(
        system_prompt: str,
        user_query: str,
        retrieval_results: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, str]]:
        """Build a basic prompt without retrieval augmentation."""
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query}
        ]
    
    @staticmethod
    def augmented_prompt(
        system_prompt: str,
        user_query: str,
        retrieval_results: Optional[List[Dict[str, Any]]] = None,
        max_context_length: int = 2000
    ) -> List[Dict[str, str]]:
        # print(retrieval_results)
        """Build an augmented prompt with retrieval results as context."""
        messages = [{"role": "system", "content": system_prompt}]
        
        # print(f" Retrieval Results: {retrieval_results["document"]} \n\n\n\n")
        if retrieval_results:
            context_parts = []
            current_length = 0
            
            for hit in retrieval_results:
                # print(f"Current Hits: {hit.document}")
                doc = hit.document # or hit.get("document", "") or hit.get("Document", "")
                if isinstance(doc, list):
                    doc = "\n".join(doc)
                
                # Check if adding this context would exceed the limit
                # if current_length + len(doc) > max_context_length:
                #     # If this is the first document and it's too long, truncate it
                #     if len(context_parts) == 0:
                #         doc = doc[:max_context_length] + "..."
                #         # meta = hit.metadata
                #         # source_info = ", ".join(f"{k}={v}" for k, v in meta.items())
                #         # context_part = f"[Source: {source_info}]\n{doc}"
                #         context_parts.append(doc)
                #     break
                
                # meta = [hit.metadata]
                # source_info = ", ".join(f"{k}={v}" for k, v in meta.items())
                
                # context_part = f"[Source: {source_info}]\n{doc}"
                context_part = f"{doc}"
                context_parts.append(context_part)
                current_length += len(doc)
            
            if context_parts:
                context_content = "\n\n---\n\n".join(context_parts)
                augmented_query = f"""Based on the following context information, please answer the query.

Context:
{context_content}

Query: {user_query}

Please provide a comprehensive answer based on the context provided."""
                
                messages.append({"role": "user", "content": augmented_query})
            else:
                messages.append({"role": "user", "content": user_query})
        else:
            messages.append({"role": "user", "content": user_query})
            
        return messages
    
    @staticmethod
    def contextual_prompt(
        system_prompt: str,
        user_query: str,
        retrieval_results: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, str]]:
        """Build a contextual prompt with retrieval results as assistant messages."""
        messages = [{"role": "system", "content": system_prompt}]
        
        if retrieval_results:
            for hit in retrieval_results:
                doc = hit.get("text") or hit.get("document", "")
                if isinstance(doc, list):
                    doc = "\n".join(doc)
                    
                meta = hit.get("metadata", {})
                tag = ", ".join(f"{k}={v}" for k, v in meta.items())
                
                messages.append({
                    "role": "assistant",
                    "content": f"[Reference] {tag}:\n{doc}"
                })
        
        messages.append({"role": "user", "content": user_query})
        return messages
    
    @staticmethod
    def summarized_prompt(
        system_prompt: str,
        user_query: str,
        retrieval_results: Optional[List[Dict[str, Any]]] = None,
        max_snippets: int = 3
    ) -> List[Dict[str, str]]:
        """Build a prompt with summarized retrieval results."""
        messages = [{"role": "system", "content": system_prompt}]
        
        if retrieval_results:
            # Take top snippets and create a concise summary
            top_results = retrieval_results[:max_snippets]
            summaries = []
            
            for i, hit in enumerate(top_results, 1):
                doc = hit.get("text") or hit.get("document", "")
                if isinstance(doc, list):
                    doc = "\n".join(doc)
                
                # Truncate long documents
                if len(doc) > 300:
                    doc = doc[:300] + "..."
                
                meta = hit.get("metadata", {})
                source = meta.get("source", f"Document {i}")
                
                summaries.append(f"{i}. {source}: {doc}")
            
            if summaries:
                summary_content = "\n".join(summaries)
                enhanced_query = f"""Relevant information:
{summary_content}

Question: {user_query}

Please answer based on the information provided above."""
                
                messages.append({"role": "user", "content": enhanced_query})
            else:
                messages.append({"role": "user", "content": user_query})
        else:
            messages.append({"role": "user", "content": user_query})
            
        return messages


class EnhancedPromptHelper:
    """
    Builds prompts for LLMs and provides an interface to call injected tools.
    Supports multiple prompt building strategies for efficient retrieval augmentation.
    """

    def __init__(
        self,
        llm: Any,
        system_prompt: str,
        tools: Optional[Dict[str, Any]] = None,
        default_mode: PromptMode = PromptMode.AUGMENTED,
        max_context_length: int = 2000,
        max_snippets: int = 3
    ):
        """
        Initialize the EnhancedPromptHelper.
        
        :param llm: an object with .chat(messages, **kwargs) -> str
        :param system_prompt: the initial system-level instruction
        :param tools: a dict mapping tool names to tool instances
        :param default_mode: default prompt building mode
        :param max_context_length: maximum context length for augmented mode
        :param max_snippets: maximum number of snippets for summarized mode
        """
        self.llm = llm
        self.system_prompt = system_prompt
        self.tools = tools or {}
        self.default_mode = default_mode
        self.max_context_length = max_context_length
        self.max_snippets = max_snippets
        
        # Map modes to builder functions
        self._builders = {
            PromptMode.BASIC: PromptBuilder.basic_prompt,
            PromptMode.AUGMENTED: PromptBuilder.augmented_prompt,
            PromptMode.CONTEXTUAL: PromptBuilder.contextual_prompt,
            PromptMode.SUMMARIZED: PromptBuilder.summarized_prompt
        }
    
    def call_tool(self, tool_name: str, *args, **kwargs) -> Any:
        """
        Call a registered tool by name.
        
        :param tool_name: name of the tool to call
        :param args: positional arguments for the tool
        :param kwargs: keyword arguments for the tool
        :return: result from the tool
        :raises ValueError: if tool is not found
        """
        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' not found. Available tools: {list(self.tools.keys())}")
        
        tool = self.tools[tool_name]
        
        # Check if the tool has a 'run' method first (prioritize run method)
        if hasattr(tool, 'run') and callable(tool.run):
            return tool.run(*args, **kwargs)
        elif callable(tool):
            return tool(*args, **kwargs)
        else:
            raise ValueError(f"Tool '{tool_name}' is not callable and has no 'run' method")
    
    def register_tool(self, name: str, tool: Any) -> None:
        """Register a new tool."""
        self.tools[name] = tool
    
    def list_tools(self) -> List[str]:
        """List available tool names."""
        return list(self.tools.keys())
    
    def build_prompt(
        self,
        user_query: str,
        retrieval_results: Optional[List[Dict[str, Any]]] = None,
        mode: Optional[PromptMode] = None,
        custom_system_prompt: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """
        Build a prompt using the specified mode.
        
        :param user_query: the user's query
        :param retrieval_results: optional retrieval results to include
        :param mode: prompt building mode (uses default if None)
        :param custom_system_prompt: override system prompt for this request
        :return: list of message dictionaries
        """
        mode = mode or self.default_mode
        system_prompt = custom_system_prompt or self.system_prompt
        
        builder = self._builders.get(mode)
        if not builder:
            raise ValueError(f"Unknown prompt mode: {mode}")
        
        # Pass additional parameters based on mode
        if mode == PromptMode.AUGMENTED:
            return builder(
                system_prompt, 
                user_query, 
                retrieval_results,
                max_context_length=self.max_context_length
            )
        elif mode == PromptMode.SUMMARIZED:
            return builder(
                system_prompt, 
                user_query, 
                retrieval_results,
                max_snippets=self.max_snippets
            )
        else:
            return builder(system_prompt, user_query, retrieval_results)

    def run(
        self,
        user_query: str,
        retrieval_results: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 512,
        mode: Optional[PromptMode] = None,
        custom_system_prompt: Optional[str] = None,
        **llm_kwargs
    ) -> str:
        """
        Run the LLM with the built prompt.
        
        :param user_query: the user's query
        :param retrieval_results: optional retrieval results to include
        :param temperature: sampling temperature for the LLM
        :param max_tokens: maximum tokens to generate
        :param mode: prompt building mode (uses default if None)
        :param custom_system_prompt: override system prompt for this request
        :param llm_kwargs: additional keyword arguments for the LLM
        :return: LLM response
        """
        try:
            messages = self.build_prompt(
                user_query=user_query,
                retrieval_results=retrieval_results,
                mode=mode,
                custom_system_prompt=custom_system_prompt
            )
            
            # Merge default parameters with custom ones
            chat_params = {
                'messages': messages,
                'temperature': temperature,
                'max_tokens': max_tokens,
                **llm_kwargs            }
            
            return self.llm.chat(**chat_params)
            
        except Exception as e:
            raise RuntimeError(f"Error during LLM execution: {str(e)}") from e
    
    def run_with_tools(
        self,
        user_query: str,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
        retrieval_results: Optional[List[Dict[str, Any]]] = None,
        **run_kwargs
    ) -> Dict[str, Any]:
        """
        Run the LLM with optional tool calls.
        
        :param user_query: the user's query
        :param tool_calls: list of tool calls to execute before LLM
        :param retrieval_results: optional retrieval results to include
        :param run_kwargs: arguments for the run method
        :return: dictionary with LLM response and tool results
        """
        tool_results = {}
        
        # Execute tool calls if provided
        if tool_calls:
            for tool_call in tool_calls:
                tool_name = tool_call.get('name')
                tool_args = tool_call.get('args', [])
                tool_kwargs = tool_call.get('kwargs', {})
                
                if tool_name:
                    try:
                        result = self.call_tool(tool_name, *tool_args, **tool_kwargs)
                        tool_results[tool_name] = result
                    except Exception as e:
                        tool_results[tool_name] = f"Error: {str(e)}"
        
        # Run LLM
        llm_response = self.run(
            user_query=user_query,
            retrieval_results=retrieval_results,
            **run_kwargs
        )
        
        return {
            'llm_response': llm_response,
            'tool_results': tool_results
        }
    
    def update_config(
        self,
        default_mode: Optional[PromptMode] = None,
        max_context_length: Optional[int] = None,
        max_snippets: Optional[int] = None,
        system_prompt: Optional[str] = None
    ) -> None:
        """Update configuration parameters."""
        if default_mode is not None:
            self.default_mode = default_mode
        if max_context_length is not None:
            self.max_context_length = max_context_length
        if max_snippets is not None:
            self.max_snippets = max_snippets
        if system_prompt is not None:
            self.system_prompt = system_prompt
    
    def get_config(self) -> Dict[str, Any]:
        """Get current configuration."""
        return {
            'default_mode': self.default_mode.value,
            'max_context_length': self.max_context_length,
            'max_snippets': self.max_snippets,
            'available_tools': list(self.tools.keys())
        }



class PromptHelper:
    """
    Builds prompts for LLMs and provides an interface to call injected tools.
    """

    def __init__(
        self,
        llm: Any,
        system_prompt: str,
        tools: Optional[Dict[str, Any]] = None
    ):
        """
        :param llm: an object with .chat(messages, **kwargs) -> str
        :param system_prompt: the initial system-level instruction
        :param tools: a dict mapping tool names to tool instances
        """
        self.llm = llm
        self.system_prompt = system_prompt
      


    def run(
        self,
        user_query: str,
        retrieval_results: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 512
    ) -> str:
        
        # otherwise build a normal chat
        messages: List[Dict[str, str]] = [
            {"role": "system", "content": self.system_prompt}
        ]

        if retrieval_results:
            # include retrieved snippets as assistant messages
            for hit in retrieval_results:
                doc = hit.get("text") or hit.get("document", "")
                if isinstance(doc, list):
                    doc = "\n".join(doc)
                meta = hit.get("metadata", {})
                tag = ", ".join(f"{k}={v}" for k, v in meta.items())
                messages.append({
                    "role": "assistant",
                    "content": f"[Snippet] {tag}:\n{doc}"
                })

        messages.append({"role": "user", "content": user_query})

        return self.llm.chat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
