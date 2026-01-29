"""Tests for LLM-based judging and generation.

These tests require a valid OPENAI_API_KEY environment variable to run the LLM tests.
Tests will be skipped if the API key is not available.
"""

import os
import pytest

from agent_evals import (
    AdversarialGenerator,
    SimpleGenerator,
    SimpleLLMJudge,
    DeterministicJudge,
    EvalResult,
)


# Check if OpenAI API key is available
HAS_API_KEY = bool(os.environ.get("OPENAI_API_KEY"))
skip_without_api_key = pytest.mark.skipif(
    not HAS_API_KEY, reason="OPENAI_API_KEY not set"
)


class TestAdversarialGenerator:
    """Tests for the AdversarialGenerator."""

    @skip_without_api_key
    def test_generate_variations(self):
        """Test generating adversarial prompt variations."""
        generator = AdversarialGenerator(topic="refund request", style="frustrated")

        variations = generator.generate("I want a refund", n=3)

        print("\n--- Generated Adversarial Variations ---")
        for i, v in enumerate(variations, 1):
            print(f"{i}. {v}")
        print("---")

        assert len(variations) == 3
        assert all(isinstance(v, str) for v in variations)
        assert all(len(v) > 0 for v in variations)

    @skip_without_api_key
    def test_generate_rude_style(self):
        """Test generating rude-style variations."""
        generator = AdversarialGenerator(topic="customer support", style="rude and impatient")

        variations = generator.generate("I need help", n=3)

        print("\n--- Generated Rude Variations ---")
        for i, v in enumerate(variations, 1):
            print(f"{i}. {v}")
        print("---")

        assert len(variations) == 3

    @skip_without_api_key
    def test_generate_confused_style(self):
        """Test generating confused-style variations."""
        generator = AdversarialGenerator(topic="password reset", style="confused and elderly")

        variations = generator.generate("How do I reset my password?", n=3)

        print("\n--- Generated Confused Variations ---")
        for i, v in enumerate(variations, 1):
            print(f"{i}. {v}")
        print("---")

        assert len(variations) == 3


class TestSimpleGenerator:
    """Tests for the SimpleGenerator (no API key required)."""

    def test_generate_default_templates(self):
        """Test generating variations with default templates."""
        generator = SimpleGenerator()

        variations = generator.generate("billing issues", n=5)

        print("\n--- Simple Generator Variations ---")
        for i, v in enumerate(variations, 1):
            print(f"{i}. {v}")
        print("---")

        assert len(variations) == 5
        assert all("billing issues" in v for v in variations)

    def test_generate_custom_templates(self):
        """Test generating with custom templates."""
        templates = [
            "Help me with {topic}!",
            "What's the deal with {topic}?",
            "Explain {topic} please",
        ]
        generator = SimpleGenerator(templates=templates)

        variations = generator.generate("shipping", n=3)

        assert variations[0] == "Help me with shipping!"
        assert variations[1] == "What's the deal with shipping?"
        assert variations[2] == "Explain shipping please"


class TestSimpleLLMJudge:
    """Tests for the SimpleLLMJudge."""

    @skip_without_api_key
    def test_judge_rude_response(self):
        """Test that a rude response gets a low score."""
        judge = SimpleLLMJudge()

        result = judge.evaluate(
            input="Hi, can you help me?",
            output="Go away, I don't have time for you."
        )

        print(f"\n--- Rude Response Evaluation ---")
        print(f"Score: {result.score}")
        print(f"Reason: {result.reason}")
        print("---")

        assert isinstance(result, EvalResult)
        assert result.score < 0.5, f"Expected low score for rude response, got {result.score}"

    @skip_without_api_key
    def test_judge_helpful_response(self):
        """Test that a helpful response gets a high score."""
        judge = SimpleLLMJudge()

        result = judge.evaluate(
            input="What's the weather like today?",
            output="I'd be happy to help! However, I don't have access to real-time weather data. "
                   "I recommend checking a weather service like weather.com or your phone's weather app "
                   "for the most accurate and up-to-date information for your location."
        )

        print(f"\n--- Helpful Response Evaluation ---")
        print(f"Score: {result.score}")
        print(f"Reason: {result.reason}")
        print("---")

        assert isinstance(result, EvalResult)
        assert result.score > 0.5, f"Expected high score for helpful response, got {result.score}"

    @skip_without_api_key
    def test_judge_with_custom_criteria(self):
        """Test judging with custom criteria."""
        judge = SimpleLLMJudge(
            custom_criteria="The response must be empathetic and acknowledge the user's feelings."
        )

        result = judge.evaluate(
            input="I'm really frustrated with your service!",
            output="I understand your frustration and I'm truly sorry for the inconvenience. "
                   "Let me help make this right for you."
        )

        print(f"\n--- Custom Criteria Evaluation ---")
        print(f"Score: {result.score}")
        print(f"Reason: {result.reason}")
        print("---")

        assert result.score > 0.6

    @skip_without_api_key
    def test_judge_metadata(self):
        """Test that evaluation includes useful metadata."""
        judge = SimpleLLMJudge()

        result = judge.evaluate(input="Hello", output="Hi there!")

        assert "model" in result.metadata
        assert "input_length" in result.metadata
        assert "output_length" in result.metadata


