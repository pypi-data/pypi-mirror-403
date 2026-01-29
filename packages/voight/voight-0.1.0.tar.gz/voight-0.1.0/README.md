# Voight

[![CI](https://github.com/your-org/voight/actions/workflows/ci.yml/badge.svg)](https://github.com/your-org/voight/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/voight.svg)](https://badge.fury.io/py/voight)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**The Pytest for Probabilistic Software.**

Voight is a Python testing framework designed specifically for non-deterministic AI agents. It replaces standard unit tests with probabilistic scenarios that run multiple times and pass based on success rate thresholds.

## Why Voight?

Traditional testing assumes deterministic behavior: same input → same output. But AI agents are **probabilistic**—they may produce different outputs each time, use tools unpredictably, or fail intermittently.

Voight solves this with:

- **🎲 Probabilistic Testing**: Run tests N times, pass if success rate exceeds threshold
- **🧪 Generative Fixtures**: Use LLM-generated adversarial inputs instead of static test data
- **📦 Side-Effect Sandboxing**: Safely test agents that write files without cluttering your system
- **⚖️ Semantic Judging**: Evaluate outputs using LLM-based semantic analysis, not just string matching

## Installation

```bash
pip install voight
```

Or with [uv](https://github.com/astral-sh/uv):

```bash
uv add voight
```

## Quick Start

### 1. Initialize a Project

```bash
voight init
```

This creates:
- `voight.config.toml` - Configuration file
- `tests/test_agent.py` - Sample test scenarios

### 2. Write Your First Scenario

```python
from agent_evals import scenario, Sandbox, check
from agent_evals.judges import FileExistsJudge, DeterministicJudge

@scenario(runs=10, threshold=0.8)
def test_agent_creates_output():
    """Test passes if agent creates file in ≥80% of runs."""
    with Sandbox() as box:
        my_agent.run("Create a report")

        # Verify file was created
        assert check(box, FileExistsJudge("report.txt"))
```

### 3. Run Tests

```bash
voight run
```

Output:
```
Discovering scenarios in: tests
Found 3 scenario(s)

Running: test_agent::test_agent_creates_output... 9/10 PASS

===============================================
Scenario                           Passed  Rate  Status
-----------------------------------------------
test_agent::test_agent_creates_output  9/10   90%  [PASS]
===============================================
```

## Core Concepts

### @scenario Decorator

The `@scenario` decorator transforms a test function into a probabilistic test:

```python
@scenario(
    runs=10,           # Run 10 times
    threshold=0.8,     # Pass if ≥80% succeed
    generator=my_gen,  # Optional: generate diverse inputs
    base_prompt="test" # Base prompt for generator
)
def test_my_agent(input_text: str):
    # input_text is injected by the generator
    response = agent.run(input_text)
    assert "success" in response
```

### Generators

Create diverse test inputs automatically:

```python
from agent_evals import SimpleGenerator, AdversarialGenerator

# Template-based (no API key needed)
generator = SimpleGenerator(templates=[
    "Tell me about {topic}",
    "Explain {topic} simply",
    "What is {topic}?",
])

# LLM-powered adversarial inputs (requires OpenAI API key)
generator = AdversarialGenerator(
    topic="refund request",
    style="frustrated customer"
)

@scenario(runs=5, generator=generator, base_prompt="Python")
def test_with_varied_inputs(prompt: str):
    response = agent.run(prompt)
    assert len(response) > 0
```

### Sandbox

Isolate file system side effects:

```python
from agent_evals import Sandbox

@scenario(runs=5)
def test_file_creation():
    with Sandbox() as box:
        # All file operations happen in a temp directory
        agent.run("Create output.json")

        # Check files in the sandbox
        assert box.file_exists("output.json")
        content = box.get_file_content("output.json")
        assert "data" in content

    # Sandbox is automatically cleaned up
    # Original directory is restored even if test fails
```

### Judges

Evaluate outputs with different strategies:

```python
from agent_evals import check
from agent_evals.judges import (
    DeterministicJudge,
    FileExistsJudge,
    SimpleLLMJudge,
)

# Rule-based text checking
judge = DeterministicJudge(
    required_phrases=["thank you", "help"],
    forbidden_phrases=["error", "failed"],
)
assert check(response, judge, input="greeting")

# File existence with validation
judge = FileExistsJudge(
    "output.json",
    min_size_bytes=100,
    contains='"status": "success"'
)
assert check(sandbox, judge)

# LLM-based semantic evaluation (requires API key)
judge = SimpleLLMJudge(
    model="gpt-4o-mini",
    custom_criteria="Response must be polite and helpful"
)
result = judge.evaluate(input="Help me", output=response)
assert result.score >= 0.8
```

## CLI Commands

```bash
# Initialize a new project
voight init

# Run all scenarios
voight run

# Run with verbose output
voight run --verbose

# Run specific tests by pattern
voight run -k "test_customer"

# Run tests in a specific directory
voight run path/to/tests/

# Show version
voight --version
```

## Example: Testing a Customer Service Agent

```python
from agent_evals import scenario, Sandbox, check, AdversarialGenerator
from agent_evals.judges import DeterministicJudge, FileExistsJudge

# Generate frustrated customer messages
generator = AdversarialGenerator(
    topic="product return",
    style="angry and impatient"
)

@scenario(runs=10, threshold=0.9, generator=generator)
def test_handles_angry_customers(customer_message: str):
    """Agent should respond empathetically to angry customers."""
    response = customer_service_agent.respond(customer_message)

    # Must be empathetic, never dismissive
    judge = DeterministicJudge(
        required_phrases=["sorry", "understand"],
        forbidden_phrases=["calm down", "your fault"],
    )
    assert check(response, judge, input=customer_message)


@scenario(runs=5, threshold=1.0)
def test_creates_support_ticket():
    """Agent should always create a ticket for complaints."""
    with Sandbox() as box:
        agent.handle_complaint("I want a refund!")

        # Ticket must be created
        assert check(box, FileExistsJudge("ticket.json"))

        # Ticket must have required fields
        import json
        ticket = json.loads(box.get_file_content("ticket.json"))
        assert "customer_id" in ticket
        assert "issue" in ticket
```

## Recipes

See the `recipes/` directory for complete examples:

- **[hallucination_check.py](recipes/hallucination_check.py)** - Detect hallucinations in RAG systems
- **[tool_use_verification.py](recipes/tool_use_verification.py)** - Verify agents use tools correctly
- **[rag_accuracy_eval.py](recipes/rag_accuracy_eval.py)** - Evaluate RAG retrieval accuracy
- **[customer_service_agent.py](recipes/customer_service_agent.py)** - Test customer service bots

## Configuration

Create `voight.config.toml` in your project root:

```toml
[voight]
default_runs = 10
default_threshold = 0.8
test_path = "tests/"
output_format = "table"

[voight.llm]
model = "gpt-4o-mini"
api_key_env = "OPENAI_API_KEY"
```

## API Reference

### Core Classes

| Class | Description |
|-------|-------------|
| `scenario` | Decorator for probabilistic tests |
| `Sandbox` | Context manager for file system isolation |
| `EvalResult` | Result of judge evaluation (score, reason, metadata) |
| `ScenarioResult` | Result of running a scenario (pass/fail counts) |

### Generators

| Generator | Description |
|-----------|-------------|
| `SimpleGenerator` | Template-based input generation |
| `AdversarialGenerator` | LLM-powered adversarial inputs |

### Judges

| Judge | Description |
|-------|-------------|
| `DeterministicJudge` | Rule-based text checking |
| `FileExistsJudge` | File existence and content validation |
| `SimpleLLMJudge` | LLM-based semantic evaluation |

### Helper Functions

| Function | Description |
|----------|-------------|
| `check(target, judge)` | Evaluate target with judge, return bool |

## Requirements

- Python 3.10+
- For LLM features: OpenAI API key (`OPENAI_API_KEY` environment variable)

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Related Projects

- [pytest](https://pytest.org) - The standard Python testing framework
- [LangSmith](https://smith.langchain.com) - LangChain's tracing and evaluation platform
- [promptfoo](https://promptfoo.dev) - LLM prompt testing framework

---

**Voight** - *"More human than human"* - Testing AI agents the probabilistic way.
