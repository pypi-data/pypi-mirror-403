"""
API Integration Smoke Test Library
----------------------------------
Performs fast, single-probe health checks on external APIs.

Designed for:
- CI/CD pipelines
- Monitoring dashboards
- Automation workflows
- Fail-fast integration checks

This library intentionally focuses on SAFE, single-request probes.
It is NOT a testing framework or request builder.
"""

import time
import logging
from datetime import datetime, timezone
from typing import Optional, Literal

import requests
from requests.exceptions import (
    Timeout,
    ConnectionError,
    SSLError,
    RequestException
)

# --------------------------------------------------------------------------
# Logging
# --------------------------------------------------------------------------

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------
# Types
# --------------------------------------------------------------------------

HttpMethod = Literal["GET", "POST", "HEAD", "PUT", "DELETE", "OPTIONS"]

# --------------------------------------------------------------------------
# HTTP status code classification
# --------------------------------------------------------------------------

STATUS_CODE_MAP = {
    401: {
        "category": "AUTH_ERROR",
        "message": "Unauthorized",
        "hint": "Token is invalid or expired. Check Authorization header.",
        "action": "REFRESH_TOKEN",
    },
    403: {
        "category": "PERMISSION_ERROR",
        "message": "Forbidden",
        "hint": "Valid credentials, but insufficient permissions.",
        "action": "CHECK_PERMISSIONS",
    },
    404: {
        "category": "ENDPOINT_ERROR",
        "message": "Not Found",
        "hint": "The endpoint URL may be incorrect.",
        "action": "FIX_URL",
    },
    429: {
        "category": "RATE_LIMITED",
        "message": "Too Many Requests",
        "hint": "API rate limit exceeded.",
        "action": "RETRY_LATER",
    },
}

# --------------------------------------------------------------------------
# Public API
# --------------------------------------------------------------------------

def check_integration(
    url: str,
    method: HttpMethod = "GET",
    headers: Optional[dict] = None,
    timeout: float = 5.0,
    session: Optional[requests.Session] = None,
) -> dict:
    """
    Perform a lightweight smoke test on an external API endpoint.

    A single HTTP request is sent to verify:
    - network reachability
    - credential validity
    - endpoint correctness

    Args:
        url: API endpoint to probe.
        method: HTTP method (default: GET).
        headers: Optional HTTP headers (e.g., Authorization).
        timeout: Request timeout in seconds.
        session: Optional requests.Session for connection pooling.

    Returns:
        A standardized dictionary with health check results.
    """

    # ----------------------------------------------------------------------
    # Safety guard
    # ----------------------------------------------------------------------
    if method not in ("GET", "HEAD"):
        logger.warning(
            "Non-GET/HEAD method used for smoke test. "
            "Ensure the endpoint is non-destructive."
        )

    start_time = time.perf_counter()
    timestamp = datetime.now(timezone.utc).isoformat()

    requester = session if session else requests

    # Ensure headers exist and add a clear User-Agent
    final_headers = headers.copy() if headers else {}
    final_headers.setdefault("User-Agent", "integration-smoke-test/0.1.0")

    result = {
        "ok": False,
        "category": "UNKNOWN_ERROR",
        "status_code": None,
        "message": "",
        "hint": "",
        "action": "INVESTIGATE",
        "latency_ms": 0,
        "url": url,
        "method": method,
        "timestamp": timestamp,
    }

    try:
        logger.debug("Probing %s %s", method, url)

        response = requester.request(
            method=method,
            url=url,
            headers=final_headers,
            timeout=timeout,
            allow_redirects=True,
        )

        result["latency_ms"] = int((time.perf_counter() - start_time) * 1000)
        result["status_code"] = response.status_code

        # -------------------- SUCCESS --------------------
        if 200 <= response.status_code < 300:
            result.update({
                "ok": True,
                "category": "OK",
                "message": "Integration healthy",
                "hint": "No action required",
                "action": "NONE",
            })
            return result

        # -------------------- SPECIFIC ERRORS --------------------
        if response.status_code in STATUS_CODE_MAP:
            result.update(STATUS_CODE_MAP[response.status_code])
            return result

        # -------------------- GENERIC RANGES --------------------
        if 500 <= response.status_code < 600:
            result.update({
                "category": "SERVER_ERROR",
                "message": f"Server Error ({response.status_code})",
                "hint": "The API server is experiencing issues.",
                "action": "RETRY_LATER",
            })
        elif 400 <= response.status_code < 500:
            result.update({
                "category": "CLIENT_ERROR",
                "message": f"Client Error ({response.status_code})",
                "hint": "The request is malformed or invalid.",
                "action": "FIX_REQUEST",
            })
        else:
            result.update({
                "message": f"Unexpected status code: {response.status_code}",
                "hint": "Received an unusual HTTP response.",
            })

    except Timeout:
        result["latency_ms"] = int((time.perf_counter() - start_time) * 1000)
        result.update({
            "category": "TIMEOUT",
            "message": f"Request timed out after {timeout}s",
            "hint": "The API is slow or unreachable.",
            "action": "RETRY_LATER",
        })

    except SSLError:
        result["latency_ms"] = int((time.perf_counter() - start_time) * 1000)
        result.update({
            "category": "SSL_ERROR",
            "message": "SSL certificate validation failed",
            "hint": "Check SSL certificates or CA bundle.",
            "action": "CHECK_SSL",
        })

    except ConnectionError:
        result["latency_ms"] = int((time.perf_counter() - start_time) * 1000)
        result.update({
            "category": "NETWORK_ERROR",
            "message": "Failed to establish connection",
            "hint": "DNS resolution failed or network is down.",
            "action": "CHECK_NETWORK",
        })

    except RequestException as e:
        result["latency_ms"] = int((time.perf_counter() - start_time) * 1000)
        result.update({
            "category": "UNKNOWN_ERROR",
            "message": f"Request failed: {type(e).__name__}",
            "hint": "An unexpected HTTP error occurred.",
            "action": "INVESTIGATE",
        })

    except Exception as e:
        result["latency_ms"] = int((time.perf_counter() - start_time) * 1000)
        result.update({
            "category": "SYSTEM_ERROR",
            "message": f"Internal error: {str(e)}",
            "hint": "The smoke test library encountered an internal failure.",
            "action": "DEBUG_LIBRARY",
        })

    return result
