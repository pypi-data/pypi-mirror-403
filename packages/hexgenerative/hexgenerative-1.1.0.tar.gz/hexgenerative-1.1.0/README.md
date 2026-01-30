# Hexa Generative AI - Python SDK

Official Python client for Hexa AI API.

## Installation

```bash
pip install hexgenerative
```

## Quick Start

```python
from hexgenerative import HexaAI

# Initialize client
client = HexaAI(api_key="hgx-your-api-key")

# Create chat completion
response = client.chat.completions.create(
    model="hexa-pro",
    messages=[
        {"role": "user", "content": "Explain quantum computing in simple terms"}
    ]
)

print(response.choices[0].message.content)
```

## Available Models

| Model | Description | Best For |
|-------|-------------|----------|
| `hexa-instant` | Fastest model | Quick responses, simple tasks |
| `hexa-balanced` | General purpose | Most use cases |
| `hexa-reasoning` | Deep analysis | Complex reasoning |
| `hexa-advanced` | Coding expert | Programming tasks |
| `hexa-pro` | Premium quality | Best results |
| `hexa-vision-scout` | Vision model | Image understanding |

## Smart Routing

Let Hexa AI pick the best model automatically:

```python
# By task type
response = client.chat.completions.create(
    task="coding",
    messages=[{"role": "user", "content": "Write a Python function"}]
)

# By optimization preference
response = client.chat.completions.create(
    optimize_for="speed",
    messages=[{"role": "user", "content": "Quick answer please"}]
)

# Full auto-select
response = client.chat.completions.create(
    auto_select=True,
    messages=[{"role": "user", "content": "Your message"}]
)
```

## Async Support

```python
import asyncio
from hexgenerative import HexaAI

client = HexaAI(api_key="hgx-your-api-key")

async def main():
    response = await client.chat.completions.acreate(
        model="hexa-pro",
        messages=[{"role": "user", "content": "Hello!"}]
    )
    print(response.choices[0].message.content)

asyncio.run(main())
```

## Error Handling

```python
from hexgenerative import HexaAI
from hexgenerative.client import HexaAIError

client = HexaAI(api_key="hgx-your-api-key")

try:
    response = client.chat.completions.create(
        model="hexa-pro",
        messages=[{"role": "user", "content": "Hello"}]
    )
except HexaAIError as e:
    print(f"Error: {e.message}")
    print(f"Status: {e.status_code}")
```

## Agentic Features

### Agents (Beta)
Run complex tasks with autonomous agents.
```python
result = client.agent.run(
    task="Research the latest AI trends",
    model="hexa-ultra"
)
print(result["result"])
```

### RAG (Knowledge Base)
High-accuracy retrieval augmented generation.
```python
# Upload document
client.rag.upload(
    title="Company Policy", 
    content="Employees get 30 days of leave..."
)

# Search
results = client.rag.search(query="leave policy")
```

### Context Management (300K Tokens)
Manage massive context sessions.
```python
# Create session
session = client.context.create(system_prompt="You are a helpful assistant")
session_id = session["data"]["session_id"]

# Add message
client.context.add(
    session_id=session_id,
    message={"role": "user", "content": "..."}
)
```

### Tools & Code Execution
```python
# List tools
tools = client.tools.list()

# Execute Code
result = client.code.execute(code="print(10 + 20)")
```

## License

MIT
