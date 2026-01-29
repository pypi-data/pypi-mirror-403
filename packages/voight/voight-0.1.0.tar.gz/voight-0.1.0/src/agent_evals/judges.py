"""Judge implementations for evaluating agent outputs."""

import json
import os
import re
from typing import Any

from openai import OpenAI, APIError, APIConnectionError, RateLimitError

from agent_evals.core import EvalResult


JUDGE_SYSTEM_PROMPT = """You are an impartial judge evaluating AI agent responses.

Your task is to grade the following output on a scale of 0.0 to 1.0 based on:
- Helpfulness: Does the response address the user's needs?
- Appropriateness: Is the tone and content suitable?
- Accuracy: Is the information correct (if applicable)?
- Completeness: Does the response fully address the query?

You MUST respond with valid JSON in this exact format:
{
    "score": <float between 0.0 and 1.0>,
    "reason": "<brief explanation of your score>"
}

Scoring guidelines:
- 0.0-0.2: Completely inappropriate, harmful, or wrong
- 0.2-0.4: Poor quality, unhelpful, or mostly incorrect
- 0.4-0.6: Mediocre, partially helpful or correct
- 0.6-0.8: Good quality, helpful and mostly correct
- 0.8-1.0: Excellent, fully addresses the query appropriately"""


class SimpleLLMJudge:
    """An LLM-based judge that evaluates agent outputs using OpenAI."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gpt-4o-mini",
        custom_criteria: str | None = None,
    ):
        """
        Initialize the LLM judge.

        Args:
            api_key: OpenAI API key. If not provided, reads from OPENAI_API_KEY env var.
            model: The model to use for judging (default: gpt-4o-mini).
            custom_criteria: Optional custom evaluation criteria to append to the system prompt.
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenAI API key must be provided or set in OPENAI_API_KEY environment variable"
            )

        self.model = model
        self.custom_criteria = custom_criteria
        self.client = OpenAI(api_key=self.api_key)

    def _build_system_prompt(self) -> str:
        """Build the system prompt, optionally including custom criteria."""
        prompt = JUDGE_SYSTEM_PROMPT
        if self.custom_criteria:
            prompt += f"\n\nAdditional evaluation criteria:\n{self.custom_criteria}"
        return prompt

    def _parse_response(self, content: str) -> tuple[float, str]:
        """
        Parse the LLM response to extract score and reason.

        Handles both clean JSON and JSON embedded in markdown code blocks.
        """
        # Try to extract JSON from markdown code blocks
        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", content, re.DOTALL)
        if json_match:
            content = json_match.group(1)

        # Try to parse as JSON
        try:
            data = json.loads(content)
            score = float(data.get("score", 0.5))
            reason = str(data.get("reason", "No reason provided"))
            # Clamp score to valid range
            score = max(0.0, min(1.0, score))
            return score, reason
        except (json.JSONDecodeError, ValueError, TypeError):
            pass

        # Fallback: try to extract score from text
        score_match = re.search(r"(?:score|rating)[:\s]*([0-9]*\.?[0-9]+)", content, re.I)
        if score_match:
            score = float(score_match.group(1))
            score = max(0.0, min(1.0, score))
            return score, content[:200]

        # If all parsing fails, return a default
        return 0.5, f"Failed to parse response: {content[:100]}"

    def evaluate(self, input: str, output: str) -> EvalResult:
        """
        Evaluate an agent's output given the input.

        Args:
            input: The input that was given to the agent
            output: The output produced by the agent

        Returns:
            EvalResult with score, reason, and metadata
        """
        user_message = f"""Evaluate this agent interaction:

**User Input:**
{input}

**Agent Output:**
{output}

Provide your evaluation as JSON with "score" and "reason" fields."""

        metadata: dict[str, Any] = {
            "model": self.model,
            "input_length": len(input),
            "output_length": len(output),
        }

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._build_system_prompt()},
                    {"role": "user", "content": user_message},
                ],
                temperature=0.1,  # Low temperature for consistent judging
                max_tokens=256,
            )

            content = response.choices[0].message.content or ""
            metadata["raw_response"] = content
            metadata["usage"] = {
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
            }

            score, reason = self._parse_response(content)

            return EvalResult(score=score, reason=reason, metadata=metadata)

        except RateLimitError as e:
            return EvalResult(
                score=0.0,
                reason=f"Rate limit exceeded: {e}",
                metadata={**metadata, "error": "rate_limit", "error_message": str(e)},
            )
        except APIConnectionError as e:
            return EvalResult(
                score=0.0,
                reason=f"API connection failed: {e}",
                metadata={**metadata, "error": "connection", "error_message": str(e)},
            )
        except APIError as e:
            return EvalResult(
                score=0.0,
                reason=f"API error: {e}",
                metadata={**metadata, "error": "api_error", "error_message": str(e)},
            )
        except Exception as e:
            return EvalResult(
                score=0.0,
                reason=f"Unexpected error during evaluation: {e}",
                metadata={**metadata, "error": "unexpected", "error_message": str(e)},
            )


