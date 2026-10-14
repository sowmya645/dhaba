
from app.schemas import Category, RefundDecision


def decide_refund(
    category: Category,
    injection_detected: bool,
    payment_verified: bool,
    refund_policy_defined: bool = False,
    confidence: float = 0.0,
) -> RefundDecision:
    """
    Make a conservative refund decision using trusted inputs.

    This function does not issue a payment or execute a refund.
    """
    if injection_detected:
        return RefundDecision(
            eligible=False,
            amount_inr=0,
            reason="Possible prompt injection detected; manual review required.",
            requires_human_review=True,
        )

    if category == Category.FRAUD:
        return RefundDecision(
            eligible=False,
            amount_inr=0,
            reason="Possible fraud requires investigation before any refund decision.",
            requires_human_review=True,
        )

    if category != Category.REFUND:
        return RefundDecision(
            eligible=False,
            amount_inr=0,
            reason="No refund request identified.",
            requires_human_review=False,
        )

    if not payment_verified:
        return RefundDecision(
            eligible=False,
            amount_inr=0,
            reason="Payment is not verified; refund eligibility cannot be established.",
            requires_human_review=True,
        )

    if confidence < 0.80:
        return RefundDecision(
            eligible=False,
            amount_inr=0,
            reason="Classification confidence is too low for an automated decision.",
            requires_human_review=True,
        )

    if not refund_policy_defined:
        return RefundDecision(
            eligible=False,
            amount_inr=0,
            reason="Refund eligibility rules are not defined; manual review required.",
            requires_human_review=True,
        )

    # Do not invent eligibility or an amount when no explicit policy is supplied.
    return RefundDecision(
        eligible=False,
        amount_inr=0,
        reason="No implemented rule authorizes automatic refund approval.",
        requires_human_review=True,
    )
