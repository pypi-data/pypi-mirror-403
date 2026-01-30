"""Analytics event types and payloads"""

from typing import Optional, Any, Dict
from dataclasses import dataclass


@dataclass
class BaseAnalyticsEvent:
    """Base analytics event payload"""

    session_id: Optional[str] = None
    user_id: Optional[str] = None
    anonymous_id: Optional[str] = None
    page_location: Optional[str] = None


@dataclass
class StartSessionEvent(BaseAnalyticsEvent):
    """Start session event payload"""

    pass


@dataclass
class StartSessionResponse:
    """Start session response"""

    success: bool
    session_id: str
    timestamp: str
    anonymous_id: Optional[str] = None
    linked: Optional[bool] = None


@dataclass
class EndSessionEvent(BaseAnalyticsEvent):
    """End session event payload"""

    event: str = "end_session"
    event_name: str = "end_session"
    ended_at: Optional[str] = None


@dataclass
class AnalyticsEventResponse:
    """Generic analytics event response"""

    success: bool
    timestamp: str
