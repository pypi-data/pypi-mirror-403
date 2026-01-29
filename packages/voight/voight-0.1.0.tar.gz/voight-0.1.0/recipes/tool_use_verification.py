"""Recipe: Tool Use Verification for Agentic AI

This recipe demonstrates how to test that an AI agent correctly uses tools
and produces the expected side effects (file creation, API calls, etc.).

Use Case:
- Testing agents that write files (code generators, report writers)
- Verifying correct tool invocation patterns
- Ensuring side effects are properly isolated during testing
"""

from pathlib import Path
import json

from agent_evals import scenario, Sandbox, check, SimpleGenerator
from agent_evals.judges import FileExistsJudge, DeterministicJudge


# --- Mock Tool-Using Agent ---

def code_generator_agent(prompt: str) -> dict:
    """A mock agent that generates code files based on prompts."""
    # Simulate code generation
    if "python" in prompt.lower() or "function" in prompt.lower():
        code = '''def hello(name: str) -> str:
    """Greet someone by name."""
    return f"Hello, {name}!"


if __name__ == "__main__":
    print(hello("World"))
'''
        filename = "generated_code.py"
    elif "json" in prompt.lower() or "config" in prompt.lower():
        code = json.dumps({"name": "app", "version": "1.0.0", "debug": False}, indent=2)
        filename = "config.json"
    else:
        code = f"# Generated from: {prompt}\nprint('Hello')"
        filename = "output.py"

    # Write the file (this will go into the Sandbox)
    Path(filename).write_text(code)

    return {"filename": filename, "lines": len(code.splitlines())}


def report_generator_agent(data: dict) -> str:
    """A mock agent that generates a report file."""
    report = f"""# Analysis Report

## Summary
Processed {len(data)} data points.

## Results
"""
    for key, value in data.items():
        report += f"- {key}: {value}\n"

    report += "\n## Conclusion\nAnalysis complete."

    Path("report.md").write_text(report)
    return "Report generated successfully"


# --- Test Scenarios ---

generator = SimpleGenerator(templates=[
    "Write a Python {topic}",
    "Create a {topic} in Python",
    "Generate Python code for {topic}",
])


@scenario(runs=5, threshold=1.0, generator=generator, base_prompt="function")
def test_code_generation_creates_file(prompt: str):
    """Test that the code generator creates a Python file."""
    with Sandbox() as box:
        result = code_generator_agent(prompt)

        # Verify file was created
        assert check(box, FileExistsJudge("generated_code.py"))

        # Verify it's valid Python (contains def)
        content = box.get_file_content("generated_code.py")
        assert "def " in content, "Generated code should contain a function"


@scenario(runs=5, threshold=1.0)
def test_code_generation_file_quality():
    """Test that generated code meets quality standards."""
    with Sandbox() as box:
        code_generator_agent("Write a Python function")

        # Check file exists with minimum size
        assert check(box, FileExistsJudge("generated_code.py", min_size_bytes=50))

        # Check for docstring
        judge = FileExistsJudge("generated_code.py", contains='"""')
        assert check(box, judge), "Generated code should have docstrings"


@scenario(runs=3, threshold=1.0)
def test_json_config_generation():
    """Test JSON configuration file generation."""
    with Sandbox() as box:
        code_generator_agent("Generate a JSON config file")

        # Verify JSON file created
        assert check(box, FileExistsJudge("config.json"))

        # Verify it's valid JSON
        content = box.get_file_content("config.json")
        data = json.loads(content)  # Will raise if invalid
        assert "version" in data


@scenario(runs=5, threshold=1.0)
def test_report_generation():
    """Test report generation with structured data."""
    test_data = {
        "total_users": 1000,
        "active_users": 750,
        "conversion_rate": "7.5%",
    }

    with Sandbox() as box:
        report_generator_agent(test_data)

        # Check report was created
        assert check(box, FileExistsJudge("report.md"))

        # Verify report contains expected sections
        content = box.get_file_content("report.md")
        assert "# Analysis Report" in content
        assert "## Summary" in content
        assert "1000" in content  # Contains our data


@scenario(runs=3, threshold=1.0)
def test_sandbox_isolation():
    """Verify that Sandbox properly isolates file operations."""
    import os
    original_cwd = os.getcwd()

    with Sandbox() as box:
        # Create a file inside sandbox
        Path("isolated_file.txt").write_text("This should be isolated")

        # Verify it exists in sandbox
        assert box.file_exists("isolated_file.txt")

        sandbox_path = box.path

    # After exiting, verify:
    # 1. We're back to original directory
    assert os.getcwd() == original_cwd

    # 2. The file doesn't exist in original directory
    assert not Path("isolated_file.txt").exists()

    # 3. The sandbox directory was cleaned up
    assert not sandbox_path.exists()


if __name__ == "__main__":
    print("Running Tool Use Verification Tests...")
    print()

    result = test_code_generation_creates_file()
    print(result)

    result = test_code_generation_file_quality()
    print(result)

    result = test_json_config_generation()
    print(result)

    result = test_report_generation()
    print(result)

    result = test_sandbox_isolation()
    print(result)
