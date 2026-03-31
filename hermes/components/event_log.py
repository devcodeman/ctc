"""Event log panel component."""

import reflex as rx
from hermes.state import HermesState
from hermes.utilities.constants import BG, BORDER, TEXT, FONT_MONO
from hermes.components.panel import panel
from hermes.components.ui_helpers import section_title


def event_log_panel() -> rx.Component:
    return panel(
        rx.vstack(
            section_title("Event Log"),
            rx.box(
                rx.vstack(
                    rx.foreach(
                        HermesState.event_log,
                        lambda entry: rx.text(
                            entry,
                            font_family=FONT_MONO,
                            font_size="0.68rem",
                            color=TEXT,
                            padding="0.15rem 0",
                            border_bottom=f"1px solid {BORDER}",
                            width="100%",
                        ),
                    ),
                    gap="0",
                    width="100%",
                ),
                background=BG,
                border=f"1px solid {BORDER}",
                border_radius="4px",
                padding="0.75rem",
                height="250px",
                overflow_y="auto",
                width="100%",
            ),
            gap="0",
            width="100%",
        ),
        width="100%",
    )
