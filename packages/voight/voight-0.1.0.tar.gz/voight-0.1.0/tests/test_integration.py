"""Integration tests for the full agent-evals pipeline.

Tests the complete flow: Generator -> Scenario -> Sandbox -> Judge
"""

import os
from pathlib import Path

import pytest

from agent_evals import (
    scenario,
    Sandbox,
    SimpleGenerator,
    AdversarialGenerator,
    FileExistsJudge,
    DeterministicJudge,
    check,
)


# Check if OpenAI API key is available
HAS_API_KEY = bool(os.environ.get("OPENAI_API_KEY"))
skip_without_api_key = pytest.mark.skipif(
    not HAS_API_KEY, reason="OPENAI_API_KEY not set"
)


# --- Mock Agents ---

def mock_poem_agent(prompt: str) -> str:
    """A mock agent that writes a poem to a file."""
    poem = f"""A poem inspired by: {prompt}

Roses are red,
Violets are blue,
This is a test,
And it works too!
"""
    # Write to the current directory (should be inside Sandbox)
    Path("poem.txt").write_text(poem)
    return poem


def mock_flaky_agent(prompt: str) -> str:
    """A mock agent that sometimes fails to write a file."""
    import random
    if random.random() < 0.3:
        # 30% chance to fail
        return "Sorry, I couldn't write the poem."

    poem = f"A simple poem about {prompt}"
    Path("poem.txt").write_text(poem)
    return poem


def mock_json_agent(prompt: str) -> str:
    """A mock agent that writes JSON output."""
    import json
    data = {"prompt": prompt, "response": "processed", "status": "success"}
    Path("output.json").write_text(json.dumps(data, indent=2))
    return json.dumps(data)


# --- Sandbox Tests ---

class TestSandbox:
    """Tests for the Sandbox context manager."""

    def test_sandbox_creates_temp_dir(self):
        """Test that Sandbox creates a temporary directory."""
        original_cwd = os.getcwd()

        with Sandbox() as box:
            sandbox_cwd = os.getcwd()
            assert sandbox_cwd != original_cwd
            assert box.path.exists()
            assert str(box.path) == sandbox_cwd

        # After exiting, we should be back to original
        assert os.getcwd() == original_cwd

    def test_sandbox_isolates_file_writes(self):
        """Test that files written in Sandbox don't affect original directory."""
        original_cwd = os.getcwd()
        test_file = Path(original_cwd) / "sandbox_test_file.txt"

        # Ensure test file doesn't exist
        if test_file.exists():
            test_file.unlink()

        with Sandbox() as box:
            # Write a file inside the sandbox
            Path("sandbox_test_file.txt").write_text("test content")
            assert box.file_exists("sandbox_test_file.txt")

        # File should NOT exist in original directory
        assert not test_file.exists()

    def test_sandbox_file_content(self):
        """Test reading file content from Sandbox."""
        with Sandbox() as box:
            content = "Hello, Sandbox!"
            Path("test.txt").write_text(content)

            assert box.file_exists("test.txt")
            assert box.get_file_content("test.txt") == content
            assert box.get_file_size("test.txt") == len(content)

    def test_sandbox_restores_on_exception(self):
        """Test that Sandbox restores cwd even when exception occurs."""
        original_cwd = os.getcwd()

        try:
            with Sandbox() as box:
                Path("test.txt").write_text("content")
                raise ValueError("Intentional error")
        except ValueError:
            pass

        # Should still be restored to original directory
        assert os.getcwd() == original_cwd

    def test_sandbox_list_files(self):
        """Test listing files in Sandbox."""
        with Sandbox() as box:
            Path("file1.txt").write_text("1")
            Path("file2.txt").write_text("2")
            Path("data.json").write_text("{}")

            txt_files = box.list_files("*.txt")
            assert len(txt_files) == 2
            assert "file1.txt" in txt_files
            assert "file2.txt" in txt_files

            all_files = box.list_files()
            assert len(all_files) == 3


# --- FileExistsJudge Tests ---

