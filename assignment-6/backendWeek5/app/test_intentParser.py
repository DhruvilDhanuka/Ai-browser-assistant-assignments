# test_intent_parser.py
import json
import pytest
from unittest.mock import patch, MagicMock

from app.intentParser import parse_intent


def _mock_response(payload: dict):
    """Builds a fake Gemini response object with .text set to the given JSON payload."""
    mock_response = MagicMock()
    mock_response.text = json.dumps(payload)
    return mock_response


@pytest.mark.parametrize("command,expected_action,expected_url", [
    ("go to amazon.com",                       "navigate",   "amazon.com"),
    ("fill out the signup form",                "fill_form",  None),
    ("email the report to john@example.com",    "email",      None),
    ("summarize this article",                  "summarize",  None),
    ("click the login button",                  "click",      None),
])
@patch("app.intentParser.client")
def test_action_types(mock_client, command, expected_action, expected_url):
    mock_client.models.generate_content.return_value = _mock_response({
        "needs_clarification": False,
        "clarification_question": None,
        "actions": [
            {"action": expected_action, "target_url": expected_url, "data": {}}
        ],
        "steps": ["step 1"],
    })

    result = parse_intent(command)

    assert result["needs_clarification"] is False
    assert result["actions"][0]["action"] == expected_action
    assert result["actions"][0]["target_url"] == expected_url
    assert mock_client.models.generate_content.called
