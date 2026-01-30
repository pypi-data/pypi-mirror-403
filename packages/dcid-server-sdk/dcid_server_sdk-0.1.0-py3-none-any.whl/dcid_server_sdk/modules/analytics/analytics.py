"""Analytics for tracking user events"""

from typing import Optional
from .types import (
    StartSessionEvent,
    StartSessionResponse,
    EndSessionEvent,
    AnalyticsEventResponse,
)
from ...utils.http import HTTPClient


class Analytics:
    """Analytics module for tracking user events"""

    def __init__(self, http_client: HTTPClient, base_url: str):
        self.http_client = http_client
        self.base_url = base_url

    def start_session(
        self, params: Optional[StartSessionEvent] = None
    ) -> StartSessionResponse:
        """
        Start session - Creates a new session and returns session_id and anonymous_id

        Args:
            params: Start session event data

        Returns:
            StartSessionResponse with session_id, anonymous_id, and linked status
        """
        payload = {
            "event": "start_session",
            "event_name": "start_session",
        }

        if params:
            if params.user_id:
                payload["user_id"] = params.user_id
            if params.anonymous_id:
                payload["anonymous_id"] = params.anonymous_id
            if params.page_location:
                payload["page_location"] = params.page_location
            if params.session_id:
                payload["session_id"] = params.session_id

        response = self.http_client.post(
            f"{self.base_url}/analytics/sgtm", json=payload
        )

        return StartSessionResponse(
            success=response["success"],
            session_id=response["session_id"],
            timestamp=response["timestamp"],
            anonymous_id=response.get("anonymous_id"),
            linked=response.get("linked"),
        )

    def end_session(self, event: EndSessionEvent) -> AnalyticsEventResponse:
        """
        End session - Marks a session as ended

        Args:
            event: End session event data

        Returns:
            AnalyticsEventResponse with success status

        Raises:
            ValueError: If session_id is not provided
        """
        if not event.session_id:
            raise ValueError("session_id is required for end_session event")

        payload = {
            "event": "end_session",
            "event_name": "end_session",
            "session_id": event.session_id,
        }

        if event.user_id:
            payload["user_id"] = event.user_id
        if event.anonymous_id:
            payload["anonymous_id"] = event.anonymous_id
        if event.ended_at:
            payload["ended_at"] = event.ended_at

        response = self.http_client.post(
            f"{self.base_url}/analytics/sgtm", json=payload
        )

        return AnalyticsEventResponse(
            success=response["success"], timestamp=response["timestamp"]
        )
