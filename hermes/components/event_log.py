"""Event log panel component."""

import reflex as rx
from hermes.state import HermesState
from hermes.utilities.constants import ACCENT, BG, BORDER, DANGER, WARNING, FONT_MONO
from hermes.components.panel import panel
from hermes.components.ui_helpers import section_title


def event_entry(entry: str) -> rx.Component:
    """Render a single event log line with severity-aware coloring."""
    color = rx.cond(
        entry.contains("] ERROR:"),
        DANGER,
        rx.cond(
            entry.contains("] WARNING:"),
            WARNING,
            ACCENT,
        ),
    )
    return rx.text(
        entry,
        font_family=FONT_MONO,
        font_size="0.82rem",
        color=color,
        padding="0.3rem 0",
        border_bottom=f"1px solid {BORDER}",
        width="100%",
        line_height="1.45",
    )


def event_log_panel() -> rx.Component:
    """Render the event log viewer panel."""
    return panel(
        rx.vstack(
            section_title("Event Log"),
            rx.box(
                rx.vstack(
                    rx.foreach(HermesState.event_log, event_entry),
                    gap="0",
                    width="100%",
                ),
                background=BG,
                border=f"1px solid {BORDER}",
                border_radius="4px",
                padding="0.95rem",
                height="280px",
                overflow_y="auto",
                width="100%",
            ),
            gap="0",
            width="100%",
        ),
        width="100%",
    )
