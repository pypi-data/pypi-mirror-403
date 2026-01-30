"""HTTP client utilities for DCID Server SDK"""

import requests
from typing import Optional, Dict, Any, Callable
from datetime import datetime
from ..types import (
    DCIDServerSDKError,
    NetworkError,
    AuthenticationError,
    ServerError,
    TokenResponse,
    ErrorContext,
)
from .logger import Logger, NoOpLogger


def sanitize_headers(headers: Dict[str, str]) -> Dict[str, str]:
    """Sanitizes headers by removing sensitive information"""
    sanitized = {}
    sensitive = ["authorization", "x-api-key", "cookie"]

    for key, value in headers.items():
        if key.lower() in sensitive:
            sanitized[key] = "[REDACTED]"
        else:
            sanitized[key] = value

    return sanitized


def is_krakend_error(response: Optional[requests.Response]) -> bool:
    """Checks if error is from KrakenD gateway"""
    if not response:
        return False

    headers = response.headers
    try:
        response_data = response.json() if response.text else {}
    except:
        response_data = {}

    return bool(
        headers.get("x-krakend")
        or headers.get("X-Krakend")
        or headers.get("X-KrakenD")
        or (
            isinstance(response_data.get("error"), str)
            and "api key" in response_data["error"].lower()
        )
        or (
            isinstance(response_data.get("message"), str)
            and "api key" in response_data["message"].lower()
        )
    )


def is_api_key_error(response: Optional[requests.Response]) -> bool:
    """Checks if error is an API-KEY authentication error"""
    if not response or response.status_code != 401:
        return False

    try:
        response_data = response.json() if response.text else {}
    except:
        response_data = {}

    error_message = (
        response_data.get("error", "") or response_data.get("message", "")
    ).lower()

    jwt_token_keywords = [
        "invalid token",
        "invalid signature",
        "token expired",
        "expired token",
        "jwt",
        "bearer",
        "unauthorized",
        "access denied",
        "token invalid",
        "malformed token",
    ]

    is_jwt_token_error = any(keyword in error_message for keyword in jwt_token_keywords)

    if is_jwt_token_error:
        return False

    api_key_keywords = [
        "api key",
        "api-key",
        "invalid api key",
        "missing api key",
        "api key required",
        "unauthorized: missing api key",
        "unauthorized: invalid api key",
    ]

    has_api_key_message = any(keyword in error_message for keyword in api_key_keywords)

    if has_api_key_message:
        return True

    is_krakend = is_krakend_error(response)
    if is_krakend and not is_jwt_token_error:
        return not error_message or has_api_key_message

    return False


def is_backend_connectivity_error(response: Optional[requests.Response]) -> bool:
    """Checks if error is a backend connectivity error"""
    if not response:
        return False

    status = response.status_code
    is_krakend = is_krakend_error(response)

    if not is_krakend:
        return False

    if status not in [500, 502, 503]:
        return False

    try:
        response_data = response.json() if response.text else {}
    except:
        response_data = {}

    error_message = (
        response_data.get("error", "") or response_data.get("message", "")
    ).lower()

    return bool(
        "backend" in error_message
        or "connection" in error_message
        or "unreachable" in error_message
        or "timeout" in error_message
        or "no response" in error_message
    )


def create_error_context(
    response: Optional[requests.Response] = None,
    error: Optional[Exception] = None,
    url: Optional[str] = None,
    method: Optional[str] = None,
) -> ErrorContext:
    """Creates error context for debugging"""
    is_krakend = is_krakend_error(response) if response else False

    return ErrorContext(
        url=url or (response.url if response else None),
        method=method or (response.request.method if response and response.request else None),
        status_code=response.status_code if response else None,
        status_text=response.reason if response else None,
        response_headers=dict(response.headers) if response else None,
        request_headers=(
            sanitize_headers(dict(response.request.headers))
            if response and response.request
            else None
        ),
        timestamp=datetime.utcnow().isoformat(),
        request_id=(
            response.headers.get("x-request-id")
            or response.headers.get("X-Request-ID")
            if response
            else None
        ),
        is_krakend_error=is_krakend,
        error_source=(
            "krakend"
            if is_krakend
            else ("backend" if response else "network")
        ),
    )


