import reflex as rx

from .state import TelemetryState


def status_badge() -> rx.Component:
    return rx.badge(
        TelemetryState.connection_label,
        color_scheme=rx.cond(
            TelemetryState.connected,
            "green",
            rx.cond(TelemetryState.running, "yellow", "gray"),
        ),
        variant="solid",
    )


def metric_card(title: str, value, unit: str = "") -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.text(title, size="2", color="gray"),
            rx.hstack(
                rx.heading(value, size="6"),
                rx.text(unit, color="gray"),
                align="end",
                spacing="2",
            ),
            spacing="2",
            align="start",
        ),
        size="3",
        width="100%",
    )


def control_panel() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.heading("Connection", size="5"),
            rx.hstack(
                rx.vstack(
                    rx.text("IP Address", size="2", color="gray"),
                    rx.input(
                        value=TelemetryState.device_host,
                        on_change=TelemetryState.set_device_host,
                        disabled=TelemetryState.running,
                        placeholder="192.168.1.50",
                        width="260px",
                    ),
                    spacing="1",
                    align="start",
                ),
                rx.vstack(
                    rx.text("Port", size="2", color="gray"),
                    rx.input(
                        value=TelemetryState.device_port,
                        on_change=TelemetryState.set_device_port,
                        disabled=TelemetryState.running,
                        placeholder="8001",
                        width="110px",
                    ),
                    spacing="1",
                    align="start",
                ),
                rx.vstack(
                    rx.text("Refresh Rate (seconds)", size="2", color="gray"),
                    rx.select(
                        ["0.5", "1.0", "2.0", "5.0"],
                        value=TelemetryState.poll_interval_s,
                        on_change=TelemetryState.set_poll_interval,
                        disabled=TelemetryState.running,
                        width="180px",
                    ),
                    spacing="1",
                    align="start",
                ),
                rx.vstack(
                    rx.text("Status", size="2", color="gray"),
                    rx.flex(
                        status_badge(),
                        align="center",
                        height="32px",   # adjust to match your input/select height
                    ),
                    spacing="1",
                    align="start",
                ),
                spacing="3",
                wrap="wrap",
                width="100%",
                align="start",
            ),
            rx.hstack(
                rx.button(
                    "Connect",
                    on_click=TelemetryState.connect,
                    color_scheme="green",
                    disabled=TelemetryState.running,
                ),
                rx.button(
                    "Disconnect",
                    on_click=TelemetryState.disconnect,
                    color_scheme="red",
                    variant="soft",
                    disabled=~TelemetryState.running,
                ),
                rx.button("Clear Log", on_click=TelemetryState.clear_log, variant="soft"),
                spacing="3",
                wrap="wrap",
            ),
            rx.hstack(
                rx.text("Last seen:", color="gray"),
                rx.text(TelemetryState.last_seen_text),
                rx.text("|", color="gray"),
                rx.text("Failures:", color="gray"),
                rx.text(TelemetryState.consecutive_failures),
                spacing="2",
                wrap="wrap",
            ),
            rx.text(
                rx.cond(
                    TelemetryState.last_error == "",
                    "No errors",
                    TelemetryState.last_error,
                ),
                color=rx.cond(TelemetryState.last_error == "", "gray", "tomato"),
                width="100%",
            ),
            rx.text(
                rx.cond(
                    TelemetryState.connected,
                    "Connection settings are locked while connected. Press Disconnect to edit.",
                    "",
                ),
                size="2",
                color="gray",
            ),
            spacing="3",
            align="start",
            width="100%",
        ),
        size="3",
    )


def summary_grid() -> rx.Component:
    return rx.grid(
        metric_card("Mode", TelemetryState.mode),
        metric_card("Temperature", TelemetryState.temp_c, "°C"),
        metric_card("Voltage", TelemetryState.voltage_v, "V"),
        metric_card("Current", TelemetryState.current_a, "A"),
        metric_card("Uptime", TelemetryState.uptime_s, "s"),
        metric_card("Latency", TelemetryState.latency_ms_display, "ms"),
        columns="3",
        spacing="4",
        width="100%",
    )


