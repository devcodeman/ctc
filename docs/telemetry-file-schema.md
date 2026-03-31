# Telemetry Analysis File Schema

The full telemetry analysis page only accepts telemetry datasets in `.json` or `.jsonl` format.

## Accepted Containers

- A top-level JSON array of telemetry records.
- A top-level JSON object containing one of these arrays:
  - `records`
  - `data`
  - `telemetry`
  - `telemetry_history`
- A `.jsonl` file where each non-empty line is a telemetry record object.

## Record Requirements

Each telemetry record must:

- Be a JSON object.
- Include a `timestamp` field.
- Include at least one additional telemetry field.
- Include at least one numeric telemetry value so the plotter can graph it.

Example:

```json
[
  {
    "timestamp": "2026-03-30T18:00:00Z",
    "battery_voltage": 12.4,
    "altitude_m": 1245.8,
    "link_ok": true
  },
  {
    "timestamp": "2026-03-30T18:00:05Z",
    "battery_voltage": 12.3,
    "altitude_m": 1251.1,
    "link_ok": true
  }
]
```

## Validation Behavior

Hermes validates telemetry analysis uploads before exposing them to the full telemetry page.

- Invalid files are rejected.
- Uploaded files are first validated against the JSON Schema definition.
- Validation errors are surfaced in the telemetry upload status and event log.
- A second runtime check ensures each record still contains at least one numeric telemetry field for plotting.
- The implementation reference schema lives at [telemetry_file.schema.json](/home/dev/repos/hermes/hermes/schemas/telemetry_file.schema.json).
