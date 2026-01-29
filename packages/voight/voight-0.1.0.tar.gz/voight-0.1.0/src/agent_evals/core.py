"""Core interfaces and data structures for agent-evals."""

from typing import Protocol, Any
from pydantic import BaseModel, Field


class EvalResult(BaseModel):
    """Result of evaluating an agent's output."""

    score: float = Field(ge=0.0, le=1.0, description="Score from 0.0 to 1.0")
    reason: str = Field(description="Explanation of the score")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Optional extra information"
    )


class Judge(Protocol):
    """Protocol for evaluating agent outputs."""

    def evaluate(self, input: str, output: str) -> EvalResult:
        """
        Evaluate an agent's output given the input.

        Args:
            input: The input that was given to the agent
            output: The output produced by the agent

        Returns:
            EvalResult with score, reason, and optional metadata
        """
        ...


class Generator(Protocol):
    """Protocol for generating test input variations."""

    def generate(self, base_prompt: str, n: int) -> list[str]:
        """
        Generate variations of a base prompt.

        Args:
            base_prompt: The base prompt to generate variations of
            n: Number of variations to generate

        Returns:
            List of generated prompt variations
        """
        ...


def check(
    target: Any,
    judge: Any,
    threshold: float = 0.5,
    input: str = "",
    output: str | None = None,
) -> bool:
    """
    Evaluate a target using a judge and return pass/fail based on threshold.

    This is syntactic sugar for calling judge.evaluate() and checking the score.
    It supports different judge signatures:
    - FileExistsJudge: evaluate(sandbox) -> EvalResult
    - SimpleLLMJudge/DeterministicJudge: evaluate(input, output) -> EvalResult

    Args:
        target: The target to evaluate (Sandbox, output string, etc.)
        judge: A judge instance with an evaluate() method
        threshold: Minimum score to pass (default: 0.5)
        input: Input string (for text-based judges)
        output: Output string (for text-based judges, or uses target if not provided)

    Returns:
        True if score >= threshold, False otherwise.

    Example:
        # With FileExistsJudge
        with Sandbox() as box:
            agent.run(prompt)
        assert check(box, FileExistsJudge("output.txt"))

        # With text judge
        assert check(response, DeterministicJudge(required_phrases=["hello"]))
    """
    # Import Sandbox here to avoid circular imports
    from agent_evals.sandbox import Sandbox

    try:
        # Determine how to call the judge based on the target type
        if isinstance(target, Sandbox):
            # FileExistsJudge pattern: evaluate(sandbox)
            result = judge.evaluate(target)
        elif output is not None:
            # Text judge with explicit input/output
            result = judge.evaluate(input, output)
        elif isinstance(target, str):
            # Text judge: target is the output, input is provided separately
            result = judge.evaluate(input, target)
        else:
            # Try calling with just the target
            result = judge.evaluate(target)

        return result.score >= threshold

    except Exception:
        # If evaluation fails, return False
        return False
