
import json
from pathlib import Path

from app.rules import detect_prompt_injection


def load_tickets():
    path = Path("data/dhaba_tickets.json")
    with path.open(encoding="utf-8") as file:
        data = json.load(file)
    return data["tickets"]


def test_injection_flags_expected_tickets():
    tickets = load_tickets()

    flagged = {
        ticket["id"]
        for ticket in tickets
        if detect_prompt_injection(ticket["subject"], ticket["body"])
    }

    assert flagged == {"T-1003", "T-1011"}
