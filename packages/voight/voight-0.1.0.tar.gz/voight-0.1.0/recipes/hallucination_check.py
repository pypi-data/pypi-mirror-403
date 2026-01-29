"""Recipe: Hallucination Detection for RAG Agents

This recipe demonstrates how to test a RAG (Retrieval-Augmented Generation)
agent for hallucinations by verifying outputs against known source documents.

Use Case:
- Testing that an agent's responses are grounded in provided context
- Detecting when an agent makes up information not in the source
- Validating factual accuracy of generated responses
"""

from agent_evals import scenario, check, SimpleGenerator
from agent_evals.judges import DeterministicJudge, SimpleLLMJudge


# --- Mock RAG Agent ---

KNOWLEDGE_BASE = {
    "company_policy": """
    Our refund policy allows returns within 30 days of purchase.
    Items must be in original packaging. Digital products are non-refundable.
    Contact support@example.com for assistance.
    """,
    "product_specs": """
    Model X-500: 16GB RAM, 512GB SSD, 15.6" display.
    Battery life: 10 hours. Weight: 1.8kg.
    Available colors: Silver, Space Gray.
    """,
}


def mock_rag_agent(query: str, context_key: str = "company_policy") -> str:
    """A mock RAG agent that sometimes hallucinates."""
    import random

    context = KNOWLEDGE_BASE.get(context_key, "")

    # Simulate different response qualities
    if random.random() < 0.2:
        # 20% chance of hallucination
        return "Our refund policy allows returns within 60 days. We also offer free shipping on all returns."
    else:
        # Grounded response
        return f"Based on the policy: Returns are accepted within 30 days. Items must be in original packaging."


# --- Test Scenarios ---

@scenario(runs=10, threshold=0.8)
def test_refund_policy_accuracy():
    """Test that refund policy responses are grounded in source."""
    response = mock_rag_agent("What is your refund policy?", "company_policy")

    # Check for known facts from the source
    judge = DeterministicJudge(
        required_phrases=["30 days"],  # Must mention correct timeframe
        forbidden_phrases=["60 days", "90 days", "free shipping"],  # Hallucinations
    )

    assert check(response, judge, input="refund policy query")


@scenario(runs=10, threshold=0.9)
def test_no_invented_features():
    """Test that product responses don't invent features."""
    response = mock_rag_agent("What are the specs?", "product_specs")

    # Known hallucination patterns to forbid
    judge = DeterministicJudge(
        forbidden_phrases=[
            "32GB",  # Wrong RAM
            "1TB",  # Wrong storage
            "20 hours",  # Wrong battery
            "touchscreen",  # Not mentioned in source
        ],
    )

    assert check(response, judge, input="product specs query")


# --- Advanced: LLM-Based Hallucination Detection ---

# Uncomment to use with OpenAI API key

# @scenario(runs=5, threshold=0.8)
# def test_semantic_grounding():
#     """Use LLM to detect semantic hallucinations."""
#     context = KNOWLEDGE_BASE["company_policy"]
#     response = mock_rag_agent("What is your refund policy?")
#
#     judge = SimpleLLMJudge(
#         custom_criteria=f"""
#         Verify that the response is ONLY based on this context:
#         {context}
#
#         Score 0.0 if the response contains ANY information not in the context.
#         Score 1.0 if ALL claims in the response are supported by the context.
#         """
#     )
#
#     result = judge.evaluate(input="refund policy", output=response)
#     assert result.score >= 0.8, f"Potential hallucination detected: {result.reason}"


if __name__ == "__main__":
    print("Running Hallucination Detection Tests...")
    print()

    result = test_refund_policy_accuracy()
    print(result)

    result = test_no_invented_features()
    print(result)
