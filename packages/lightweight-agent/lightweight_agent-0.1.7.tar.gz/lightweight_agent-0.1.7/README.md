# Lightweight Agent

A lightweight LLM agent framework supporting async OpenAI and Anthropic APIs with streaming/non-streaming responses, built-in ReAct agents and TODO-based agents.

## Features

- ✅ Async OpenAI and Anthropic API support
- ✅ Streaming and non-streaming responses
- ✅ Built-in ReAct Agent and TODO-based Agent
- ✅ Specialized Agent Extensions (Citation Agent, Figure Agent)
- ✅ Rich built-in tools (file operations, Python execution, batch editing, etc.)
- ✅ Citation tools for BibTeX processing
- ✅ Environment variable configuration support
- ✅ Unified interface design
- ✅ Comprehensive error handling
- ✅ Published to PyPI, supports pip installation
- ✅ Skill extension and Node.js script runner tools

## Installation

### Install from PyPI (Recommended)

```bash
pip install lightweight-agent
```

### Install from Source

```bash
# Clone repository
git clone https://github.com/mbt1909432/lightweight-agent.git
cd lightweight-agent

# Install dependencies
pip install -e .
```

### Development Installation

```bash
pip install -e ".[dev]"
```

## Quick Start

### Environment Variables Configuration

Before using, you need to set the corresponding environment variables:

**OpenAI Configuration:**
```bash
export OPENAI_API_KEY="your-openai-api-key"
export OPENAI_BASE_URL="https://api.openai.com/v1"  # Optional
export OPENAI_MODEL="gpt-3.5-turbo"  # Optional, defaults to gpt-3.5-turbo
```

**Anthropic Configuration:**
```bash
export ANTHROPIC_API_KEY="your-anthropic-api-key"
export ANTHROPIC_BASE_URL="https://api.anthropic.com"  # Optional
export ANTHROPIC_MODEL="claude-3-sonnet-20240229"  # Optional, defaults to claude-3-sonnet-20240229
```

### Basic Usage

#### OpenAI Non-streaming Response

```python
import asyncio
from lightweight_agent import OpenAIClient

async def main():
    client = OpenAIClient()
    response = await client.generate("Hello, how are you?")
    print(response)

asyncio.run(main())
```

#### OpenAI Streaming Response

```python
import asyncio
from lightweight_agent import OpenAIClient

async def main():
    client = OpenAIClient()
    async for chunk in await client.generate("Tell me a story", stream=True):
        print(chunk, end="", flush=True)
    print()  # New line

asyncio.run(main())
```

#### Anthropic Non-streaming Response

```python
import asyncio
from lightweight_agent import AnthropicClient

async def main():
    client = AnthropicClient()
    response = await client.generate("Hello, how are you?", max_tokens=1024)
    print(response)

asyncio.run(main())
```

#### Anthropic Streaming Response

```python
import asyncio
from lightweight_agent import AnthropicClient

async def main():
    client = AnthropicClient()
    async for chunk in await client.generate("Tell me a story", stream=True, max_tokens=1024):
        print(chunk, end="", flush=True)
    print()  # New line

asyncio.run(main())
```

### Runtime Configuration

You can also pass configuration parameters when initializing the client. These parameters will override environment variables:

```python
from lightweight_agent import OpenAIClient

client = OpenAIClient(
    api_key="your-api-key",
    base_url="https://api.openai.com/v1",
    model="gpt-4"
)
```

### Advanced Parameters

The `generate` method supports passing additional API parameters:

```python
# OpenAI example
response = await client.generate(
    "Write a poem",
    stream=False,
    temperature=0.7,
    max_tokens=500
)

# Anthropic example
response = await client.generate(
    "Write a poem",
    stream=False,
    max_tokens=500,
    temperature=0.7
)
```

## API Documentation

### OpenAIClient

#### `__init__(api_key=None, base_url=None, model=None)`

Initialize OpenAI client.

**Parameters:**
- `api_key` (str, optional): OpenAI API key
- `base_url` (str, optional): API base URL
- `model` (str, optional): Model name

#### `generate(prompt, stream=False, **kwargs)`

Generate response.

