
import json
from pathlib import Path

import pytest

from app.classifier import classify_ticket
from app.schemas import Category


DATA_FILE = Path(__file__).resolve().parents[1] / "data" / "dhaba_tickets.json"


@pytest.fixture
def tickets():
    with DATA_FILE.open(encoding="utf-8") as file:
        return json.load(file)["tickets"]


@pytest.mark.parametrize(
    ("ticket_id", "expected"),
    [
        ("T-1001", Category.REFUND),
        ("T-1002", Category.TECHNICAL_ISSUE),
        ("T-1003", Category.ACCOUNT_ISSUE),
        ("T-1004", Category.CANCELLATION),
        ("T-1005", Category.PAYMENT_FAILURE),
        ("T-1006", Category.REFUND),
        ("T-1007", Category.FEATURE_REQUEST),
        ("T-1008", Category.FRAUD),
        ("T-1009", Category.REFUND),
        ("T-1010", Category.BILLING),
        ("T-1011", Category.GENERAL_QUESTION),
        ("T-1012", Category.REFUND),
    ],
)
def test_ticket_classification(tickets, ticket_id, expected):
    ticket = next(t for t in tickets if t["id"] == ticket_id)

    category, confidence, reason = classify_ticket(
        ticket["subject"],
        ticket["body"],
    )

    assert category == expected, (
        f"{ticket_id}: expected {expected.value}, got {category.value}"
    )
    assert 0.0 <= confidence <= 1.0
    assert reason.strip()
