"""Hermes – app entry point, routing only."""

import reflex as rx
from hermes.utilities.constants import BG, FONT_MONO
from hermes.pages import index, telemetry_page  # noqa: F401 – registers @rx.page routes

app = rx.App(
    stylesheets=[],
    style={
        "body": {
            "margin": "0",
            "padding": "0",
            "font_family": FONT_MONO,
            "background": BG,
        },
        "*": {"box_sizing": "border-box"},
    },
)
