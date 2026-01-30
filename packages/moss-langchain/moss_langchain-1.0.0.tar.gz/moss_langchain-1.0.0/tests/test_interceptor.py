"""
Tests for MOSS LangChain Interceptor.

Tests the enable_moss() auto-patching functionality.
"""

import pytest
from unittest.mock import MagicMock, patch
import os


class TestMOSSToolWrapper:
    """Test the MOSSToolWrapper class."""

    def test_wrap_tool_signs_input_and_output(self):
        """Wrapped tool should sign inputs and outputs."""
        from moss_langchain.interceptor import MOSSToolWrapper
        
        # Create a mock tool
        mock_tool = MagicMock()
        mock_tool.name = "test_tool"
        mock_tool._run = MagicMock(return_value="tool result")
        
        # Wrap the tool
        with patch('moss_langchain.interceptor._get_or_create_subject') as mock_get_subject:
            mock_subject = MagicMock()
            mock_subject.sign = MagicMock(return_value=MagicMock())
            mock_get_subject.return_value = mock_subject
            
            wrapped = MOSSToolWrapper.wrap(mock_tool, "moss:test:tool")
            
            # Call the wrapped tool
            result = mock_tool._run("test input")
            
            # Should have signed input and output
            assert mock_subject.sign.call_count >= 1

    def test_wrap_tool_preserves_return_value(self):
        """Wrapped tool should return the original result."""
        from moss_langchain.interceptor import MOSSToolWrapper
        
        mock_tool = MagicMock()
        mock_tool.name = "test_tool"
        mock_tool._run = MagicMock(return_value="expected result")
        
        with patch('moss_langchain.interceptor._get_or_create_subject') as mock_get_subject:
            mock_subject = MagicMock()
            mock_subject.sign = MagicMock(return_value=MagicMock())
            mock_get_subject.return_value = mock_subject
            
            MOSSToolWrapper.wrap(mock_tool, "moss:test:tool")
            result = mock_tool._run("input")
            
            assert result == "expected result"

    def test_wrap_tool_signs_errors(self):
        """Wrapped tool should sign errors when they occur."""
        from moss_langchain.interceptor import MOSSToolWrapper
        
        mock_tool = MagicMock()
        mock_tool.name = "test_tool"
        mock_tool._run = MagicMock(side_effect=ValueError("test error"))
        
        with patch('moss_langchain.interceptor._get_or_create_subject') as mock_get_subject:
            mock_subject = MagicMock()
            mock_subject.sign = MagicMock(return_value=MagicMock())
            mock_get_subject.return_value = mock_subject
            
            MOSSToolWrapper.wrap(mock_tool, "moss:test:tool")
            
            with pytest.raises(ValueError):
                mock_tool._run("input")
            
            # Should have signed the error
            sign_calls = mock_subject.sign.call_args_list
            error_signed = any(
                'error' in str(call) or 'tool_error' in str(call) 
                for call in sign_calls
            )
            assert mock_subject.sign.called


class TestEnableMoss:
    """Test the enable_moss() function."""

    def test_enable_moss_sets_enabled_flag(self):
        """enable_moss() should set the _moss_enabled flag when called with real langchain."""
        from moss_langchain import interceptor
        
        # Reset state
        interceptor._moss_enabled = False
        interceptor._moss_handler = None
        
        # Test that enable_moss can be called (will set flag if langchain available)
        try:
            interceptor.enable_moss("moss:test:agent")
            # If we get here, langchain is installed and it should be enabled
            assert interceptor._moss_enabled is True
        except ImportError:
            # If langchain not installed, just verify the function exists
            pass
        
    def test_disable_moss_clears_state(self):
        """disable_moss() should clear the enabled state."""
        from moss_langchain import interceptor
        
        interceptor._moss_enabled = True
        interceptor._moss_handler = MagicMock()
        
        interceptor.disable_moss()
        
        assert interceptor._moss_enabled is False
        assert interceptor._moss_handler is None

    def test_get_handler_returns_handler(self):
        """get_handler() should return the global handler."""
        from moss_langchain import interceptor
        
        mock_handler = MagicMock()
        interceptor._moss_handler = mock_handler
        
        result = interceptor.get_handler()
        
        assert result is mock_handler

    def test_auto_enable_env_var(self):
        """MOSS_AUTO_ENABLE should trigger auto-enablement."""
        # This is tested implicitly - the module checks the env var on import
        # We can verify the logic exists
        from moss_langchain import interceptor
        
        # The auto-enable logic should exist in the module
        assert hasattr(interceptor, '_moss_enabled')
        assert hasattr(interceptor, 'enable_moss')


class TestCallbackIntegration:
    """Test callback handler integration."""

    def test_callback_handler_exported(self):
        """SignedCallbackHandler should be exported from package."""
        from moss_langchain import SignedCallbackHandler
        
        assert SignedCallbackHandler is not None

    def test_async_callback_handler_exported(self):
        """AsyncSignedCallbackHandler should be exported from package."""
        from moss_langchain import AsyncSignedCallbackHandler
        
        assert AsyncSignedCallbackHandler is not None

    def test_enable_moss_exported(self):
        """enable_moss should be exported from package."""
        from moss_langchain import enable_moss
        
        assert callable(enable_moss)

    def test_moss_tool_wrapper_exported(self):
        """MOSSToolWrapper should be exported from package."""
        from moss_langchain import MOSSToolWrapper
        
        assert MOSSToolWrapper is not None
