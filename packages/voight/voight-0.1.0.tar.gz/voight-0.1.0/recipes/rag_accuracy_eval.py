"""Recipe: RAG Accuracy Evaluation

This recipe demonstrates how to evaluate the accuracy of a RAG
(Retrieval-Augmented Generation) system using both deterministic
and LLM-based judges.

Use Case:
- Measuring retrieval quality
- Testing answer relevance and completeness
- Evaluating citation accuracy
"""

from agent_evals import scenario, check, SimpleGenerator
from agent_evals.judges import DeterministicJudge


# --- Mock RAG System ---

DOCUMENTS = [
    {
        "id": "doc1",
        "title": "Python Basics",
        "content": "Python is a high-level programming language. It supports multiple paradigms including procedural, object-oriented, and functional programming.",
    },
    {
        "id": "doc2",
        "title": "Python Data Types",
        "content": "Python has several built-in data types: int, float, str, list, dict, set, and tuple. Lists are mutable while tuples are immutable.",
    },
    {
        "id": "doc3",
        "title": "Python Functions",
        "content": "Functions in Python are defined using the 'def' keyword. They can have default arguments and return multiple values using tuples.",
    },
]


def mock_retriever(query: str, top_k: int = 2) -> list[dict]:
    """Simple keyword-based retriever."""
    query_lower = query.lower()
    scored = []

    for doc in DOCUMENTS:
        score = sum(1 for word in query_lower.split() if word in doc["content"].lower())
        scored.append((score, doc))

    scored.sort(reverse=True, key=lambda x: x[0])
    return [doc for _, doc in scored[:top_k]]


def mock_rag_agent(query: str) -> dict:
    """A mock RAG agent that retrieves and generates."""
    # Retrieve relevant documents
    retrieved = mock_retriever(query)

    # Generate answer based on retrieved context
    context = " ".join(doc["content"] for doc in retrieved)

    # Simple response generation (in practice, this would be an LLM)
    if "data type" in query.lower():
        answer = "Python has several data types including int, float, str, list, dict, set, and tuple."
        sources = ["doc2"]
    elif "function" in query.lower():
        answer = "Python functions are defined with 'def' and can have default arguments."
        sources = ["doc3"]
    else:
        answer = "Python is a high-level programming language supporting multiple paradigms."
        sources = ["doc1"]

    return {
        "answer": answer,
        "sources": sources,
        "retrieved_docs": [d["id"] for d in retrieved],
    }


# --- Test Scenarios ---

@scenario(runs=5, threshold=1.0)
def test_retrieval_relevance():
    """Test that retriever returns relevant documents."""
    result = mock_rag_agent("What are Python data types?")

    # The relevant document should be retrieved
    assert "doc2" in result["retrieved_docs"], "Should retrieve data types document"


@scenario(runs=5, threshold=1.0)
def test_answer_contains_facts():
    """Test that answers contain facts from retrieved documents."""
    result = mock_rag_agent("What are Python data types?")

    judge = DeterministicJudge(
        required_phrases=["int", "str", "list"],  # Must mention common types
    )

    assert check(result["answer"], judge, input="data types query")


@scenario(runs=5, threshold=1.0)
def test_answer_cites_sources():
    """Test that answers cite their sources."""
    result = mock_rag_agent("How do you define functions in Python?")

    # Answer should cite the functions document
    assert len(result["sources"]) > 0, "Should cite at least one source"
    assert "doc3" in result["sources"], "Should cite the functions document"


generator = SimpleGenerator(templates=[
    "What is {topic}?",
    "Explain {topic}",
    "Tell me about {topic}",
    "How does {topic} work?",
])


@scenario(runs=6, threshold=0.8, generator=generator, base_prompt="Python")
def test_general_python_queries(query: str):
    """Test various Python-related queries."""
    result = mock_rag_agent(query)

    # Should always return some answer
    assert len(result["answer"]) > 20, "Answer should be substantive"

    # Should always retrieve some documents
    assert len(result["retrieved_docs"]) > 0, "Should retrieve documents"

    # Answer should mention Python
    judge = DeterministicJudge(required_phrases=["Python"])
    assert check(result["answer"], judge, input=query)


@scenario(runs=5, threshold=1.0)
def test_no_hallucinated_sources():
    """Test that cited sources actually exist."""
    result = mock_rag_agent("What are Python data types?")

    valid_doc_ids = {doc["id"] for doc in DOCUMENTS}

    for source in result["sources"]:
        assert source in valid_doc_ids, f"Source {source} doesn't exist in corpus"


# --- Metrics Calculation ---

def calculate_retrieval_metrics():
    """Calculate precision and recall for retrieval."""
    test_cases = [
        {
            "query": "What are Python data types?",
            "relevant_docs": {"doc2"},
        },
        {
            "query": "How do functions work?",
            "relevant_docs": {"doc3"},
        },
        {
            "query": "What is Python?",
            "relevant_docs": {"doc1"},
        },
    ]

    total_precision = 0
    total_recall = 0

    for case in test_cases:
        result = mock_rag_agent(case["query"])
        retrieved = set(result["retrieved_docs"])
        relevant = case["relevant_docs"]

        # Precision: relevant retrieved / total retrieved
        precision = len(retrieved & relevant) / len(retrieved) if retrieved else 0

        # Recall: relevant retrieved / total relevant
        recall = len(retrieved & relevant) / len(relevant) if relevant else 0

        total_precision += precision
        total_recall += recall

    avg_precision = total_precision / len(test_cases)
    avg_recall = total_recall / len(test_cases)

    return {
        "precision": avg_precision,
        "recall": avg_recall,
        "f1": 2 * (avg_precision * avg_recall) / (avg_precision + avg_recall) if (avg_precision + avg_recall) > 0 else 0,
    }


if __name__ == "__main__":
    print("Running RAG Accuracy Evaluation...")
    print()

    result = test_retrieval_relevance()
    print(result)

    result = test_answer_contains_facts()
    print(result)

    result = test_answer_cites_sources()
    print(result)

    result = test_general_python_queries()
    print(result)

    result = test_no_hallucinated_sources()
    print(result)

    print()
    print("Retrieval Metrics:")
    metrics = calculate_retrieval_metrics()
    print(f"  Precision: {metrics['precision']:.2%}")
    print(f"  Recall: {metrics['recall']:.2%}")
    print(f"  F1 Score: {metrics['f1']:.2%}")
