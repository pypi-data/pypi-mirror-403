"""
MOSS LangChain Integration - Explicit Signing Functions

This module provides explicit signing functions for LangChain outputs.
Users decide exactly what to sign - no auto-signing.

Example:
    from langchain_openai import ChatOpenAI
    from moss_langchain import sign_output, sign_tool_call
    
    llm = ChatOpenAI()
    response = llm.invoke("What's the weather?")
    
    # Sign only what matters
    if response.tool_calls:
        result = sign_tool_call(response.tool_calls[0], agent_id="weather-agent")
        print(f"Signed: {result.signature}")
"""

from typing import Any, Dict, List, Optional, Union

from moss import sign, sign_async, verify, SignResult, VerifyResult


def _extract_tool_call_payload(tool_call: Any) -> Dict[str, Any]:
    """Extract payload from a LangChain tool call."""
    if isinstance(tool_call, dict):
        return {
            "type": "tool_call",
            "name": tool_call.get("name"),
            "args": tool_call.get("args", {}),
            "id": tool_call.get("id"),
        }
    
    # Handle ToolCall object
    return {
        "type": "tool_call",
        "name": getattr(tool_call, "name", None),
        "args": getattr(tool_call, "args", {}),
        "id": getattr(tool_call, "id", None),
    }


def _extract_message_payload(message: Any) -> Dict[str, Any]:
    """Extract payload from a LangChain message."""
    if isinstance(message, dict):
        return {
            "type": "message",
            "content": message.get("content"),
            "role": message.get("role") or message.get("type"),
        }
    
    return {
        "type": "message",
        "content": getattr(message, "content", str(message)),
        "role": getattr(message, "type", None),
        "tool_calls": [
            _extract_tool_call_payload(tc) 
            for tc in getattr(message, "tool_calls", [])
        ] if hasattr(message, "tool_calls") and message.tool_calls else None,
    }


def _extract_chain_payload(output: Any) -> Dict[str, Any]:
    """Extract payload from chain output."""
    if isinstance(output, dict):
        return {"type": "chain_output", **output}
    
    if hasattr(output, "to_dict"):
        return {"type": "chain_output", **output.to_dict()}
    
    if hasattr(output, "content"):
        return {"type": "chain_output", "content": output.content}
    
    return {"type": "chain_output", "output": str(output)}


def sign_output(
    output: Any,
    agent_id: str,
    *,
    action: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
) -> SignResult:
    """
    Sign any LangChain output.
    
    This is the general-purpose signing function. Use more specific functions
    (sign_tool_call, sign_message, etc.) for better payload structure.
    
    Args:
        output: Any LangChain output (message, chain result, etc.)
        agent_id: Identifier for the agent
        action: Action name for policy evaluation (default: "langchain_output")
        context: Optional context (user_id, session_id, etc.)
    
    Returns:
        SignResult with envelope and enterprise info
    
    Example:
        from moss_langchain import sign_output
        
        result = sign_output(chain_result, agent_id="my-chain")
        print(result.envelope.signature)
    """
    payload = _extract_chain_payload(output)
    return sign(
        output=payload,
        agent_id=agent_id,
        action=action or "langchain_output",
        context=context,
    )


async def sign_output_async(
    output: Any,
    agent_id: str,
    *,
    action: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
) -> SignResult:
    """Async version of sign_output."""
    payload = _extract_chain_payload(output)
    return await sign_async(
        output=payload,
        agent_id=agent_id,
        action=action or "langchain_output",
        context=context,
    )


def sign_tool_call(
    tool_call: Any,
    agent_id: str,
    *,
    context: Optional[Dict[str, Any]] = None,
) -> SignResult:
    """
    Sign a LangChain tool call.
    
    Tool calls are typically the most important outputs to sign - they
    represent actions the agent wants to take.
    
    Args:
        tool_call: LangChain ToolCall object or dict
        agent_id: Identifier for the agent
        context: Optional context (user_id, session_id, etc.)
    
    Returns:
        SignResult with envelope and enterprise info
    
    Example:
        from moss_langchain import sign_tool_call
        
        response = llm.invoke("Send email to user@example.com")
        if response.tool_calls:
            for tc in response.tool_calls:
                result = sign_tool_call(tc, agent_id="email-agent")
                if result.blocked:
                    print(f"Action blocked: {result.enterprise.policy.reason}")
    """
    payload = _extract_tool_call_payload(tool_call)
    tool_name = payload.get("name", "unknown")
    
    return sign(
        output=payload,
        agent_id=agent_id,
        action=f"tool_call:{tool_name}",
        context=context,
    )


