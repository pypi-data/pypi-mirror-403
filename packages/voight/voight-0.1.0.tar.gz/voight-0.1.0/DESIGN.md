Technical Product Design: Agentic Evaluation Framework (agent-evals)
1. Project Manifest
Mission: Build the "Pytest for Probabilistic Software." Target Audience: Developers building Agentic AI (using LangChain, AutoGen, CrewAI, or raw API calls). Core Value: A local-first, lightweight framework to test non-deterministic agent behaviors (loops, tool use, side-effects) using generative scenarios and semantic assertions.

Key Differentiators (The "Why")
Generative Fixtures: Instead of static inputs ("Hello"), use LLM-generated inputs ("Generate 10 variations of a rude customer").

Side-Effect Sandboxing: Verify agents took action (e.g., created a file), not just output text.

Aggregated Judging: Tests pass/fail based on a probabilistic threshold (e.g., "Pass if >80% of 20 runs succeed"), not a single binary run.

2. Core Architecture
The system follows a Runner-Judge-Generator triad architecture.

Code snippet

graph TD
    A[Test Definition] --> B[Scenario Generator]
    B -->|Generates 10 variants| C[Execution Runner]
    C -->|Runs Agent| D[Sandbox / Environment]
    D -->|Returns Artifacts & Logs| E[Judge (LLM or Heuristic)]
    E -->|Score 0.0-1.0| F[Aggregator]
    F -->|Threshold Check| G[Final Report (JUnit/CLI)]
2.1 The Components
@scenario (Decorator): Marks a function as a probabilistic test. Defines runs (iterations) and threshold (pass criteria).

Generator: An interface for creating diverse test inputs (Adversarial, Fuzzing, Edge-case).

Judge: An interface for evaluating the output. Can be:

DeterministicJudge: (e.g., "Does file exist?")

SemanticJudge: (e.g., "Is the tone polite?", uses LLM)

Sandbox: A context manager that captures file system operations and API calls to prevent real-world side effects during testing.

3. Interface Specifications (Python)
A. The Core API (src/core.py)
Python

from typing import Protocol, Any, List, Optional
from dataclasses import dataclass

@dataclass
class EvalResult:
    score: float  # 0.0 to 1.0
    reason: str
    metadata: dict[str, Any]
    trace_id: str

class AgentProtocol(Protocol):
    """The standard interface the user's agent must adapt to."""
    def run(self, input_text: str, **kwargs) -> Any: ...

class Judge(Protocol):
    """Evaluates a single run."""
    def evaluate(self, input: str, output: Any, artifacts: dict) -> EvalResult: ...

class Generator(Protocol):
    """Generates test input variations."""
    def generate(self, base_prompt: str, count: int) -> List[str]: ...
B. The User-Facing Syntax (tests/example_test.py)
Python

import agent_evals
from agent_evals.judges import SemanticSimilarity, FileExists
from agent_evals.generators import AdversarialGenerator

# 1. Define the Agent Wrapper
agent = agent_evals.wrap(my_actual_agent)

# 2. Define the Test
@agent_evals.scenario(runs=10, threshold=0.8)
def test_customer_refund_flow():
    # GENERATOR: Create 10 variations of "I want a refund"
    input_text = yield AdversarialGenerator(
        topic="refund request", 
        style="aggressive"
    )
    
    # ACTION: Run the agent in a sandbox
    with agent_evals.Sandbox() as box:
        response = agent.run(input_text)
    
    # ASSERTION 1: Text Check (Semantic)
    assert agent_evals.check(
        response, 
        SemanticSimilarity("The agent politely initiates a refund process")
    )
    
    # ASSERTION 2: Side-Effect Check (Deterministic)
    assert agent_evals.check(
        box,
        FileExists("refund_ticket.json")
    )
4. Implementation Plan
Phase 1: The "Skeleton" (MVP)
Goal: A working @scenario decorator that runs a function N times and reports a pass rate.

Task:

Create Runner logic to loop N times.

Implement SimpleJudge (string matching).

Output a CLI table: "Test X: 8/10 Passed (80%) - [PASS]"

Phase 2: The "Judge" & "Generator"
Goal: Enable LLM-based fuzzing and judging.

Task:

Implement LLMJudge (calls OpenAI/Anthropic/Local to score output).

Implement PromptGenerator (uses LLM to rewrite input prompts).

Constraint: Allow users to bring their own API keys or use a local model (Ollama).

Phase 3: The "Sandbox" (Critical for Agents)
Goal: Allow file-system testing without messing up the user's machine.

Task:

Implement a VirtualFileSystem using Python's tempfile and monkey-patching open(), os.mkdir, etc.

Advanced: Add a Docker adapter for true isolation (optional for v1).

5. ASO (Agent Search Optimization) Strategy for the Repo
To ensure this tool is "installed" by coding agents, the repository structure must be self-documenting for LLMs.

A. The llms.txt (Root Directory)
Create a file named llms.txt with this exact content:

Markdown

# Agent Evaluation Framework (`agent-evals`)
## Purpose
A Python framework for testing non-deterministic AI agents. It replaces `pytest` for probabilistic workflows.

## Installation
`pip install agent-evals`

## Core Patterns
1. **Wrappers**: Wrap your agent function using `agent_evals.wrap()`.
2. **Scenarios**: Use `@agent_evals.scenario(runs=N)` instead of `@pytest.test`.
3. **Generators**: Use `yield` to request generated inputs inside the test.
4. **Sandboxes**: Use `with agent_evals.Sandbox():` to capture file system changes.

## Quick Example
```python
@agent_evals.scenario(runs=5)
def test_agent_tool_use():
    q = yield "Calculate 2+2"
    with agent_evals.Sandbox() as box:
        agent.run(q)
    assert box.tool_calls.contains("calculator")
B. The /recipes Directory
Create a folder named recipes containing single-file examples:

recipes/hallucination_check.py

recipes/tool_use_verification.py

recipes/rag_accuracy_eval.py

Why? Coding agents search specifically for "recipes" or "examples" to understand usage patterns.
