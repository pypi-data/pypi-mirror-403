"""HTTP client and LiteLLM response metadata capture utilities.

This module provides a preconfigured ``httpx.Client`` with a response hook that
captures LiteLLM-specific headers from non-streaming responses:

- ``x-litellm-response-cost`` → stored in ``LAST_LLM_COST``
- ``x-request-id`` → stored in ``LAST_REQUEST_ID``

The hook ignores Server-Sent Events (``text/event-stream``) because LiteLLM only
includes the final cost on the terminal (non-streaming) response.
"""

from __future__ import annotations

import httpx

# The last observed LiteLLM response cost (as a string), if available.
LAST_LLM_COST: str | None = None

# The last observed request ID emitted by LiteLLM, if available.
LAST_REQUEST_ID: str | None = None


def _capture_litellm_headers(response: httpx.Response) -> None:
    """Capture LiteLLM headers from an ``httpx`` response.

    Args:
        response: The HTTP response object received by the client.

    Side Effects:
        Updates the module-level globals ``LAST_LLM_COST`` and
        ``LAST_REQUEST_ID`` when the headers are present on a non-streaming
        response. Streaming responses (``text/event-stream``) are ignored.
    """
    global LAST_LLM_COST, LAST_REQUEST_ID

    # Ignore streaming
    if "text/event-stream" in response.headers.get("content-type", ""):
        return

    cost = response.headers.get("x-litellm-response-cost")
    request_id = response.headers.get("x-request-id")

    # LiteLLM only sets cost on the FINAL response
    if cost is None:
        return

    LAST_LLM_COST = cost
    LAST_REQUEST_ID = request_id


def make_litellm_http_client() -> httpx.Client:
    """Create an ``httpx.Client`` that records LiteLLM metadata via hooks.

    The returned client:
        - Uses a 60-second timeout.
        - Follows redirects.
        - Registers a response hook to capture LiteLLM cost and request ID from
          final (non-streaming) responses.

    Returns:
        httpx.Client: A configured client suitable for calling LiteLLM-backed endpoints.
    """
    return httpx.Client(
        timeout=60.0,
        event_hooks={"response": [_capture_litellm_headers]},
        follow_redirects=True,
    )


__all__ = [
    "make_litellm_http_client",
    "LAST_LLM_COST",
    "LAST_REQUEST_ID",
]
