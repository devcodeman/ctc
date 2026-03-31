"""Export panel component."""

import reflex as rx
from hermes.state import HermesState
from hermes.utilities.constants import ACCENT, MUTED, FONT_MONO, FONT_DISPLAY
from hermes.components.panel import panel
from hermes.components.ui_helpers import section_title


def export_panel() -> rx.Component:
    return panel(
        rx.vstack(
            section_title("Export"),
            rx.vstack(
                rx.hstack(
                    rx.vstack(
                        rx.text(
                            "Telemetry Log File",
                            color=MUTED,
                            font_size="0.74rem",
                            font_family=FONT_DISPLAY,
                            font_weight="600",
                            letter_spacing="0.08em",
                        ),
                        rx.cond(
                            HermesState.telemetry_log_files.length() > 0,
                            rx.select(
                                HermesState.telemetry_log_files,
                                value=HermesState.active_selected_telemetry_log_file,
                                on_change=HermesState.set_selected_telemetry_log_file,
                                placeholder="Select telemetry log",
                                width="100%",
                                color_scheme="cyan",
                                variant="surface",
                                radius="small",
                            ),
                            rx.text(
                                "No telemetry log files found.",
                                color=MUTED,
                                font_size="0.78rem",
                                font_family=FONT_MONO,
                            ),
                        ),
                        rx.button(
                            "Download Telemetry Log",
                            on_click=HermesState.export_selected_telemetry_log_file,
                            background="transparent",
                            color=ACCENT,
                            border=f"1px solid {ACCENT}",
                            border_radius="4px",
                            font_family=FONT_DISPLAY,
                            font_size="0.8rem",
                            font_weight="600",
                            letter_spacing="0.08em",
                            cursor="pointer",
                            padding="0.5rem 0.95rem",
                            width="100%",
                        ),
                        gap="0.5rem",
                        width="100%",
                    ),
                    rx.vstack(
                        rx.text(
                            "Event Log File",
                            color=MUTED,
                            font_size="0.74rem",
                            font_family=FONT_DISPLAY,
                            font_weight="600",
                            letter_spacing="0.08em",
                        ),
                        rx.cond(
                            HermesState.event_log_files.length() > 0,
                            rx.select(
                                HermesState.event_log_files,
                                value=HermesState.active_selected_event_log_file,
                                on_change=HermesState.set_selected_event_log_file,
                                placeholder="Select event log",
                                width="100%",
                                color_scheme="cyan",
                                variant="surface",
                                radius="small",
                            ),
                            rx.text(
                                "No event log files found.",
                                color=MUTED,
                                font_size="0.78rem",
                                font_family=FONT_MONO,
                            ),
                        ),
                        rx.button(
                            "Download Event Log",
                            on_click=HermesState.export_selected_event_log_file,
                            background="transparent",
                            color=ACCENT,
                            border=f"1px solid {ACCENT}",
                            border_radius="4px",
                            font_family=FONT_DISPLAY,
                            font_size="0.8rem",
                            font_weight="600",
                            letter_spacing="0.08em",
                            cursor="pointer",
                            padding="0.5rem 0.95rem",
                            width="100%",
                        ),
                        gap="0.5rem",
                        width="100%",
                    ),
                    gap="0.75rem",
                    width="100%",
                    align="start",
                    flex_wrap="wrap",
                ),
                gap="0.6rem",
                width="100%",
            ),
            rx.text(
                "Event Logs: /tmp/hermes/logs  |  Telemetry Logs: /tmp/hermes/telemetry",
                color=MUTED,
                font_size="0.82rem",
                font_family=FONT_MONO,
                margin_top="0.65rem",
            ),
            gap="0.65rem",
            width="100%",
        ),
        width="100%",
    )
