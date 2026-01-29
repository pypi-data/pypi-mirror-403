"""Decorators for defining probabilistic test scenarios."""

from dataclasses import dataclass, field
from functools import wraps
from typing import Callable, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from agent_evals.core import Generator


@dataclass
class RunResult:
    """Result of a single scenario run."""

    run_index: int
    input: str | None
    passed: bool
    exception: Exception | None = None

    def __str__(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        input_preview = self.input[:50] + "..." if self.input and len(self.input) > 50 else self.input
        return f"Run {self.run_index}: [{status}] input={input_preview!r}"


@dataclass
class ScenarioResult:
    """Result of running a scenario multiple times."""

    name: str
    runs: int
    passed: int
    failed: int
    threshold: float
    exceptions: list[Exception] = field(default_factory=list)
    run_results: list[RunResult] = field(default_factory=list)
    inputs_used: list[str] = field(default_factory=list)

    @property
    def pass_rate(self) -> float:
        """Calculate the pass rate as a fraction."""
        return self.passed / self.runs if self.runs > 0 else 0.0

    @property
    def passed_threshold(self) -> bool:
        """Check if the pass rate meets the threshold."""
        return self.pass_rate >= self.threshold

    def __str__(self) -> str:
        status = "PASS" if self.passed_threshold else "FAIL"
        return (
            f"Test {self.name}: {self.passed}/{self.runs} Passed "
            f"({self.pass_rate:.0%}) - [{status}]"
        )


def scenario(
    runs: int = 10,
    threshold: float = 0.8,
    generator: "Generator | None" = None,
    base_prompt: str = "",
) -> Callable:
    """
    Decorator that marks a function as a probabilistic test scenario.

    The decorated function will be run `runs` times, and the test passes
    if at least `threshold` fraction of runs succeed (don't raise exceptions).

    If a generator is provided, it will be used to create diverse inputs
    for each run. The generated input is passed as the first argument to
    the decorated function.

    Args:
        runs: Number of times to run the function (default: 10)
        threshold: Minimum pass rate required (0.0 to 1.0, default: 0.8)
        generator: Optional Generator instance for creating test inputs
        base_prompt: Base prompt for the generator (used if generator is provided)

    Returns:
        A decorator that wraps the function with scenario execution logic.

    Example:
        # Without generator (runs same test N times)
        @scenario(runs=10, threshold=0.8)
        def test_agent_response():
            response = agent.run("Hello")
            assert "greeting" in response.lower()

        # With generator (runs with different inputs)
        @scenario(runs=5, generator=AdversarialGenerator("refund", "angry"))
        def test_refund_handling(input_prompt: str):
            response = agent.run(input_prompt)
            assert "sorry" in response.lower()
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> ScenarioResult:
            passed = 0
            failed = 0
            exceptions: list[Exception] = []
            run_results: list[RunResult] = []
            inputs_used: list[str] = []

            # Generate inputs if generator is provided
            if generator is not None:
                prompt = base_prompt or func.__name__.replace("_", " ")
                generated_inputs = generator.generate(prompt, runs)
            else:
                generated_inputs = [None] * runs

            for i, input_text in enumerate(generated_inputs):
                run_result = RunResult(run_index=i, input=input_text, passed=False)

                try:
                    if input_text is not None:
                        # Pass generated input as first argument
                        func(input_text, *args, **kwargs)
                        inputs_used.append(input_text)
                    else:
                        func(*args, **kwargs)

                    passed += 1
                    run_result.passed = True

                except Exception as e:
                    failed += 1
                    exceptions.append(e)
                    run_result.exception = e

                run_results.append(run_result)

            result = ScenarioResult(
                name=func.__name__,
                runs=runs,
                passed=passed,
                failed=failed,
                threshold=threshold,
                exceptions=exceptions,
                run_results=run_results,
                inputs_used=inputs_used,
            )

            return result

        # Mark the wrapper as a scenario for test discovery
        wrapper._is_scenario = True
        wrapper._scenario_runs = runs
        wrapper._scenario_threshold = threshold
        wrapper._scenario_generator = generator

        return wrapper

    return decorator
