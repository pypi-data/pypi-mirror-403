# moss-autogen

MOSS signing integration for AutoGen. **Unsigned output is broken output.**

[![PyPI](https://img.shields.io/pypi/v/moss-autogen)](https://pypi.org/project/moss-autogen/)

## Installation

```bash
pip install moss-autogen
```

## Quick Start: Explicit Signing (Recommended)

Sign messages, function results, and conversations:

```python
from autogen import AssistantAgent
from moss_autogen import sign_message, sign_function_result, sign_conversation

# Create your agent
agent = AssistantAgent(name="analyst", llm_config={"model": "gpt-4"})

# Get a reply and sign it
reply = agent.generate_reply(messages=[{"content": "Analyze this"}])
result = sign_message(reply, agent_id="analyst")
print(f"Signed: {result.signature[:20]}...")

# Sign function/tool results
func_result = execute_tool(args)
result = sign_function_result(func_result, agent_id="analyst", function="execute_tool")

# Sign entire conversation
result = sign_conversation(chat_history, agent_id="chat-session")
```

## Enterprise Mode

Set `MOSS_API_KEY` for automatic policy evaluation:

```python
import os
os.environ["MOSS_API_KEY"] = "your-api-key"

from moss_autogen import sign_message, enterprise_enabled

print(f"Enterprise: {enterprise_enabled()}")  # True

result = sign_message(
    {"role": "assistant", "content": "Transfer approved"},
    agent_id="finance-agent",
    context={"user_id": "u123", "action": "transfer"}
)

if result.blocked:
    print(f"Blocked by policy: {result.policy.reason}")
```

## Verification

```python
from moss_autogen import verify_envelope

verify_result = verify_envelope(result.envelope)
if verify_result.valid:
    print(f"Signed by: {verify_result.subject}")
```

## All Functions

| Function | Description |
|----------|-------------|
| `sign_message()` | Sign a message |
| `sign_message_async()` | Async version |
| `sign_function_result()` | Sign tool/function result |
| `sign_function_result_async()` | Async version |
| `sign_conversation()` | Sign full conversation |
| `sign_conversation_async()` | Async version |
| `sign_reply()` | Sign generate_reply output |
| `sign_reply_async()` | Async version |
| `verify_envelope()` | Verify a signed envelope |

## Legacy API

The old wrapper API is still available:

```python
from moss_autogen import signed_agent

agent = signed_agent(
    AssistantAgent(name="analyst", ...),
    "moss:lab:analyst"
)
# agent.moss_envelope available after each reply
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
