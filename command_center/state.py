from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path
from datetime import datetime, timezone

import reflex as rx

from .device_client import fetch_status, parse_status, send_command


class TelemetryState(rx.State):
    # ---- controls ----
    device_host: str = "127.0.0.1" # default to simulator
    device_port: str = "8080" # default to simulator
    poll_interval_s: str = "1.0" # keep as string for select compatibility
    running: bool = False
    poll_session_id: int = 0

    # ---- connection ----
    connected: bool = False
    last_error: str = ""
    last_seen_epoch: float = 0.0
    latency_ms: float = 0.0
    consecutive_failures: int = 0

    # ---- telemetry ----
    mode: str = "UNKNOWN"
    uptime_s: int = 0
    temp_c: float = 0.0
    voltage_v: float = 0.0
    current_a: float = 0.0
    faults: list[str] = []

    # ---- trend history ----
    history: list[dict] = []
    history_limit: int = 50  # ~5 minutes at 1 Hz
    sample_index: int = 0

    # ---- debug/logging ----
    raw_json: str = "{}"
    event_log: list[str] = []

    # ---- file logging ----
    log_to_file: bool = False
    log_file_path: str = ""
    log_samples_written: int = 0
    last_export_json_path: str = ""

    # ---- command state ----
    command_input: str = ""
    command_args_json: str = "{}"
    command_busy: bool = False
    last_command_name: str = ""
    last_command_status: str = "Idle"
    last_command_response: str = ""
    last_command_latency_ms: float = 0.0

    @rx.var
    def connection_label(self) -> str:
        if self.running and self.connected:
            return "Connected"
        if self.running and not self.connected:
            return "Reconnecting"
        return "Disconnected"

    @rx.var
    def fault_count(self) -> int:
        return len(self.faults)

    @rx.var
    def last_seen_text(self) -> str:
        if self.last_seen_epoch <= 0:
            return "Never"
        delta = max(0, int(time.time() - self.last_seen_epoch))
        return f"{delta}s ago"

    @rx.var
    def poll_interval_float(self) -> float:
        try:
            return max(0.1, float(self.poll_interval_s))
        except Exception:
            return 1.0

    @rx.var
    def history_points(self) -> int:
        return len(self.history)

    @rx.var
    def latency_ms_display(self) -> float:
        return round(self.latency_ms, 2)

    @rx.var
    def can_export_json(self) -> bool:
        return self.log_file_path != ""

    @rx.var
    def logging_status_label(self) -> str:
        return "Logging ON" if self.log_to_file else "Logging OFF"
    
    def cmd_reset(self):
        if self.command_busy:
            return
        return TelemetryState.send_command_background("reset", "{}")

    def cmd_clear_faults(self):
        if self.command_busy:
            return
        return TelemetryState.send_command_background("clear_faults", "{}")

    def cmd_set_mode_idle(self):
        if self.command_busy:
            return
        return TelemetryState.send_command_background("set_mode", '{"mode":"IDLE"}')

    def cmd_set_mode_run(self):
        if self.command_busy:
            return
        return TelemetryState.send_command_background("set_mode", '{"mode":"RUN"}')

    def set_device_host(self, value: str):
        self.device_host = value.strip()

    def set_device_port(self, value: str):
        v = value.strip()
        # Allow blank while typing
        if v == "":
            self.device_port = v
            return

        # Simple numeric guard
        if v.isdigit():
            try:
                port = int(v)
                if 1 <= port <= 65535:
                    self.device_port = v
                    return
            except ValueError:
                pass

        # Keep previous value and surface a user-friendly error
        self.last_error = "Port must be a number between 1 and 65535"

    def set_poll_interval(self, value: str):
        self.poll_interval_s = value

    def set_command_input(self, value: str):
        self.command_input = value.strip()

    def set_command_args_json(self, value: str):
        self.command_args_json = value

    @rx.var
    def device_address(self) -> str:
        host = self.device_host.strip()
        port = self.device_port.strip()
        if port:
            return f"{host}:{port}"
        return host

    def send_custom_command(self):
        """Send command from UI input fields."""
        if self.command_busy:
            return
        cmd = self.command_input.strip()
        if not cmd:
            self.last_command_status = "Error"
            self.last_command_response = "Command name is required"
            return
        return TelemetryState._send_command_background(cmd, self.command_args_json)

    def connect(self):
        if self.running:
            return
        self.running = True
        self.last_error = ""
        self.history = []
        self.sample_index = 0
        self.poll_session_id += 1
        self.event_log.append(f"Starting poll loop for {self.device_address}")
        if len(self.event_log) > 200:
            self.event_log = self.event_log[-200:]
        return TelemetryState.poll_loop

    def disconnect(self):
        self.running = False
        self.connected = False
        self.event_log.append("Polling stopped by operator")
        if len(self.event_log) > 200:
            self.event_log = self.event_log[-200:]

    def clear_log(self):
        self.event_log = []

    def toggle_file_logging(self):
        """Toggle background telemetry file logging on/off."""
        # Turning ON
        if not self.log_to_file:
            logs_dir = Path("logs")
            logs_dir.mkdir(parents=True, exist_ok=True)

            # Filename example: tlm_20260223T193012Z_127_0_0_1_8001.jsonl
            ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            safe_ip = self.device_address.replace(":", "_").replace(".", "_")
            file_path = logs_dir / f"tlm_{ts}_{safe_ip}.jsonl"

            self.log_file_path = str(file_path)
            self.log_samples_written = 0
            self.log_to_file = True
            self.event_log.append(f"File logging enabled: {self.log_file_path}")
        else:
            # Turning OFF
            self.log_to_file = False
            self.event_log.append("File logging disabled")

        if len(self.event_log) > 200:
            self.event_log = self.event_log[-200:]

    def _append_jsonl_record(self, record: dict):
        """Append one JSON object as a line to the current log file."""
        if not self.log_to_file or not self.log_file_path:
            return

        path = Path(self.log_file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, separators=(",", ":")) + "\n")

    def export_log_to_json(self):
        """Convert current session JSONL log file into a nominal JSON file (array payload)."""
        if not self.log_file_path:
            self.event_log.append("Export skipped: no log file path available")
            if len(self.event_log) > 200:
                self.event_log = self.event_log[-200:]
            return

        src = Path(self.log_file_path)
        if not src.exists():
            self.event_log.append(f"Export failed: log file not found: {src}")
            if len(self.event_log) > 200:
                self.event_log = self.event_log[-200:]
            return

        try:
            samples: list[dict] = []
            with src.open("r", encoding="utf-8") as f:
                for line_no, line in enumerate(f, start=1):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        samples.append(json.loads(line))
                    except json.JSONDecodeError as e:
                        # Skip malformed line but log it
                        self.event_log.append(f"Export warning: bad JSONL line {line_no}: {e}")
                        if len(self.event_log) > 200:
                            self.event_log = self.event_log[-200:]

            export_obj = {
                "exported_at_utc": datetime.now(timezone.utc).isoformat(),
                "source_jsonl": str(src),
                "sample_count": len(samples),
                "device_address": self.device_address,
                "samples": samples,
            }

            dst = src.with_suffix(".json")
            with dst.open("w", encoding="utf-8") as f:
                json.dump(export_obj, f, indent=2)

            self.last_export_json_path = str(dst)
            self.event_log.append(f"Exported JSON: {self.last_export_json_path} ({len(samples)} samples)")
            if len(self.event_log) > self.history_limit:
                self.event_log = self.event_log[-self.history_limit:]

        except Exception as e:
            self.event_log.append(f"Export failed: {e}")
            if len(self.event_log) > self.history_limit:
                self.event_log = self.event_log[-self.history_limit:]

    @rx.event(background=True)
    async def poll_loop(self):
        async with self:
            my_session = self.poll_session_id

        while True:
            async with self:
                if not self.running:
                    break
                ip = self.device_address
                interval_s = self.poll_interval_float

            try:
                raw, latency_ms = await asyncio.to_thread(fetch_status, ip, 1.0, "/status")
                snapshot = parse_status(raw, latency_ms)

                async with self:
                    if not self.running:
                        break

                    self.connected = True
                    self.last_error = ""
                    self.last_seen_epoch = snapshot.timestamp
                    self.latency_ms = snapshot.latency_ms
                    self.consecutive_failures = 0

                    self.mode = snapshot.mode
                    self.uptime_s = snapshot.uptime_s
                    self.temp_c = snapshot.temp_c
                    self.voltage_v = snapshot.voltage_v
                    self.current_a = snapshot.current_a
                    self.faults = snapshot.faults
                    self.raw_json = json.dumps(snapshot.raw, indent=2)

                    # ---- append trend sample ----
                    self.sample_index += 1
                    self.history.append(
                        {
                            "t": self.sample_index,
                            "temp_c": round(self.temp_c, 3),
                            "voltage_v": round(self.voltage_v, 3),
                            "current_a": round(self.current_a, 3),
                            "latency_ms": round(self.latency_ms, 2),
                        }
                    )
                    if len(self.history) > self.history_limit:
                        self.history = self.history[-self.history_limit:]

                    if self.log_to_file and self.log_file_path:
                        record = {
                            "ts_utc": datetime.now(timezone.utc).isoformat(),
                            "device_ip": self.device_ip,
                            "sample_index": self.sample_index,
                            "mode": self.mode,
                            "uptime_s": self.uptime_s,
                            "temp_c": round(self.temp_c, 3),
                            "voltage_v": round(self.voltage_v, 3),
                            "current_a": round(self.current_a, 3),
                            "latency_ms": round(self.latency_ms, 2),
                            "faults": self.faults,
                            "connected": self.connected,
                        }
                        try:
                            self._append_jsonl_record(record)
                            self.log_samples_written += 1
                        except Exception as log_err:
                            self.event_log.append(f"Log write error: {log_err}")
                            if len(self.event_log) > 200:
                                self.event_log = self.event_log[-200:]

            except Exception as e:
                async with self:
                    if not self.running:
                        break

                    self.connected = False
                    self.consecutive_failures += 1
                    self.last_error = str(e)
                    self.event_log.append(f"Poll error ({self.consecutive_failures}): {e}")
                    if len(self.event_log) > 200:
                        self.event_log = self.event_log[-200:]

            await asyncio.sleep(interval_s)

    @rx.event(background=True)
    async def send_command_background(self, command_name: str, args_json: str = "{}"):
        # mark busy + capture current IP
        async with self:
            if self.command_busy:
                return
            self.command_busy = True
            ip = self.device_address
            self.last_command_name = command_name
            self.last_command_status = "Sending..."

        # parse args JSON outside lock
        try:
            parsed_args = json.loads(args_json) if args_json.strip() else {}
            if not isinstance(parsed_args, dict):
                raise ValueError("Command args must be a JSON object")
        except Exception as e:
            async with self:
                self.command_busy = False
                self.last_command_status = "Error"
                self.last_command_response = f"Invalid args JSON: {e}"
                self.event_log.append(f"Command '{command_name}' invalid args: {e}")
                if len(self.event_log) > 200:
                    self.event_log = self.event_log[-200:]
            return

        # send command in thread
        try:
            resp_json, latency_ms = await asyncio.to_thread(
                send_command, ip, command_name, parsed_args, 2.0, "/command"
            )

            async with self:
                self.command_busy = False
                self.last_command_status = "Success"
                self.last_command_latency_ms = round(latency_ms, 2)
                self.last_command_response = json.dumps(resp_json, indent=2)
                self.event_log.append(
                    f"Command '{command_name}' OK ({self.last_command_latency_ms} ms)"
                )
                if len(self.event_log) > self.history_limit:
                    self.event_log = self.event_log[-self.history_limit:]

        except Exception as e:
            async with self:
                self.command_busy = False
                self.last_command_status = "Error"
                self.last_command_response = str(e)
                self.event_log.append(f"Command '{command_name}' failed: {e}")
                if len(self.event_log) > self.history_limit:
                    self.event_log = self.event_log[-self.history_limit:]