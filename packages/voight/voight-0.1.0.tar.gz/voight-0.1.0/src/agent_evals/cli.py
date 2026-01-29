"""Command-line interface for Voight agent evaluation framework."""

import importlib.util
import sys
from pathlib import Path
from typing import Any

import click

from agent_evals import __version__


# Default configuration content
DEFAULT_CONFIG = '''# Voight Configuration
# https://github.com/your-org/voight

[voight]
# Default number of runs per scenario
default_runs = 10

# Default pass threshold (0.0 to 1.0)
default_threshold = 0.8

# Test discovery path
test_path = "tests/"

# Output format: "table", "json", or "junit"
output_format = "table"

[voight.llm]
# Default model for LLM-based judges and generators
# model = "gpt-4o-mini"

# API key environment variable name
# api_key_env = "OPENAI_API_KEY"
'''

# Sample test file content
SAMPLE_TEST = '''"""Example Voight test file demonstrating the framework."""

from agent_evals import scenario, Sandbox, check, SimpleGenerator
from agent_evals.judges import FileExistsJudge, DeterministicJudge


# --- Example 1: Simple Probabilistic Test ---

@scenario(runs=5, threshold=0.8)
def test_basic_assertion():
    """A simple test that should always pass."""
    result = 2 + 2
    assert result == 4


# --- Example 2: Testing with a Generator ---

generator = SimpleGenerator(templates=[
    "Hello, {topic}!",
    "Hi there, {topic}!",
    "Greetings, {topic}!",
])

@scenario(runs=3, threshold=1.0, generator=generator, base_prompt="world")
def test_with_generated_inputs(input_text: str):
    """Test that runs with different generated inputs."""
    assert "world" in input_text.lower()


# --- Example 3: Testing File Side Effects ---

def mock_agent(prompt: str) -> str:
    """A mock agent that writes a file."""
    from pathlib import Path
    Path("output.txt").write_text(f"Processed: {prompt}")
    return "Done"


@scenario(runs=3, threshold=1.0)
def test_agent_creates_file():
    """Test that an agent creates the expected file."""
    with Sandbox() as box:
        mock_agent("test input")

        # Verify the file was created
        assert check(box, FileExistsJudge("output.txt"))

        # Verify content
        content = box.get_file_content("output.txt")
        assert "Processed" in content


# --- Example 4: Testing Response Quality ---

@scenario(runs=5, threshold=0.8)
def test_response_contains_greeting():
    """Test that responses contain expected phrases."""
    mock_response = "Hello! How can I help you today?"

    judge = DeterministicJudge(
        required_phrases=["hello", "help"],
        forbidden_phrases=["error", "fail"],
    )

    assert check(mock_response, judge, input="greeting request")
'''


def discover_scenarios(path: Path) -> list[tuple[str, Any]]:
    """
    Discover all @scenario-decorated functions in test files.

    Args:
        path: Directory or file path to search

    Returns:
        List of (name, function) tuples for discovered scenarios
    """
    scenarios = []

    if path.is_file():
        test_files = [path] if path.name.startswith("test_") else []
    else:
        test_files = list(path.glob("**/test_*.py"))

    for test_file in test_files:
        try:
            # Load the module
            spec = importlib.util.spec_from_file_location(
                test_file.stem, test_file
            )
            if spec is None or spec.loader is None:
                continue

            module = importlib.util.module_from_spec(spec)
            sys.modules[test_file.stem] = module
            spec.loader.exec_module(module)

            # Find scenario-decorated functions
            for name in dir(module):
                obj = getattr(module, name)
                if callable(obj) and hasattr(obj, "_is_scenario") and obj._is_scenario:
                    scenarios.append((f"{test_file.stem}::{name}", obj))

        except Exception as e:
            click.echo(f"Warning: Failed to load {test_file}: {e}", err=True)

    return scenarios


def format_table(results: list[tuple[str, Any]]) -> str:
    """Format results as a CLI table."""
    if not results:
        return "No scenarios found."

    # Calculate column widths
    name_width = max(len(name) for name, _ in results)
    name_width = max(name_width, 10)

    lines = []
    lines.append("")
    lines.append("=" * (name_width + 40))
    lines.append(f"{'Scenario':<{name_width}}  {'Passed':>6}  {'Rate':>7}  {'Status':>8}")
    lines.append("-" * (name_width + 40))

    total_passed = 0
    total_runs = 0

    for name, result in results:
        status = "PASS" if result.passed_threshold else "FAIL"
        status_color = "green" if result.passed_threshold else "red"
        rate = f"{result.pass_rate:.0%}"

        lines.append(
            f"{name:<{name_width}}  "
            f"{result.passed}/{result.runs:>3}  "
            f"{rate:>7}  "
            f"[{status}]"
        )

        total_passed += result.passed
        total_runs += result.runs

    lines.append("-" * (name_width + 40))

    overall_rate = total_passed / total_runs if total_runs > 0 else 0
    lines.append(
        f"{'TOTAL':<{name_width}}  "
        f"{total_passed}/{total_runs:>3}  "
        f"{overall_rate:.0%}  "
    )
    lines.append("=" * (name_width + 40))

    return "\n".join(lines)


