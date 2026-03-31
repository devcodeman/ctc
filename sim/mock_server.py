"""
Mock telemetry HTTP server — for testing Hermes IP/Ethernet connection.
Serves random telemetry JSON on GET /status.

Usage:
    python mock_server.py

Then connect Hermes to 127.0.0.1:5001 with any poll interval.
"""

import json
import math
import random
import time
from http.server import HTTPServer, BaseHTTPRequestHandler

HOST = "127.0.0.1"
PORT = 5001

_t = 0.0


def generate_telemetry() -> dict:
    global _t
    data = {
        "temperature_c": round(20.0 + 5 * math.sin(_t / 10) + random.uniform(-0.5, 0.5), 2),
        "pressure_hpa": round(1013.25 + 2 * math.cos(_t / 15) + random.uniform(-0.2, 0.2), 2),
        "voltage_v": round(3.3 + 0.1 * math.sin(_t / 5) + random.uniform(-0.02, 0.02), 3),
        "current_ma": round(150 + 20 * math.sin(_t / 8) + random.uniform(-2, 2), 1),
        "rssi_dbm": round(-60 + 5 * math.sin(_t / 20) + random.uniform(-1, 1), 1),
    }
    _t += 1.0
    return data


class StatusHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/status":
            data = generate_telemetry()
            payload = json.dumps(data).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            print(f"  → /status: {data}")
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Suppress default request logging
        pass


def serve():
    server = HTTPServer((HOST, PORT), StatusHandler)
    print(f"Mock telemetry server listening on http://{HOST}:{PORT}/status")
    server.serve_forever()


if __name__ == "__main__":
    serve()
