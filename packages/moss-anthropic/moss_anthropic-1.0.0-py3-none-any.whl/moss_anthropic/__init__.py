"""
MOSS Anthropic Integration - Cryptographic Signing for Claude SDK Outputs

Sign tool uses, responses, and text blocks from the Anthropic/Claude SDK.

Quick Start:
    from anthropic import Anthropic
    from moss_anthropic import sign_tool_use, sign_response
    
    client = Anthropic()
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        messages=[{"role": "user", "content": "What's the weather?"}],
        tools=[...]
    )
    
    # Sign tool uses (the actions that matter)
    for block in response.content:
        if block.type == "tool_use":
            result = sign_tool_use(block, agent_id="weather-agent")
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
    sign_tool_use,
    sign_tool_use_async,
    sign_text,
    sign_text_async,
    sign_message,
    sign_message_async,
    verify_envelope,
)

from moss import SignResult, VerifyResult, Envelope, enterprise_enabled

__all__ = [
    "sign_response",
    "sign_response_async",
    "sign_tool_use",
    "sign_tool_use_async",
    "sign_text",
    "sign_text_async",
    "sign_message",
    "sign_message_async",
    "verify_envelope",
    "SignResult",
    "VerifyResult",
    "Envelope",
    "enterprise_enabled",
]