class TestDeterministicJudge:
    """Tests for the DeterministicJudge (no API key required)."""

    def test_required_phrases_present(self):
        """Test that required phrases are detected."""
        judge = DeterministicJudge(required_phrases=["thank you", "help"])

        result = judge.evaluate(
            input="Hi",
            output="Thank you for reaching out! I'm here to help."
        )

        assert result.score == 1.0
        assert "All criteria met" in result.reason

    def test_required_phrases_missing(self):
        """Test that missing required phrases lower the score."""
        judge = DeterministicJudge(required_phrases=["thank you", "apologies"])

        result = judge.evaluate(
            input="Hi",
            output="Thank you for your message."
        )

        assert result.score == 0.5  # 1 of 2 phrases found
        assert "apologies" in str(result.metadata["missing_required"])

    def test_forbidden_phrases_detected(self):
        """Test that forbidden phrases lower the score."""
        judge = DeterministicJudge(forbidden_phrases=["stupid", "idiot"])

        result = judge.evaluate(
            input="Hi",
            output="That's a stupid question."
        )

        assert result.score == 0.5  # 1 of 2 forbidden phrases found
        assert "stupid" in result.metadata["found_forbidden"]

    def test_combined_criteria(self):
        """Test with both required and forbidden phrases."""
        judge = DeterministicJudge(
            required_phrases=["please", "thank you"],
            forbidden_phrases=["no", "can't"]
        )

        result = judge.evaluate(
            input="Help me",
            output="Please let me help. Thank you for asking!"
        )

        assert result.score == 1.0

    def test_case_sensitivity(self):
        """Test case-sensitive matching."""
        judge = DeterministicJudge(
            required_phrases=["URGENT"],
            case_sensitive=True
        )

        # Lowercase should fail
        result = judge.evaluate(input="", output="This is urgent")
        assert result.score == 0.0

        # Uppercase should pass
        result = judge.evaluate(input="", output="This is URGENT")
        assert result.score == 1.0


class TestIntegration:
    """Integration tests combining generators and judges."""

    @skip_without_api_key
    def test_generate_and_judge(self):
        """Test full flow: generate variations and judge mock responses."""
        generator = AdversarialGenerator(topic="account cancellation", style="angry")
        judge = SimpleLLMJudge()

        # Generate test inputs
        inputs = generator.generate("I want to cancel my account", n=2)

        print("\n--- Integration Test: Generate and Judge ---")

        # Mock agent responses (in real use, these would come from the actual agent)
        mock_responses = [
            "I'm sorry to hear you want to leave. Let me help you with the cancellation process.",
            "Whatever, cancel it yourself.",
        ]

        for i, (inp, resp) in enumerate(zip(inputs, mock_responses)):
            result = judge.evaluate(input=inp, output=resp)
            print(f"\nInput {i+1}: {inp}")
            print(f"Response: {resp}")
            print(f"Score: {result.score:.2f} - {result.reason}")

        print("---")


def test_api_key_validation():
    """Test that missing API key raises an error."""
    # Temporarily remove API key
    original_key = os.environ.pop("OPENAI_API_KEY", None)

    try:
        with pytest.raises(ValueError, match="API key must be provided"):
            SimpleLLMJudge()

        with pytest.raises(ValueError, match="API key must be provided"):
            AdversarialGenerator(topic="test", style="test")
    finally:
        # Restore API key
        if original_key:
            os.environ["OPENAI_API_KEY"] = original_key


if __name__ == "__main__":
    """Run tests manually for quick verification."""
    print("=" * 60)
    print("Agent Evals - Intelligence Tests")
    print("=" * 60)

    # Run tests that don't require API key
    print("\n[Testing SimpleGenerator]")
    test_gen = TestSimpleGenerator()
    test_gen.test_generate_default_templates()
    print("OK")

    print("\n[Testing DeterministicJudge]")
    test_judge = TestDeterministicJudge()
    test_judge.test_required_phrases_present()
    test_judge.test_required_phrases_missing()
    test_judge.test_forbidden_phrases_detected()
    print("OK")

    if HAS_API_KEY:
        print("\n[Testing AdversarialGenerator with LLM]")
        test_adv = TestAdversarialGenerator()
        test_adv.test_generate_variations()
        print("OK")

        print("\n[Testing SimpleLLMJudge]")
        test_llm = TestSimpleLLMJudge()
        test_llm.test_judge_rude_response()
        test_llm.test_judge_helpful_response()
        print("OK")

        print("\n[Testing Integration]")
        test_int = TestIntegration()
        test_int.test_generate_and_judge()
        print("OK")
    else:
        print("\n[Skipping LLM tests - OPENAI_API_KEY not set]")

    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)
