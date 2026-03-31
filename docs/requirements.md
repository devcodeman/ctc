# Hermes Requirements

[Hermes-1]: Hermes `shall` have the option for the user to connect to a device via Ethernet using IP address, port, and poll interval.

[Hermes-2]: Hermes `shall` have the option for the user to connect to a device via Serial at baud 115200.

[Hermes-3]: Hermes `shall` display the last provided telemetry sample.

[Hermes-4]: Hermes `shall` log events to rotating JSONL files.

[Hermes-5]: Hermes `shall` log events to the UI.

[Hermes-6]: Hermes `shall` timestamp logs in the format `YYYY-MM-DD-hh-mm-ss`.

[Hermes-7]: Hermes `shall` use UTC as the standard time.

[Hermes-8]: Hermes `shall` log all telemetry to rotating JSONL files.

[Hermes-9]: Hermes `shall` export telemetry and event data from recorded log files.

[Hermes-10]: Hermes `shall` have the capability to plot telemetry data.

[Hermes-11]: Hermes `shall` have the capability to upload files.

[Hermes-12]: Hermes `shall` have the capability to parse telemetry analysis `.json` and `.jsonl` files.

[Hermes-13]: Hermes `shall` have the capability to select up to 4 (four) data points to plot.

[Hermes-14]: Hermes `shall` query the `/status` endpoint when connected to a device via Ethernet.

[Hermes-15]: Hermes `shall` color-code UI event log entries by severity for info, warning, and error states.

[Hermes-16]: Hermes `shall` separate telemetry data from event log messages so that event logs contain only operational status, warnings, and errors.

[Hermes-17]: Hermes `shall` display a telemetry sample counter in the telemetry preview.

[Hermes-18]: Hermes `shall` provide a dedicated full telemetry viewer for uploaded telemetry analysis files.

[Hermes-19]: Hermes `shall` accept telemetry analysis uploads in `.json` and `.jsonl` formats only.

[Hermes-20]: Hermes `shall` validate telemetry analysis uploads against the published telemetry file schema before loading them.

[Hermes-21]: Hermes `shall` reject invalid telemetry analysis files and surface validation errors in the UI and event log.

[Hermes-22]: Hermes `shall` allow the user to clear a selected telemetry analysis file and any loaded telemetry analysis dataset.

[Hermes-23]: Hermes `shall` allow the user to see selected files before staging or loading them.

[Hermes-24]: Hermes `shall` support generic non-telemetry file staging for binaries, configuration files, firmware, and other system files.

[Hermes-25]: Hermes `shall` allow the user to clear a staged generic file upload.

[Hermes-26]: Hermes `shall` rotate telemetry log files when the next write would cause a file to exceed 50% of system memory.

[Hermes-27]: Hermes `shall` rotate event log files when the next write would cause a file to exceed 50% of system memory.

[Hermes-28]: Hermes `shall` allow the user to export a selected telemetry log file from the available rotated telemetry logs.

[Hermes-29]: Hermes `shall` allow the user to export a selected event log file from the available rotated event logs.

[Hermes-30]: Hermes `shall` present available telemetry and event log files for export selection in the UI.

[Hermes-31]: Hermes `shall` use recorded log files as the source of truth for exported telemetry and event data.