**Parameters:**
- `prompt` (str): Prompt text
- `stream` (bool): Whether to stream response, defaults to False
- `**kwargs`: Other OpenAI API parameters (e.g., temperature, max_tokens, etc.)

**Returns:**
- If `stream=False`, returns `str`
- If `stream=True`, returns `AsyncIterator[str]`

### AnthropicClient

#### `__init__(api_key=None, base_url=None, model=None)`

Initialize Anthropic client.

**Parameters:**
- `api_key` (str, optional): Anthropic API key
- `base_url` (str, optional): API base URL
- `model` (str, optional): Model name

#### `generate(prompt, stream=False, **kwargs)`

Generate response.

**Parameters:**
- `prompt` (str): Prompt text
- `stream` (bool): Whether to stream response, defaults to False
- `**kwargs`: Other Anthropic API parameters (e.g., max_tokens, temperature, etc.)
  - Note: `max_tokens` is a required parameter for Anthropic API. If not provided, the default value is 1024

**Returns:**
- If `stream=False`, returns `str`
- If `stream=True`, returns `AsyncIterator[str]`

## Exception Handling

The library provides the following exception classes:

- `LLMClientError`: Base exception class
- `ConfigurationError`: Configuration error
- `APIError`: API call error
- `NetworkError`: Network error
- `ValidationError`: Validation error

Usage example:

```python
from lightweight_agent import OpenAIClient, ConfigurationError, APIError

try:
    client = OpenAIClient()
    response = await client.generate("Hello")
except ConfigurationError as e:
    print(f"Configuration error: {e}")
except APIError as e:
    print(f"API error: {e}")
```

## Agent Usage

### ReAct Agent

ReAct Agent is an intelligent agent based on reasoning and action that can automatically call tools to complete tasks.

```python
import asyncio
from lightweight_agent import ReActAgent, OpenAIClient
import os
from pathlib import Path

async def main():
    # Initialize client
    client = OpenAIClient(
        api_key=os.getenv("LLM_API_KEY"),
        base_url=os.getenv("LLM_API_BASE"),
        model=os.getenv("MODEL")
    )
    
    # Create agent
    agent = ReActAgent(
        client=client,
        working_dir="./agent_work"
    )
    
    # Run task
    async for message in agent.run("Create a text file and write content"):
        # Process message stream
        print(message)

asyncio.run(main())
```

### TODO-based Agent

TODO-based Agent can automatically create task lists and execute them step by step.

```python
import asyncio
from lightweight_agent import TodoBasedAgent, OpenAIClient
import os

async def main():
    client = OpenAIClient(
        api_key=os.getenv("LLM_API_KEY"),
        base_url=os.getenv("LLM_API_BASE"),
        model=os.getenv("MODEL")
    )
    
    agent = TodoBasedAgent(
        client=client,
        working_dir="./todo_work"
    )
    
    async for message in agent.run("Create a chart using matplotlib"):
        print(message)
    
    # View TODO summary
    summary = agent.get_todo_summary()
    print(f"Completed: {summary['completed']}/{summary['total']}")

asyncio.run(main())
```

### Citation Agent

Citation Agent is specialized for inserting BibTeX citations into LaTeX documents. It automatically extracts BibTeX entries from source files and inserts them at semantically appropriate locations.

```python
import asyncio
from lightweight_agent import CitationAgent, OpenAIClient
import os

async def main():
    client = OpenAIClient(
        api_key=os.getenv("LLM_API_KEY"),
        base_url=os.getenv("LLM_API_BASE"),
        model=os.getenv("MODEL")
    )
    
    agent = CitationAgent(
        client=client,
        working_dir="./citation_work"
    )
    
    async for message in agent.run("Extract BibTeX entries from references.txt and insert them into paper.tex"):
        print(message)
    
    # View TODO summary
    summary = agent.get_todo_summary()
    print(f"Completed: {summary['completed']}/{summary['total']}")

asyncio.run(main())
```

### Figure Agent

Figure Agent is specialized for inserting figures into LaTeX documents. It scans figure directories and automatically inserts figures at semantically appropriate locations.