def faults_panel() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.heading("Faults", size="5"),
                rx.badge(TelemetryState.fault_count, color_scheme="red", variant="soft"),
                justify="between",
                width="100%",
            ),
            rx.cond(
                TelemetryState.fault_count > 0,
                rx.vstack(
                    rx.foreach(
                        TelemetryState.faults,
                        lambda fault: rx.badge(fault, color_scheme="red", variant="soft"),
                    ),
                    align="start",
                    spacing="2",
                    width="100%",
                ),
                rx.text("No active faults", color="gray"),
            ),
            spacing="3",
            align="start",
            width="100%",
        ),
        size="3",
    )


def event_log_panel() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.heading("Event Log", size="5"),
            rx.box(
                rx.cond(
                    TelemetryState.event_log.length() > 0,
                    rx.vstack(
                        rx.foreach(
                            TelemetryState.event_log,
                            lambda line: rx.text(line, size="2"),
                        ),
                        align="start",
                        spacing="1",
                        width="100%",
                    ),
                    rx.text("No events yet", color="gray"),
                ),
                max_height="220px",
                overflow_y="auto",
                width="100%",
                border="1px solid var(--gray-5)",
                border_radius="8px",
                padding="8px",
            ),
            spacing="3",
            align="start",
            width="100%",
        ),
        size="3",
    )

def trends_panel() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.heading("Telemetry Trends", size="5"),
                rx.badge(
                    rx.cond(TelemetryState.history_points > 0, "Live", "No Data"),
                    color_scheme=rx.cond(TelemetryState.history_points > 0, "green", "gray"),
                    variant="soft",
                ),
                rx.spacer(),
                rx.text("Samples:", color="gray"),
                rx.text(TelemetryState.sample_index),
                width="100%",
                align="center",
            ),
            rx.recharts.line_chart(
                rx.recharts.cartesian_grid(stroke_dasharray="3 3"),
                rx.recharts.x_axis(data_key="t"),
                rx.recharts.y_axis(y_axis_id="left"),
                rx.recharts.y_axis(y_axis_id="right", orientation="right"),
                rx.recharts.graphing_tooltip(),
                rx.recharts.legend(),
                rx.recharts.line(
                    data_key="temp_c",
                    name="Temp (°C)",
                    y_axis_id="left",
                    type_="monotone",
                    dot=False,
                    stroke="#f59e0b",  # amber
                    stroke_width=2
                ),
                rx.recharts.line(
                    data_key="voltage_v",
                    name="Voltage (V)",
                    y_axis_id="right",
                    type_="monotone",
                    dot=False,
                    stroke="#3b82f6",  # blue
                    stroke_width=2
                ),
                rx.recharts.line(
                    data_key="current_a",
                    name="Current (A)",
                    y_axis_id="right",
                    type_="monotone",
                    dot=False,
                    stroke="#10b981",  # green
                    stroke_width=2
                ),
                data=TelemetryState.history,
                width="100%",
                height=320,
            ),
            rx.text(
                "X-axis = sample number (latest on the right).",
                color="gray",
                size="2",
            ),
            spacing="3",
            align="start",
            width="100%",
        ),
        size="3",
    )

def logging_panel() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.heading("Telemetry Logging", size="5"),
                rx.badge(
                    TelemetryState.logging_status_label,
                    color_scheme=rx.cond(TelemetryState.log_to_file, "green", "gray"),
                    variant="soft",
                ),
                width="100%",
                justify="between",
            ),
            rx.hstack(
                rx.button(
                    rx.cond(TelemetryState.log_to_file, "Stop Logging", "Start Logging"),
                    on_click=TelemetryState.toggle_file_logging,
                    color_scheme=rx.cond(TelemetryState.log_to_file, "red", "green"),
                    variant=rx.cond(TelemetryState.log_to_file, "soft", "solid"),
                ),
                rx.button(
                    "Export JSON",
                    on_click=TelemetryState.export_log_to_json,
                    variant="soft",
                    disabled=~TelemetryState.can_export_json,
                ),
                spacing="3",
                wrap="wrap",
            ),
            rx.hstack(
                rx.text("Samples written:", color="gray"),
                rx.text(TelemetryState.log_samples_written),
                spacing="2",
            ),
            rx.text("Log file:", color="gray"),
            rx.text(
                rx.cond(
                    TelemetryState.log_file_path == "",
                    "No file yet",
                    TelemetryState.log_file_path,
                ),
                size="2",
                width="100%",
                overflow_wrap="anywhere",
            ),
            rx.text("Last JSON export:", color="gray"),
            rx.text(
                rx.cond(
                    TelemetryState.last_export_json_path == "",
                    "No export yet",
                    TelemetryState.last_export_json_path,
                ),
                size="2",
                width="100%",
                overflow_wrap="anywhere",
            ),
            spacing="3",
            align="start",
            width="100%",
        ),
        size="3",
    )

