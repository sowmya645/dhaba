import os
import re

from app.classifier import classify_ticket
from app.llm import generate_model_output
from app.refundpolicy import decide_refund
from app.replay import replay_model_output
from app.rules import detect_prompt_injection
from app.schemas import Category, Severity, TriageResponse


# These patterns target promises/confirmations, not generic mentions of
# "refund", "return", "money", or amounts such as "Rs 249".
UNSUPPORTED_REFUND_PROMISE_PATTERNS = (
    # Approval/confirmation, including "Your refund of Rs 249 has been approved."
    r"\brefund\b.{0,80}\b(?:approved|accepted|confirmed)\b",
    r"\brefund\s+(?:has been|was|is being|will be)\s+"
    r"(?:processed|issued|completed|credited)\b",
    r"\brefund\s+(?:will arrive|will reach|will be credited)\b",
    r"\brefund\s+(?:within|in)\s+\d+\s+(?:hours?|days?|weeks?)\b",

    # Explicit promises from the company.
    r"\bwe(?:'ll| will)\s+(?:refund|reimburse|repay)\s+you\b",
    r"\bwe\s+(?:have|had|'ve)\s+(?:refunded|reimbursed|repaid)\s+you\b",
    r"\bwe(?:'ll| will)\s+(?:process|issue|approve|initiate|send|"
    r"credit|reverse)\s+(?:your\s+)?refund\b",
    r"\byou(?:'ll| will)\s+(?:get|receive)\s+(?:your\s+)?"
    r"(?:refund|money back|amount back)\b",

    # Crediting/reversing/returning money.
    r"\bcredited\b.{0,40}\b(?:back|refund|your account|your bank)\b",
    r"\b(?:money|amount|charge)\s+(?:is|has been|will be|is being)\s+"
    r"(?:refunded|returned|credited|reversed)\b",
    r"\b(?:charge|payment|transaction)\s+(?:has been|was|is being|"
    r"will be)\s+reversed\b",
    r"\b(?:your\s+)?money\s+(?:is|will be|has been)\s+"
    r"(?:on its way back|coming back|returned)\b",
    r"\b(?:we(?:'ll| will)|we have|we've)\s+"
    r"(?:send|sent|return|returned|transfer|transferred|"
    r"credit|credited)\s+(?:the\s+)?(?:money|amount)\s+back\b",
    # Matches "We will return the 249 to your bank."
    r"\bwe(?:'ll| will)\s+return\s+(?:the\s+)?"
    r"(?:(?:rs\.?|inr)\s*|₹\s*)?\d+(?:\.\d{1,2})?\s+"
    r"to\s+(?:your\s+)?(?:bank|account)\b",
    r"\bwe(?:'ll| will)\s+return\s+(?:the\s+)?(?:amount|money)\s+"
    r"to\s+(?:your\s+)?(?:bank|account)\b",

    # Common Hinglish promises.
    r"\b(?:paise|paisa|rakam)\s+wapis?\s+"
    r"(?:aa jayenge|aa jayega|mil jayenge|mil jayega|"
    r"kar diye jayenge|bhej diye jayenge)\b",
)

SENSITIVE_PATTERNS = (
    r"\b[A-Z]{5}[0-9]{4}[A-Z]\b",  # PAN-like identifier
    r"\b[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][0-9A-Z]Z[0-9A-Z]\b",  # GSTIN
    r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",  # Email
    r"(?<!\w)(?:\+?91[-\s]?)?[6-9]\d{9}(?!\w)",  # Indian phone
)


def _matches_any(patterns: tuple[str, ...], text: str) -> bool:
    """Return True when any regular expression matches the text."""
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)


def safe_reply_for_category(category: Category) -> str:
    """Return a conservative fallback appropriate to the ticket category."""
    category_name = (
        category.value if hasattr(category, "value") else str(category)
    ).lower()

    templates = {
        "refund": (
            "Thanks for contacting Dhaba about this charge. Our support "
            "team will review the payment and refund eligibility before "
            "confirming the outcome."
        ),
        "billing": (
            "Thanks for contacting Dhaba about your billing request. "
            "Our support team will review the billing details and "
            "help with the next steps."
        ),
        "payment_failure": (
            "Thanks for reporting the payment issue. Our support team "
            "will check the payment status and subscription activation."
        ),
        "technical_issue": (
            "Thanks for reporting this technical issue. Our support "
            "team will review the problem and help with the next steps."
        ),
        "account_issue": (
            "Thanks for reporting this account issue. Our support team "
            "will review the account details and help with the next steps."
        ),
        "cancellation": (
            "Thanks for contacting Dhaba about cancellation. Our support "
            "team will check your subscription status and applicable "
            "cancellation policy before confirming the next steps."
        ),
        "feature_request": (
            "Thanks for sharing your feature suggestion. Our team will "
            "review your feedback for consideration."
        ),
        "fraud": (
            "Thanks for reporting this concern. Our support team will "
            "review it carefully and confirm the next steps."
        ),
        "general_question": (
            "Thanks for contacting Dhaba. Our support team will review "
            "your question and help with the next steps."
        ),
        "technical": (
            "Thanks for reporting this technical issue. Our support "
            "team will review the problem and help with the next steps."
        ),
    }

    return templates.get(
        category_name,
        "Thanks for contacting Dhaba. Our support team will review "
        "your request and help with the next steps.",
    )