```python
import asyncio
from lightweight_agent import FigureAgent, OpenAIClient
import os

async def main():
    client = OpenAIClient(
        api_key=os.getenv("LLM_API_KEY"),
        base_url=os.getenv("LLM_API_BASE"),
        model=os.getenv("MODEL")
    )
    
    agent = FigureAgent(
        client=client,
        working_dir="./figure_work"
    )
    
    async for message in agent.run("Insert all figures from the figure directory into paper.tex"):
        print(message)
    
    # View TODO summary
    summary = agent.get_todo_summary()
    print(f"Completed: {summary['completed']}/{summary['total']}")

asyncio.run(main())
```

For more Agent usage examples, see [`Use_Case/README.md`](Use_Case/README.md).

## Example Code

For more example code, see:

- `examples/` directory - Basic client usage examples
  - `examples/openai_streaming.py` - OpenAI streaming response example
  - `examples/openai_non_streaming.py` - OpenAI non-streaming response example
  - `examples/anthropic_streaming.py` - Anthropic streaming response example
  - `examples/anthropic_non_streaming.py` - Anthropic non-streaming response example
  - `examples/citation_agent/` - Citation Agent usage example
    - `examples/citation_agent/example.py` - Citation Agent example
    - `examples/citation_agent/README.md` - Citation Agent documentation
- `Use_Case/` directory - Agent usage examples
  - `Use_Case/base_agent_example.py` - ReAct Agent example
  - `Use_Case/todo_agent_example.py` - TODO-based Agent example
  - `Use_Case/citation_agent_example.py` - Citation Agent example

## Development

### Run Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black src/ tests/ examples/
```

### Code Linting

```bash
ruff check src/ tests/ examples/
```

## License

MIT License

## Contributing

Issues and Pull Requests are welcome!

## Changelog

### 0.1.0 (2025-01-01)

- Initial release
- Support for async OpenAI and Anthropic APIs
- Support for streaming and non-streaming responses
- Environment variable configuration support
- Built-in ReAct Agent and TODO-based Agent
- Rich built-in tool support

### 0.2.0 (2025-01-10)

- Added Citation Agent extension for BibTeX citation insertion
- Added Figure Agent extension for LaTeX figure insertion
- Added BatchEditTool for efficient batch file editing
- Added Citation tools (bibtex_extract, bibtex_insert, bibtex_save)
- Enhanced TODO-based Agent with specialized workflows

### 0.1.4 (2026-01-20)

- Added Skill extension (`SkillTool`) with registry support for reusable skills
- Added Node.js runner tool for executing local `.js` files inside the agent
- Synchronized version documentation and packaging metadata

### 0.1.7 (2026-01-24)

- Insert bibliography commands before citation insertion to avoid citation overflow errors
- Refresh version documentation examples

## Version Updates

The project has been published to [PyPI](https://pypi.org/project/lightweight-agent/). To update versions:

### 1. Update Version Number

You need to update the version number in two files:

**`pyproject.toml`**:
```toml
[project]
version = "0.1.7"  # Update version number
```

**`src/lightweight_agent/__init__.py`**:
```python
__version__ = "0.1.7"  # Update version number
```

### 2. Build New Version

```bash
# Clean old builds
rm -rf build dist *.egg-info  # Linux/Mac
# Or PowerShell
Remove-Item -Recurse -Force build, dist, *.egg-info -ErrorAction SilentlyContinue

# Build new package
python -m build

# Validate package
twine check dist/*
```

### 3. Publish to PyPI

```bash
# Upload to PyPI
twine upload dist/*

# Or use environment variables to set authentication
export TWINE_USERNAME="__token__"
export TWINE_PASSWORD="pypi-your-api-token"
twine upload dist/*
```

### 4. Verify Release

```bash
# Wait a few minutes, then test installation
pip install --upgrade lightweight-agent
```

For detailed packaging and publishing process, refer to [`PACKAGING.md`](PACKAGING.md).

### Version Numbering Convention

Follow [Semantic Versioning](https://semver.org/):
- **MAJOR version**: Incompatible API changes
- **MINOR version**: Backward-compatible functionality additions
- **PATCH version**: Backward-compatible bug fixes

Examples:
- `0.1.0` → `0.1.1` (PATCH: bug fix)
- `0.1.0` → `0.2.0` (MINOR: new feature)
- `0.1.0` → `1.0.0` (MAJOR: breaking change)
