"""
MOSS Google GenAI Signing Functions

Explicit signing functions for Google GenAI/Gemini SDK outputs.
"""

from typing import Any, Dict, List, Optional

from moss import sign, sign_async, verify, SignResult, VerifyResult


def _extract_function_call_payload(function_call: Any) -> Dict[str, Any]:
    """Extract payload from Google GenAI function call."""
    if isinstance(function_call, dict):
        return {
            "type": "function_call",
            "name": function_call.get("name"),
            "args": function_call.get("args"),
        }
    
    # Handle FunctionCall object
    name = getattr(function_call, "name", None)
    args = getattr(function_call, "args", None)
    
    # Args might be a proto MapComposite, convert to dict
    if args is not None and hasattr(args, "items"):
        args = dict(args.items())
    elif args is not None and not isinstance(args, dict):
        args = dict(args) if hasattr(args, "__iter__") else str(args)
    
    return {
        "type": "function_call",
        "name": name,
        "args": args,
    }


def _extract_part_payload(part: Any) -> Dict[str, Any]:
    """Extract payload from Google GenAI Part."""
    if isinstance(part, dict):
        if "function_call" in part:
            return _extract_function_call_payload(part["function_call"])
        if "text" in part:
            return {"type": "text", "text": part["text"]}
        return {"type": "part", "content": str(part)}
    
    # Handle Part object
    if hasattr(part, "function_call") and part.function_call:
        return _extract_function_call_payload(part.function_call)
    
    if hasattr(part, "text") and part.text:
        return {"type": "text", "text": part.text}
    
    return {"type": "part", "content": str(part)}


def _extract_content_payload(content: Any) -> Dict[str, Any]:
    """Extract payload from Google GenAI Content."""
    if isinstance(content, dict):
        parts = content.get("parts", [])
        return {
            "type": "content",
            "role": content.get("role"),
            "parts": [_extract_part_payload(p) for p in parts],
        }
    
    # Handle Content object
    parts = getattr(content, "parts", [])
    return {
        "type": "content",
        "role": getattr(content, "role", None),
        "parts": [_extract_part_payload(p) for p in parts],
    }


def _extract_response_payload(response: Any) -> Dict[str, Any]:
    """Extract payload from Google GenAI GenerateContentResponse."""
    if isinstance(response, dict):
        candidates = response.get("candidates", [])
        return {
            "type": "response",
            "candidates": [
                {
                    "content": _extract_content_payload(c.get("content", {})),
                    "finish_reason": c.get("finish_reason"),
                }
                for c in candidates
            ],
        }
    
    # Handle GenerateContentResponse object
    candidates = getattr(response, "candidates", [])
    result = {
        "type": "response",
        "candidates": [],
    }
    
    for c in candidates:
        content = getattr(c, "content", None)
        result["candidates"].append({
            "content": _extract_content_payload(content) if content else None,
            "finish_reason": str(getattr(c, "finish_reason", None)),
        })
    
    return result


def sign_response(
    response: Any,
    agent_id: str,
    *,
    context: Optional[Dict[str, Any]] = None,
) -> SignResult:
    """
    Sign a full Google GenAI response.
    
    Args:
        response: GenerateContentResponse from Gemini
        agent_id: Identifier for the agent
        context: Optional context (user_id, session_id, etc.)
    
    Returns:
        SignResult with envelope and enterprise info
    
    Example:
        response = model.generate_content("...")
        result = sign_response(response, agent_id="my-agent")
    """
    payload = _extract_response_payload(response)
    return sign(
        output=payload,
        agent_id=agent_id,
        action="response",
        context=context,
    )


async def sign_response_async(
    response: Any,
    agent_id: str,
    *,
    context: Optional[Dict[str, Any]] = None,
) -> SignResult:
    """Async version of sign_response."""
    payload = _extract_response_payload(response)
    return await sign_async(
        output=payload,
        agent_id=agent_id,
        action="response",
        context=context,
    )


def sign_function_call(
    function_call: Any,
    agent_id: str,
    *,
    context: Optional[Dict[str, Any]] = None,
) -> SignResult:
    """
    Sign a Google GenAI function call.
    
    Function calls represent actions the model wants to take. These are
    typically the most important outputs to sign.
    
    Args:
        function_call: FunctionCall from response part
        agent_id: Identifier for the agent
        context: Optional context
    
    Returns:
        SignResult with envelope and enterprise info
    
    Example:
        response = model.generate_content("...", tools=[...])
        
        for part in response.parts:
            if part.function_call:
                result = sign_function_call(part.function_call, agent_id="my-agent")
                
                if result.blocked:
                    print(f"Blocked: {result.enterprise.policy.reason}")
    """
    payload = _extract_function_call_payload(function_call)
    func_name = payload.get("name", "unknown")
    
    return sign(
        output=payload,
        agent_id=agent_id,
        action=f"function_call:{func_name}",
        context=context,
    )


async def sign_function_call_async(
    function_call: Any,
    agent_id: str,
    *,
    context: Optional[Dict[str, Any]] = None,
) -> SignResult:
    """Async version of sign_function_call."""
    payload = _extract_function_call_payload(function_call)
    func_name = payload.get("name", "unknown")
    
    return await sign_async(
        output=payload,
        agent_id=agent_id,
        action=f"function_call:{func_name}",
        context=context,
    )


def sign_content(
    content: Any,
    agent_id: str,
    *,
    context: Optional[Dict[str, Any]] = None,
) -> SignResult:
    """
    Sign Google GenAI Content.
    
    Args:
        content: Content object
        agent_id: Identifier for the agent
        context: Optional context
    
    Returns:
        SignResult with envelope and enterprise info
    """
    payload = _extract_content_payload(content)
    return sign(
        output=payload,
        agent_id=agent_id,
        action="content",
        context=context,
    )


async def sign_content_async(
    content: Any,
    agent_id: str,
    *,
    context: Optional[Dict[str, Any]] = None,
) -> SignResult:
    """Async version of sign_content."""
    payload = _extract_content_payload(content)
    return await sign_async(
        output=payload,
        agent_id=agent_id,
        action="content",
        context=context,
    )


def sign_part(
    part: Any,
    agent_id: str,
    *,
    context: Optional[Dict[str, Any]] = None,
) -> SignResult:
    """
    Sign a Google GenAI Part (text or function call).
    
    Args:
        part: Part from content
        agent_id: Identifier for the agent
        context: Optional context
    
    Returns:
        SignResult with envelope and enterprise info
    """
    payload = _extract_part_payload(part)
    action = payload.get("type", "part")
    
    if action == "function_call":
        action = f"function_call:{payload.get('name', 'unknown')}"
    
    return sign(
        output=payload,
        agent_id=agent_id,
        action=action,
        context=context,
    )


async def sign_part_async(
    part: Any,
    agent_id: str,
    *,
    context: Optional[Dict[str, Any]] = None,
) -> SignResult:
    """Async version of sign_part."""
    payload = _extract_part_payload(part)
    action = payload.get("type", "part")
    
    if action == "function_call":
        action = f"function_call:{payload.get('name', 'unknown')}"
    
    return await sign_async(
        output=payload,
        agent_id=agent_id,
        action=action,
        context=context,
    )


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
