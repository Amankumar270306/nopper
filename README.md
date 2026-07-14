# Nopper 🤖

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Nopper** is a production-grade, 4-layer Python SDK and CLI to manage every AI provider (**OpenAI, Anthropic, Google Gemini, Ollama, Groq, Mistral, OpenRouter, Together AI, LM Studio, and vLLM**) from a unified interface.

Stop wrestling with dozens of incompatible provider SDKs, conflicting message formats, and complex environment variables. Configure Nopper once via the CLI or code, and your applications will run seamlessly on any AI model or execution node.

---

## 🏗️ Production Architecture

Nopper v2 is engineered around a decoupled **4-Layer Architecture**:

```
Application  ──>  Wrapper (AI / AsyncAI)  ──>  Node Execution Engine  ──>  Provider Adapter  ──>  HTTP Transport
```

- **Application Layer**: Your Python code calls standard methods (`ai.chat()`, `ai.stream()`, `ai.embed()`).
- **Wrapper Layer (`AI`, `AsyncAI`)**: The public user-facing API surface. Manages prompts, stateful history, middleware pipelines, and event subscriptions. Knows **nothing** about specific AI providers.
- **Node Layer (`NodeManager`, `LocalNode`, `FallbackNode`, `CachedNode`)**: The execution engine. Owns execution strategies, provider selection, model configuration, retry policies, fallback chains, and response caching.
- **Provider Layer (`ProviderRegistry`, `ProviderFactory`)**: Uniform adapter contract (`BaseProvider`). Adapters self-register dynamically into a singleton registry without modifying core code.
- **Transport**: Pure `httpx` async & sync clients. Zero heavy SDK dependencies.

---

## ⚡ Key Features

- 🔌 **Unified SDK**: `from nopper import AI` gives you access to every provider.
- 🧱 **Execution Nodes**: Decouple model execution from code. Define nodes in `~/.nopper/nodes/*.json` and swap providers on the fly.
- 🔄 **Hot-Swappable**: Update provider or model parameters via the CLI without restarting or editing your Python code.
- 🔌 **Provider Registry**: Pluggable provider adapter framework. Add new custom providers via `registry.register()`.
- ⚙️ **Middleware Pipeline**: Inspect or transform requests and responses before and after execution.
- 📡 **Event Bus**: Subscribe to lifecycle events (`on_request`, `on_response`, `on_token`) for custom logging, analytics, or guardrails.
- 📦 **Zero Heavy Dependencies**: Built on `httpx` and `pydantic`. No heavy provider SDKs.
- 🌊 **Native Streaming**: Real-time token streaming for synchronous and asynchronous clients.
- 🤖 **Structured Outputs**: Native support for Pydantic response models out of the box.
- 💬 **Stateful Conversations**: Automatic message history, persistence to disk, and context window trimming.
- 🤖 **Native Agentic Loop**: Built-in `Agent` and `@tool` decorator supporting ReAct tool-calling loops.
- ⚡ **Async Support**: Fully asynchronous `AsyncAI` client for high-performance applications.
- 🛡️ **Failover & Retries**: Built-in exponential backoff and seamless failover across fallback provider chains.
- 🧠 **Embeddings**: Unified `ai.embed()` interface across OpenAI, Gemini, Ollama, etc.
- 🏟️ **Arena Mode**: Run prompts across multiple models concurrently and compare responses.
- ⚡ **Response Caching**: In-memory and disk-based LRU caching for deterministic responses.

---

## 🚀 Installation

Install Nopper directly in editable mode or from source:

```bash
pip install nopper
```

---

## 💻 CLI Usage

Manage your global configuration, nodes, wrappers, caches, and aliases straight from the terminal.

### 1. Interactive Setup & Status
```bash
# Interactive setup wizard
nopper start

# Switch global active provider
nopper use anthropic

# Check environment health (API keys, internet, model reachability)
nopper doctor

# See current active context
nopper whoami
```

### 2. Node Management (Execution Engine)
```bash
# List all configured execution nodes
nopper node list

# Add a custom remote node (e.g. Tailscale or local Ollama endpoint)
nopper node add my_ollama --url http://100.x.y.z:11434/v1 --model llama3

# Update node configuration
nopper node update my_ollama --model llama3.1

# Remove a node
nopper node remove my_ollama
```

