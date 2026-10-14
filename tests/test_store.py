
import json
from pathlib import Path

import app.store as store


def setup_function():
    db_path = Path("data/test_dhaba.sqlite3")
    if db_path.exists():
        db_path.unlink()
    store.DB_PATH = db_path


def sample_ticket():
    return {
        "id": "T-TEST-1",
        "subject": "Need help",
        "body": "Please check my account",
        "purchases": [],
        "app_opens_since_renewal": 0,
    }


def test_new_ticket_can_be_claimed_and_completed():
    ticket = sample_ticket()

    status, result = store.claim_ticket(ticket)
    assert status == "claimed"
    assert result is None

    expected = {"ticket_id": ticket["id"], "category": "account_issue"}
    store.complete_ticket(ticket["id"], expected)

    status, result = store.claim_ticket(ticket)
    assert status == "completed"
    assert result == expected


def test_same_id_with_changed_content_conflicts():
    ticket = sample_ticket()
    assert store.claim_ticket(ticket)[0] == "claimed"

    changed = {**ticket, "body": "A different request"}
    status, result = store.claim_ticket(changed)

    assert status == "conflict"
    assert result is None


def test_ticket_already_processing_conflicts():
    ticket = sample_ticket()
    assert store.claim_ticket(ticket)[0] == "claimed"

    status, result = store.claim_ticket(ticket)

    assert status == "conflict"
    assert result is None

