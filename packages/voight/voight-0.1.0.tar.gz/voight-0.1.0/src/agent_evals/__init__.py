"""Agent Evals - A framework for testing non-deterministic AI agents."""

from agent_evals.decorators import scenario, ScenarioResult, RunResult
from agent_evals.core import EvalResult, Judge, Generator, check
from agent_evals.judges import SimpleLLMJudge, DeterministicJudge, FileExistsJudge
from agent_evals.generators import AdversarialGenerator, SimpleGenerator
from agent_evals.sandbox import Sandbox

__all__ = [
    # Decorator
    "scenario",
    "ScenarioResult",
    "RunResult",
    # Core types
    "EvalResult",
    "Judge",
    "Generator",
    "check",
    # Judges
    "SimpleLLMJudge",
    "DeterministicJudge",
    "FileExistsJudge",
    # Generators
    "AdversarialGenerator",
    "SimpleGenerator",
    # Sandbox
    "Sandbox",
]
__version__ = "0.1.0"
