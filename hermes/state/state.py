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
from typing import Any
import plotly.graph_objects as go


# ── helpers ──────────────────────────────────────────────────────────────────

def utc_stamp() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d-%H-%M-%S")

LOG_DIR = pathlib.Path("/tmp/hermes/logs")
TELEMETRY_DIR = pathlib.Path("/tmp/hermes/telemetry")
LOG_DIR.mkdir(parents=True, exist_ok=True)
TELEMETRY_DIR.mkdir(parents=True, exist_ok=True)

_SESSION_STAMP = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")
TELEMETRY_LOG = TELEMETRY_DIR / f"hermes_telemetry_{_SESSION_STAMP}.jsonl"
EVENT_LOG = LOG_DIR / f"hermes_events_{_SESSION_STAMP}.jsonl"


def append_jsonl(path: pathlib.Path, record: dict):
    with jsonlines.open(str(path), mode="a") as w:
        w.write(record)


# ── state ─────────────────────────────────────────────────────────────────────

class HermesState(rx.State):
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

    # Log (UI)
    event_log: list[str] = []

    # File upload / parse
    uploaded_json: dict = {}
    upload_status: str = ""

    # Internal: stop flag stored in backend var
    _stop_polling: bool = False
    _poll_thread_active: bool = False

    # ── logging ────────────────────────────────────────────────────────────

    def _log_event(self, message: str):
        stamp = utc_stamp()
        entry = {"timestamp": stamp, "message": message}
        self.event_log = [f"[{stamp}] {message}"] + self.event_log[:199]
        append_jsonl(EVENT_LOG, entry)

    def _ingest_telemetry(self, data: dict):
        stamp = utc_stamp()
        record = {"timestamp": stamp, **data}
        self.last_telemetry = data
        self.telemetry_history = self.telemetry_history[-999:] + [record]
        # update known keys
        for k in data:
            if k not in self.telemetry_keys:
                self.telemetry_keys = self.telemetry_keys + [k]
        append_jsonl(TELEMETRY_LOG, record)
        self._log_event(f"Telemetry: {json.dumps(data)}")

    # ── connection ─────────────────────────────────────────────────────────

    def set_conn_mode(self, mode: str):
        self.conn_mode = mode

    def set_ip_address(self, v: str):
        self.ip_address = v

    def set_ip_port(self, v: str):
        self.ip_port = v

    def set_poll_interval(self, v: str):
        self.poll_interval = v

    def set_serial_port(self, v: str):
        self.serial_port = v

    def connect(self):
        if self.connected:
            return
        self._stop_polling = False
        if self.conn_mode == "ip":
            self._log_event(
                f"Connecting via IP {self.ip_address}:{self.ip_port} "
                f"@ {self.poll_interval}s interval"
            )
            t = threading.Thread(target=self._ip_poll_loop, daemon=True)
            t.start()
        else:
            self._log_event(f"Connecting via Serial {self.serial_port} @ 115200")
            t = threading.Thread(target=self._serial_read_loop, daemon=True)
            t.start()
        self.connected = True
        self._poll_thread_active = True

    def disconnect(self):
        self._stop_polling = True
        self.connected = False
        self._poll_thread_active = False
        self._log_event("Disconnected")

    # ── background loops (run in threads) ─────────────────────────────────

    def _ip_poll_loop(self):
        interval = max(0.1, float(self.poll_interval or "1"))
        url = f"http://{self.ip_address}:{self.ip_port}/status"
        while not self._stop_polling:
            try:
                resp = httpx.get(url, timeout=3)
                resp.raise_for_status()
                data = resp.json()
                asyncio.run(self._async_ingest(data))
            except Exception as e:
                asyncio.run(self._async_log(f"IP poll error: {e}"))
            time.sleep(interval)

    def _serial_read_loop(self):
        try:
            ser = serial.Serial(self.serial_port, 115200, timeout=2)
            asyncio.run(self._async_log(f"Serial opened: {self.serial_port}"))
            while not self._stop_polling:
                line = ser.readline().decode(errors="replace").strip()
                if line:
                    try:
                        data = json.loads(line)
                        asyncio.run(self._async_ingest(data))
                    except json.JSONDecodeError:
                        asyncio.run(self._async_log(f"Serial non-JSON: {line}"))
            ser.close()
        except Exception as e:
            asyncio.run(self._async_log(f"Serial error: {e}"))

    async def _async_ingest(self, data: dict):
        self._ingest_telemetry(data)

    async def _async_log(self, msg: str):
        self._log_event(msg)

    # ── refresh ticks ─────────────────────────────────────────────────────

    def tick(self):
        """Fires at poll interval; refreshes telemetry display and event log."""
        pass

    def refresh_plot(self):
        """Fires every 5s; snapshots telemetry history for the plot."""
        self.plot_history_snapshot = list(self.telemetry_history)

    # ── plot key selection ─────────────────────────────────────────────────

    def toggle_plot_key(self, key: str):
        if key in self.selected_keys:
            self.selected_keys = [k for k in self.selected_keys if k != key]
        elif len(self.selected_keys) < 4:
            self.selected_keys = self.selected_keys + [key]

    # ── export ────────────────────────────────────────────────────────────

    def export_telemetry_json(self):
        filename = f"hermes_export_{utc_stamp()}.json"
        data = json.dumps(self.telemetry_history, indent=2)
        self._log_event(f"Exported telemetry as {filename}")
        return rx.download(data=data, filename=filename)

    # ── file upload / parse ───────────────────────────────────────────────

    async def handle_upload(self, files: list[rx.UploadFile]):
        for file in files:
            data = await file.read()
            try:
                parsed = json.loads(data)
                self.uploaded_json = parsed if isinstance(parsed, dict) else {"data": parsed}
                self.upload_status = f"Parsed {file.filename} — {len(self.uploaded_json)} top-level keys"
                self._log_event(f"Uploaded & parsed: {file.filename}")
            except Exception as e:
                self.upload_status = f"Parse error: {e}"
                self._log_event(f"Upload parse error ({file.filename}): {e}")

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
    def uploaded_json_preview(self) -> str:
        if not self.uploaded_json:
            return ""
        return json.dumps(self.uploaded_json, indent=2)[:2000]
