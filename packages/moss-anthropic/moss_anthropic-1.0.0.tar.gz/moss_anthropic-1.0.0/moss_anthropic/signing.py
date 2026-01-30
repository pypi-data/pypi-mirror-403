"""
MOSS Anthropic Signing Functions

Explicit signing functions for Anthropic/Claude SDK outputs.
"""

from typing import Any, Dict, List, Optional

from moss import sign, sign_async, verify, SignResult, VerifyResult


def _extract_tool_use_payload(tool_use: Any) -> Dict[str, Any]:
    """Extract payload from Anthropic tool use block."""
    if isinstance(tool_use, dict):
        return {
            "type": "tool_use",
            "id": tool_use.get("id"),
            "name": tool_use.get("name"),
            "input": tool_use.get("input"),
        }
    
    # Handle ToolUseBlock object
    return {
        "type": "tool_use",
        "id": getattr(tool_use, "id", None),
        "name": getattr(tool_use, "name", None),
        "input": getattr(tool_use, "input", None),
    }


def _extract_text_payload(text_block: Any) -> Dict[str, Any]:
    """Extract payload from Anthropic text block."""
    if isinstance(text_block, dict):
        return {
            "type": "text",
            "text": text_block.get("text"),
        }
    
    # Handle TextBlock object
    return {
        "type": "text",
        "text": getattr(text_block, "text", str(text_block)),
    }


def _extract_content_block_payload(block: Any) -> Dict[str, Any]:
    """Extract payload from any Anthropic content block."""
    block_type = block.get("type") if isinstance(block, dict) else getattr(block, "type", None)
    
    if block_type == "tool_use":
        return _extract_tool_use_payload(block)
    elif block_type == "text":
        return _extract_text_payload(block)
    else:
        return {"type": block_type, "content": str(block)}


def _extract_message_payload(message: Any) -> Dict[str, Any]:
    """Extract payload from Anthropic Message response."""
    if isinstance(message, dict):
        content = message.get("content", [])
        return {
            "type": "message",
            "id": message.get("id"),
            "model": message.get("model"),
            "role": message.get("role"),
            "stop_reason": message.get("stop_reason"),
            "content": [_extract_content_block_payload(b) for b in content],
        }
    
    # Handle Message object
    content = getattr(message, "content", [])
    return {
        "type": "message",
        "id": getattr(message, "id", None),
        "model": getattr(message, "model", None),
        "role": getattr(message, "role", None),
        "stop_reason": getattr(message, "stop_reason", None),
        "content": [_extract_content_block_payload(b) for b in content],
    }


def sign_response(
    response: Any,
    agent_id: str,
    *,
    context: Optional[Dict[str, Any]] = None,
) -> SignResult:
    """
    Sign a full Anthropic Message response.
    
    Args:
        response: Message object from Anthropic SDK
        agent_id: Identifier for the agent
        context: Optional context (user_id, session_id, etc.)
    
    Returns:
        SignResult with envelope and enterprise info
    
    Example:
        response = client.messages.create(...)
        result = sign_response(response, agent_id="my-agent")
    """
    payload = _extract_message_payload(response)
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
    payload = _extract_message_payload(response)
    return await sign_async(
        output=payload,
        agent_id=agent_id,
        action="response",
        context=context,
    )


def sign_tool_use(
    tool_use: Any,
    agent_id: str,
    *,
    context: Optional[Dict[str, Any]] = None,
) -> SignResult:
    """
    Sign an Anthropic tool use block.
    
    Tool uses represent actions the model wants to take. These are typically
    the most important outputs to sign for audit and compliance.
    
    Args:
        tool_use: ToolUseBlock object from response.content
        agent_id: Identifier for the agent
        context: Optional context
    
    Returns:
        SignResult with envelope and enterprise info
    
    Example:
        response = client.messages.create(model="claude-sonnet-4-20250514", tools=[...])
        
        for block in response.content:
            if block.type == "tool_use":
                result = sign_tool_use(block, agent_id="my-agent")
                
                if result.blocked:
                    print(f"Blocked: {result.enterprise.policy.reason}")
    """
    payload = _extract_tool_use_payload(tool_use)
    tool_name = payload.get("name", "unknown")
    
    return sign(
        output=payload,
        agent_id=agent_id,
        action=f"tool_use:{tool_name}",
        context=context,
    )


async def sign_tool_use_async(
    tool_use: Any,
    agent_id: str,
    *,
    context: Optional[Dict[str, Any]] = None,
) -> SignResult:
    """Async version of sign_tool_use."""
    payload = _extract_tool_use_payload(tool_use)
    tool_name = payload.get("name", "unknown")
    
    return await sign_async(
        output=payload,
        agent_id=agent_id,
        action=f"tool_use:{tool_name}",
        context=context,
    )


def sign_text(
    text_block: Any,
    agent_id: str,
    *,
    context: Optional[Dict[str, Any]] = None,
) -> SignResult:
    """
    Sign an Anthropic text block.
    
    Args:
        text_block: TextBlock object from response.content
        agent_id: Identifier for the agent
        context: Optional context
    
    Returns:
        SignResult with envelope and enterprise info
    """
    payload = _extract_text_payload(text_block)
    return sign(
        output=payload,
        agent_id=agent_id,
        action="text",
        context=context,
    )


async def sign_text_async(
    text_block: Any,
    agent_id: str,
    *,
    context: Optional[Dict[str, Any]] = None,
) -> SignResult:
    """Async version of sign_text."""
    payload = _extract_text_payload(text_block)
    return await sign_async(
        output=payload,
        agent_id=agent_id,
        action="text",
        context=context,
    )


def sign_message(
    message: Any,
    agent_id: str,
    *,
    context: Optional[Dict[str, Any]] = None,
) -> SignResult:
    """
    Sign an Anthropic message (alias for sign_response).
    
    Args:
        message: Message object from Anthropic SDK
        agent_id: Identifier for the agent
        context: Optional context
    
    Returns:
        SignResult with envelope and enterprise info
    """
    return sign_response(message, agent_id, context=context)


async def sign_message_async(
    message: Any,
    agent_id: str,
    *,
    context: Optional[Dict[str, Any]] = None,
) -> SignResult:
    """Async version of sign_message."""
    return await sign_response_async(message, agent_id, context=context)


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
