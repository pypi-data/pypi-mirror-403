"""Basic tests to verify the @scenario decorator works."""

import random
from agent_evals import scenario


@scenario(runs=10, threshold=0.8)
def test_always_passes():
    """A scenario that always passes."""
    assert True


@scenario(runs=10, threshold=0.8)
def test_always_fails():
    """A scenario that always fails."""
    assert False, "This always fails"


@scenario(runs=20, threshold=0.5)
def test_sometimes_fails():
    """A scenario that fails ~30% of the time (should pass with 0.5 threshold)."""
    if random.random() < 0.3:
        raise ValueError("Random failure")


@scenario(runs=10, threshold=0.9)
def test_flaky_high_threshold():
    """A scenario that fails ~20% of the time (likely to fail with 0.9 threshold)."""
    if random.random() < 0.2:
        raise RuntimeError("Flaky failure")


def test_decorator_preserves_metadata():
    """Verify the decorator preserves function metadata."""
    assert test_always_passes.__name__ == "test_always_passes"
    assert hasattr(test_always_passes, "_is_scenario")
    assert test_always_passes._is_scenario is True
    assert test_always_passes._scenario_runs == 10
    assert test_always_passes._scenario_threshold == 0.8


def test_scenario_result_output():
    """Test the ScenarioResult string formatting."""
    result = test_always_passes()
    assert result.passed == 10
    assert result.failed == 0
    assert result.pass_rate == 1.0
    assert result.passed_threshold is True
    assert "PASS" in str(result)

    result = test_always_fails()
    assert result.passed == 0
    assert result.failed == 10
    assert result.pass_rate == 0.0
    assert result.passed_threshold is False
    assert "FAIL" in str(result)
    assert len(result.exceptions) == 10


def test_scenario_captures_exceptions():
    """Test that exceptions are captured and stored."""
    result = test_always_fails()
    assert len(result.exceptions) == 10
    for exc in result.exceptions:
        assert isinstance(exc, AssertionError)


if __name__ == "__main__":
    # Manual test runner for quick verification
    print("Running scenario tests...\n")

    print(test_always_passes())
    print(test_always_fails())
    print(test_sometimes_fails())
    print(test_flaky_high_threshold())

    print("\nRunning unit tests...")
    test_decorator_preserves_metadata()
    print("test_decorator_preserves_metadata: OK")

    test_scenario_result_output()
    print("test_scenario_result_output: OK")

    test_scenario_captures_exceptions()
    print("test_scenario_captures_exceptions: OK")

    print("\nAll tests completed!")
