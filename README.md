
# Hermes

![hermes-logo](assets/hermes-logo-w-wording.png)

A ground support command and telemetry dashboard built with Python 3.12, Reflex 0.8, and UV.

## Requirements

- Ubuntu 24.04 VM
- Python 3.12
- [UV](https://docs.astral.sh/uv/) package manager

## Setup

```bash
# Install UV (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone project (if using SSH)
git clone git@github.com:devcodeman/Hermes.git hermes

# Clone project (if using https)
git clone https://github.com/devcodeman/Hermes.git hermes

# Navigate to project
cd hermes

# Create virtual environment and install dependencies
uv venv --python 3.12
source .venv/bin/activate
uv pip install -r requirements.txt
```

## Run

```bash
source .venv/bin/activate
uv run reflex run
```

App will be available at: http://localhost:3000

## Test with Mock TCP Server

In a separate terminal, run the included mock server to simulate telemetry:

```bash
source .venv/bin/activate
python sim/mock_server.py
```

Then connect Hermes to `127.0.0.1:5001` with a 1s poll interval.

## Features

| Requirement | Description |
|---|---|
| Hermes-1 | Connect via IP address, port, and poll interval |
| Hermes-2 | Connect via Serial at 115200 baud |
| Hermes-3 | Display last received telemetry values |
| Hermes-4 | Log events to `hermes_events.jsonl` |
| Hermes-5 | Display events in UI log panel |
| Hermes-6 | Timestamps in `YYYY-MM-DD-hh-mm-ss` format |
| Hermes-7 | All times in UTC |
| Hermes-8 | Log all telemetry to `hermes_telemetry.jsonl` |
| Hermes-9 | Export telemetry to JSON file |
| Hermes-10 | Plot all telemetry data with Plotly |
| Hermes-11 | Upload files via drag-and-drop |
| Hermes-12 | Parse uploaded JSON files |
| Hermes-13 | Select up to 4 data points to plot |

## Output Files

- `hermes_telemetry.jsonl` — all received telemetry (JSONL, UTC timestamped)
- `hermes_events.jsonl` — all events (JSONL, UTC timestamped)
- `hermes_export_<timestamp>.json` — on-demand telemetry export

## Disclaimer

Hermes is an operator-facing tool intended for development/testing and internal workflows.

Use caution before connecting to production or safety-critical devices, especially when enabling command functions.

## Contributing

Contributions, ideas, and feedback are welcome.

If you open an issue, please include:

OS + Python version
Reflex version
Steps to reproduce
Error logs/screenshots (if applicable)

