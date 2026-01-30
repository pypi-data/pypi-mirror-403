"""Tests for moss-autogen signing functions."""

import pytest
from unittest.mock import MagicMock

from moss_autogen import (
    sign_message,
    sign_function_result,
    sign_conversation,
    sign_reply,
    verify_envelope,
    SignResult,
)


class TestSignMessage:
    """Test sign_message function."""
    
    def test_sign_message_dict(self):
        """Sign a message from dict."""
        message = {
            "role": "assistant",
            "content": "Hello!",
        }
        
        result = sign_message(message, agent_id="test-agent")
        
        assert isinstance(result, SignResult)
        assert result.payload["type"] == "message"
        assert result.payload["content"] == "Hello!"
    
    def test_sign_message_string(self):
        """Sign a string message."""
        result = sign_message("Hello, world!", agent_id="test-agent")
        
        assert result.payload["type"] == "message"
        assert result.payload["content"] == "Hello, world!"
    
    def test_sign_message_with_context(self):
        """Sign message with context."""
        message = {"content": "Transfer request"}
        
        result = sign_message(
            message,
            agent_id="finance-agent",
            context={"user_id": "u123"},
        )
        
        assert result.payload.get("_context") == {"user_id": "u123"}


class TestSignFunctionResult:
    """Test sign_function_result function."""
    
    def test_sign_function_result_dict(self):
        """Sign a function result from dict."""
        func_result = {
            "temperature": 72,
            "conditions": "sunny",
        }
        
        result = sign_function_result(
            func_result,
            agent_id="weather-agent",
            function="get_weather",
        )
        
        assert result.payload["type"] == "function_result"
        assert result.payload["function"] == "get_weather"
        assert result.payload["temperature"] == 72
    
    def test_sign_function_result_string(self):
        """Sign a string function result."""
        result = sign_function_result(
            "Email sent successfully",
            agent_id="email-agent",
            function="send_email",
        )
        
        assert result.payload["output"] == "Email sent successfully"
        assert result.payload["function"] == "send_email"
    
    def test_sign_function_result_with_context(self):
        """Sign function result with context."""
        result = sign_function_result(
            {"success": True},
            agent_id="finance-agent",
            function="transfer",
            context={"transaction_id": "tx123"},
        )
        
        assert result.payload.get("_context") == {"transaction_id": "tx123"}


class TestSignConversation:
    """Test sign_conversation function."""
    
    def test_sign_conversation_list(self):
        """Sign a conversation from list of messages."""
        messages = [
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello!"},
            {"role": "user", "content": "How are you?"},
            {"role": "assistant", "content": "I'm doing well!"},
        ]
        
        result = sign_conversation(messages, agent_id="chat-agent")
        
        assert result.payload["type"] == "conversation"
        assert result.payload["message_count"] == 4
        assert len(result.payload["messages"]) == 4
    
    def test_sign_empty_conversation(self):
        """Sign an empty conversation."""
        result = sign_conversation([], agent_id="chat-agent")
        
        assert result.payload["message_count"] == 0
        assert result.payload["messages"] == []
    
    def test_sign_conversation_with_context(self):
        """Sign conversation with context."""
        messages = [{"content": "Test"}]
        
        result = sign_conversation(
            messages,
            agent_id="chat-agent",
            context={"session_id": "s123"},
        )
        
        assert result.payload.get("_context") == {"session_id": "s123"}


class TestSignReply:
    """Test sign_reply function."""
    
    def test_sign_reply_dict(self):
        """Sign a reply from dict."""
        reply = {"content": "Here's my response"}
        
        result = sign_reply(reply, agent_id="assistant")
        
        assert result.payload["type"] == "message"
        assert result.payload["content"] == "Here's my response"
    
    def test_sign_reply_string(self):
        """Sign a string reply."""
        result = sign_reply("My response", agent_id="assistant")
        
        assert result.payload["content"] == "My response"
    
    def test_sign_reply_with_agent_name(self):
        """Sign reply with agent name."""
        result = sign_reply(
            {"content": "Done"},
            agent_id="multi-agent-system",
            agent_name="researcher",
        )
        
        assert result.payload["agent_name"] == "researcher"
    
    def test_sign_reply_with_context(self):
        """Sign reply with context."""
        result = sign_reply(
            "Approved",
            agent_id="approver",
            context={"request_id": "r123"},
        )
        
        assert result.payload.get("_context") == {"request_id": "r123"}


class TestVerifyEnvelope:
    """Test verify_envelope function."""
    
    def test_verify_signed_envelope(self):
        """Verify a signed envelope."""
        sign_result = sign_message("test", agent_id="test-agent")
        
        verify_result = verify_envelope(sign_result.envelope)
        
        assert verify_result.valid is True
