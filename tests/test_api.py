
import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def load_first_ticket():
    path = Path("data/dhaba_tickets.json")
    with path.open(encoding="utf-8") as file:
        return json.load(file)["tickets"][0]


def test_health_endpoint():
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_triage_endpoint_returns_result_and_request_id():
    response = client.post("/triage", json=load_first_ticket())

    assert response.status_code == 200
    assert response.headers.get("X-Request-ID")
    assert response.json()["ticket_id"] == "T-1001"
    assert response.json()["refund"]["eligible"] is False


def test_invalid_ticket_returns_422():
    response = client.post("/triage", json={"id": "missing-fields"})

    assert response.status_code == 422

def test_duplicate_ticket_returns_stored_result():
    ticket = load_first_ticket()

    first = client.post("/triage", json=ticket)
    second = client.post("/triage", json=ticket)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json() == second.json()


def test_same_ticket_id_with_changed_content_returns_409():
    ticket = load_first_ticket()

    first = client.post("/triage", json=ticket)
    assert first.status_code == 200

    changed = {**ticket, "body": ticket["body"] + " Please check again."}
    second = client.post("/triage", json=changed)

    assert second.status_code == 409
