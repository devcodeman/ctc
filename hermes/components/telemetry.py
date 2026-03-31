"""Last telemetry panel component."""

import reflex as rx
from hermes.state import HermesState
from hermes.utilities.constants import (
    BG, PANEL, BORDER, ACCENT, ACCENT2, TEXT, MUTED, FONT_MONO, FONT_DISPLAY,
)
from hermes.components.panel import panel
from hermes.components.ui_helpers import section_title


def telemetry_panel() -> rx.Component:
    return panel(
        rx.vstack(
            section_title("Last Telemetry"),
            rx.cond(
                HermesState.last_telemetry_items.length() == 0,
                rx.text("No data received.", color=MUTED, font_size="0.78rem", font_family=FONT_MONO),
                rx.vstack(
                    rx.foreach(
                        HermesState.last_telemetry_items,
                        lambda item: rx.hstack(
                            rx.text(
                                item[0],
                                font_family=FONT_MONO,
                                font_size="0.75rem",
                                color=MUTED,
                                min_width="120px",
                            ),
                            rx.text(
                                item[1],
                                font_family=FONT_MONO,
                                font_size="0.8rem",
                                color=ACCENT,
                                font_weight="600",
                            ),
                            gap="1rem",
                        ),
                    ),
                    gap="0.3rem",
                ),
            ),
            gap="0",
            width="100%",
        ),
        width="100%",
    )

def plot_key_badge(key: str) -> rx.Component:
    selected = HermesState.selected_keys.contains(key)
    return rx.button(
        key,
        on_click=HermesState.toggle_plot_key(key),
        background=rx.cond(selected, ACCENT2, "transparent"),
        color=rx.cond(selected, BG, TEXT),
        border=rx.cond(selected, f"1px solid {ACCENT2}", f"1px solid {BORDER}"),
        border_radius="4px",
        font_family=FONT_MONO,
        font_size="0.7rem",
        cursor="pointer",
        padding="0.25rem 0.6rem",
    )


def telemetry_preview_panel() -> rx.Component:
    return panel(
        rx.vstack(
            rx.hstack(
                section_title("Telemetry Preview"),
                rx.spacer(),
                rx.link(
                    rx.text(
                        "OPEN FULL VIEW →",
                        font_family=FONT_DISPLAY,
                        font_size="0.65rem",
                        font_weight="600",
                        letter_spacing="0.1em",
                        color=ACCENT,
                    ),
                    href="/telemetry",
                    text_decoration="none",
                ),
                align="center",
                width="100%",
                margin_bottom="0.25rem",
            ),
            rx.text(
                "Select up to 4 data points to plot:",
                color=MUTED,
                font_size="0.72rem",
                font_family=FONT_MONO,
                margin_bottom="0.5rem",
            ),
            rx.cond(
                HermesState.telemetry_keys.length() == 0,
                rx.text("No keys available yet.", color=MUTED, font_size="0.75rem", font_family=FONT_MONO),
                rx.flex(
                    rx.foreach(HermesState.telemetry_keys, plot_key_badge),
                    flex_wrap="wrap",
                    gap="0.4rem",
                ),
            ),
            rx.cond(
                HermesState.selected_keys.length() > 0,
                rx.plotly(
                    data=HermesState.plot_figure,
                    width="100%",
                    height="300px",
                ),
                rx.box(),
            ),
            gap="0.5rem",
            width="100%",
        ),
        width="100%",
    )