@click.group()
@click.version_option(version=__version__, prog_name="voight")
def cli():
    """Voight: The Agent Evaluation Framework.

    A probabilistic testing framework for non-deterministic AI agents.
    """
    pass


@cli.command()
@click.option(
    "--force", "-f",
    is_flag=True,
    help="Overwrite existing files"
)
def init(force: bool):
    """Initialize a new Voight project in the current directory.

    Creates:
    - voight.config.toml: Configuration file
    - tests/test_agent.py: Sample test file
    """
    config_path = Path("voight.config.toml")
    tests_dir = Path("tests")
    sample_test_path = tests_dir / "test_agent.py"

    # Create config file
    if config_path.exists() and not force:
        click.echo(f"Config file already exists: {config_path}")
        click.echo("Use --force to overwrite.")
    else:
        config_path.write_text(DEFAULT_CONFIG)
        click.echo(f"Created: {config_path}")

    # Create tests directory
    if not tests_dir.exists():
        tests_dir.mkdir(parents=True)
        click.echo(f"Created: {tests_dir}/")

    # Create sample test file
    if sample_test_path.exists() and not force:
        click.echo(f"Sample test already exists: {sample_test_path}")
        click.echo("Use --force to overwrite.")
    else:
        sample_test_path.write_text(SAMPLE_TEST)
        click.echo(f"Created: {sample_test_path}")

    # Create __init__.py if it doesn't exist
    init_file = tests_dir / "__init__.py"
    if not init_file.exists():
        init_file.write_text("")

    click.echo("")
    click.echo("Voight project initialized!")
    click.echo("")
    click.echo("Next steps:")
    click.echo("  1. Edit tests/test_agent.py to add your agent tests")
    click.echo("  2. Run: voight run")


@cli.command()
@click.argument(
    "path",
    type=click.Path(exists=True),
    default="tests/",
    required=False,
)
@click.option(
    "--verbose", "-v",
    is_flag=True,
    help="Show detailed output for each run"
)
@click.option(
    "--filter", "-k",
    "pattern",
    type=str,
    default=None,
    help="Only run scenarios matching this pattern"
)
def run(path: str, verbose: bool, pattern: str | None):
    """Run agent evaluation scenarios.

    PATH: Directory or file containing test scenarios (default: tests/)
    """
    test_path = Path(path)

    click.echo(f"Discovering scenarios in: {test_path}")

    # Discover scenarios
    scenarios = discover_scenarios(test_path)

    if not scenarios:
        click.echo("No scenarios found.", err=True)
        click.echo("")
        click.echo("Make sure your test files:")
        click.echo("  - Start with 'test_' (e.g., test_agent.py)")
        click.echo("  - Contain functions decorated with @scenario")
        sys.exit(1)

    # Filter by pattern if provided
    if pattern:
        scenarios = [(name, func) for name, func in scenarios if pattern in name]
        if not scenarios:
            click.echo(f"No scenarios matching '{pattern}'", err=True)
            sys.exit(1)

    click.echo(f"Found {len(scenarios)} scenario(s)")
    click.echo("")

    # Run scenarios
    results = []
    failed_count = 0

    for name, scenario_func in scenarios:
        click.echo(f"Running: {name}...", nl=False)

        try:
            result = scenario_func()
            results.append((name, result))

            if result.passed_threshold:
                click.echo(f" {result.passed}/{result.runs} PASS")
            else:
                click.echo(f" {result.passed}/{result.runs} FAIL")
                failed_count += 1

            if verbose:
                for run_result in result.run_results:
                    status = "OK" if run_result.passed else "FAIL"
                    click.echo(f"  Run {run_result.run_index}: [{status}]")
                    if run_result.input:
                        preview = run_result.input[:60] + "..." if len(run_result.input) > 60 else run_result.input
                        click.echo(f"    Input: {preview}")
                    if run_result.exception:
                        click.echo(f"    Error: {run_result.exception}")

        except Exception as e:
            click.echo(f" ERROR: {e}")
            failed_count += 1

    # Print summary table
    click.echo(format_table(results))

    # Exit with appropriate code
    if failed_count > 0:
        click.echo(f"\n{failed_count} scenario(s) failed.")
        sys.exit(1)
    else:
        click.echo("\nAll scenarios passed!")
        sys.exit(0)


@cli.command()
def version():
    """Show the Voight version."""
    click.echo(f"Voight v{__version__}")


if __name__ == "__main__":
    cli()