class FileExistsJudge:
    """A judge that checks if a file exists in a Sandbox."""

    def __init__(
        self,
        filename: str,
        min_size_bytes: int | None = None,
        max_size_bytes: int | None = None,
        contains: str | None = None,
    ):
        """
        Initialize the file existence judge.

        Args:
            filename: The filename to check for.
            min_size_bytes: Minimum file size in bytes (optional).
            max_size_bytes: Maximum file size in bytes (optional).
            contains: String that must be present in file content (optional).
        """
        self.filename = filename
        self.min_size_bytes = min_size_bytes
        self.max_size_bytes = max_size_bytes
        self.contains = contains

    def evaluate(self, sandbox: "Sandbox") -> EvalResult:
        """
        Evaluate if the file exists and meets criteria.

        Args:
            sandbox: The Sandbox instance to check.

        Returns:
            EvalResult with score 1.0 if file exists and meets criteria, 0.0 otherwise.
        """
        # Import here to avoid circular imports
        from agent_evals.sandbox import Sandbox

        if not isinstance(sandbox, Sandbox):
            return EvalResult(
                score=0.0,
                reason="Expected a Sandbox instance",
                metadata={"error": "invalid_input"},
            )

        # Check if file exists
        if not sandbox.file_exists(self.filename):
            return EvalResult(
                score=0.0,
                reason=f"File '{self.filename}' does not exist",
                metadata={"filename": self.filename, "exists": False},
            )

        # Get file size
        file_size = sandbox.get_file_size(self.filename)
        metadata: dict[str, Any] = {
            "filename": self.filename,
            "exists": True,
            "size_bytes": file_size,
        }

        # Check minimum size
        if self.min_size_bytes is not None and file_size < self.min_size_bytes:
            return EvalResult(
                score=0.0,
                reason=f"File '{self.filename}' is too small ({file_size} < {self.min_size_bytes} bytes)",
                metadata=metadata,
            )

        # Check maximum size
        if self.max_size_bytes is not None and file_size > self.max_size_bytes:
            return EvalResult(
                score=0.0,
                reason=f"File '{self.filename}' is too large ({file_size} > {self.max_size_bytes} bytes)",
                metadata=metadata,
            )

        # Check content if required
        if self.contains is not None:
            try:
                content = sandbox.get_file_content(self.filename)
                metadata["content_length"] = len(content)
                if self.contains not in content:
                    return EvalResult(
                        score=0.0,
                        reason=f"File '{self.filename}' does not contain required text",
                        metadata=metadata,
                    )
            except Exception as e:
                return EvalResult(
                    score=0.0,
                    reason=f"Error reading file '{self.filename}': {e}",
                    metadata={**metadata, "error": str(e)},
                )

        return EvalResult(
            score=1.0,
            reason=f"File '{self.filename}' exists and meets all criteria",
            metadata=metadata,
        )


class DeterministicJudge:
    """A simple deterministic judge using string matching."""

    def __init__(
        self,
        required_phrases: list[str] | None = None,
        forbidden_phrases: list[str] | None = None,
        case_sensitive: bool = False,
    ):
        """
        Initialize the deterministic judge.

        Args:
            required_phrases: Phrases that must be present in the output
            forbidden_phrases: Phrases that must NOT be present in the output
            case_sensitive: Whether matching is case-sensitive
        """
        self.required_phrases = required_phrases or []
        self.forbidden_phrases = forbidden_phrases or []
        self.case_sensitive = case_sensitive

    def evaluate(self, input: str, output: str) -> EvalResult:
        """Evaluate based on presence/absence of specified phrases."""
        check_output = output if self.case_sensitive else output.lower()

        missing_required = []
        for phrase in self.required_phrases:
            check_phrase = phrase if self.case_sensitive else phrase.lower()
            if check_phrase not in check_output:
                missing_required.append(phrase)

        found_forbidden = []
        for phrase in self.forbidden_phrases:
            check_phrase = phrase if self.case_sensitive else phrase.lower()
            if check_phrase in check_output:
                found_forbidden.append(phrase)

        total_checks = len(self.required_phrases) + len(self.forbidden_phrases)
        if total_checks == 0:
            return EvalResult(score=1.0, reason="No criteria specified, passing by default")

        failed_checks = len(missing_required) + len(found_forbidden)
        score = 1.0 - (failed_checks / total_checks)

        reasons = []
        if missing_required:
            reasons.append(f"Missing required phrases: {missing_required}")
        if found_forbidden:
            reasons.append(f"Found forbidden phrases: {found_forbidden}")

        reason = "; ".join(reasons) if reasons else "All criteria met"

        return EvalResult(
            score=score,
            reason=reason,
            metadata={
                "missing_required": missing_required,
                "found_forbidden": found_forbidden,
            },
        )