async def sign_tool_call_async(
    tool_call: Any,
    agent_id: str,
    *,
    context: Optional[Dict[str, Any]] = None,
) -> SignResult:
    """Async version of sign_tool_call."""
    payload = _extract_tool_call_payload(tool_call)
    tool_name = payload.get("name", "unknown")
    
    return await sign_async(
        output=payload,
        agent_id=agent_id,
        action=f"tool_call:{tool_name}",
        context=context,
    )


def sign_message(
    message: Any,
    agent_id: str,
    *,
    context: Optional[Dict[str, Any]] = None,
) -> SignResult:
    """
    Sign a LangChain message (AIMessage, HumanMessage, etc.).
    
    Args:
        message: LangChain message object
        agent_id: Identifier for the agent
        context: Optional context
    
    Returns:
        SignResult with envelope and enterprise info
    """
    payload = _extract_message_payload(message)
    return sign(
        output=payload,
        agent_id=agent_id,
        action="message",
        context=context,
    )


async def sign_message_async(
    message: Any,
    agent_id: str,
    *,
    context: Optional[Dict[str, Any]] = None,
) -> SignResult:
    """Async version of sign_message."""
    payload = _extract_message_payload(message)
    return await sign_async(
        output=payload,
        agent_id=agent_id,
        action="message",
        context=context,
    )


def sign_chain_result(
    result: Any,
    agent_id: str,
    *,
    chain_name: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
) -> SignResult:
    """
    Sign a LangChain chain result.
    
    Args:
        result: Chain output (dict, string, or object)
        agent_id: Identifier for the agent
        chain_name: Optional name of the chain
        context: Optional context
    
    Returns:
        SignResult with envelope and enterprise info
    
    Example:
        from moss_langchain import sign_chain_result
        
        chain = prompt | llm | parser
        output = chain.invoke({"input": "..."})
        
        result = sign_chain_result(output, agent_id="my-chain", chain_name="qa_chain")
    """
    payload = _extract_chain_payload(result)
    if chain_name:
        payload["chain_name"] = chain_name
    
    action = f"chain:{chain_name}" if chain_name else "chain_result"
    
    return sign(
        output=payload,
        agent_id=agent_id,
        action=action,
        context=context,
    )


async def sign_chain_result_async(
    result: Any,
    agent_id: str,
    *,
    chain_name: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
) -> SignResult:
    """Async version of sign_chain_result."""
    payload = _extract_chain_payload(result)
    if chain_name:
        payload["chain_name"] = chain_name
    
    action = f"chain:{chain_name}" if chain_name else "chain_result"
    
    return await sign_async(
        output=payload,
        agent_id=agent_id,
        action=action,
        context=context,
    )


def sign_tool_result(
    result: Any,
    agent_id: str,
    *,
    tool_name: str,
    context: Optional[Dict[str, Any]] = None,
) -> SignResult:
    """
    Sign the result of a tool execution.
    
    Args:
        result: Tool execution result
        agent_id: Identifier for the agent
        tool_name: Name of the tool that was executed
        context: Optional context
    
    Returns:
        SignResult with envelope and enterprise info
    """
    if isinstance(result, dict):
        payload = {"type": "tool_result", "tool": tool_name, **result}
    else:
        payload = {"type": "tool_result", "tool": tool_name, "output": str(result)}
    
    return sign(
        output=payload,
        agent_id=agent_id,
        action=f"tool_result:{tool_name}",
        context=context,
    )


async def sign_tool_result_async(
    result: Any,
    agent_id: str,
    *,
    tool_name: str,
    context: Optional[Dict[str, Any]] = None,
) -> SignResult:
    """Async version of sign_tool_result."""
    if isinstance(result, dict):
        payload = {"type": "tool_result", "tool": tool_name, **result}
    else:
        payload = {"type": "tool_result", "tool": tool_name, "output": str(result)}
    
    return await sign_async(
        output=payload,
        agent_id=agent_id,
        action=f"tool_result:{tool_name}",
        context=context,
    )


# Re-export verify from moss
def verify_envelope(envelope: Any, payload: Any = None) -> VerifyResult:
    """
    Verify a signed envelope.
    
    Args:
        envelope: MOSS Envelope or dict
        payload: Original payload for hash verification (optional)
    
    Returns:
        VerifyResult with valid=True/False and details
    """
    return verify(envelope, payload)
