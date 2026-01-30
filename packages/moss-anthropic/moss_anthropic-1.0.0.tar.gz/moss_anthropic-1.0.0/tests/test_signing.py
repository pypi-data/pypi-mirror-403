"""Tests for moss-anthropic signing functions."""

import pytest
from unittest.mock import MagicMock

from moss_anthropic import (
    sign_response,
    sign_tool_use,
    sign_text,
    sign_message,
    verify_envelope,
    SignResult,
)


class TestSignToolUse:
    """Test sign_tool_use function."""
    
    def test_sign_tool_use_dict(self):
        """Sign a tool use from dict."""
        tool_use = {
            "type": "tool_use",
            "id": "tu_123",
            "name": "get_weather",
            "input": {"location": "NYC"},
        }
        
        result = sign_tool_use(tool_use, agent_id="test-agent")
        
        assert isinstance(result, SignResult)
        assert result.payload["type"] == "tool_use"
        assert result.payload["name"] == "get_weather"
        assert result.payload["input"] == {"location": "NYC"}
    
    def test_sign_tool_use_object(self):
        """Sign a tool use from mock object."""
        tool_use = MagicMock()
        tool_use.id = "tu_456"
        tool_use.name = "send_email"
        tool_use.input = {"to": "user@example.com", "subject": "Hello"}
        
        result = sign_tool_use(tool_use, agent_id="email-agent")
        
        assert result.payload["name"] == "send_email"
        assert result.payload["id"] == "tu_456"
    
    def test_sign_tool_use_with_context(self):
        """Sign tool use with context."""
        tool_use = {
            "type": "tool_use",
            "id": "tu_789",
            "name": "transfer",
            "input": {"amount": 1000},
        }
        
        result = sign_tool_use(
            tool_use,
            agent_id="finance-agent",
            context={"user_id": "u123"},
        )
        
        assert result.payload.get("_context") == {"user_id": "u123"}


class TestSignResponse:
    """Test sign_response function."""
    
    def test_sign_response_dict(self):
        """Sign a response from dict."""
        response = {
            "id": "msg_123",
            "model": "claude-sonnet-4-20250514",
            "role": "assistant",
            "stop_reason": "end_turn",
            "content": [
                {"type": "text", "text": "Hello!"},
            ],
        }
        
        result = sign_response(response, agent_id="test-agent")
        
        assert result.payload["type"] == "message"
        assert result.payload["model"] == "claude-sonnet-4-20250514"
    
    def test_sign_response_with_tool_use(self):
        """Sign a response containing tool use."""
        response = {
            "id": "msg_456",
            "model": "claude-sonnet-4-20250514",
            "role": "assistant",
            "stop_reason": "tool_use",
            "content": [
                {"type": "text", "text": "Let me check the weather."},
                {
                    "type": "tool_use",
                    "id": "tu_1",
                    "name": "get_weather",
                    "input": {"location": "NYC"},
                },
            ],
        }
        
        result = sign_response(response, agent_id="test-agent")
        
        assert len(result.payload["content"]) == 2
        assert result.payload["content"][1]["type"] == "tool_use"


class TestSignText:
    """Test sign_text function."""
    
    def test_sign_text_dict(self):
        """Sign a text block from dict."""
        text_block = {
            "type": "text",
            "text": "Hello, world!",
        }
        
        result = sign_text(text_block, agent_id="test-agent")
        
        assert result.payload["type"] == "text"
        assert result.payload["text"] == "Hello, world!"
    
    def test_sign_text_object(self):
        """Sign a text block from mock object."""
        text_block = MagicMock()
        text_block.text = "This is a response."
        
        result = sign_text(text_block, agent_id="test-agent")
        
        assert result.payload["text"] == "This is a response."


class TestSignMessage:
    """Test sign_message function (alias for sign_response)."""
    
    def test_sign_message_is_alias(self):
        """sign_message is an alias for sign_response."""
        message = {
            "id": "msg_789",
            "model": "claude-sonnet-4-20250514",
            "role": "assistant",
            "content": [{"type": "text", "text": "Hi!"}],
        }
        
        result = sign_message(message, agent_id="test-agent")
        
        assert result.payload["type"] == "message"


class TestVerifyEnvelope:
    """Test verify_envelope function."""
    
    def test_verify_signed_envelope(self):
        """Verify a signed envelope."""
        tool_use = {"type": "tool_use", "id": "tu_1", "name": "test", "input": {}}
        sign_result = sign_tool_use(tool_use, agent_id="test-agent")
        
        verify_result = verify_envelope(sign_result.envelope)
        
        assert verify_result.valid is True
