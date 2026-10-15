
"""Deterministic fixture-based replay mode for Dhaba triage."""

from app.schemas import Category, ModelOutput, Severity


REPLAY_FIXTURES: dict[str, dict] = {
    "T-1001": {
        "category": "refund",
        "severity": "medium",
        "confidence": 0.85,
        "confidence_reason": "Fixture: customer requests a charge review.",
        "reply_draft": "Our support team will review the payment and refund eligibility.",
    },
    "T-1002": {
        "category": "technical_issue",
        "severity": "low",
        "confidence": 0.90,
        "confidence_reason": "Fixture: customer reports an app issue.",
        "reply_draft": "Our support team will investigate the reported app issue.",
    },
    "T-1003": {
        "category": "account_issue",
        "severity": "high",
        "confidence": 0.85,
        "confidence_reason": "Fixture: customer reports missing account history.",
        "reply_draft": "Our support team will review the missing order history.",
    },
    "T-1004": {
        "category": "cancellation",
        "severity": "low",
        "confidence": 0.90,
        "confidence_reason": "Fixture: customer requests cancellation.",
        "reply_draft": "Our support team will review your cancellation request.",
    },
    "T-1005": {
        "category": "payment_failure",
        "severity": "medium",
        "confidence": 0.90,
        "confidence_reason": "Fixture: customer reports a payment problem.",
        "reply_draft": "Our support team will check the payment and activation status.",
    },
    "T-1006": {
        "category": "refund",
        "severity": "medium",
        "confidence": 0.85,
        "confidence_reason": "Fixture: customer requests a refund review.",
        "reply_draft": "Our support team will review your refund request.",
    },
    "T-1007": {
        "category": "feature_request",
        "severity": "low",
        "confidence": 0.90,
        "confidence_reason": "Fixture: customer suggests a product feature.",
        "reply_draft": "Thank you for suggesting this feature. We will share your feedback.",
    },
    "T-1008": {
        "category": "fraud",
        "severity": "high",
        "confidence": 0.95,
        "confidence_reason": "Fixture: possible unauthorized payment.",
        "reply_draft": "Our support team will review this security concern.",
    },
    "T-1009": {
        "category": "refund",
        "severity": "medium",
        "confidence": 0.85,
        "confidence_reason": "Fixture: customer requests a charge review.",
        "reply_draft": "Our support team will review your payment concern.",
    },
    "T-1010": {
        "category": "billing",
        "severity": "low",
        "confidence": 0.90,
        "confidence_reason": "Fixture: customer has a billing question.",
        "reply_draft": "Our support team will review your billing request.",
    },
    "T-1011": {
        "category": "general_question",
        "severity": "high",
        "confidence": 0.85,
        "confidence_reason": "Fixture: customer asks about product functionality.",
        "reply_draft": "Our support team will review your question before responding.",
    },
    "T-1012": {
        "category": "refund",
        "severity": "medium",
        "confidence": 0.85,
        "confidence_reason": "Fixture: customer requests a refund review.",
        "reply_draft": "Our support team will review your refund request.",
    },
}


def replay_model_output(ticket_id: str) -> ModelOutput:
    """Return a validated, deterministic fixture for a known ticket ID."""
    fixture = REPLAY_FIXTURES.get(ticket_id)

    if fixture is None:
        raise KeyError(f"No replay fixture exists for ticket {ticket_id!r}")

    return ModelOutput.model_validate(fixture)