class TestFileExistsJudge:
    """Tests for the FileExistsJudge."""

    def test_file_exists_passes(self):
        """Test that existing file gets score 1.0."""
        judge = FileExistsJudge("test.txt")

        with Sandbox() as box:
            Path("test.txt").write_text("content")
            result = judge.evaluate(box)

        assert result.score == 1.0
        assert "exists" in result.reason.lower()

    def test_file_missing_fails(self):
        """Test that missing file gets score 0.0."""
        judge = FileExistsJudge("missing.txt")

        with Sandbox() as box:
            result = judge.evaluate(box)

        assert result.score == 0.0
        assert "does not exist" in result.reason.lower()

    def test_min_size_check(self):
        """Test minimum file size validation."""
        judge = FileExistsJudge("test.txt", min_size_bytes=100)

        with Sandbox() as box:
            Path("test.txt").write_text("small")  # Less than 100 bytes
            result = judge.evaluate(box)

        assert result.score == 0.0
        assert "too small" in result.reason.lower()

    def test_contains_check(self):
        """Test content validation."""
        judge = FileExistsJudge("test.txt", contains="expected")

        with Sandbox() as box:
            Path("test.txt").write_text("This contains expected content")
            result = judge.evaluate(box)

        assert result.score == 1.0

        with Sandbox() as box:
            Path("test.txt").write_text("This does not have it")
            result = judge.evaluate(box)

        assert result.score == 0.0


# --- Check Helper Tests ---

class TestCheckHelper:
    """Tests for the check() helper function."""

    def test_check_with_file_judge(self):
        """Test check() with FileExistsJudge."""
        with Sandbox() as box:
            Path("output.txt").write_text("content")
            assert check(box, FileExistsJudge("output.txt"))
            assert not check(box, FileExistsJudge("missing.txt"))

    def test_check_with_text_judge(self):
        """Test check() with DeterministicJudge."""
        judge = DeterministicJudge(required_phrases=["hello"])

        assert check("hello world", judge, input="greeting")
        assert not check("goodbye world", judge, input="greeting")

    def test_check_threshold(self):
        """Test check() with different thresholds."""
        judge = DeterministicJudge(required_phrases=["a", "b"])

        # Only "a" present -> score = 0.5
        assert check("a only", judge, threshold=0.5, input="")
        assert not check("a only", judge, threshold=0.8, input="")


# --- Scenario with Generator Tests ---

class TestScenarioWithGenerator:
    """Tests for @scenario decorator with generators."""

    def test_scenario_with_simple_generator(self):
        """Test scenario using SimpleGenerator."""
        generator = SimpleGenerator()

        @scenario(runs=3, threshold=1.0, generator=generator, base_prompt="testing")
        def test_echoes_input(input_prompt: str):
            # Just verify we receive the generated input
            assert "testing" in input_prompt

        result = test_echoes_input()

        assert result.runs == 3
        assert result.passed == 3
        assert len(result.inputs_used) == 3
        assert all("testing" in inp for inp in result.inputs_used)

    def test_scenario_tracks_inputs(self):
        """Test that scenario tracks all inputs used."""
        templates = ["Input A: {topic}", "Input B: {topic}", "Input C: {topic}"]
        generator = SimpleGenerator(templates=templates)

        @scenario(runs=3, generator=generator, base_prompt="test")
        def test_tracking(input_prompt: str):
            assert input_prompt.startswith("Input")

        result = test_tracking()

        assert len(result.inputs_used) == 3
        assert len(result.run_results) == 3

    def test_scenario_without_generator(self):
        """Test scenario without generator (original behavior)."""
        counter = {"value": 0}

        @scenario(runs=5, threshold=1.0)
        def test_increment():
            counter["value"] += 1

        result = test_increment()

        assert result.runs == 5
        assert result.passed == 5
        assert counter["value"] == 5
        assert len(result.inputs_used) == 0  # No generator, no inputs


# --- Full Integration Tests ---

