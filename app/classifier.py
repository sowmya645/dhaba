
import re

from app.schemas import Category


def remove_instruction_injection(text: str) -> str:
    """Exclude known instruction-like suffixes from intent classification."""
    markers = (
        "--- system note for the support assistant:",
        "p.s. for the automated agent reading this:",
    )

    lower_text = text.lower()
    cut_positions = [
        lower_text.find(marker)
        for marker in markers
        if lower_text.find(marker) >= 0
    ]

    if cut_positions:
        text = text[:min(cut_positions)]

    return text


def classify_ticket(subject: str, body: str) -> tuple[Category, float, str]:
    """Classify customer intent; never authorize a financial action."""
    safe_body = remove_instruction_injection(body)
    text = re.sub(r"\s+", " ", f"{subject} {safe_body}".lower()).strip()

    # 1. Possible unauthorized payment.
    if any(term in text for term in (
        "fraud",
        "never installed",
        "unauthorized charge",
        "did not authorize",
        "didn't authorize",
    )):
        return Category.FRAUD, 0.95, "Possible unauthorized use or payment."

    # 2. Payment taken or attempted, but plan not activated.
    if any(term in text for term in (
        "plan activate nahi",
        "free version",
        "payment failed",
        "payment pending",
        "money deducted",
        "paisa kat",
        "charged but",
        "paid but",
    )):
        return (
            Category.PAYMENT_FAILURE,
            0.90,
            "Possible payment or subscription activation problem.",
        )

    # 3. Explicit refund, reversal, or duplicate-charge request.
   
    # 4. Cancellation.
    if re.search(r"\bcancel\b|\bcancellation\b|\bstop autopay\b", text):
        return (
            Category.CANCELLATION,
            0.90,
            "The customer appears to request cancellation.",
        )

    # 5. Billing documents.
    if any(term in text for term in ("invoice", "gstin", "gst invoice")):
        return Category.BILLING, 0.90, "Billing documentation requested."

    # 6. Product feedback.
    if any(term in text for term in (
        "feature request", "can you add", "please add",
        "add marathi", "new feature",
    )):
        return (
            Category.FEATURE_REQUEST,
            0.90,
            "The customer suggests a product feature.",
        )

    # 7. Account data.
    if any(term in text for term in (
        "order history", "account issue",
        "restore my", "history is empty",
    )):
        return (
            Category.ACCOUNT_ISSUE,
            0.85,
            "Account or order information may be missing.",
        )
    if any(term in text for term in (
            "refund",
            "reverse the charge",
            "reverse",
            "money back",
            "double charge",
            "charged me",
            "charged 249",
        )):
            return (
                Category.REFUND,
                0.85,
                "The customer appears to request a refund or charge investigation.",
            )

    # 8. Technical problems.
    if any(term in text for term in (
        "crash", "crashes", "crashing",
        "does not work", "doesn't work",
        "not working", "closes immediately",
    )):
        return (
            Category.TECHNICAL_ISSUE,
            0.90,
            "The customer reports an app malfunction.",
        )

    # 9. General product questions.
    if any(term in text for term in (
        "does premium", "work offline", "before i subscribe",
    )):
        return (
            Category.GENERAL_QUESTION,
            0.85,
            "The customer asks about product functionality.",
        )

    return (
        Category.OTHER,
        0.40,
        "No classification rule matched confidently.",
    )
