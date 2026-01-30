"""Tests for moss-google signing functions."""

import pytest
from unittest.mock import MagicMock

from moss_google import (
    sign_response,
    sign_function_call,
    sign_content,
    sign_part,
    verify_envelope,
    SignResult,
)


class TestSignFunctionCall:
    """Test sign_function_call function."""
    
    def test_sign_function_call_dict(self):
        """Sign a function call from dict."""
        function_call = {
            "name": "get_weather",
            "args": {"location": "NYC"},
        }
        
        result = sign_function_call(function_call, agent_id="test-agent")
        
        assert isinstance(result, SignResult)
        assert result.payload["type"] == "function_call"
        assert result.payload["name"] == "get_weather"
        assert result.payload["args"] == {"location": "NYC"}
    
    def test_sign_function_call_object(self):
        """Sign a function call from mock object."""
        function_call = MagicMock()
        function_call.name = "send_email"
        function_call.args = {"to": "user@example.com"}
        
        result = sign_function_call(function_call, agent_id="email-agent")
        
        assert result.payload["name"] == "send_email"
    
    def test_sign_function_call_with_context(self):
        """Sign function call with context."""
        function_call = {
            "name": "transfer",
            "args": {"amount": 1000},
        }
        
        result = sign_function_call(
            function_call,
            agent_id="finance-agent",
            context={"user_id": "u123"},
        )
        
        assert result.payload.get("_context") == {"user_id": "u123"}


class TestSignResponse:
    """Test sign_response function."""
    
    def test_sign_response_dict(self):
        """Sign a response from dict."""
        response = {
            "candidates": [
                {
                    "content": {
                        "role": "model",
                        "parts": [{"text": "Hello!"}],
                    },
                    "finish_reason": "STOP",
                }
            ],
        }
        
        result = sign_response(response, agent_id="test-agent")
        
        assert result.payload["type"] == "response"
        assert len(result.payload["candidates"]) == 1
    
    def test_sign_response_with_function_call(self):
        """Sign a response containing function call."""
        response = {
            "candidates": [
                {
                    "content": {
                        "role": "model",
                        "parts": [
                            {"text": "Let me check."},
                            {
                                "function_call": {
                                    "name": "get_weather",
                                    "args": {"location": "NYC"},
                                }
                            },
                        ],
                    },
                    "finish_reason": "STOP",
                }
            ],
        }
        
        result = sign_response(response, agent_id="test-agent")
        
        content = result.payload["candidates"][0]["content"]
        assert len(content["parts"]) == 2


class TestSignContent:
    """Test sign_content function."""
    
    def test_sign_content_dict(self):
        """Sign content from dict."""
        content = {
            "role": "model",
            "parts": [{"text": "Hello!"}],
        }
        
        result = sign_content(content, agent_id="test-agent")
        
        assert result.payload["type"] == "content"
        assert result.payload["role"] == "model"


class TestSignPart:
    """Test sign_part function."""
    
    def test_sign_text_part(self):
        """Sign a text part."""
        part = {"text": "Hello, world!"}
        
        result = sign_part(part, agent_id="test-agent")
        
        assert result.payload["type"] == "text"
        assert result.payload["text"] == "Hello, world!"
    
    def test_sign_function_call_part(self):
        """Sign a function call part."""
        part = {
            "function_call": {
                "name": "get_weather",
                "args": {"location": "NYC"},
            }
        }
        
        result = sign_part(part, agent_id="test-agent")
        
        assert result.payload["type"] == "function_call"
        assert result.payload["name"] == "get_weather"


class TestVerifyEnvelope:
    """Test verify_envelope function."""
    
    def test_verify_signed_envelope(self):
        """Verify a signed envelope."""
        function_call = {"name": "test", "args": {}}
        sign_result = sign_function_call(function_call, agent_id="test-agent")
        
        verify_result = verify_envelope(sign_result.envelope)
        
        assert verify_result.valid is True