def command_panel() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.heading("Commands", size="5"),
                rx.badge(
                    rx.cond(TelemetryState.command_busy, "Sending", TelemetryState.last_command_status),
                    color_scheme=rx.cond(
                        TelemetryState.command_busy,
                        "blue",
                        rx.cond(
                            TelemetryState.last_command_status == "Success",
                            "green",
                            rx.cond(TelemetryState.last_command_status == "Error", "red", "gray"),
                        ),
                    ),
                    variant="soft",
                ),
                width="100%",
                justify="between",
            ),

            # Quick actions
            rx.hstack(
                rx.button(
                    "Reset",
                    on_click=TelemetryState.cmd_reset,
                    disabled=TelemetryState.command_busy,
                    variant="soft",
                ),
                rx.button(
                    "Clear Faults",
                    on_click=TelemetryState.cmd_clear_faults,
                    disabled=TelemetryState.command_busy,
                    variant="soft",
                ),
                rx.button(
                    "Mode: IDLE",
                    on_click=TelemetryState.cmd_set_mode_idle,
                    disabled=TelemetryState.command_busy,
                    variant="soft",
                ),
                rx.button(
                    "Mode: RUN",
                    on_click=TelemetryState.cmd_set_mode_run,
                    disabled=TelemetryState.command_busy,
                    variant="soft",
                ),
                spacing="2",
                wrap="wrap",
            ),

            # Custom command
            rx.text("Custom command", color="gray", size="2"),
            rx.input(
                value=TelemetryState.command_input,
                on_change=TelemetryState.set_command_input,
                placeholder="command name (e.g. set_mode)",
                width="100%",
            ),
            rx.text("Args JSON object", color="gray", size="2"),
            rx.text_area(
                value=TelemetryState.command_args_json,
                on_change=TelemetryState.set_command_args_json,
                placeholder='{"mode":"RUN"}',
                width="100%",
                min_height="100px",
            ),
            rx.button(
                "Send Custom Command",
                on_click=TelemetryState.send_custom_command,
                disabled=TelemetryState.command_busy,
                color_scheme="blue",
            ),

            # Last response
            rx.hstack(
                rx.text("Last:", color="gray"),
                rx.text(TelemetryState.last_command_name),
                rx.text("|", color="gray"),
                rx.text("Latency:", color="gray"),
                rx.text(TelemetryState.last_command_latency_ms),
                rx.text("ms", color="gray"),
                spacing="2",
                wrap="wrap",
            ),
            rx.box(
                rx.text(
                    rx.cond(
                        TelemetryState.last_command_response == "",
                        "No command response yet",
                        TelemetryState.last_command_response,
                    ),
                    size="2",
                    white_space="pre-wrap",
                    font_family="monospace",
                ),
                width="100%",
                max_height="220px",
                overflow_y="auto",
                border="1px solid var(--gray-5)",
                border_radius="8px",
                padding="8px",
            ),
            spacing="3",
            align="start",
            width="100%",
        ),
        size="3",
    )

def index() -> rx.Component:
    return rx.container(
        rx.vstack(
            rx.heading("Command & Telemetry Center", size="8"),
            rx.text(
                "MVP: poll /status from a device over Ethernet and display normalized telemetry",
                color="gray",
            ),
            control_panel(),
            logging_panel(),
            command_panel(),
            summary_grid(),
            trends_panel(),
            rx.grid(
                faults_panel(),
                event_log_panel(),
                columns="2",
                spacing="4",
                width="100%",
            ),
            spacing="5",
            align="stretch",
            width="100%",
            padding_y="6",
        ),
        max_width="1200px",
    )

app = rx.App()
app.add_page(index, route="/")