"""
MOSS LangChain Integration - Automatic Output Signing

Import this module to enable automatic signing of all LangChain outputs.

Usage:
    from moss_langchain import enable_moss
    enable_moss()
    
    # All LangChain tool calls and agent outputs are now signed
"""

from typing import Any, Optional
from functools import wraps
import os

from .callback import SignedCallbackHandler, _get_or_create_subject


class MOSSToolWrapper:
    """
    Wraps LangChain tools to sign all inputs and outputs.
    """

    @staticmethod
    def wrap(tool: Any, subject_id: str = "moss:langchain:tool") -> Any:
        """
        Wrap a tool to sign its inputs and outputs.

        Args:
            tool: LangChain tool to wrap
            subject_id: Subject identifier for signing

        Returns:
            Wrapped tool with MOSS signing
        """
        subject = _get_or_create_subject(subject_id)
        original_run = tool._run
        original_arun = getattr(tool, '_arun', None)
        tool_name = getattr(tool, 'name', 'unknown')

        @wraps(original_run)
        def signed_run(*args, **kwargs) -> Any:
            # Sign input
            subject.sign({
                "type": "tool_input",
                "tool": tool_name,
                "args": str(args),
                "kwargs": str(kwargs)
            })

            # Execute
            try:
                result = original_run(*args, **kwargs)
            except Exception as e:
                subject.sign({
                    "type": "tool_error",
                    "tool": tool_name,
                    "error": str(e)
                })
                raise

            # Sign output
            envelope = subject.sign({
                "type": "tool_output",
                "tool": tool_name,
                "output": str(result)
            })

            # Store envelope on tool
            tool._moss_envelope = envelope
            return result

        tool._run = signed_run

        if original_arun:
            @wraps(original_arun)
            async def signed_arun(*args, **kwargs) -> Any:
                subject.sign({
                    "type": "tool_input",
                    "tool": tool_name,
                    "args": str(args),
                    "kwargs": str(kwargs)
                })

                try:
                    result = await original_arun(*args, **kwargs)
                except Exception as e:
                    subject.sign({
                        "type": "tool_error",
                        "tool": tool_name,
                        "error": str(e)
                    })
                    raise

                envelope = subject.sign({
                    "type": "tool_output",
                    "tool": tool_name,
                    "output": str(result)
                })

                tool._moss_envelope = envelope
                return result

            tool._arun = signed_arun

        return tool


_moss_enabled = False
_moss_handler: Optional[SignedCallbackHandler] = None


def enable_moss(subject_id: str = "moss:langchain:agent"):
    """
    Enable MOSS signing for all LangChain operations.

    This function:
    1. Patches BaseTool to auto-sign all tool operations
    2. Registers a global callback handler for agent actions

    Args:
        subject_id: Default agent identifier for signing

    Example:
        from moss_langchain import enable_moss
        enable_moss()

        # All subsequent LangChain operations are signed
    """
    global _moss_enabled, _moss_handler

    if _moss_enabled:
        return

    try:
        from langchain_core.tools import BaseTool
    except ImportError:
        raise ImportError("langchain-core not installed. Run: pip install langchain-core")

    # Patch BaseTool.__init__ to auto-wrap
    original_init = BaseTool.__init__

    @wraps(original_init)
    def patched_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        MOSSToolWrapper.wrap(self, f"{subject_id}:tool")

    BaseTool.__init__ = patched_init

    # Create global callback handler
    _moss_handler = SignedCallbackHandler(subject_id)

    # Try to patch AgentExecutor to always include MOSS callback
    try:
        from langchain.agents import AgentExecutor
        original_agent_init = AgentExecutor.__init__

        @wraps(original_agent_init)
        def patched_agent_init(self, *args, **kwargs):
            callbacks = kwargs.get('callbacks', []) or []
            if _moss_handler not in callbacks:
                callbacks.append(_moss_handler)
            kwargs['callbacks'] = callbacks
            original_agent_init(self, *args, **kwargs)

        AgentExecutor.__init__ = patched_agent_init
    except ImportError:
        pass  # AgentExecutor not available

    _moss_enabled = True
    print(f"MOSS: LangChain signing enabled for subject '{subject_id}'")


def disable_moss():
    """
    Disable MOSS auto-signing (for testing).
    Note: Already-wrapped tools remain wrapped.
    """
    global _moss_enabled, _moss_handler
    _moss_enabled = False
    _moss_handler = None


def get_handler() -> Optional[SignedCallbackHandler]:
    """Get the global MOSS callback handler."""
    return _moss_handler


# Auto-enable on import if MOSS_AUTO_ENABLE is set
if os.environ.get("MOSS_AUTO_ENABLE", "").lower() in ("1", "true", "yes"):
    enable_moss()
