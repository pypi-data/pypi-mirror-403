"""Tests for moss-langchain signing functions."""

import pytest
from unittest.mock import MagicMock

from moss_langchain import (
    sign_output,
    sign_tool_call,
    sign_message,
    sign_chain_result,
    sign_tool_result,
    verify_envelope,
    SignResult,
)


class TestSignToolCall:
    """Test sign_tool_call function."""
    
    def test_sign_tool_call_dict(self):
        """Sign a tool call from dict."""
        tool_call = {
            "name": "get_weather",
            "args": {"location": "NYC"},
            "id": "call_123",
        }
        
        result = sign_tool_call(tool_call, agent_id="test-agent")
        
        assert isinstance(result, SignResult)
        assert result.payload["type"] == "tool_call"
        assert result.payload["name"] == "get_weather"
    
    def test_sign_tool_call_object(self):
        """Sign a tool call from mock object."""
        tool_call = MagicMock()
        tool_call.name = "send_email"
        tool_call.args = {"to": "user@example.com"}
        tool_call.id = "call_456"
        
        result = sign_tool_call(tool_call, agent_id="email-agent")
        
        assert result.payload["name"] == "send_email"
    
    def test_sign_tool_call_with_context(self):
        """Sign tool call with context."""
        tool_call = {"name": "transfer", "args": {}, "id": "call_789"}
        
        result = sign_tool_call(
            tool_call,
            agent_id="finance-agent",
            context={"user_id": "u123"},
        )
        
        assert result.payload.get("_context") == {"user_id": "u123"}


class TestSignMessage:
    """Test sign_message function."""
    
    def test_sign_message_dict(self):
        """Sign a message from dict."""
        message = {
            "content": "Hello!",
            "role": "assistant",
        }
        
        result = sign_message(message, agent_id="test-agent")
        
        assert result.payload["type"] == "message"
        assert result.payload["content"] == "Hello!"
    
    def test_sign_message_object(self):
        """Sign a message from mock object."""
        message = MagicMock()
        message.content = "Hi there!"
        message.type = "ai"
        message.tool_calls = []
        
        result = sign_message(message, agent_id="test-agent")
        
        assert result.payload["content"] == "Hi there!"


class TestSignChainResult:
    """Test sign_chain_result function."""
    
    def test_sign_chain_result_dict(self):
        """Sign a chain result from dict."""
        chain_output = {
            "output": "The answer is 42.",
            "intermediate_steps": [],
        }
        
        result = sign_chain_result(chain_output, agent_id="test-agent")
        
        assert result.payload["type"] == "chain_output"
        assert "output" in result.payload
    
    def test_sign_chain_result_with_name(self):
        """Sign chain result with chain name."""
        chain_output = {"result": "Done"}
        
        result = sign_chain_result(
            chain_output,
            agent_id="test-agent",
            chain_name="qa_chain",
        )
        
        assert result.payload.get("chain_name") == "qa_chain"
    
    def test_sign_chain_result_string(self):
        """Sign a string chain result."""
        result = sign_chain_result("Final answer", agent_id="test-agent")
        
        assert "Final answer" in str(result.payload)


class TestSignToolResult:
    """Test sign_tool_result function."""
    
    def test_sign_tool_result_dict(self):
        """Sign a tool result from dict."""
        tool_result = {
            "temperature": 72,
            "conditions": "sunny",
        }
        
        result = sign_tool_result(
            tool_result,
            agent_id="test-agent",
            tool_name="get_weather",
        )
        
        assert result.payload["type"] == "tool_result"
        assert result.payload["tool"] == "get_weather"
    
    def test_sign_tool_result_string(self):
        """Sign a string tool result."""
        result = sign_tool_result(
            "Success",
            agent_id="test-agent",
            tool_name="send_email",
        )
        
        assert result.payload["output"] == "Success"
        assert result.payload["tool"] == "send_email"


class TestSignOutput:
    """Test sign_output function (generic)."""
    
    def test_sign_output_dict(self):
        """Sign generic dict output."""
        output = {"key": "value"}
        
        result = sign_output(output, agent_id="test-agent")
        
        assert result.payload["type"] == "chain_output"
    
    def test_sign_output_with_action(self):
        """Sign output with custom action."""
        result = sign_output(
            {"data": "test"},
            agent_id="test-agent",
            action="custom_action",
        )
        
        assert isinstance(result, SignResult)


class TestVerifyEnvelope:
    """Test verify_envelope function."""
    
    def test_verify_signed_envelope(self):
        """Verify a signed envelope."""
        tool_call = {"name": "test", "args": {}, "id": "call_1"}
        sign_result = sign_tool_call(tool_call, agent_id="test-agent")
        
        verify_result = verify_envelope(sign_result.envelope)
        
        assert verify_result.valid is True
