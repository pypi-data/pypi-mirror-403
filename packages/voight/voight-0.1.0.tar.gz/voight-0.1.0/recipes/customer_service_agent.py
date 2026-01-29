"""Recipe: Customer Service Agent Testing

This recipe demonstrates comprehensive testing of a customer service
chatbot agent, including tone analysis, policy compliance, and
escalation handling.

Use Case:
- Testing customer-facing AI agents
- Verifying policy compliance
- Ensuring appropriate tone and empathy
- Testing edge cases and adversarial inputs
"""

from agent_evals import scenario, Sandbox, check, SimpleGenerator
from agent_evals.judges import DeterministicJudge, FileExistsJudge


# --- Mock Customer Service Agent ---

class CustomerServiceAgent:
    """A mock customer service agent with various response patterns."""

    RESPONSES = {
        "refund": "I understand you'd like a refund. I'm sorry for any inconvenience. "
                  "Our policy allows returns within 30 days. Let me help you process this.",
        "complaint": "I'm truly sorry to hear about your experience. "
                     "Your feedback is important to us. Let me escalate this to a supervisor.",
        "question": "Great question! I'd be happy to help. "
                    "Could you provide a bit more detail about what you need?",
        "angry": "I completely understand your frustration, and I sincerely apologize. "
                 "Let me make this right for you immediately.",
        "default": "Thank you for contacting us. How can I assist you today?",
    }

    def __init__(self):
        self.conversation_log = []

    def respond(self, message: str) -> str:
        """Generate a response based on the customer message."""
        message_lower = message.lower()

        # Determine response type
        if any(word in message_lower for word in ["refund", "return", "money back"]):
            response_type = "refund"
        elif any(word in message_lower for word in ["angry", "furious", "terrible", "worst"]):
            response_type = "angry"
        elif any(word in message_lower for word in ["complaint", "problem", "issue"]):
            response_type = "complaint"
        elif "?" in message:
            response_type = "question"
        else:
            response_type = "default"

        response = self.RESPONSES[response_type]

        # Log the conversation
        self.conversation_log.append({"customer": message, "agent": response})

        return response

    def save_ticket(self, customer_id: str, issue: str):
        """Create a support ticket file."""
        import json
        from pathlib import Path

        ticket = {
            "customer_id": customer_id,
            "issue": issue,
            "conversation": self.conversation_log,
            "status": "open",
        }

        Path("ticket.json").write_text(json.dumps(ticket, indent=2))
        return ticket


# --- Test Scenarios ---

# Polite customer inputs
polite_generator = SimpleGenerator(templates=[
    "Hello, I have a question about {topic}",
    "Hi there, could you help me with {topic}?",
    "Good morning, I need assistance with {topic}",
])


@scenario(runs=5, threshold=1.0, generator=polite_generator, base_prompt="my order")
def test_polite_customer_gets_helpful_response(message: str):
    """Test that polite customers receive helpful responses."""
    agent = CustomerServiceAgent()
    response = agent.respond(message)

    judge = DeterministicJudge(
        required_phrases=["help", "happy"],
        forbidden_phrases=["unfortunately", "cannot", "won't"],
    )

    assert check(response, judge, input=message)


# Angry customer inputs
angry_generator = SimpleGenerator(templates=[
    "This is terrible! I'm furious about {topic}!",
    "I'm so angry about {topic}. This is unacceptable!",
    "Worst experience ever with {topic}!",
])


@scenario(runs=5, threshold=1.0, generator=angry_generator, base_prompt="my order")
def test_angry_customer_gets_empathetic_response(message: str):
    """Test that angry customers receive empathetic de-escalation."""
    agent = CustomerServiceAgent()
    response = agent.respond(message)

    # Must show empathy and apologize
    judge = DeterministicJudge(
        required_phrases=["understand", "sorry", "apologize"],
        forbidden_phrases=["calm down", "relax", "wrong"],  # Never dismissive
    )

    assert check(response, judge, input=message)


@scenario(runs=5, threshold=1.0)
def test_refund_request_mentions_policy():
    """Test that refund requests reference the return policy."""
    agent = CustomerServiceAgent()
    response = agent.respond("I want a refund for my purchase")

    judge = DeterministicJudge(
        required_phrases=["30 days", "policy"],  # Must mention policy
    )

    assert check(response, judge, input="refund request")


@scenario(runs=3, threshold=1.0)
def test_ticket_creation():
    """Test that support tickets are properly created."""
    with Sandbox() as box:
        agent = CustomerServiceAgent()
        agent.respond("I have a complaint about my order")
        agent.save_ticket("CUST-123", "Order complaint")

        # Verify ticket was created
        assert check(box, FileExistsJudge("ticket.json"))

        # Verify ticket content
        import json
        content = box.get_file_content("ticket.json")
        ticket = json.loads(content)

        assert ticket["customer_id"] == "CUST-123"
        assert ticket["status"] == "open"
        assert len(ticket["conversation"]) > 0


@scenario(runs=5, threshold=1.0)
def test_no_inappropriate_language():
    """Test that agent never uses inappropriate language."""
    agent = CustomerServiceAgent()

    test_messages = [
        "You guys are idiots!",
        "This is the worst company ever!",
        "I hate your service!",
    ]

    for message in test_messages:
        response = agent.respond(message)

        judge = DeterministicJudge(
            forbidden_phrases=[
                "idiot", "stupid", "dumb",  # Insults
                "your fault", "you're wrong",  # Blame
                "deal with it", "too bad",  # Dismissive
            ],
        )

        assert check(response, judge, input=message), f"Inappropriate response to: {message}"


@scenario(runs=5, threshold=1.0)
def test_complaint_escalation():
    """Test that serious complaints are escalated."""
    agent = CustomerServiceAgent()
    response = agent.respond("I have a serious complaint about my experience")

    # Should mention escalation
    judge = DeterministicJudge(
        required_phrases=["supervisor", "escalate"],
    )

    assert check(response, judge, input="complaint")


# --- Conversation Flow Test ---

@scenario(runs=3, threshold=1.0)
def test_multi_turn_conversation():
    """Test a multi-turn conversation flow."""
    agent = CustomerServiceAgent()

    # Turn 1: Greeting
    response1 = agent.respond("Hello")
    assert "assist" in response1.lower() or "help" in response1.lower()

    # Turn 2: State issue
    response2 = agent.respond("I want to return an item")
    assert "refund" in response2.lower() or "return" in response2.lower()

    # Verify conversation was logged
    assert len(agent.conversation_log) == 2


if __name__ == "__main__":
    print("Running Customer Service Agent Tests...")
    print()

    result = test_polite_customer_gets_helpful_response()
    print(result)

    result = test_angry_customer_gets_empathetic_response()
    print(result)

    result = test_refund_request_mentions_policy()
    print(result)

    result = test_ticket_creation()
    print(result)

    result = test_no_inappropriate_language()
    print(result)

    result = test_complaint_escalation()
    print(result)

    result = test_multi_turn_conversation()
    print(result)
