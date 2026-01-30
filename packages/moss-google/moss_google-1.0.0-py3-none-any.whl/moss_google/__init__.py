"""
MOSS Google GenAI Integration - Cryptographic Signing for Gemini SDK Outputs

Sign function calls, responses, and content from the Google GenAI/Gemini SDK.

Quick Start:
    import google.generativeai as genai
    from moss_google import sign_function_call, sign_response
    
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content("What's the weather?", tools=[...])
    
    # Sign function calls (the actions that matter)
    for part in response.parts:
        if part.function_call:
            result = sign_function_call(part.function_call, agent_id="weather-agent")
            print(f"Signature: {result.signature}")

Enterprise Mode:
    Set MOSS_API_KEY environment variable to enable:
    - Policy evaluation (allow/block/reauth)
    - Evidence retention
    - Usage tracking
"""

__version__ = "0.1.0"

from .signing import (
    sign_response,
    sign_response_async,
    sign_function_call,
    sign_function_call_async,
    sign_content,
    sign_content_async,
    sign_part,
    sign_part_async,
    verify_envelope,
)

from moss import SignResult, VerifyResult, Envelope, enterprise_enabled

__all__ = [
    "sign_response",
    "sign_response_async",
    "sign_function_call",
    "sign_function_call_async",
    "sign_content",
    "sign_content_async",
    "sign_part",
    "sign_part_async",
    "verify_envelope",
    "SignResult",
    "VerifyResult",
    "Envelope",
    "enterprise_enabled",
]