class HTTPClient:
    """HTTP client with automatic token refresh and error handling"""

    def __init__(
        self,
        base_url: str,
        timeout: int = 30,
        default_headers: Optional[Dict[str, str]] = None,
        get_auth_token: Optional[Callable[[], Optional[str]]] = None,
        get_refresh_token: Optional[Callable[[], Optional[str]]] = None,
        refresh_token_callback: Optional[Callable[[str], TokenResponse]] = None,
        on_token_refreshed: Optional[Callable[[TokenResponse], None]] = None,
        logger: Optional[Logger] = None,
        enable_request_logging: bool = False,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout / 1000.0  # Convert ms to seconds
        self.default_headers = default_headers or {}
        self.get_auth_token = get_auth_token
        self.get_refresh_token = get_refresh_token
        self.refresh_token_callback = refresh_token_callback
        self.on_token_refreshed = on_token_refreshed
        self.logger = logger or NoOpLogger()
        self.enable_request_logging = enable_request_logging
        self._retry_attempted = False

    def _build_headers(self) -> Dict[str, str]:
        """Build request headers"""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            **self.default_headers,
        }

        if self.get_auth_token:
            token = self.get_auth_token()
            if token:
                headers["Authorization"] = f"Bearer {token}"

        return headers

    def _handle_response_error(
        self, response: requests.Response, url: str, method: str
    ) -> None:
        """Handle response errors"""
        context = create_error_context(response, url=url, method=method)

        try:
            response_data = response.json() if response.text else {}
        except:
            response_data = {}

        message = (
            response_data.get("message")
            or response_data.get("error")
            or "Request failed"
        )

        api_key_error = is_api_key_error(response)
        backend_connectivity_error = is_backend_connectivity_error(response)
        is_krakend = is_krakend_error(response)

        if api_key_error:
            message = "Invalid API-KEY. Please check your X-API-Key header."
            error = AuthenticationError(
                message, True, response.status_code, response_data, context
            )
            self.logger.error("API-KEY authentication failed", {"error": message, "context": context})
            raise error
        elif backend_connectivity_error:
            message = "Backend server is unreachable. Please try again later or contact support."
            error = ServerError(
                message, True, response.status_code, response_data, context
            )
            self.logger.error("Backend connectivity error", {"error": message, "context": context})
            raise error
        elif is_krakend and response.status_code >= 500:
            message = f"Gateway error: {message}"
            error = ServerError(
                message, False, response.status_code, response_data, context
            )
            self.logger.error("Gateway error", {"error": message, "context": context})
            raise error
        elif response.status_code == 401:
            error = AuthenticationError(
                message, False, response.status_code, response_data, context
            )
            self.logger.error("Authentication error", {"error": message, "context": context})
            raise error
        elif response.status_code >= 500:
            error = ServerError(
                message, False, response.status_code, response_data, context
            )
            self.logger.error("Server error", {"error": message, "context": context})
            raise error
        else:
            error = DCIDServerSDKError(message, response.status_code, response_data, context)
            self.logger.error("API request failed", {"error": message, "context": context})
            raise error

    def _request(
        self,
        method: str,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Make HTTP request"""
        url = f"{self.base_url}{path}" if self.base_url else path
        headers = self._build_headers()

        if self.enable_request_logging:
            self.logger.debug(
                "Outgoing API request",
                {
                    "method": method.upper(),
                    "url": url,
                    "headers": sanitize_headers(headers),
                    "data": json,
                },
            )

        try:
            response = requests.request(
                method,
                url,
                json=json,
                params=params,
                headers=headers,
                timeout=self.timeout,
            )

            if response.status_code >= 400:
                # Check if we should attempt token refresh
                if (
                    response.status_code == 401
                    and not is_api_key_error(response)
                    and not self._retry_attempted
                    and "/auth/refresh-token" not in path
                    and self.get_refresh_token
                    and self.refresh_token_callback
                    and self.on_token_refreshed
                ):
                    self._retry_attempted = True
                    self.logger.debug("Token expired, attempting automatic refresh", {"url": url})

                    try:
                        refresh_token = self.get_refresh_token()
                        if not refresh_token:
                            raise ValueError("No refresh token available")

                        # Refresh token
                        tokens = self.refresh_token_callback(refresh_token)
                        self.on_token_refreshed(tokens)

                        self.logger.debug("Token refreshed successfully, retrying request", {"url": url})

                        # Retry with new token
                        headers["Authorization"] = f"Bearer {tokens.access_token}"
                        response = requests.request(
                            method,
                            url,
                            json=json,
                            params=params,
                            headers=headers,
                            timeout=self.timeout,
                        )

                        self._retry_attempted = False

                        if response.status_code >= 400:
                            self._handle_response_error(response, url, method)
                    except Exception as e:
                        self._retry_attempted = False
                        self.logger.error("Token refresh failed", {"error": str(e), "url": url})
                        raise
                else:
                    self._handle_response_error(response, url, method)

            if self.enable_request_logging:
                self.logger.debug(
                    "API request successful",
                    {"status": response.status_code, "url": url, "method": method.upper()},
                )

            return response.json() if response.text else {}

        except requests.exceptions.Timeout:
            context = create_error_context(url=url, method=method)
            error = NetworkError(
                "Request timeout - server took too long to respond", "ETIMEDOUT", context
            )
            self.logger.error("Network error", {"error": error.message, "context": context})
            raise error
        except requests.exceptions.ConnectionError as e:
            context = create_error_context(url=url, method=method)
            error = NetworkError(
                "Connection refused - server may be down or unreachable",
                "ECONNREFUSED",
                context,
            )
            self.logger.error("Network error", {"error": error.message, "context": context})
            raise error
        except requests.exceptions.RequestException as e:
            context = create_error_context(url=url, method=method)
            error = NetworkError(
                f"No response received from server: {str(e)}", None, context
            )
            self.logger.error("Network error", {"error": error.message, "context": context})
            raise error

    def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Make GET request"""
        return self._request("GET", path, params=params)

    def post(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Make POST request"""
        return self._request("POST", path, json=json, params=params)

    def put(self, path: str, json: Optional[Dict[str, Any]] = None) -> Any:
        """Make PUT request"""
        return self._request("PUT", path, json=json)

    def delete(self, path: str) -> Any:
        """Make DELETE request"""
        return self._request("DELETE", path)


def create_http_client(
    base_url: str,
    timeout: int = 30000,
    default_headers: Optional[Dict[str, str]] = None,
    get_auth_token: Optional[Callable[[], Optional[str]]] = None,
    get_refresh_token: Optional[Callable[[], Optional[str]]] = None,
    refresh_token_callback: Optional[Callable[[str], TokenResponse]] = None,
    on_token_refreshed: Optional[Callable[[TokenResponse], None]] = None,
    logger: Optional[Logger] = None,
    enable_request_logging: bool = False,
) -> HTTPClient:
    """Create HTTP client instance"""
    return HTTPClient(
        base_url,
        timeout,
        default_headers,
        get_auth_token,
        get_refresh_token,
        refresh_token_callback,
        on_token_refreshed,
        logger,
        enable_request_logging,
    )
