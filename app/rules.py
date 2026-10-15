
import re


INJECTION_PATTERNS = (
    # Attempts to override earlier instructions.
    r"\b(ignore|disregard|forget|override|bypass)\b"
    r".{0,50}\b(previous|prior|above|earlier|all)\b"
    r".{0,40}\b(instructions|rules|prompts|directives)\b",

    # Common alternative: "ignore all previous instructions".
    r"\b(ignore|disregard)\b.{0,30}\b(all|every)\b"
    r".{0,30}\b(previous|prior|earlier)\b"
    r".{0,30}\b(instructions|rules|prompts)\b",

    # Direct references to an assistant-directed system note or override.
    r"\b(system\s+(note|prompt|override|instruction))\b",
    r"\b(note|instruction|message)\s+to\s+"
    r"(the\s+)?(ai|assistant|automated agent|support assistant|bot|model)\b",

    # Attempts to extract hidden instructions or internal information.
    r"\b(reveal|print|show|output|disclose|repeat|leak)\b"
    r".{0,100}\b(system prompt|your instructions|internal rules)\b",

    # Attempts to force ticket resolution.
    r"\b(mark|set)\b.{0,30}\b(ticket|case|request)\b"
    r".{0,30}\b(resolved|closed)\b",

    # Known VIP/social-engineering wording.
    r"\bverified vip\b",

    # Hinglish/Hindi variants of instruction override attempts.
    r"\b(pichle|pichhli|purane|purani)\b"
    r".{0,40}\b(instructions|nirdesh|hidayat)\b"
    r".{0,40}\b(ignore|disregard|bhool|hatao|maano mat)\b",

    r"\b(instructions|nirdesh|hidayat)\b"
    r".{0,40}\b(ignore|disregard|bhool|hatao)\b",
)


def detect_prompt_injection(subject: str, body: str) -> bool:
    """Flag likely instructions aimed at the assistant."""
    text = f"{subject}\n{body}"

    return any(
        re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        for pattern in INJECTION_PATTERNS
    )
