"""
MOSS LangChain Callback Handler - Selective Auto-Signing

A callback handler that signs specific events. Unlike auto-signing everything,
you configure which events to sign.

Example:
    from moss_langchain import MOSSCallbackHandler
    
    handler = MOSSCallbackHandler(
        agent_id="my-agent",
        sign_on=["tool_end", "chain_end"],  # Only sign these events
    )
    
    chain.invoke(input, config={"callbacks": [handler]})
"""

from typing import Any, Dict, List, Optional, Set
from uuid import UUID

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult

from moss import sign, SignResult


class MOSSCallbackHandler(BaseCallbackHandler):
    """
    LangChain callback handler for selective MOSS signing.
    
    Configure which events trigger signing via the sign_on parameter.
    Access signed results via the results list or last_result property.
    
    Args:
        agent_id: MOSS agent identifier
        sign_on: List of events to sign. Options:
            - "llm_end": Sign LLM completions
            - "chain_end": Sign chain outputs  
            - "tool_end": Sign tool results
            - "agent_finish": Sign agent final output
            - "retriever_end": Sign retrieved documents
            Default: ["tool_end"] (sign tool executions only)
        context: Optional context to include in all signatures
    
    Attributes:
        results: List of all SignResult objects from this session
        last_result: Most recent SignResult (or None)
    
    Example:
        handler = MOSSCallbackHandler(
            agent_id="finance-agent",
            sign_on=["tool_end", "agent_finish"],
            context={"user_id": "u123"}
        )
        
        agent.invoke(query, config={"callbacks": [handler]})
        
        for result in handler.results:
            print(f"Signed: {result.envelope.payload_hash}")
    """
    
    VALID_EVENTS = {"llm_end", "chain_end", "tool_end", "agent_finish", "retriever_end"}
    
    def __init__(
        self,
        agent_id: str,
        sign_on: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        super().__init__()
        self.agent_id = agent_id
        self.context = context or {}
        
        # Default to signing tool executions only
        events = sign_on or ["tool_end"]
        
        # Validate events
        invalid = set(events) - self.VALID_EVENTS
        if invalid:
            raise ValueError(
                f"Invalid sign_on events: {invalid}. "
                f"Valid options: {self.VALID_EVENTS}"
            )
        
        self._sign_events: Set[str] = set(events)
        self.results: List[SignResult] = []
        self.last_result: Optional[SignResult] = None
    
    def _should_sign(self, event: str) -> bool:
        """Check if we should sign this event type."""
        return event in self._sign_events
    
    def _sign(self, event: str, output: Any, action: str) -> Optional[SignResult]:
        """Sign output if this event type is enabled."""
        if not self._should_sign(event):
            return None
        
        payload = self._to_payload(output)
        payload["_event"] = event
        
        result = sign(
            output=payload,
            agent_id=self.agent_id,
            action=action,
            context=self.context if self.context else None,
        )
        
        self.results.append(result)
        self.last_result = result
        return result
    
    def _to_payload(self, output: Any) -> Dict[str, Any]:
        """Convert output to signable dict."""
        if isinstance(output, dict):
            return output.copy()
        
        if hasattr(output, "to_dict"):
            try:
                return output.to_dict()
            except Exception:
                pass
        
        if isinstance(output, LLMResult):
            generations = []
            for gen_list in output.generations:
                for gen in gen_list:
                    generations.append({
                        "text": getattr(gen, "text", str(gen)),
                        "type": type(gen).__name__,
                    })
            return {
                "generations": generations,
                "llm_output": output.llm_output,
            }
        
        if hasattr(output, "content"):
            return {"content": output.content}
        
        if hasattr(output, "return_values"):
            return {"return_values": output.return_values}
        
        return {"output": str(output)}
    
    # Callback methods
    
    def on_llm_end(
        self,
        response: LLMResult,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """Sign LLM output if enabled."""
        self._sign("llm_end", response, "llm_completion")
    
    def on_chain_end(
        self,
        outputs: Dict[str, Any],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """Sign chain output if enabled."""
        self._sign("chain_end", outputs, "chain_result")
    
    def on_tool_end(
        self,
        output: Any,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """Sign tool output if enabled."""
        name = kwargs.get("name", "unknown")
        self._sign("tool_end", output, f"tool:{name}")
    
    def on_agent_finish(
        self,
        finish: Any,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """Sign agent output if enabled."""
        self._sign("agent_finish", finish, "agent_finish")
    
    def on_retriever_end(
        self,
        documents: List[Any],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """Sign retriever output if enabled."""
        payload = {"documents": [str(d) for d in documents]}
        self._sign("retriever_end", payload, "retrieval")
    
    def clear(self) -> None:
        """Clear all stored results."""
        self.results = []
        self.last_result = None


class AsyncMOSSCallbackHandler(MOSSCallbackHandler):
    """
    Async version of MOSSCallbackHandler.
    
    Use this with async LangChain chains and agents.
    """
    
    async def on_llm_end(
        self,
        response: LLMResult,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        self._sign("llm_end", response, "llm_completion")
    
    async def on_chain_end(
        self,
        outputs: Dict[str, Any],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        self._sign("chain_end", outputs, "chain_result")
    
    async def on_tool_end(
        self,
        output: Any,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        name = kwargs.get("name", "unknown")
        self._sign("tool_end", output, f"tool:{name}")
    
    async def on_agent_finish(
        self,
        finish: Any,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        self._sign("agent_finish", finish, "agent_finish")
    
    async def on_retriever_end(
        self,
        documents: List[Any],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        payload = {"documents": [str(d) for d in documents]}
        self._sign("retriever_end", payload, "retrieval")
