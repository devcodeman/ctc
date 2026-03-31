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
            rx.hstack(
                rx.button(
                    "Export Telemetry → JSON",
                    on_click=HermesState.export_telemetry_json,
                    background="transparent",
                    color=ACCENT,
                    border=f"1px solid {ACCENT}",
                    border_radius="4px",
                    font_family=FONT_DISPLAY,
                    font_size="0.7rem",
                    font_weight="600",
                    letter_spacing="0.08em",
                    cursor="pointer",
                    padding="0.4rem 0.9rem",
                ),
                gap="0.5rem",
                flex_wrap="wrap",
            ),
            rx.text(
                "Logs: /tmp/hermes/logs  |  Telemetry: /tmp/hermes/telemetry",
                color=MUTED,
                font_size="0.68rem",
                font_family=FONT_MONO,
                margin_top="0.5rem",
            ),
            gap="0.5rem",
            width="100%",
        ),
        width="100%",
    )
