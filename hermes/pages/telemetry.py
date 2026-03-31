"""Telemetry plot page – full-screen plotting view."""

import reflex as rx
from hermes.state import HermesState
from hermes.utilities.constants import (
    BG, PANEL, BORDER, ACCENT, ACCENT2, TEXT, MUTED,
    FONT_MONO, FONT_DISPLAY,
)
from hermes.components.ui_helpers import section_title, status_dot


def _plot_key_badge(key: str) -> rx.Component:
    selected = HermesState.selected_keys.contains(key)
    return rx.button(
        key,
        on_click=HermesState.toggle_plot_key(key),
        background=rx.cond(selected, ACCENT2, "transparent"),
        color=rx.cond(selected, BG, TEXT),
        border=rx.cond(selected, f"1px solid {ACCENT2}", f"1px solid {BORDER}"),
        border_radius="4px",
        font_family=FONT_MONO,
        font_size="0.75rem",
        cursor="pointer",
        padding="0.3rem 0.75rem",
    )


def _header() -> rx.Component:
    return rx.hstack(
        rx.hstack(
            rx.link(
                rx.hstack(
                    rx.text(
                        "←",
                        color=ACCENT,
                        font_size="1rem",
                    ),
                    rx.text(
                        "DASHBOARD",
                        font_family=FONT_DISPLAY,
                        font_size="0.7rem",
                        font_weight="600",
                        letter_spacing="0.1em",
                        color=ACCENT,
                    ),
                    align="center",
                    gap="0.35rem",
                ),
                href="/",
                text_decoration="none",
            ),
            rx.box(
                width="1px",
                height="1.2rem",
                background=BORDER,
                margin_x="1rem",
            ),
            rx.text(
                "TELEMETRY PLOT",
                font_family=FONT_DISPLAY,
                font_size="1.1rem",
                font_weight="700",
                letter_spacing="0.2em",
                color=TEXT,
            ),
            align="center",
        ),
        rx.spacer(),
        rx.hstack(
            status_dot(HermesState.connected),
            rx.text(
                rx.cond(HermesState.connected, "LIVE", "OFFLINE"),
                font_family=FONT_DISPLAY,
                font_size="0.65rem",
                font_weight="700",
                letter_spacing="0.15em",
                color=rx.cond(HermesState.connected, "#69ff47", MUTED),
            ),
            align="center",
            gap="0.4rem",
        ),
        align="center",
        border_bottom=f"1px solid {BORDER}",
        padding="0.75rem 1.5rem",
        background=PANEL,
        width="100%",
    )


@rx.page(route="/telemetry", title="Hermes — Telemetry Plot")
def telemetry_page() -> rx.Component:
    return rx.box(
        rx.html(
            '<link rel="preconnect" href="https://fonts.googleapis.com">'
            '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
            '<link href="https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;600;700&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">'
        ),
        _header(),
        # Hidden timer: triggers state refresh every 5 seconds
        rx.moment(interval=HermesState.poll_interval_ms, on_change=HermesState.tick, display="none"),
        rx.moment(interval=5000, on_change=HermesState.refresh_plot, display="none"),
        rx.vstack(
            # Key selector bar
            rx.hstack(
                rx.text(
                    "DATA CHANNELS",
                    font_family=FONT_DISPLAY,
                    font_size="0.7rem",
                    font_weight="600",
                    letter_spacing="0.12em",
                    color=MUTED,
                ),
                rx.cond(
                    HermesState.telemetry_keys.length() == 0,
                    rx.text(
                        "— no keys available (connect to a device first)",
                        color=MUTED,
                        font_size="0.72rem",
                        font_family=FONT_MONO,
                    ),
                    rx.flex(
                        rx.foreach(HermesState.telemetry_keys, _plot_key_badge),
                        flex_wrap="wrap",
                        gap="0.4rem",
                    ),
                ),
                align="center",
                gap="1rem",
                padding="0.75rem 1.25rem",
                background=PANEL,
                border=f"1px solid {BORDER}",
                border_radius="6px",
                width="100%",
            ),
            # Full-height plot
            rx.cond(
                HermesState.selected_keys.length() > 0,
                rx.box(
                    rx.plotly(
                        data=HermesState.plot_figure,
                        width="100%",
                        height="100%",
                    ),
                    background=PANEL,
                    border=f"1px solid {BORDER}",
                    border_radius="6px",
                    padding="0.75rem",
                    width="100%",
                    flex="1",
                    min_height="0",
                ),
                rx.box(
                    rx.vstack(
                        rx.text(
                            "SELECT DATA CHANNELS ABOVE TO BEGIN PLOTTING",
                            font_family=FONT_DISPLAY,
                            font_size="0.85rem",
                            font_weight="600",
                            letter_spacing="0.15em",
                            color=MUTED,
                        ),
                        align="center",
                        justify="center",
                        height="100%",
                    ),
                    background=PANEL,
                    border=f"1px solid {BORDER}",
                    border_radius="6px",
                    width="100%",
                    flex="1",
                    min_height="0",
                ),
            ),
            gap="0.75rem",
            padding="1rem",
            width="100%",
            height="calc(100vh - 52px)",
        ),
        background=BG,
        min_height="100vh",
        color=TEXT,
    )
