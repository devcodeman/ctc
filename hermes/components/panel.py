"""Base panel wrapper component."""

import reflex as rx
from hermes.utilities.constants import PANEL, BORDER


def panel(*children, **kwargs) -> rx.Component:
    return rx.box(
        *children,
        background=PANEL,
        border=f"1px solid {BORDER}",
        border_radius="6px",
        padding="1.25rem",
        **kwargs,
    )