### 3. Wrapper & Cache Management
```bash
# Manage response cache
nopper cache enable
nopper cache disable
nopper cache stats
nopper cache clear

# Manage model aliases
nopper alias add fast gpt-4o-mini
nopper alias list
```

---

## 🐍 Python SDK Usage

### Basic Chat Completion

```python
from nopper import AI

# Initializes using default CLI / disk configuration
ai = AI()

# 1. Simple text generation
response = ai.chat("What is the capital of France?")
print(response)  # Returns AIString containing text + metadata
```

### Response Metadata

Responses contain rich execution metadata:

```python
response = ai.chat("Explain quantum computing.")

print(response)           # Text content
print(response.tokens)    # Total token count
print(response.cost)      # Calculated cost in USD
print(response.latency)   # Execution latency in seconds
print(response.model)     # Model used
print(response.provider)  # Provider used
```

### Native Streaming

```python
ai = AI()

for chunk in ai.stream("Write a short poem about the ocean."):
    print(chunk, end="", flush=True)
```

### Async Client (`AsyncAI`)

```python
import asyncio
from nopper import AsyncAI

async def main():
    ai = AsyncAI()
    response = await ai.chat("Hello async world!")
    print(response)

asyncio.run(main())
```

### Structured Outputs (Pydantic)

Enforce structured JSON responses using Pydantic models:

```python
from pydantic import BaseModel
from nopper import AI

class Person(BaseModel):
    name: str
    age: int

ai = AI()
person = ai.chat("John is 25 years old.", response_model=Person)

print(person.name)  # John
print(person.age)   # 25
print(person.cost)  # Dynamically attached metadata
```

### Stateful Conversations

Maintain chat history automatically with history persistence and window trimming:

```python
from nopper import AI

ai = AI()
chat = ai.conversation(
    system_prompt="You are a helpful programming tutor.",
    save_file="history.json",  # Saves & reloads context automatically
    max_history=10             # Keeps 10 most recent messages
)

reply1 = chat.ask("Hello, my name is Alice.")
print(reply1)

reply2 = chat.ask("What is my name?")
print(reply2)  # Remembers "Alice"
```

### Middleware Pipeline & Events

Inject custom hooks or subscribe to lifecycle events:

```python
from nopper import AI, Middleware

class AuditMiddleware(Middleware):
    def before_request(self, request):
        print(f"[Audit] Sending {len(request.messages)} messages")
        return request

    def after_response(self, response):
        print(f"[Audit] Received {response.total_tokens} tokens")
        return response

ai = AI()
ai.use_middleware(AuditMiddleware())

# Event bus listener
ai.on("on_token", lambda chunk: print(".", end=""))

ai.chat("Tell me a quick joke.")
```

### Agentic Loop & Tools

Nopper includes a native `Agent` class supporting ReAct tool-execution loops:

```python
from nopper import AI, Agent, tool

@tool
def add(a: float, b: float) -> float:
    """Add two numbers together."""
    return a + b

ai = AI()
agent = Agent(
    ai=ai,
    system_prompt="You are a helpful math assistant.",
    tools=[add]
)

result = agent.run("What is 15.5 added to 4.5?")
print(result)  # Automatically executes the `add` tool
```

### Embeddings

```python
from nopper import AI

ai = AI()
embeddings = ai.embed("Nopper makes vector embeddings unified.")
print(len(embeddings))
```

### Arena Mode

Compare responses across multiple providers concurrently:

```python
from nopper import AI

ai = AI(provider=["openai", "anthropic", "gemini"])
response = ai.arena("What is the speed of light?")

print(response)  # Formatted side-by-side comparison
```

### Automatic Fallbacks & Retries

Define primary and fallback providers. If the primary fails, Nopper retries with exponential backoff and fails over seamlessly:

```python
from nopper import AI

ai = AI(provider=["groq", "openrouter", "gemini"], max_retries=3)
response = ai.chat("Build a website outline.")
print(f"Fulfilled by: {response.provider}")
```

---

## 🛠️ Registering Custom Providers

You can register third-party provider adapters at runtime without modifying Nopper core:

```python
from nopper import BaseProvider, AI
from nopper.provider import registry

class MyCustomAdapter(BaseProvider):
    def chat(self, messages, **kwargs):
        # Translate to proprietary API calls...
        ...

# Register adapter
registry.register("my_custom", MyCustomAdapter)

# Bind and execute
ai = AI(provider="my_custom")
```

---

## 📄 License

MIT License © 2026 Aman Kumar
