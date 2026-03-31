"""Hermes - Application State"""

import reflex as rx
import asyncio
import json
import jsonlines
import serial
import httpx
import threading
import time
import datetime
import pathlib
import os
from functools import lru_cache
from typing import Any
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError
import plotly.graph_objects as go


# ── helpers ──────────────────────────────────────────────────────────────────

def utc_stamp() -> str:
    """Return a UTC timestamp string suitable for filenames and log entries."""
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d-%H-%M-%S")

LOG_DIR = pathlib.Path("/tmp/hermes/logs")
TELEMETRY_DIR = pathlib.Path("/tmp/hermes/telemetry")
LOG_DIR.mkdir(parents=True, exist_ok=True)
TELEMETRY_DIR.mkdir(parents=True, exist_ok=True)

_SESSION_STAMP = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")
_LOG_PATHS = {
    "telemetry": TELEMETRY_DIR / f"hermes_telemetry_{_SESSION_STAMP}_part000.jsonl",
    "events": LOG_DIR / f"hermes_events_{_SESSION_STAMP}_part000.jsonl",
}
_LOG_FILE_INDEX = {
    "telemetry": 0,
    "events": 0,
}


@lru_cache(maxsize=1)
def system_memory_bytes() -> int:
    """Return the total system memory in bytes, with a conservative fallback."""
    try:
        page_size = os.sysconf("SC_PAGE_SIZE")
        page_count = os.sysconf("SC_PHYS_PAGES")
        return int(page_size * page_count)
    except (ValueError, OSError, AttributeError):
        return 1024 * 1024 * 1024


