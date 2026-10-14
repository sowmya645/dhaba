
import re


INJECTION_PATTERNS = (
    r"\bignore\s+(your\s+)?(previous|prior|all)\s+"
    r"(instructions|rules|prompts)\b",
    r"\bsystem\s+(note|prompt|override)\b",
    r"\bfor the (automated agent|support assistant|bot|model)\b",
    r"\b(reveal|print|show)\b.{0,100}\b"
    r"(system prompt|your instructions|internal rules)\b",
    r"\bverified vip\b",
    r"\bmark this ticket resolved\b",
    r"\bapprove\b.{0,80}\bfull refund\b",
)


def detect_prompt_injection(subject: str, body: str) -> bool:
    """Flag suspicious instructions aimed at the assistant."""
    text = f"{subject}\n{body}"

    return any(
        re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        for pattern in INJECTION_PATTERNS
    )
