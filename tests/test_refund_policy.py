
from app.refundpolicy import decide_refund
from app.schemas import Category


def test_injection_always_requires_human_review():
    result = decide_refund(
        category=Category.REFUND,
        injection_detected=True,
        payment_verified=True,
        refund_policy_defined=True,
        confidence=0.99,
    )

    assert result.eligible is False
    assert result.amount_inr == 0
    assert result.requires_human_review is True


def test_unverified_payment_requires_review():
    result = decide_refund(
        category=Category.REFUND,
        injection_detected=False,
        payment_verified=False,
        confidence=0.99,
    )

    assert result.eligible is False
    assert result.requires_human_review is True


def test_undefined_policy_never_approves_refund():
    result = decide_refund(
        category=Category.REFUND,
        injection_detected=False,
        payment_verified=True,
        confidence=0.99,
    )

    assert result.eligible is False
    assert result.amount_inr == 0
    assert result.requires_human_review is True


def test_non_refund_category_does_not_request_refund():
    result = decide_refund(
        category=Category.ACCOUNT_ISSUE,
        injection_detected=False,
        payment_verified=False,
    )

    assert result.eligible is False
    assert result.amount_inr == 0
    assert result.requires_human_review is False
