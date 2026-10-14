
import json
from pathlib import Path

from app.schemas import Category
from app.triage import triage_ticket


def load_tickets():
    path = Path("data/dhaba_tickets.json")
    with path.open(encoding="utf-8") as file:
        return json.load(file)["tickets"]


def test_t1003_is_account_issue_and_injection_is_flagged():
    ticket = next(t for t in load_tickets() if t["id"] == "T-1003")

    result = triage_ticket(ticket)

    assert result.category == Category.ACCOUNT_ISSUE
    assert result.prompt_injection_detected is True
    assert result.needs_human is True
    assert result.refund.eligible is False
    assert result.refund.amount_inr == 0


def test_t1011_is_question_and_injection_is_flagged():
    ticket = next(t for t in load_tickets() if t["id"] == "T-1011")

    result = triage_ticket(ticket)

    assert result.category == Category.GENERAL_QUESTION
    assert result.prompt_injection_detected is True
    assert result.needs_human is True
    assert result.refund.eligible is False


def test_t1001_refund_is_not_automatically_approved():
    ticket = next(t for t in load_tickets() if t["id"] == "T-1001")

    result = triage_ticket(ticket)

    assert result.category == Category.REFUND
    assert result.refund.eligible is False
    assert result.refund.amount_inr == 0
    assert result.needs_human is True
