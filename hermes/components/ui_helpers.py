"""Reusable UI helper components."""

import reflex as rx
from hermes.utilities.constants import ACCENT, MUTED, SUCCESS, DANGER, FONT_DISPLAY


def label(text: str) -> rx.Component:
    return rx.text(
        text,
        font_family=FONT_DISPLAY,
        font_size="0.65rem",
        font_weight="600",
        letter_spacing="0.12em",
        color=MUTED,
        text_transform="uppercase",
        margin_bottom="0.35rem",
    )


def section_title(text: str) -> rx.Component:
    return rx.hstack(
        rx.box(width="3px", height="1rem", background=ACCENT, border_radius="2px"),
        rx.text(
            text,
            font_family=FONT_DISPLAY,
            font_size="0.75rem",
            font_weight="700",
            letter_spacing="0.15em",
            color=ACCENT,
            text_transform="uppercase",
        ),
        align="center",
        gap="0.5rem",
        margin_bottom="1rem",
    )


def status_dot(active) -> rx.Component:
    return rx.box(
        width="8px",
        height="8px",
        border_radius="50%",
        background=rx.cond(active, SUCCESS, DANGER),
        box_shadow=rx.cond(active, f"0 0 6px {SUCCESS}", f"0 0 6px {DANGER}"),
    )
