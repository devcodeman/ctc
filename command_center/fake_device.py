from __future__ import annotations

import random
import time
from fastapi import FastAPI
from typing import Any
from pydantic import BaseModel
import uvicorn

app = FastAPI()
START = time.time()

# Operating mode simulation
_modes = ["BOOT", "IDLE", "RUN", "RUN", "RUN", "RUN"]
_mode_idx = 0

# State variables so telemetry evolves over time (not pure random every sample)
_temp_c = 35.0
_vin_mv = 12100
_current_a = 1.50

# Fault latches / timers to make faults persist for multiple samples
_fault_timers = {
    "TEMP_WARN": 0,
    "TEMP_HIGH": 0,
    "VOLT_LOW": 0,
    "VOLT_HIGH": 0,
    "CURRENT_HIGH": 0,
    "COMM_RETRY": 0,
    "SENSOR_GLITCH": 0,
    "FAN_WARN": 0,
}

# Optional: inject periodic bursts so you can reliably test UI
_sample_count = 0


def _tick_fault_timers():
    """Decay active fault timers by one sample."""
    for key in _fault_timers:
        if _fault_timers[key] > 0:
            _fault_timers[key] -= 1


def _set_fault(name: str, duration_samples: int):
    _fault_timers[name] = max(_fault_timers[name], duration_samples)


def _active_faults() -> list[str]:
    return [name for name, remaining in _fault_timers.items() if remaining > 0]

class CommandRequest(BaseModel):
    command: str
    args: dict[str, Any] = {}

@app.get("/status")
def status():
    global _mode_idx, _temp_c, _vin_mv, _current_a, _sample_count

    _sample_count += 1
    _mode_idx = (_mode_idx + 1) % len(_modes)
    mode = _modes[_mode_idx]

    # --- Telemetry evolution (random walk / drift) ---
    # Temperature drifts slowly with noise
    _temp_c += random.uniform(-0.25, 0.35)

    # Voltage bounces slightly around nominal
    _vin_mv += random.randint(-35, 35)

    # Current changes more in RUN than IDLE/BOOT
    if mode == "RUN":
        _current_a += random.uniform(-0.08, 0.12)
    elif mode == "IDLE":
        _current_a += random.uniform(-0.03, 0.03)
    else:  # BOOT
        _current_a += random.uniform(-0.05, 0.07)

    # Clamp to sane-ish ranges
    _temp_c = max(25.0, min(_temp_c, 95.0))
    _vin_mv = max(10800, min(_vin_mv, 13250))
    _current_a = max(0.2, min(_current_a, 4.5))

    # --- Inject occasional disturbances to force faults ---
    # Every ~25 samples, bump temperature upward briefly
    if _sample_count % 25 == 0:
        _temp_c += random.uniform(4.0, 8.0)

    # Every ~40 samples, create a voltage dip
    if _sample_count % 40 == 0:
        _vin_mv -= random.randint(300, 700)

    # Every ~55 samples, create a current spike
    if _sample_count % 55 == 0:
        _current_a += random.uniform(0.8, 1.8)

    # Clamp again after disturbances
    _temp_c = max(25.0, min(_temp_c, 95.0))
    _vin_mv = max(9800, min(_vin_mv, 13500))
    _current_a = max(0.2, min(_current_a, 5.5))

    # --- Fault timer decay ---
    _tick_fault_timers()

    # --- Threshold-based faults (more deterministic and testable) ---
    if _temp_c >= 70.0:
        _set_fault("TEMP_HIGH", duration_samples=8)
    elif _temp_c >= 55.0:
        _set_fault("TEMP_WARN", duration_samples=6)

    if _vin_mv <= 11200:
        _set_fault("VOLT_LOW", duration_samples=6)
    elif _vin_mv >= 12800:
        _set_fault("VOLT_HIGH", duration_samples=5)

    if _current_a >= 3.2:
        _set_fault("CURRENT_HIGH", duration_samples=6)

    # --- Random transient faults (simulate real-world weirdness) ---
    if random.random() < 0.08:  # was too rare before
        _set_fault("COMM_RETRY", duration_samples=random.randint(2, 5))

    if random.random() < 0.04:
        _set_fault("SENSOR_GLITCH", duration_samples=random.randint(1, 3))

    if random.random() < 0.03 and mode == "RUN":
        _set_fault("FAN_WARN", duration_samples=random.randint(3, 7))

    # Optional synthetic error code for compatibility testing
    faults = _active_faults()

    # Simulate a bit of noisy endpoint latency if you want (uncomment to test latency trends)
    time.sleep(random.uniform(0.005, 0.03))

    return {
        "st": mode,                              # alternate field name for your parser
        "uptime_s": int(time.time() - START),
        "tmp1": round(_temp_c, 2),              # alternate temp field
        "vin_mv": int(_vin_mv),                 # millivolts
        "current_a": round(_current_a, 3),
        "faults": faults,
        # Extra fields (safe for parser, useful for future expansion)
        "sample_count": _sample_count,
    }

@app.post("/command")
def command(req: CommandRequest):
    global _mode_idx, _temp_c, _vin_mv, _current_a

    cmd = req.command.strip().lower()
    args = req.args or {}

    if cmd == "reset":
        _temp_c = 35.0
        _vin_mv = 12100
        _current_a = 1.50
        for k in _fault_timers:
            _fault_timers[k] = 0
        return {
            "ok": True,
            "message": "Device reset simulated",
            "command": req.command,
            "args": args,
        }

    if cmd == "clear_faults":
        for k in _fault_timers:
            _fault_timers[k] = 0
        return {
            "ok": True,
            "message": "Faults cleared",
            "command": req.command,
            "args": args,
        }

    if cmd == "set_mode":
        mode = str(args.get("mode", "")).upper()
        if mode not in {"BOOT", "IDLE", "RUN"}:
            return {
                "ok": False,
                "message": "Invalid mode",
                "valid_modes": ["BOOT", "IDLE", "RUN"],
                "command": req.command,
                "args": args,
            }
        # bias the mode cycle so next status reflects chosen mode quickly
        if mode == "BOOT":
            _mode_idx = 0
        elif mode == "IDLE":
            _mode_idx = 1
        else:
            _mode_idx = 2
        return {
            "ok": True,
            "message": f"Mode set to {mode}",
            "command": req.command,
            "args": args,
        }

    if cmd == "inject_fault":
        fault_name = str(args.get("fault", "COMM_RETRY")).upper()
        duration = int(args.get("duration", 5))
        if fault_name not in _fault_timers:
            return {
                "ok": False,
                "message": "Unknown fault name",
                "known_faults": list(_fault_timers.keys()),
                "command": req.command,
                "args": args,
            }
        _set_fault(fault_name, max(1, min(duration, 60)))
        return {
            "ok": True,
            "message": f"Injected fault {fault_name} for {duration} samples",
            "command": req.command,
            "args": args,
        }

    return {
        "ok": False,
        "message": "Unknown command",
        "command": req.command,
        "args": args,
        "supported_commands": ["reset", "clear_faults", "set_mode", "inject_fault"],
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)