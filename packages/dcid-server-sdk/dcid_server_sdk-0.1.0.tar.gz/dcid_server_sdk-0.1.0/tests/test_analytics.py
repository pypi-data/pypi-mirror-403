"""Tests for modules/analytics/analytics.py — Analytics."""

import pytest
from unittest.mock import patch

from dcid_server_sdk.modules.analytics.analytics import Analytics
from dcid_server_sdk.modules.analytics.types import (
    StartSessionEvent,
    EndSessionEvent,
)
from dcid_server_sdk.utils.http import HTTPClient
from dcid_server_sdk.utils.logger import NoOpLogger
from tests.conftest import make_mock_response


def _make_analytics():
    http_client = HTTPClient("", logger=NoOpLogger())  # base_url empty for analytics
    return Analytics(http_client, base_url="http://test")


# ---------------------------------------------------------------------------
# start_session
# ---------------------------------------------------------------------------

class TestStartSession:
    @patch("dcid_server_sdk.utils.http.requests.request")
    def test_success_no_params(self, mock_request):
        mock_request.return_value = make_mock_response(
            json_data={
                "success": True,
                "session_id": "sess-123",
                "timestamp": "2024-01-01T00:00:00Z",
                "anonymous_id": "anon-456",
                "linked": False,
            },
            text="ok",
        )
        analytics = _make_analytics()
        result = analytics.start_session()
        assert result.success is True
        assert result.session_id == "sess-123"
        assert result.anonymous_id == "anon-456"

    @patch("dcid_server_sdk.utils.http.requests.request")
    def test_success_with_params(self, mock_request):
        mock_request.return_value = make_mock_response(
            json_data={
                "success": True,
                "session_id": "sess-opt",
                "timestamp": "2024-01-01T00:00:00Z",
                "anonymous_id": "anon-1",
                "linked": True,
            },
            text="ok",
        )
        analytics = _make_analytics()
        result = analytics.start_session(
            StartSessionEvent(
                user_id="user-1",
                anonymous_id="anon-1",
                page_location="https://example.com",
            )
        )
        assert result.session_id == "sess-opt"
        assert result.linked is True

    @patch("dcid_server_sdk.utils.http.requests.request")
    def test_sends_event_fields(self, mock_request):
        mock_request.return_value = make_mock_response(
            json_data={
                "success": True, "session_id": "s", "timestamp": "t",
            },
            text="ok",
        )
        analytics = _make_analytics()
        analytics.start_session(StartSessionEvent(user_id="user-1"))
        call_kwargs = mock_request.call_args
        json_body = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json", {})
        assert json_body["event"] == "start_session"
        assert json_body["event_name"] == "start_session"
        assert json_body["user_id"] == "user-1"

    @patch("dcid_server_sdk.utils.http.requests.request")
    def test_calls_correct_url(self, mock_request):
        mock_request.return_value = make_mock_response(
            json_data={"success": True, "session_id": "s", "timestamp": "t"},
            text="ok",
        )
        analytics = _make_analytics()
        analytics.start_session()
        call_args = mock_request.call_args
        assert "/analytics/sgtm" in call_args[0][1]


# ---------------------------------------------------------------------------
# end_session
# ---------------------------------------------------------------------------

class TestEndSession:
    @patch("dcid_server_sdk.utils.http.requests.request")
    def test_success(self, mock_request):
        mock_request.return_value = make_mock_response(
            json_data={"success": True, "timestamp": "2024-01-01T00:00:00Z"},
            text="ok",
        )
        analytics = _make_analytics()
        result = analytics.end_session(EndSessionEvent(session_id="sess-123"))
        assert result.success is True

    def test_missing_session_id(self):
        analytics = _make_analytics()
        with pytest.raises(ValueError, match="session_id is required"):
            analytics.end_session(EndSessionEvent())

    @patch("dcid_server_sdk.utils.http.requests.request")
    def test_sends_event_fields(self, mock_request):
        mock_request.return_value = make_mock_response(
            json_data={"success": True, "timestamp": "t"},
            text="ok",
        )
        analytics = _make_analytics()
        analytics.end_session(
            EndSessionEvent(
                session_id="sess-123",
                user_id="user-1",
                anonymous_id="anon-1",
                ended_at="2024-01-01T00:00:00Z",
            )
        )
        call_kwargs = mock_request.call_args
        json_body = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json", {})
        assert json_body["event"] == "end_session"
        assert json_body["session_id"] == "sess-123"
        assert json_body["user_id"] == "user-1"
        assert json_body["anonymous_id"] == "anon-1"
        assert json_body["ended_at"] == "2024-01-01T00:00:00Z"

    @patch("dcid_server_sdk.utils.http.requests.request")
    def test_without_optional_fields(self, mock_request):
        mock_request.return_value = make_mock_response(
            json_data={"success": True, "timestamp": "t"},
            text="ok",
        )
        analytics = _make_analytics()
        analytics.end_session(EndSessionEvent(session_id="sess-123"))
        call_kwargs = mock_request.call_args
        json_body = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json", {})
        assert "user_id" not in json_body
        assert "anonymous_id" not in json_body
        assert "ended_at" not in json_body
