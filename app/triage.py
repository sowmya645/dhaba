
from app.classifier import classify_ticket
from app.refundpolicy import decide_refund
from app.rules import detect_prompt_injection
from app.schemas import Category, Severity, TriageResponse


def triage_ticket(ticket: dict) -> TriageResponse:
    """Classify a ticket and compose a conservative triage response."""

    ticket_id = ticket["id"]
    subject = ticket["subject"]
    body = ticket["body"]

    # Keep intent classification and security detection independent.
    category, confidence, confidence_reason = classify_ticket(subject, body)
    injection_detected = detect_prompt_injection(subject, body)

    # Derive payment verification from trusted purchase records.
    purchases = ticket.get("purchases", [])
    successful_payments = [
        purchase
        for purchase in purchases
        if purchase.get("status") == "successful"
    ]
    payment_verified = bool(successful_payments)

    refund = decide_refund(
        category=category,
        injection_detected=injection_detected,
        payment_verified=payment_verified,
        confidence=confidence,
    )

    # Raise severity conservatively using deterministic rules.
    if injection_detected or category == Category.FRAUD:
        severity = Severity.HIGH
    elif category in (Category.REFUND, Category.PAYMENT_FAILURE):
        severity = Severity.MEDIUM
    else:
        severity = Severity.LOW

    if injection_detected:
        reply_draft = (
            "Thanks for contacting Dhaba. Your request needs a human "
            "review before we can confirm the next steps."
        )
    elif category == Category.ACCOUNT_ISSUE:
        reply_draft = (
            "Thanks for reporting this. Our support team will review "
            "the missing order history and help you with the next steps."
        )
    elif category == Category.REFUND:
        reply_draft = (
            "Thanks for contacting Dhaba about this charge. Our support "
            "team will review the payment and refund eligibility before "
            "confirming the outcome."
        )
    elif category == Category.PAYMENT_FAILURE:
        reply_draft = (
            "Thanks for reporting the payment issue. Our support team "
            "will check the payment status and subscription activation."
        )
    else:
        reply_draft = (
            "Thanks for contacting Dhaba. Our support team will review "
            "your request and help with the next steps."
        )

    needs_human = (
        refund.requires_human_review
        or injection_detected
        or category == Category.FRAUD
        or confidence < 0.80
    )

    return TriageResponse(
        ticket_id=ticket_id,
        category=category,
        severity=severity,
        refund=refund,
        reply_draft=reply_draft,
        needs_human=needs_human,
        confidence=confidence,
        confidence_reason=confidence_reason,
        prompt_injection_detected=injection_detected,
        processing_mode="rules",
    )
