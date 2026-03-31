"""Base panel wrapper component."""

import reflex as rx
from hermes.utilities.constants import PANEL, BORDER


def panel(*children, **kwargs) -> rx.Component:
    """Wrap child content in the shared Hermes panel styling."""
    return rx.box(
        *children,
        background=PANEL,
        border=f"1px solid {BORDER}",
        border_radius="8px",
        padding="1.5rem",
        **kwargs,
    )