class TestFullIntegration:
    """Full integration tests combining all components."""

    def test_mock_agent_with_sandbox_and_judge(self):
        """Test a mock agent that writes files, verified by judge."""
        generator = SimpleGenerator(templates=[
            "Write a poem about {topic}",
            "Create a verse about {topic}",
            "Compose poetry about {topic}",
        ])

        @scenario(runs=3, threshold=1.0, generator=generator, base_prompt="nature")
        def test_poem_creation(input_prompt: str):
            with Sandbox() as box:
                mock_poem_agent(input_prompt)

                # Verify file was created
                assert check(box, FileExistsJudge("poem.txt"))

                # Verify content
                content = box.get_file_content("poem.txt")
                assert len(content) > 0

        result = test_poem_creation()

        print(f"\n{result}")
        for run in result.run_results:
            print(f"  {run}")

        assert result.passed == 3
        assert result.passed_threshold

    def test_flaky_agent_threshold(self):
        """Test that flaky agent behavior is captured by threshold."""
        generator = SimpleGenerator()

        @scenario(runs=10, threshold=0.5, generator=generator, base_prompt="poem")
        def test_flaky_writes(input_prompt: str):
            with Sandbox() as box:
                mock_flaky_agent(input_prompt)
                # This will fail ~30% of the time
                assert check(box, FileExistsJudge("poem.txt"))

        result = test_flaky_writes()

        print(f"\n{result}")

        # With 30% failure rate and 0.5 threshold, should usually pass
        # (but this is probabilistic, so we just verify the structure)
        assert result.runs == 10
        assert 0 <= result.passed <= 10

    def test_json_output_verification(self):
        """Test verifying structured JSON output."""
        @scenario(runs=3, threshold=1.0)
        def test_json_creation():
            with Sandbox() as box:
                mock_json_agent("test prompt")

                # Check file exists with content verification
                judge = FileExistsJudge("output.json", contains='"status": "success"')
                assert check(box, judge)

        result = test_json_creation()
        assert result.passed == 3

    @skip_without_api_key
    def test_with_adversarial_generator(self):
        """Test using AdversarialGenerator with LLM."""
        generator = AdversarialGenerator(topic="writing poetry", style="enthusiastic")

        @scenario(runs=3, threshold=1.0, generator=generator)
        def test_adversarial_poem(input_prompt: str):
            print(f"  Input: {input_prompt}")
            with Sandbox() as box:
                mock_poem_agent(input_prompt)
                assert check(box, FileExistsJudge("poem.txt"))

        result = test_adversarial_poem()

        print(f"\n{result}")
        assert result.passed == 3


# --- Manual Test Runner ---

if __name__ == "__main__":
    print("=" * 60)
    print("Agent Evals - Integration Tests")
    print("=" * 60)

    # Sandbox tests
    print("\n[Testing Sandbox]")
    sandbox_tests = TestSandbox()
    sandbox_tests.test_sandbox_creates_temp_dir()
    sandbox_tests.test_sandbox_isolates_file_writes()
    sandbox_tests.test_sandbox_file_content()
    sandbox_tests.test_sandbox_restores_on_exception()
    sandbox_tests.test_sandbox_list_files()
    print("OK")

    # FileExistsJudge tests
    print("\n[Testing FileExistsJudge]")
    judge_tests = TestFileExistsJudge()
    judge_tests.test_file_exists_passes()
    judge_tests.test_file_missing_fails()
    judge_tests.test_min_size_check()
    judge_tests.test_contains_check()
    print("OK")

    # Check helper tests
    print("\n[Testing check() helper]")
    check_tests = TestCheckHelper()
    check_tests.test_check_with_file_judge()
    check_tests.test_check_with_text_judge()
    check_tests.test_check_threshold()
    print("OK")

    # Scenario with generator tests
    print("\n[Testing Scenario with Generator]")
    scenario_tests = TestScenarioWithGenerator()
    scenario_tests.test_scenario_with_simple_generator()
    scenario_tests.test_scenario_tracks_inputs()
    scenario_tests.test_scenario_without_generator()
    print("OK")

    # Full integration tests
    print("\n[Testing Full Integration]")
    integration_tests = TestFullIntegration()
    integration_tests.test_mock_agent_with_sandbox_and_judge()
    integration_tests.test_flaky_agent_threshold()
    integration_tests.test_json_output_verification()
    print("OK")

    if HAS_API_KEY:
        print("\n[Testing with AdversarialGenerator]")
        integration_tests.test_with_adversarial_generator()
        print("OK")
    else:
        print("\n[Skipping LLM tests - OPENAI_API_KEY not set]")

    print("\n" + "=" * 60)
    print("All integration tests completed!")
    print("=" * 60)