def triage_ticket(ticket: dict, mode: str | None = None) -> TriageResponse:
    """Triage a ticket using local rules, replay fixtures, or Gemini."""
    ticket_id = ticket["id"]
    subject = ticket["subject"]
    body = ticket["body"]

    # Local rules are the default, so the app works without an API key.
    selected_mode = (mode or os.getenv("TRIAGE_MODE", "rules")).lower()
    if selected_mode not in {"rules", "replay", "gemini"}:
        raise ValueError("TRIAGE_MODE must be 'rules', 'replay', or 'gemini'.")

    injection_detected = detect_prompt_injection(subject, body)
    actual_mode = selected_mode
    suggested_reply = None

    # The model may suggest classification and wording, but cannot authorize
    # a refund.
    if selected_mode == "replay":
        try:
            model_output = replay_model_output(ticket_id)
            category = model_output.category
            confidence = model_output.confidence
            confidence_reason = model_output.confidence_reason
            suggested_reply = model_output.reply_draft
        except (KeyError, ValueError):
            actual_mode = "rules_fallback"
            category, confidence, confidence_reason = classify_ticket(
                subject, body
            )

    elif selected_mode == "gemini":
        if injection_detected:
            # Do not send tickets flagged by the injection detector to Gemini.
            actual_mode = "rules_fallback"
            category, confidence, confidence_reason = classify_ticket(
                subject, body
            )
        else:
            try:
                model_output = generate_model_output(ticket)
                category = model_output.category
                confidence = model_output.confidence
                confidence_reason = model_output.confidence_reason
                suggested_reply = model_output.reply_draft
            except Exception:
                # API, validation, or other model errors degrade to local rules.
                actual_mode = "rules_fallback"
                category, confidence, confidence_reason = classify_ticket(
                    subject, body
                )
    else:
        category, confidence, confidence_reason = classify_ticket(
            subject, body
        )

    # Payment status must come from trusted purchase records, not ticket text.
    purchases = ticket.get("purchases", [])
    payment_verified = any(
        purchase.get("status") == "successful" for purchase in purchases
    )

    # Failed or pending payment states need reconciliation.
    unresolved_payment = (
        category == Category.PAYMENT_FAILURE
        and any(
            purchase.get("status") in {"initiated", "failed"}
            for purchase in purchases
        )
    )
    cancellation_needs_review = category == Category.CANCELLATION

    # Refund eligibility is determined independently of model output.
    refund = decide_refund(
        category=category,
        injection_detected=injection_detected,
        payment_verified=payment_verified,
        refund_policy_defined=False,
        confidence=confidence,
    )

    # Assign severity.
    if injection_detected or category == Category.FRAUD:
        severity = Severity.HIGH
    elif category in (Category.REFUND, Category.PAYMENT_FAILURE):
        severity = Severity.MEDIUM
    else:
        severity = Severity.LOW

    # Choose the initial reply.
    if injection_detected:
        reply_draft = (
            "Thanks for contacting Dhaba. Your request needs a human "
            "review before we can confirm the next steps."
        )
    elif suggested_reply is not None:
        reply_draft = suggested_reply
    elif category == Category.ACCOUNT_ISSUE:
        reply_draft = (
            "Thanks for reporting this. Our support team will review "
            "the missing order history and help you with the next steps."
        )
    elif category == Category.REFUND:
        reply_draft = safe_reply_for_category(category)
    elif category == Category.PAYMENT_FAILURE:
        is_hinglish = bool(
            re.search(
                r"\b(paisa|bhai|nahi|nahin|kar|kiya|dikha|gaya|hai|ho)\b",
                f"{subject} {body}",
                re.IGNORECASE,
            )
        )
        if is_hinglish:
            reply_draft = (
                "Payment issue batane ke liye shukriya. Hamari support "
                "team payment status check karegi aur confirm karegi ki "
                "aapka plan activate hua hai ya nahi. Abhi payment "
                "successfully complete hua hai, yeh confirm nahi hai."
            )
        else:
            reply_draft = safe_reply_for_category(category)
    elif category == Category.CANCELLATION:
        reply_draft = safe_reply_for_category(category)
    else:
        reply_draft = safe_reply_for_category(category)

    # Detect unsupported promises, not generic mentions of money. A refund
    # promise is unsafe whenever the system has not approved the refund.
    unsafe_refund_claim = bool(
        not refund.eligible
        and _matches_any(
            UNSUPPORTED_REFUND_PROMISE_PATTERNS,
            reply_draft,
        )
    )

    # Detect sensitive identifiers repeated from the ticket. This is a
    # heuristic, not a complete PII detector.
    combined_ticket_text = f"{subject}\n{body}"
    echoed_sensitive_info = any(
        re.search(pattern, combined_ticket_text, re.IGNORECASE)
        and re.search(pattern, reply_draft, re.IGNORECASE)
        for pattern in SENSITIVE_PATTERNS
    )

    # Replace unsafe replies with a fallback for this ticket's category.
    # Never turn a crash, invoice, or feature reply into refund wording.
    reply_guard_triggered = unsafe_refund_claim or echoed_sensitive_info
    if reply_guard_triggered:
        reply_draft = safe_reply_for_category(category)

    # Human review is required for policy decisions, security risks,
    # low confidence, and unresolved payment/cancellation cases.
    needs_human = (
        refund.requires_human_review
        or injection_detected
        or category == Category.FRAUD
        or confidence < 0.80
        or cancellation_needs_review
        or unresolved_payment
        or reply_guard_triggered
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
        processing_mode=actual_mode,
    )