@lru_cache(maxsize=1)
def log_rotation_threshold_bytes() -> int:
    """Return the maximum size allowed for a single rotated log file."""
    return max(1, system_memory_bytes() // 2)


def log_path(log_type: str, index: int) -> pathlib.Path:
    """Build the rotated file path for the given log type and part index."""
    directory = TELEMETRY_DIR if log_type == "telemetry" else LOG_DIR
    prefix = "hermes_telemetry" if log_type == "telemetry" else "hermes_events"
    return directory / f"{prefix}_{_SESSION_STAMP}_part{index:03d}.jsonl"


def active_log_path(log_type: str, incoming_size: int = 0) -> pathlib.Path:
    """Return the active log file path, rotating first if the next write would overflow it."""
    current_path = _LOG_PATHS[log_type]
    if current_path.exists() and (current_path.stat().st_size + incoming_size) > log_rotation_threshold_bytes():
        _LOG_FILE_INDEX[log_type] += 1
        current_path = log_path(log_type, _LOG_FILE_INDEX[log_type])
        _LOG_PATHS[log_type] = current_path
    return current_path


def append_jsonl(log_type: str, record: dict):
    """Append a JSONL record to the active rotated log file for the given log type."""
    record_size = len(json.dumps(record).encode("utf-8")) + 1
    path = active_log_path(log_type, incoming_size=record_size)
    with jsonlines.open(str(path), mode="a") as w:
        w.write(record)


@lru_cache(maxsize=1)
def telemetry_schema() -> dict[str, Any]:
    """Load and cache the telemetry file validation schema."""
    schema_path = pathlib.Path(__file__).resolve().parents[1] / "schemas" / "telemetry_file.schema.json"
    with schema_path.open("r", encoding="utf-8") as schema_file:
        return json.load(schema_file)


def parse_json_or_jsonl(raw: bytes, filename: str) -> Any:
    """Parse telemetry upload content from either JSON or JSONL."""
    suffix = pathlib.Path(filename).suffix.lower()
    text = raw.decode("utf-8")
    if suffix == ".jsonl":
        rows = []
        for line_number, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                rows.append(json.loads(stripped))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL on line {line_number}: {exc.msg}") from exc
        return rows
    return json.loads(text)


def validate_telemetry_dataset(payload: Any) -> tuple[list[dict[str, Any]], list[str]]:
    """Validate and normalize telemetry upload content for plotting."""
    try:
        Draft202012Validator(telemetry_schema()).validate(payload)
    except ValidationError as exc:
        path = " -> ".join(str(part) for part in exc.absolute_path)
        if path:
            raise ValueError(f"Schema validation failed at {path}: {exc.message}") from exc
        raise ValueError(f"Schema validation failed: {exc.message}") from exc

    if isinstance(payload, list):
        rows = payload
    elif isinstance(payload, dict):
        for key in ("telemetry_history", "telemetry", "records", "data"):
            value = payload.get(key)
            if isinstance(value, list):
                rows = value
                break
        else:
            raise ValueError(
                "Telemetry files must be a JSON array of records or an object containing "
                "a records/data/telemetry/telemetry_history array."
            )
    else:
        raise ValueError("Telemetry files must contain JSON objects.")

    if not rows:
        raise ValueError("Telemetry file contains no records.")

    normalized_rows: list[dict[str, Any]] = []
    telemetry_keys: list[str] = []
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            raise ValueError(f"Record {index} must be a JSON object.")
        sample_keys = [key for key in row.keys() if key != "timestamp"]
        has_numeric_value = any(isinstance(row[key], (int, float)) for key in sample_keys)
        if not has_numeric_value:
            raise ValueError(f"Record {index} must include at least one numeric telemetry value.")
        normalized_rows.append(row)
        for key in sample_keys:
            if key not in telemetry_keys:
                telemetry_keys.append(key)
    return normalized_rows, telemetry_keys


# ── state ─────────────────────────────────────────────────────────────────────

class HermesState(rx.State):
    """Application state for connections, telemetry, uploads, plotting, and exports."""
    # Connection
    conn_mode: str = "ip"          # "ip" | "serial"
    ip_address: str = "127.0.0.1"
    ip_port: str = "5000"
    poll_interval: str = "1"
    serial_port: str = "/dev/ttyUSB0"
    connected: bool = False

    # Telemetry
    telemetry_keys: list[str] = []
    last_telemetry: dict[str, Any] = {}
    telemetry_history: list[dict] = []   # list of {timestamp, ...values}

    # Plot
    selected_keys: list[str] = []        # up to 4
    plot_history_snapshot: list[dict] = []  # refreshed every 5s for plot
    uploaded_selected_keys: list[str] = []   # up to 4 for uploaded telemetry analysis

    # Log (UI)
    event_log: list[str] = []

    # Generic dashboard file upload
    upload_status: str = ""
    uploaded_file_name: str = ""
    uploaded_file_size: int = 0

    # Export selections
    selected_telemetry_log_file: str = ""
    selected_event_log_file: str = ""

    # Telemetry analysis file upload
    telemetry_upload_status: str = ""
    telemetry_upload_name: str = ""
    uploaded_telemetry_data: list[dict[str, Any]] = []

    # Internal: stop flag stored in backend var
    _stop_polling: bool = False
    _poll_thread_active: bool = False

    # ── logging ────────────────────────────────────────────────────────────

    def _log_event(self, message: str, level: str = "INFO"):
        """Append a formatted event entry to the UI list and rotated event log."""
        stamp = utc_stamp()
        normalized_level = level.upper()
        entry = {"timestamp": stamp, "level": normalized_level, "message": message}
        self.event_log = [f"[{stamp}] {normalized_level}: {message}"] + self.event_log[:199]
        append_jsonl("events", entry)

    def _log_info(self, message: str):
        """Record an informational event."""
        self._log_event(message, level="INFO")

    def _log_warning(self, message: str):
        """Record a warning event."""
        self._log_event(message, level="WARNING")

    def _log_error(self, message: str):
        """Record an error event."""
        self._log_event(message, level="ERROR")

    def _ingest_telemetry(self, data: dict):
        """Store incoming telemetry in UI state, history, and the rotated telemetry log."""
        stamp = utc_stamp()
        record = {"timestamp": stamp, **data}
        self.last_telemetry = data
        self.telemetry_history = self.telemetry_history[-999:] + [record]
        # update known keys
        for k in data:
            if k not in self.telemetry_keys:
                self.telemetry_keys = self.telemetry_keys + [k]
        append_jsonl("telemetry", record)

    # ── connection ─────────────────────────────────────────────────────────

    def set_conn_mode(self, mode: str):
        """Set the active connection mode."""
        self.conn_mode = mode

    def set_ip_address(self, v: str):
        """Update the configured IP address."""
        self.ip_address = v

    def set_ip_port(self, v: str):
        """Update the configured IP port."""
        self.ip_port = v

    def set_poll_interval(self, v: str):
        """Update the telemetry polling interval."""
        self.poll_interval = v

    def set_serial_port(self, v: str):
        """Update the configured serial device path."""
        self.serial_port = v

    def connect(self):
        """Start the selected telemetry connection and its background reader thread."""
        if self.connected:
            return
        self._stop_polling = False
        if self.conn_mode == "ip":
            self._log_info(
                f"Connected via IP {self.ip_address}:{self.ip_port} "
                f"at {self.poll_interval}s interval"
            )
            t = threading.Thread(target=self._ip_poll_loop, daemon=True)
            t.start()
        else:
            self._log_info(f"Connected via serial {self.serial_port} at 115200 baud")
            t = threading.Thread(target=self._serial_read_loop, daemon=True)
            t.start()
        self.connected = True
        self._poll_thread_active = True

    def disconnect(self):
        """Stop the active telemetry connection."""
        self._stop_polling = True
        self.connected = False
        self._poll_thread_active = False
        self._log_info("Disconnected")

    # ── background loops (run in threads) ─────────────────────────────────

    def _ip_poll_loop(self):
        """Poll the configured IP telemetry endpoint until disconnected."""
        interval = max(0.1, float(self.poll_interval or "1"))
        url = f"http://{self.ip_address}:{self.ip_port}/status"
        while not self._stop_polling:
            try:
                resp = httpx.get(url, timeout=3)
                resp.raise_for_status()
                data = resp.json()
                asyncio.run(self._async_ingest(data))
            except Exception as e:
                asyncio.run(self._async_log_error(f"IP poll error: {e}"))
            time.sleep(interval)

    def _serial_read_loop(self):
        """Read JSON telemetry lines from the configured serial device until disconnected."""
        try:
            ser = serial.Serial(self.serial_port, 115200, timeout=2)
            asyncio.run(self._async_log_info(f"Serial connection opened on {self.serial_port}"))
            while not self._stop_polling:
                line = ser.readline().decode(errors="replace").strip()
                if line:
                    try:
                        data = json.loads(line)
                        asyncio.run(self._async_ingest(data))
                    except json.JSONDecodeError:
                        asyncio.run(self._async_log_warning("Received non-JSON serial data"))
            ser.close()
        except Exception as e:
            asyncio.run(self._async_log_error(f"Serial error: {e}"))

    async def _async_ingest(self, data: dict):
        """Bridge threaded telemetry ingestion into state mutation."""
        self._ingest_telemetry(data)

    async def _async_log_info(self, msg: str):
        """Bridge threaded informational logging into state mutation."""
        self._log_info(msg)

    async def _async_log_warning(self, msg: str):
        """Bridge threaded warning logging into state mutation."""
        self._log_warning(msg)

    async def _async_log_error(self, msg: str):
        """Bridge threaded error logging into state mutation."""
        self._log_error(msg)

    # ── refresh ticks ─────────────────────────────────────────────────────

    def tick(self):
        """Fires at poll interval; refreshes telemetry display and event log."""
        pass

    def refresh_plot(self):
        """Fires every 5s; snapshots telemetry history for the plot."""
        self.plot_history_snapshot = list(self.telemetry_history)

    # ── plot key selection ─────────────────────────────────────────────────

    def toggle_plot_key(self, key: str):
        """Toggle a live telemetry key in the dashboard preview plot selection."""
        if key in self.selected_keys:
            self.selected_keys = [k for k in self.selected_keys if k != key]
        elif len(self.selected_keys) < 4:
            self.selected_keys = self.selected_keys + [key]

    def toggle_uploaded_plot_key(self, key: str):
        """Toggle a telemetry key in the uploaded-file analysis plot selection."""
        if key in self.uploaded_selected_keys:
            self.uploaded_selected_keys = [k for k in self.uploaded_selected_keys if k != key]
        elif len(self.uploaded_selected_keys) < 4:
            self.uploaded_selected_keys = self.uploaded_selected_keys + [key]

    # ── export ────────────────────────────────────────────────────────────

    def set_selected_telemetry_log_file(self, value: str):
        """Store the selected telemetry log filename for export."""
        self.selected_telemetry_log_file = value

    def set_selected_event_log_file(self, value: str):
        """Store the selected event log filename for export."""
        self.selected_event_log_file = value

    def export_selected_telemetry_log_file(self):
        """Download the selected rotated telemetry log file."""
        file_name = self.active_selected_telemetry_log_file
        if not file_name:
            self._log_warning("No telemetry log file selected for export")
            return
        path = TELEMETRY_DIR / file_name
        if not path.exists():
            self._log_error(f"Telemetry log file not found: {file_name}")
            return
        self._log_info(f"Exported telemetry log file {file_name}")
        return rx.download(data=path.read_text(encoding="utf-8"), filename=file_name)

    def export_selected_event_log_file(self):
        """Download the selected rotated event log file."""
        file_name = self.active_selected_event_log_file
        if not file_name:
            self._log_warning("No event log file selected for export")
            return
        path = LOG_DIR / file_name
        if not path.exists():
            self._log_error(f"Event log file not found: {file_name}")
            return
        self._log_info(f"Exported event log file {file_name}")
        return rx.download(data=path.read_text(encoding="utf-8"), filename=file_name)

    # ── file upload / parse ───────────────────────────────────────────────

    async def handle_upload(self, files: list[rx.UploadFile]):
        """Stage a generic file upload for later non-telemetry workflows."""
        for file in files:
            data = await file.read()
            self.uploaded_file_name = file.filename
            self.uploaded_file_size = len(data)
            self.upload_status = f"Staged {file.filename} — {len(data)} bytes"
            self._log_info(f"Staged generic upload file {file.filename}")

    def clear_staged_upload(self):
        """Clear the currently staged generic upload."""
        self.upload_status = ""
        self.uploaded_file_name = ""
        self.uploaded_file_size = 0
        self._log_info("Cleared staged generic upload file")

    async def handle_telemetry_upload(self, files: list[rx.UploadFile]):
        """Validate and load an uploaded telemetry analysis file."""
        for file in files:
            data = await file.read()
            self.telemetry_upload_name = file.filename
            try:
                parsed = parse_json_or_jsonl(data, file.filename)
                normalized_rows, _ = validate_telemetry_dataset(parsed)
                self.uploaded_telemetry_data = normalized_rows
                self.telemetry_upload_status = (
                    f"Validated {file.filename} — {len(normalized_rows)} telemetry records loaded"
                )
                self.uploaded_selected_keys = []
                self._log_info(f"Validated telemetry analysis file {file.filename}")
            except Exception as e:
                self.uploaded_telemetry_data = []
                self.uploaded_selected_keys = []
                self.telemetry_upload_status = f"Telemetry file error: {e}"
                self._log_error(f"Telemetry file parse error for {file.filename}: {e}")

    def clear_telemetry_upload(self):
        """Clear the loaded telemetry analysis dataset and related UI state."""
        self.telemetry_upload_status = ""
        self.telemetry_upload_name = ""
        self.uploaded_telemetry_data = []
        self.uploaded_selected_keys = []
        self._log_info("Cleared telemetry analysis file")

    # ── computed ─────────────────────────────────────────────────────────

    @rx.var
    def poll_interval_ms(self) -> int:
        """Poll interval converted to milliseconds for the frontend timer."""
        try:
            return max(100, int(float(self.poll_interval or "1") * 1000))
        except (ValueError, TypeError):
            return 1000

    @rx.var
    def last_telemetry_items(self) -> list[tuple[str, str]]:
        """Return the latest telemetry sample as stringified key-value pairs."""
        return [(k, str(v)) for k, v in self.last_telemetry.items()]

    @rx.var
    def plot_figure(self) -> go.Figure:
        """Return a Plotly Figure for selected keys."""
        fig = go.Figure()
        fig.update_layout(
            paper_bgcolor="#111820",
            plot_bgcolor="#0a0e14",
            font=dict(color="#cdd9e5", family="'JetBrains Mono', monospace", size=10),
            xaxis=dict(gridcolor="#1e2d3d", linecolor="#1e2d3d", title="Timestamp"),
            yaxis=dict(gridcolor="#1e2d3d", linecolor="#1e2d3d"),
            legend=dict(bgcolor="rgba(0,0,0,0)"),
            margin=dict(l=50, r=20, t=20, b=60),
        )
        if not self.selected_keys or not self.plot_history_snapshot:
            return fig
        colors = ["#00e5ff", "#ff4081", "#69ff47", "#ffab00"]
        for i, key in enumerate(self.selected_keys):
            xs, ys = [], []
            for row in self.plot_history_snapshot:
                if key in row:
                    xs.append(row["timestamp"])
                    try:
                        ys.append(float(row[key]))
                    except (ValueError, TypeError):
                        ys.append(None)
            fig.add_trace(go.Scatter(
                x=xs,
                y=ys,
                name=key,
                mode="lines+markers",
                line=dict(color=colors[i % len(colors)], width=2),
                marker=dict(size=4),
            ))
        return fig

    @rx.var
    def uploaded_telemetry_rows(self) -> list[dict[str, Any]]:
        """Expose the normalized uploaded telemetry records for plotting."""
        return self.uploaded_telemetry_data

    @rx.var
    def telemetry_log_files(self) -> list[str]:
        """List available rotated telemetry log files, newest first."""
        return sorted(
            [path.name for path in TELEMETRY_DIR.glob("hermes_telemetry_*.jsonl")],
            reverse=True,
        )

    @rx.var
    def event_log_files(self) -> list[str]:
        """List available rotated event log files, newest first."""
        return sorted(
            [path.name for path in LOG_DIR.glob("hermes_events_*.jsonl")],
            reverse=True,
        )

    @rx.var
    def active_selected_telemetry_log_file(self) -> str:
        """Return the currently selected telemetry log file or the newest available file."""
        if self.selected_telemetry_log_file in self.telemetry_log_files:
            return self.selected_telemetry_log_file
        return self.telemetry_log_files[0] if self.telemetry_log_files else ""

    @rx.var
    def active_selected_event_log_file(self) -> str:
        """Return the currently selected event log file or the newest available file."""
        if self.selected_event_log_file in self.event_log_files:
            return self.selected_event_log_file
        return self.event_log_files[0] if self.event_log_files else ""

    @rx.var
    def uploaded_telemetry_keys(self) -> list[str]:
        """Return distinct plottable keys from the uploaded telemetry dataset."""
        keys: list[str] = []
        for row in self.uploaded_telemetry_rows:
            for key in row:
                if key != "timestamp" and key not in keys:
                    keys.append(key)
        return keys

    @rx.var
    def uploaded_plot_figure(self) -> go.Figure:
        """Build a Plotly figure from the uploaded telemetry analysis dataset."""
        fig = go.Figure()
        fig.update_layout(
            paper_bgcolor="#111820",
            plot_bgcolor="#0a0e14",
            font=dict(color="#cdd9e5", family="'JetBrains Mono', monospace", size=10),
            xaxis=dict(gridcolor="#1e2d3d", linecolor="#1e2d3d", title="Timestamp"),
            yaxis=dict(gridcolor="#1e2d3d", linecolor="#1e2d3d"),
            legend=dict(bgcolor="rgba(0,0,0,0)"),
            margin=dict(l=50, r=20, t=20, b=60),
        )
        if not self.uploaded_selected_keys or not self.uploaded_telemetry_rows:
            return fig
        colors = ["#00e5ff", "#ff4081", "#69ff47", "#ffab00"]
        for i, key in enumerate(self.uploaded_selected_keys):
            xs, ys = [], []
            for index, row in enumerate(self.uploaded_telemetry_rows):
                if key in row:
                    xs.append(row.get("timestamp", index))
                    try:
                        ys.append(float(row[key]))
                    except (ValueError, TypeError):
                        ys.append(None)
            fig.add_trace(go.Scatter(
                x=xs,
                y=ys,
                name=key,
                mode="lines+markers",
                line=dict(color=colors[i % len(colors)], width=2),
                marker=dict(size=4),
            ))
        return fig
