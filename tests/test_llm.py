
import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from app.llm import generate_model_output


VALID_OUTPUT = {
    "category": "refund",
    "severity": "medium",
    "confidence": 0.9,
    "confidence_reason": "The customer requests a refund.",
    "reply_draft": "Our team will review your request.",
}


@patch("app.llm.genai.Client")
def test_valid_gemini_response(mock_client_class, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    mock_client.models.generate_content.return_value = SimpleNamespace(
        text=json.dumps(VALID_OUTPUT)
    )

    result = generate_model_output({"id": "T-TEST", "subject": "Refund", "body": "Please review my charge"})

    assert result.category.value == "refund"
    assert result.confidence == 0.9
    assert mock_client.models.generate_content.call_count == 1


@patch("app.llm.genai.Client")
def test_invalid_response_retries_once(mock_client_class, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    mock_client.models.generate_content.side_effect = [
        SimpleNamespace(text='{"category": "not_a_category"}'),
        SimpleNamespace(text=json.dumps(VALID_OUTPUT)),
    ]

    result = generate_model_output({"id": "T-TEST", "subject": "Refund", "body": "Please review my charge"})

    assert result.category.value == "refund"
    assert mock_client.models.generate_content.call_count == 2


@patch("app.llm.genai.Client")
def test_invalid_response_fails_after_two_attempts(mock_client_class, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    mock_client.models.generate_content.return_value = SimpleNamespace(
        text='{"category": "not_a_category"}'
    )

    with pytest.raises(ValueError, match="invalid output after two attempts"):
        generate_model_output({"id": "T-TEST", "subject": "Refund", "body": "Please review my charge"})

    assert mock_client.models.generate_content.call_count == 2


def test_missing_api_key_fails_safely(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    with pytest.raises(RuntimeError, match="GEMINI_API_KEY is not configured"):
        generate_model_output({"id": "T-TEST", "subject": "Refund", "body": "Please review my charge"})
