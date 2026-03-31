"""Reusable UI helper components."""

import reflex as rx
from hermes.utilities.constants import ACCENT, MUTED, SUCCESS, DANGER, FONT_DISPLAY


def label(text: str) -> rx.Component:
    """Render a consistent form label."""
    return rx.text(
        text,
        font_family=FONT_DISPLAY,
        font_size="0.78rem",
        font_weight="600",
        letter_spacing="0.12em",
        color=MUTED,
        text_transform="uppercase",
        margin_bottom="0.45rem",
    )


def section_title(text: str) -> rx.Component:
    """Render a shared panel section heading."""
    return rx.hstack(
        rx.box(width="4px", height="1.2rem", background=ACCENT, border_radius="2px"),
        rx.text(
            text,
            font_family=FONT_DISPLAY,
            font_size="0.92rem",
            font_weight="700",
            letter_spacing="0.15em",
            color=ACCENT,
            text_transform="uppercase",
        ),
        align="center",
        gap="0.65rem",
        margin_bottom="1.15rem",
    )


def status_dot(active) -> rx.Component:
    """Render a connection status indicator dot."""
    return rx.box(
        width="10px",
        height="10px",
        border_radius="50%",
        background=rx.cond(active, SUCCESS, DANGER),
        box_shadow=rx.cond(active, f"0 0 6px {SUCCESS}", f"0 0 6px {DANGER}"),
    )
