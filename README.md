# CTC (Command & Telemetry Center)

CTC is a local operator console for connecting to a device over Ethernet, polling telemetry, visualizing trends, sending commands, and logging/exporting session data.

Built with:
- **Python**
- **Reflex** (web UI)
- **FastAPI** (fake device simulator for local testing)

## Features (MVP)

- Connect to a device via **IP address + port**
- Polls device **`/status`** endpoint on a configurable refresh interval
- Displays current telemetry values:
  - Mode
  - Temperature
  - Voltage
  - Current
  - Uptime
  - Latency
- Live **telemetry trend chart** (temperature / voltage / current)
- Active faults display
- Event log
- Send commands to device via **`/command`**
- Background telemetry logging to **JSONL**
- Export session log to standard **JSON**

## Project Status

This project is currently in **active MVP development**.

## Tech Stack

- **Reflex** for the command/telemetry UI
- **httpx** for device HTTP calls
- **FastAPI + Uvicorn** for the local fake device simulator

## Project Structure

```text
command_center/
├─ rxconfig.py
├─ command_center/
│  ├─ __init__.py
│  ├─ command_center.py   # Reflex UI page/components
│  ├─ state.py            # App state, polling loop, logging, commands
│  ├─ device_client.py    # Device HTTP client + telemetry parsing
│  └─ fake_device.py      # Local simulator (/status, /command)
├─ logs/                  # Runtime telemetry logs (JSONL/JSON exports)
└─ README.md
```

## Requirements

- Python 3.11+ (tested on Python 3.12)

- Node.js (required by Reflex frontend tooling)

- Ubuntu 24.04 VM

## Quick Start

1. Clone and Create Virtual Environment

    ```bash
    git clone <your-repo-url>
    cd command_center

    python3 -m venv .venv
    source .venv/bin/activate
    python -m pip install --upgrade pip
    ```

1. Install Dependencies

    ```bash
    pip install reflex httpx fastapi uvicorn
    ```

1. Start The Fake Device Simulator (optional, recommended)

    ```bash
    python -m command_center.fake_device
    ```

    This starts a local simulator on:

    - http://127.0.0.1:8001/status

    - http://127.0.0.1:8001/command

1. Run the Reflex app

    ```bash
    reflex run
    ```

    Open the app in your browser (typically `http://localhost:3000`).

## Using the App

### Connection

- Enter the device **IP address** and **Port**
- Choose **Refresh Rate (seconds)**
- Click **Connect**

### Commands

CTC sends commands to the device’s **`/command`** endpoint.

Examples:
- `reset`
- `clear_faults`
- `set_mode` with args like `{"mode":"RUN"}`

### Logging

- Use **Start Logging** to record telemetry samples to a JSONL file
- Use **Export JSON** to export the current session to a standard JSON file

## Log File Format

CTC uses **JSONL (JSON Lines)** for live logging:

- one JSON object per line
- append-friendly
- easy to process and export

Exported JSON files include:

- export metadata
- sample count
- the full sample array

## Roadmap Ideas

- Import exiting Command and Telemetry Database
- Dynamic card creation
- Settings persistence (remember device IP/port/refresh rate)
- CSV export
- Alarm latching / acknowledgement
- Command confirmation dialogs
- Multiple device profiles
- Desktop packaging (portable app / installer)

## Contributing

Contributions, ideas, and feedback are welcome.

If you open an issue, please include:

- OS + Python version
- Reflex version
- Steps to reproduce
- Error logs/screenshots (if applicable)

## Disclaimer

CTC is an operator-facing tool intended for development/testing and internal workflows.  
Use caution before connecting to production or safety-critical devices, especially when enabling command functions.

## Preview

https://github.com/user-attachments/assets/65ecc39c-dcc0-40a0-8a43-669ba42dc193

