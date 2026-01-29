"""Generator implementations for creating test input variations."""

import json
import os
import re

from openai import OpenAI, APIError, APIConnectionError, RateLimitError


class AdversarialGenerator:
    """Generates adversarial variations of prompts using an LLM."""

    def __init__(
        self,
        topic: str,
        style: str = "neutral",
        api_key: str | None = None,
        model: str = "gpt-4o-mini",
    ):
        """
        Initialize the adversarial generator.

        Args:
            topic: The topic for the generated prompts (e.g., "refund request")
            style: The style/persona of the generated prompts (e.g., "rude", "confused", "polite")
            api_key: OpenAI API key. If not provided, reads from OPENAI_API_KEY env var.
            model: The model to use for generation (default: gpt-4o-mini).
        """
        self.topic = topic
        self.style = style
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenAI API key must be provided or set in OPENAI_API_KEY environment variable"
            )
        self.model = model
        self.client = OpenAI(api_key=self.api_key)

    def _parse_variations(self, content: str, n: int) -> list[str]:
        """
        Parse the LLM response to extract variations.

        Handles JSON arrays, numbered lists, and bullet points.
        """
        # Try JSON array first
        try:
            # Look for JSON array in the response
            json_match = re.search(r"\[.*\]", content, re.DOTALL)
            if json_match:
                variations = json.loads(json_match.group())
                if isinstance(variations, list) and all(isinstance(v, str) for v in variations):
                    return variations[:n]
        except (json.JSONDecodeError, ValueError):
            pass

        # Try numbered list (1. ... 2. ... etc.)
        numbered = re.findall(r"^\d+\.\s*(.+)$", content, re.MULTILINE)
        if numbered:
            return [v.strip().strip('"\'') for v in numbered[:n]]

        # Try bullet points (- ... or * ...)
        bullets = re.findall(r"^[-*]\s*(.+)$", content, re.MULTILINE)
        if bullets:
            return [v.strip().strip('"\'') for v in bullets[:n]]

        # Try quoted strings
        quoted = re.findall(r'"([^"]+)"', content)
        if quoted:
            return quoted[:n]

        # Fallback: split by newlines and filter
        lines = [line.strip() for line in content.split("\n") if line.strip()]
        # Filter out lines that look like instructions
        variations = [
            line for line in lines
            if not line.startswith(("Here", "Sure", "I'll", "Below", "The following"))
            and len(line) > 10
        ]

        return variations[:n] if variations else [f"Tell me about {self.topic}"]

    def generate(self, base_prompt: str, n: int) -> list[str]:
        """
        Generate n variations of the base prompt.

        Args:
            base_prompt: The base prompt to generate variations of
            n: Number of variations to generate

        Returns:
            List of generated prompt variations
        """
        system_prompt = f"""You are a prompt variation generator. Your task is to generate diverse
variations of user prompts for testing AI agents.

Generate exactly {n} variations. Each variation should:
1. Be about the same topic but phrased differently
2. Reflect the specified style/persona
3. Be realistic and natural-sounding
4. Vary in length and complexity

Respond with a JSON array of strings, like:
["variation 1", "variation 2", "variation 3"]"""

        user_message = f"""Generate {n} variations of a user asking about: {self.topic}

The user should appear: {self.style}

Base prompt for inspiration: {base_prompt}

Remember: Return ONLY a JSON array of {n} strings."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                temperature=0.9,  # Higher temperature for diverse outputs
                max_tokens=1024,
            )

            content = response.choices[0].message.content or ""
            variations = self._parse_variations(content, n)

            # Ensure we have exactly n variations
            while len(variations) < n:
                variations.append(f"I need help with {self.topic}")

            return variations[:n]

        except (RateLimitError, APIConnectionError, APIError) as e:
            # Return fallback variations on API error
            return [f"I have a question about {self.topic}" for _ in range(n)]
        except Exception as e:
            # Return fallback variations on unexpected error
            return [f"Tell me about {self.topic}" for _ in range(n)]


class SimpleGenerator:
    """A simple generator that creates variations using templates (no LLM required)."""

    def __init__(self, templates: list[str] | None = None):
        """
        Initialize the simple generator.

        Args:
            templates: List of template strings with {topic} placeholder.
                      If not provided, uses default templates.
        """
        self.templates = templates or [
            "I need help with {topic}",
            "Can you assist me with {topic}?",
            "I have a question about {topic}",
            "Please help me understand {topic}",
            "What can you tell me about {topic}?",
            "I'm confused about {topic}",
            "Could you explain {topic} to me?",
            "I'm having issues with {topic}",
            "Tell me more about {topic}",
            "I want to know about {topic}",
        ]

    def generate(self, base_prompt: str, n: int) -> list[str]:
        """
        Generate n variations using templates.

        Args:
            base_prompt: Used as the topic to fill in templates
            n: Number of variations to generate

        Returns:
            List of generated prompt variations
        """
        variations = []
        for i in range(n):
            template = self.templates[i % len(self.templates)]
            variations.append(template.format(topic=base_prompt))
        return variations
