
import logging
import time
import uuid

from fastapi import FastAPI, HTTPException, Request

from app.schemas import TicketInput
from app.store import claim_ticket, complete_ticket, release_ticket
from app.triage import triage_ticket

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("dhaba")

app = FastAPI(
    title="Dhaba Support Triage API",
    version="0.2.0",
)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


@app.get("/healthz")
def health():
    return {"status": "ok"}


@app.post("/triage")
def triage(request: Request, ticket: TicketInput):
    start = time.perf_counter()
    ticket_data = ticket.model_dump(mode="json")

    status, stored_result = claim_ticket(ticket_data)

    if status == "completed":
        return stored_result

    if status == "conflict":
        raise HTTPException(
            status_code=409,
            detail=(
                "Ticket is already processing or its ID "
                "was used with different content."
            ),
        )

    try:
        result = triage_ticket(ticket_data)
        result_data = result.model_dump(mode="json")

        complete_ticket(ticket_data["id"], result_data)

    except Exception:
        release_ticket(ticket_data["id"])

        logger.exception(
            "triage_failed request_id=%s ticket_id=%s",
            request.state.request_id,
            ticket_data["id"],
        )

        raise HTTPException(
            status_code=500,
            detail="Ticket processing failed.",
        )

    elapsed_ms = round(
        (time.perf_counter() - start) * 1000,
        2,
    )

    # Log metadata only; never log the subject, body, or purchases.
    logger.info(
        "triage_done request_id=%s ticket_id=%s category=%s "
        "needs_human=%s injection=%s latency_ms=%s",
        request.state.request_id,
        ticket_data["id"],
        result.category.value,
        result.needs_human,
        result.prompt_injection_detected,
        elapsed_ms,
    )

    return result_data


@app.get("/metrics")
def metrics():
    return {
        "service": "dhaba-triage",
        "metrics_status": "basic",
    }
