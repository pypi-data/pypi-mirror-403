# moss-langchain

MOSS signing integration for LangChain. **Unsigned output is broken output.**

[![PyPI](https://img.shields.io/pypi/v/moss-langchain)](https://pypi.org/project/moss-langchain/)

## Installation

```bash
pip install moss-langchain
```

## Quick Start: Explicit Signing (Recommended)

Sign specific outputs with full control:

```python
from langchain_openai import ChatOpenAI
from moss_langchain import sign_tool_call, sign_chain_result, sign_message

# Sign a tool call
tool_call = {"name": "get_weather", "args": {"location": "NYC"}, "id": "call_123"}
result = sign_tool_call(tool_call, agent_id="weather-bot")
print(f"Signed: {result.signature[:20]}...")

# Sign a chain result
chain = ChatOpenAI() | StrOutputParser()
output = chain.invoke("What is 2+2?")
result = sign_chain_result(output, agent_id="math-bot", chain_name="calculator")

# Sign a message
message = AIMessage(content="The answer is 4")
result = sign_message(message, agent_id="math-bot")
```

## Enterprise Mode

Set `MOSS_API_KEY` for automatic policy evaluation:

```python
import os
os.environ["MOSS_API_KEY"] = "your-api-key"

from moss_langchain import sign_tool_call, enterprise_enabled

print(f"Enterprise: {enterprise_enabled()}")  # True

# Tool calls are evaluated against policies
result = sign_tool_call(
    {"name": "send_email", "args": {"to": "user@example.com"}, "id": "call_1"},
    agent_id="email-bot",
    context={"user_id": "u123"}
)

if result.blocked:
    print(f"Blocked by policy: {result.policy.reason}")
```

## Callback Handler for Auto-Signing

For automatic signing of all chain events:

```python
from moss_langchain import MOSSCallbackHandler

# Create handler - signs tool calls and chain outputs
handler = MOSSCallbackHandler(
    agent_id="my-agent",
    sign_tools=True,
    sign_chains=True
)

chain = ChatOpenAI() | StrOutputParser()
result = chain.invoke("Hello", config={"callbacks": [handler]})

# Access signed envelopes
for envelope in handler.envelopes:
    print(f"Signed: {envelope.subject}")
```

## Verification

```python
from moss_langchain import verify_envelope

# Verify any signed envelope
verify_result = verify_envelope(result.envelope)
if verify_result.valid:
    print(f"Signed by: {verify_result.subject}")
```

## All Functions

| Function | Description |
|----------|-------------|
| `sign_tool_call()` | Sign a LangChain tool call |
| `sign_chain_result()` | Sign chain output |
| `sign_message()` | Sign an AI message |
| `sign_tool_result()` | Sign tool execution result |
| `sign_output()` | Sign any output (generic) |
| `verify_envelope()` | Verify a signed envelope |

## Legacy API

The old auto-signing API is still available for backwards compatibility:

```python
from moss_langchain import enable_moss, SignedCallbackHandler

enable_moss("moss:myteam:agent")  # Global auto-signing
cb = SignedCallbackHandler("moss:bot:summary")  # Per-chain signing
```

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
