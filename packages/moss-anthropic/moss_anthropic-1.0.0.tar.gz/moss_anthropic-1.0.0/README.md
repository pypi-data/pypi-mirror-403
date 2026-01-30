# moss-anthropic

MOSS signing integration for Anthropic SDK (Claude). **Unsigned output is broken output.**

[![PyPI](https://img.shields.io/pypi/v/moss-anthropic)](https://pypi.org/project/moss-anthropic/)

## Installation

```bash
pip install moss-anthropic
```

## Quick Start

Sign tool use, responses, and text blocks from Claude:

```python
from anthropic import Anthropic
from moss_anthropic import sign_tool_use, sign_response, sign_text

client = Anthropic()

# Get a response with tool use
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    messages=[{"role": "user", "content": "What's the weather?"}],
    tools=[{"name": "get_weather", "description": "Get weather", ...}]
)

# Sign the full response
result = sign_response(response, agent_id="weather-bot")
print(f"Signed: {result.signature[:20]}...")

# Sign individual tool use blocks
for block in response.content:
    if block.type == "tool_use":
        result = sign_tool_use(block, agent_id="weather-bot")
```

## Enterprise Mode

Set `MOSS_API_KEY` for automatic policy evaluation:

```python
import os
os.environ["MOSS_API_KEY"] = "your-api-key"

from moss_anthropic import sign_tool_use, enterprise_enabled

print(f"Enterprise: {enterprise_enabled()}")  # True

result = sign_tool_use(
    tool_use_block,
    agent_id="finance-bot",
    context={"user_id": "u123"}
)

if result.blocked:
    print(f"Blocked by policy: {result.policy.reason}")
```

## Verification

```python
from moss_anthropic import verify_envelope

verify_result = verify_envelope(result.envelope)
if verify_result.valid:
    print(f"Signed by: {verify_result.subject}")
```

## All Functions

| Function | Description |
|----------|-------------|
| `sign_tool_use()` | Sign a tool use block |
| `sign_tool_use_async()` | Async version |
| `sign_response()` | Sign a full Message response |
| `sign_response_async()` | Async version |
| `sign_text()` | Sign a text block |
| `sign_text_async()` | Async version |
| `sign_message()` | Alias for sign_response |
| `sign_message_async()` | Async version |
| `verify_envelope()` | Verify a signed envelope |

## Enterprise Features

| Feature | Free | Enterprise |
|---------|------|------------|
| Local signing | ✓ | ✓ |
| Offline verification | ✓ | ✓ |
| Policy evaluation | - | ✓ |
| Evidence retention | - | ✓ |
| Audit exports | - | ✓ |

## Links

- [moss-sdk](https://pypi.org/project/moss-sdk/) - Core MOSS SDK
- [mosscomputing.com](https://mosscomputing.com) - Project site

## License

This package is licensed under the [Business Source License 1.1](LICENSE).

- Free for evaluation, testing, and development
- Free for non-production use
- Production use requires a [MOSS subscription](https://mosscomputing.com/pricing)
- Converts to Apache 2.0 on January 25, 2030
