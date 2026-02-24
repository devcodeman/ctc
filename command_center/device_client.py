from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List
import httpx
import time


@dataclass
class TelemetrySnapshot:
    ok: bool
    timestamp: float
    latency_ms: float
    mode: str
    uptime_s: int
    temp_c: float
    voltage_v: float
    current_a: float
    faults: List[str]
    raw: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def fetch_status(ip: str, timeout_s: float = 1.0, endpoint: str = "/status") -> tuple[dict, float]:
    """Fetch raw JSON from device status endpoint and return (payload, latency_ms)."""
    url = f"http://{ip}{endpoint}"
    start = time.perf_counter()
    with httpx.Client(timeout=timeout_s) as client:
        resp = client.get(url)
        resp.raise_for_status()
        payload = resp.json()
    latency_ms = (time.perf_counter() - start) * 1000.0
    return payload, latency_ms


def parse_status(raw: Dict[str, Any], latency_ms: float) -> TelemetrySnapshot:
    """
    Normalize raw device JSON into a stable schema for the UI.
    Tolerates alternate field names while you're integrating with real firmware.
    """
    mode = str(raw.get("mode", raw.get("st", "UNKNOWN")))
    uptime_s = int(raw.get("uptime_s", raw.get("uptime", 0)))

    temp_raw = raw.get("temp_c", raw.get("temperature_c", raw.get("tmp1", 0.0)))
    temp_c = float(temp_raw)

    if "voltage_v" in raw:
        voltage_v = float(raw["voltage_v"])
    elif "vin_mv" in raw:
        voltage_v = float(raw["vin_mv"]) / 1000.0
    else:
        voltage_v = float(raw.get("voltage", 0.0))

    current_a = float(raw.get("current_a", raw.get("current", 0.0)))

    faults_raw = raw.get("faults", [])
    if isinstance(faults_raw, list):
        faults = [str(x) for x in faults_raw]
    elif faults_raw in (None, "", 0, False):
        faults = []
    else:
        faults = [str(faults_raw)]

    return TelemetrySnapshot(
        ok=True,
        timestamp=time.time(),
        latency_ms=latency_ms,
        mode=mode,
        uptime_s=uptime_s,
        temp_c=temp_c,
        voltage_v=voltage_v,
        current_a=current_a,
        faults=faults,
        raw=raw,
    )

def send_command(
    ip: str,
    command: str,
    args: dict | None = None,
    timeout_s: float = 2.0,
    endpoint: str = "/command",
) -> tuple[dict, float]:
    """POST a command to the device and return (response_json, latency_ms)."""
    url = f"http://{ip}{endpoint}"
    payload = {
        "command": command,
        "args": args or {},
    }

    start = time.perf_counter()
    with httpx.Client(timeout=timeout_s) as client:
        resp = client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()
    latency_ms = (time.perf_counter() - start) * 1000.0
    return data, latency_ms