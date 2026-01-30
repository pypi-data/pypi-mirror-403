"""
ThinkHive Python SDK - HTTP Client
Centralized HTTP client with authentication and error handling
"""

import os
import time
import requests
from typing import Optional, Dict, Any, TypeVar, Generic
from dataclasses import dataclass

T = TypeVar('T')

# Retry configuration
MAX_RETRIES = 3
INITIAL_BACKOFF = 0.5  # 500ms
MAX_BACKOFF = 8.0  # 8 seconds
RETRYABLE_STATUS_CODES = {408, 429, 500, 502, 503, 504}

# Global configuration
_config = {
    "api_key": None,
    "agent_id": None,
    "endpoint": "https://thinkhivemind-h25z7pvd3q-uc.a.run.app",
    "timeout": 30,
    "max_retries": MAX_RETRIES,
}


class ThinkHiveApiError(Exception):
    """API error with status code and optional error code"""

    def __init__(self, message: str, status_code: int, code: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code


class ThinkHiveValidationError(Exception):
    """Validation error with field information"""

    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(message)
        self.field = field


def configure(
    api_key: Optional[str] = None,
    agent_id: Optional[str] = None,
    endpoint: Optional[str] = None,
    timeout: Optional[int] = None,
    max_retries: Optional[int] = None,
) -> None:
    """
    Configure the HTTP client

    Args:
        api_key: ThinkHive API key
        agent_id: Agent ID for authentication
        endpoint: API endpoint URL
        timeout: Request timeout in seconds (default: 30)
        max_retries: Maximum number of retries for transient failures (default: 3)
    """
    global _config

    if api_key is not None:
        _config["api_key"] = api_key
    if agent_id is not None:
        _config["agent_id"] = agent_id
    if endpoint is not None:
        _config["endpoint"] = endpoint
    if timeout is not None:
        _config["timeout"] = timeout
    if max_retries is not None:
        _config["max_retries"] = max_retries

    # Try environment variables as fallback
    if not _config["api_key"]:
        _config["api_key"] = os.getenv("THINKHIVE_API_KEY")
    if not _config["agent_id"]:
        _config["agent_id"] = os.getenv("THINKHIVE_AGENT_ID")


def get_config() -> Dict[str, Any]:
    """Get current configuration"""
    return _config.copy()


def _get_headers() -> Dict[str, str]:
    """Get authentication headers"""
    headers = {
        "Content-Type": "application/json",
        "X-SDK-Version": "3.1.0",
        "X-SDK-Language": "python",
    }

    if _config["api_key"]:
        headers["Authorization"] = f"Bearer {_config['api_key']}"
    elif _config["agent_id"]:
        headers["X-Agent-ID"] = _config["agent_id"]

    return headers


def _calculate_backoff(attempt: int, retry_after: Optional[float] = None) -> float:
    """Calculate backoff time for retry attempt"""
    if retry_after is not None:
        return min(retry_after, MAX_BACKOFF)
    backoff = INITIAL_BACKOFF * (2 ** attempt)
    return min(backoff, MAX_BACKOFF)


def api_request(
    method: str,
    path: str,
    body: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None,
    api_version: str = "v1",
    max_retries: Optional[int] = None,
    timeout: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Make an authenticated API request with retry logic

    Args:
        method: HTTP method (GET, POST, PUT, DELETE)
        path: API path (e.g., '/human-review/queue')
        body: Request body for POST/PUT
        params: Query parameters
        api_version: API version (v1 or v3)
        max_retries: Override max retries for this request
        timeout: Override timeout for this request (seconds)

    Returns:
        Response JSON

    Raises:
        ThinkHiveApiError: On API errors after all retries exhausted
    """
    url = f"{_config['endpoint']}/api/{api_version}{path}"
    headers = _get_headers()

    retries = max_retries if max_retries is not None else _config.get("max_retries", MAX_RETRIES)
    request_timeout = timeout if timeout is not None else _config.get("timeout", 30)

    last_exception: Optional[Exception] = None

    for attempt in range(retries + 1):
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=body,
                params=params,
                timeout=request_timeout,
            )

            # Check if response is retryable
            if response.status_code in RETRYABLE_STATUS_CODES and attempt < retries:
                # Get Retry-After header if present (for 429 responses)
                retry_after = None
                if response.status_code == 429:
                    retry_after_header = response.headers.get("Retry-After")
                    if retry_after_header:
                        try:
                            retry_after = float(retry_after_header)
                        except ValueError:
                            pass

                backoff = _calculate_backoff(attempt, retry_after)
                time.sleep(backoff)
                continue

            if not response.ok:
                try:
                    error_data = response.json()
                    message = error_data.get("message") or error_data.get("error") or f"HTTP {response.status_code}"
                    code = error_data.get("code")
                except ValueError:
                    message = response.text or f"HTTP {response.status_code}"
                    code = None

                raise ThinkHiveApiError(message, response.status_code, code)

            return response.json()

        except requests.exceptions.Timeout as e:
            last_exception = e
            if attempt < retries:
                backoff = _calculate_backoff(attempt)
                time.sleep(backoff)
                continue
            raise ThinkHiveApiError(f"Request timed out after {request_timeout}s", 408)

        except requests.exceptions.ConnectionError as e:
            last_exception = e
            if attempt < retries:
                backoff = _calculate_backoff(attempt)
                time.sleep(backoff)
                continue
            raise ThinkHiveApiError(f"Connection failed: {str(e)}", 503)

    # Should not reach here, but just in case
    if last_exception:
        raise ThinkHiveApiError(f"Request failed after {retries} retries: {str(last_exception)}", 500)


def api_request_with_data(
    method: str,
    path: str,
    body: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None,
    api_version: str = "v1",
) -> Any:
    """
    Make an API request and extract data from response wrapper

    Args:
        method: HTTP method
        path: API path
        body: Request body
        params: Query parameters
        api_version: API version

    Returns:
        Response data
    """
    response = api_request(method, path, body, params, api_version)

    if not response.get("success", True):
        error = response.get("error", {})
        raise ThinkHiveApiError(
            error.get("message", "Unknown error"),
            500,
            error.get("code"),
        )

    return response.get("data")


def get(path: str, params: Optional[Dict[str, Any]] = None, api_version: str = "v1") -> Any:
    """Convenience method for GET requests"""
    return api_request_with_data("GET", path, params=params, api_version=api_version)


def post(path: str, body: Optional[Dict[str, Any]] = None, api_version: str = "v1") -> Any:
    """Convenience method for POST requests"""
    return api_request_with_data("POST", path, body=body, api_version=api_version)


def put(path: str, body: Optional[Dict[str, Any]] = None, api_version: str = "v1") -> Any:
    """Convenience method for PUT requests"""
    return api_request_with_data("PUT", path, body=body, api_version=api_version)


def delete(path: str, api_version: str = "v1") -> Any:
    """Convenience method for DELETE requests"""
    return api_request_with_data("DELETE", path, api_version=api_version)


__all__ = [
    "ThinkHiveApiError",
    "ThinkHiveValidationError",
    "configure",
    "get_config",
    "api_request",
    "api_request_with_data",
    "get",
    "post",
    "put",
    "delete",
]
