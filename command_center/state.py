from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path
from datetime import datetime, timezone

import reflex as rx

from .device_client import fetch_status, send_command

MAX_EVENT_LOG_ENTRIES = 200
DEFAULT_HISTORY_LIMIT = 25
DEFAULT_FETCH_TIMEOUT_S = 1.0
DEFAULT_COMMAND_TIMEOUT_S = 2.0
MAX_TREND_KEYS = 4

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
    faults: list[str] = []
    telemetry: dict = {}
    telemetry_rows: list[dict] = []
    numeric_telemetry_keys: list[str] = []
    telemetry_filter_text: str = ""
    filtered_telemetry_rows: list[dict] = []
    device_version: str = ""
    device_git_hash: str = ""

    # ---- trend history ----
    history: list[dict] = []
    history_limit: int = 50
    sample_index: int = 0
    dynamic_history: list[dict] = []
    dynamic_history_limit: int = DEFAULT_HISTORY_LIMIT
    dynamic_sample_index: int = 0
    selected_trend_keys: list[str] = []
    trend_filter_text: str = ""
    filtered_numeric_telemetry_keys: list[str] = []
    trend_key_rows: list[dict] = []
    trend_line_rows: list[dict] = []
    trend_keys_initialized: bool = False

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
    last_command_status: str = "IDLE"
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
        return "ON" if self.log_to_file else "OFF"
    
    @rx.var
    def has_device_info(self) -> bool:
        return bool(self.device_version or self.device_git_hash)
    
    @rx.var
    def device_address(self) -> str:
        host = self.device_host.strip()
        port = self.device_port.strip()
        if port:
            return f"{host}:{port}"
        return host
    
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
        if v == "":
            self.device_port = v
            return

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

    def set_telemetry_filter_text(self, value: str):
        self.telemetry_filter_text = value
        self._rebuild_filtered_telemetry_rows()

    def set_trend_filter_text(self, value: str):
        self.trend_filter_text = value
        self._rebuild_filtered_numeric_telemetry_keys()

    def select_filtered_trend_keys(self):
        """Add filtered keys to selection up to MAX_TREND_KEYS."""
        selected = list(self.selected_trend_keys)

        for key in self.filtered_numeric_telemetry_keys:
            if key in selected:
                continue
            if len(selected) >= MAX_TREND_KEYS:
                break
            selected.append(key)

        self.selected_trend_keys = selected

        self._rebuild_trend_key_rows()

    def clear_selected_trend_keys(self):
        """Clear all selected trend keys."""
        self.selected_trend_keys = []
        self._rebuild_trend_key_rows()
        self._rebuild_trend_line_rows()

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
        self._reset_live_snapshot()
        self.running = True
        self.poll_session_id += 1
        self._append_event_log(f"Starting poll loop for {self.device_address}")
        return TelemetryState.poll_loop

    def disconnect(self):
        self.running = False
        self.connected = False
        self._reset_live_snapshot()
        self._reset_trend_history()
        self._append_event_log("Polling stopped by operator")

    def clear_log(self):
        self.event_log = []

    def toggle_file_logging(self):
        """Toggle background telemetry file logging on/off."""
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
            self._append_event_log(f"File logging enabled: {self.log_file_path}")
        else:
            self.log_to_file = False
            self._append_event_log("File logging disabled")

    def toggle_trend_key(self, key: str):
        """Toggle a trend key on/off for plotting."""
        if key in self.selected_trend_keys:
            self.selected_trend_keys = [k for k in self.selected_trend_keys if k != key]
            return

        if len(self.selected_trend_keys) >= MAX_TREND_KEYS:
            # Optional: add an event log message here if you want user feedback.
            return

        self.selected_trend_keys = [*self.selected_trend_keys, key]

        self._rebuild_trend_key_rows()

    def export_log_to_json(self):
        """Convert current session JSONL log file into a nominal JSON file (array payload)."""
        if not self.log_file_path:
            self._append_event_log("Export skipped: no log file path available")
            return

        src = Path(self.log_file_path)
        if not src.exists():
            self._append_event_log(f"Export failed: log file not found: {src}")
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
                        self._append_event_log(f"Export warning: bad JSONL line {line_no}: {e}")

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
            self._append_event_log(f"Exported JSON: {self.last_export_json_path} ({len(samples)} samples)")

        except Exception as e:
            self._append_event_log(f"Export failed: {e}")

    def add_trend_key(self, key: str):
        if key in self.selected_trend_keys:
            return
        if len(self.selected_trend_keys) >= MAX_TREND_KEYS:
            return
        self.selected_trend_keys = [*self.selected_trend_keys, key]
        self._rebuild_trend_key_rows()

    def remove_trend_key(self, key: str):
        if key not in self.selected_trend_keys:
            return
        self.selected_trend_keys = [k for k in self.selected_trend_keys if k != key]
        self._rebuild_trend_key_rows()

    def _append_jsonl_record(self, record: dict):
        """Append one JSON object as a line to the current log file."""
        if not self.log_to_file or not self.log_file_path:
            return

        path = Path(self.log_file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, separators=(",", ":")) + "\n")

    def _append_event_log(self, message: str):
        self.event_log.append(message)
        if len(self.event_log) > MAX_EVENT_LOG_ENTRIES:
            self.event_log = self.event_log[-MAX_EVENT_LOG_ENTRIES:]

    def _append_dynamic_history_sample(self):
        """Append one trend sample using selected numeric telemetry keys."""
        # Auto-select only once per session (or until explicit reset)
        if (not self.trend_keys_initialized) and (not self.selected_trend_keys):
            self.selected_trend_keys = self.numeric_telemetry_keys[:3]
            self.trend_keys_initialized = True
            self._rebuild_trend_key_rows()
            self._rebuild_trend_line_rows()

        self.dynamic_sample_index += 1
        sample = {"t": self.dynamic_sample_index}

        has_any_selected_metric = False
        for key in self.selected_trend_keys:
            value = self.telemetry.get(key)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                sample[key] = float(value)
                has_any_selected_metric = True

        sample["latency_ms"] = float(self.latency_ms)

        if has_any_selected_metric:
            self.dynamic_history.append(sample)
            if len(self.dynamic_history) > self.dynamic_history_limit:
                self.dynamic_history.pop(0)

    def _reset_live_snapshot(self):
        """Clear current live values to avoid stale UI while disconnected/reconnecting."""
        self.telemetry = {}
        self.telemetry_rows = []
        self.numeric_telemetry_keys = []
        self.sample_index = 0
        self.device_version = ""
        self.device_git_hash = ""
        self.faults = []
        self.last_seen_epoch = 0.0
        self.telemetry_filter_text = ""
        self.filtered_telemetry_rows = []
        self.filtered_numeric_telemetry_keys = []
        self.trend_key_rows = []
        self.trend_line_rows = []

    def _reset_trend_history(self):
        """Clear the history for the telemetry trends"""
        self.dynamic_history = []
        self.dynamic_sample_index = 0
        self.selected_trend_keys = []
        self.filtered_telemetry_rows = []
        self.filtered_numeric_telemetry_keys = []
        self.trend_key_rows = []
        self.trend_line_rows = []

    def _rebuild_filtered_telemetry_rows(self):
        """Filter telemetry rows by substring match on key or value."""
        q = self.telemetry_filter_text.strip().lower()

        if not q:
            self.filtered_telemetry_rows = list(self.telemetry_rows)
            return

        self.filtered_telemetry_rows = [
            row
            for row in self.telemetry_rows
            if q in str(row.get("key", "")).lower() or q in str(row.get("value", "")).lower()
        ]

    def _rebuild_telemetry_rows(self, raw: dict):
        self.telemetry_rows = [
            {"key": str(k), "value": str(v)}
            for k, v in sorted(raw.items(), key=lambda kv: str(kv[0]))
        ]
        self._rebuild_filtered_telemetry_rows()

    def _rebuild_filtered_numeric_telemetry_keys(self):
        q = self.trend_filter_text.strip().lower()

        if not q:
            self.filtered_numeric_telemetry_keys = list(self.numeric_telemetry_keys)
            return

        self.filtered_numeric_telemetry_keys = [
            key for key in self.numeric_telemetry_keys if q in key.lower()
        ]

        self._rebuild_trend_key_rows()

    def _selected_trend_key_rows(self) -> list[dict]:
        """Build UI rows for trend keys with selected state."""
        selected = set(self.selected_trend_keys)
        return [{"key": k, "selected": k in selected} for k in self.filtered_numeric_telemetry_keys]
    
    def _rebuild_trend_key_rows(self):
        selected = set(self.selected_trend_keys)
        self.trend_key_rows = [
            {"key": k, "selected": k in selected}
            for k in self.filtered_numeric_telemetry_keys
        ]
    
    def _rebuild_trend_line_rows(self):
        palette = ["#2563EB", "#0D9488", "#7C3AED", "#EA580C"]  # blue, teal, purple, orange
        self.trend_line_rows = [
            {"key": key, "color": palette[i % len(palette)]}
            for i, key in enumerate(self.selected_trend_keys)
        ]

    @rx.event(background=True)
    async def poll_loop(self):
        while True:
            async with self:
                if not self.running:
                    break
                ip = self.device_address
                interval_s = self.poll_interval_float

            try:
                raw, latency_ms = await asyncio.to_thread(fetch_status, ip, 1.0, "/status")
                err = None
            except Exception as e:
                raw, latency_ms = None, None
                err = e

            async with self:
                if not self.running:
                    break

                if err is None:
                    self.connected = True
                    self.last_error = ""
                    self.latency_ms = round(latency_ms, 2)

                    self.telemetry = raw

                    version_val = raw.get("version", raw.get("fw_version", raw.get("sw_version")))
                    git_hash_val = raw.get("git_hash", raw.get("git", raw.get("commit", raw.get("commit_hash"))))
                    self.device_version = str(version_val) if version_val is not None else ""
                    self.device_git_hash = str(git_hash_val) if git_hash_val is not None else ""

                    self._rebuild_telemetry_rows(raw)
                    self._rebuild_filtered_numeric_telemetry_keys()

                    self.numeric_telemetry_keys = sorted(
                        [
                            str(k)
                            for k, v in raw.items()
                            if isinstance(v, (int, float)) and not isinstance(v, bool)
                        ]
                    )

                    self._append_dynamic_history_sample()

                    faults_raw = (
                        raw.get("faults")
                        or raw.get("active_faults")
                        or raw.get("alarms")
                        or []
                    )
                    if isinstance(faults_raw, list):
                        self.faults = [str(x) for x in faults_raw]
                    else:
                        self.faults = []

                    if self.log_to_file and self.log_file_path:
                        record = {
                            "ts_utc": datetime.now(timezone.utc).isoformat(),
                            "device_ip": self.device_address,
                            "sample_index": self.sample_index,
                            "latency_ms": round(self.latency_ms, 2),
                            "connected": self.connected,
                            "faults": self.faults,
                            "telemetry": self.telemetry,
                        }
                        try:
                            self._append_jsonl_record(record)
                            self.log_samples_written += 1
                        except Exception as log_err:
                            self._append_event_log(f"Log write error: {log_err}")
                else:
                    self.connected = False
                    self.last_error = str(err)
                    self._append_event_log(self.last_error)

            await asyncio.sleep(interval_s)

    @rx.event(background=True)
    async def send_command_background(self, command_name: str, args_json: str = "{}"):
        async with self:
            if self.command_busy:
                return
            self.command_busy = True
            ip = self.device_address
            self.last_command_name = command_name
            self.last_command_status = "Sending..."

        try:
            parsed_args = json.loads(args_json) if args_json.strip() else {}
            if not isinstance(parsed_args, dict):
                raise ValueError("Command args must be a JSON object")
        except Exception as e:
            async with self:
                self.command_busy = False
                self.last_command_status = "Error"
                self.last_command_response = f"Invalid args JSON: {e}"
                self._append_event_log(f"Command '{command_name}' invalid args: {e}")
            return

        try:
            resp_json, latency_ms = await asyncio.to_thread(
                send_command, ip, command_name, parsed_args, 2.0, "/command"
            )

            async with self:
                self.command_busy = False
                self.last_command_status = "Success"
                self.last_command_latency_ms = round(latency_ms, 2)
                self.last_command_response = json.dumps(resp_json, indent=2)
                self._append_event_log(
                    f"Command '{command_name}' OK ({self.last_command_latency_ms} ms)"
                )

        except Exception as e:
            async with self:
                self.command_busy = False
                self.last_command_status = "Error"
                self.last_command_response = str(e)
                self._append_event_log(f"Command '{command_name}' failed: {e}")