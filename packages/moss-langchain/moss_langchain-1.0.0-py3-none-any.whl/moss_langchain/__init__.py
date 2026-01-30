"""
MOSS LangChain Integration - Cryptographic Signing for LangChain Outputs

This package provides explicit signing functions for LangChain outputs.
You decide exactly what to sign - no auto-signing everything.

Quick Start:
    from langchain_openai import ChatOpenAI
    from moss_langchain import sign_tool_call
    
    llm = ChatOpenAI()
    response = llm.invoke("What's the weather?", tools=[...])
    
    # Sign tool calls (the actions that matter)
    if response.tool_calls:
        result = sign_tool_call(response.tool_calls[0], agent_id="weather-agent")
        print(f"Signature: {result.signature}")
        
        # Enterprise mode (if MOSS_API_KEY set)
        if result.blocked:
            print(f"Policy blocked: {result.enterprise.policy.reason}")

Enterprise Mode:
    Set MOSS_API_KEY environment variable to enable:
    - Policy evaluation (allow/block/reauth)
    - Evidence retention  
    - Usage tracking
"""

__version__ = "0.2.0"

# Explicit signing functions (recommended)
from .signing import (
    sign_output,
    sign_output_async,
    sign_tool_call,
    sign_tool_call_async,
    sign_message,
    sign_message_async,
    sign_chain_result,
    sign_chain_result_async,
    sign_tool_result,
    sign_tool_result_async,
    verify_envelope,
)

# Callback handler for selective auto-signing
from .handler import (
    MOSSCallbackHandler,
    AsyncMOSSCallbackHandler,
)

# Re-export core types
from moss import SignResult, VerifyResult, Envelope, enterprise_enabled

# Legacy exports (deprecated, for backwards compatibility)
from .callback import SignedCallbackHandler, AsyncSignedCallbackHandler
from .interceptor import enable_moss, disable_moss, get_handler, MOSSToolWrapper


__all__ = [
    # Explicit signing (recommended)
    "sign_output",
    "sign_output_async",
    "sign_tool_call",
    "sign_tool_call_async",
    "sign_message",
    "sign_message_async",
    "sign_chain_result",
    "sign_chain_result_async",
    "sign_tool_result",
    "sign_tool_result_async",
    "verify_envelope",
    
    # Callback handler
    "MOSSCallbackHandler",
    "AsyncMOSSCallbackHandler",
    
    # Core types
    "SignResult",
    "VerifyResult",
    "Envelope",
    "enterprise_enabled",
    
    # Legacy (deprecated)
    "SignedCallbackHandler",
    "AsyncSignedCallbackHandler",
    "enable_moss",
    "disable_moss",
    "get_handler",
    "MOSSToolWrapper",
]
