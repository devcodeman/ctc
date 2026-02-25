import time
from typing import Any

import httpx


DEFAULT_TIMEOUT_S = 2.0


def _build_url(address: str, endpoint: str) -> str:
    """Build an HTTP URL from device address and endpoint.

    address examples:
      - 127.0.0.1:8001
      - 192.168.1.50:8080
    endpoint examples:
      - /status
      - /command
    """
    endpoint = endpoint if endpoint.startswith("/") else f"/{endpoint}"
    return f"http://{address}{endpoint}"


def fetch_status(
    address: str,
    timeout_s: float = DEFAULT_TIMEOUT_S,
    endpoint: str = "/status",
) -> tuple[dict[str, Any], float]:
    """Fetch device status and return (raw_status_dict, latency_ms).

    Assumption (by product requirement): /status returns a JSON object (dict).
    """
    url = _build_url(address, endpoint)

    start = time.perf_counter()
    with httpx.Client(timeout=timeout_s) as client:
        response = client.get(url)
        response.raise_for_status()
        data = response.json()
    latency_ms = (time.perf_counter() - start) * 1000.0

    # Requirement says /status must be a dictionary for supported devices.
    # We still keep this defensive check to fail fast with a clear error.
    if not isinstance(data, dict):
        raise TypeError(f"/status response must be a JSON object, got {type(data).__name__}")

    return data, latency_ms


def send_command(
    address: str,
    command: str,
    args: dict[str, Any] | None = None,
    timeout_s: float = DEFAULT_TIMEOUT_S,
    endpoint: str = "/command",
) -> tuple[dict[str, Any], float]:
    """POST a command to the device and return (raw_response_dict, latency_ms)."""
    url = _build_url(address, endpoint)
    payload = {
        "command": command,
        "args": args or {},
    }

    start = time.perf_counter()
    with httpx.Client(timeout=timeout_s) as client:
        response = client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
    latency_ms = (time.perf_counter() - start) * 1000.0

    if not isinstance(data, dict):
        raise TypeError(f"/command response must be a JSON object, got {type(data).__name__}")

    return data, latency_ms