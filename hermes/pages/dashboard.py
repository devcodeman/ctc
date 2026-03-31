"""Dashboard page – main index route."""

from functools import lru_cache
from pathlib import Path
import tomllib

import reflex as rx
from hermes.utilities.constants import BG, PANEL, BORDER, TEXT, MUTED, FONT_MONO, FONT_DISPLAY
from hermes.state import HermesState
from hermes.components.connection import connection_panel
from hermes.components.telemetry import telemetry_panel, telemetry_preview_panel
from hermes.components.export import export_panel
from hermes.components.upload import upload_panel
from hermes.components.event_log import event_log_panel


@lru_cache(maxsize=1)
def app_version() -> str:
    """Read and cache the application version from ``pyproject.toml``."""
    pyproject_path = Path(__file__).resolve().parents[2] / "pyproject.toml"
    with pyproject_path.open("rb") as pyproject_file:
        project = tomllib.load(pyproject_file)["project"]
    return project["version"]


def footer() -> rx.Component:
    """Render the dashboard footer with the current application version."""
    return rx.hstack(
        rx.text(
            f"v{app_version()}",
            font_family=FONT_MONO,
            font_size="0.8rem",
            color=MUTED,
        ),
        align="center",
        border_top=f"1px solid {BORDER}",
        padding="1.1rem 1.5rem",
        background=PANEL,
        width="100%",
    )

def header() -> rx.Component:
    """Render the dashboard header and project branding."""
    return rx.hstack(
        rx.hstack(
            rx.image(
                src="hermes-logo.png",
                width=128,
                height=128
            ),
            rx.vstack(
                rx.text(
                    "HERMES",
                    font_family=FONT_DISPLAY,
                    font_size="1.8rem",
                    font_weight="700",
                    letter_spacing="0.25em",
                    color=TEXT,
                    line_height="1",
                ),
                rx.text(
                    "GROUND SUPPORT TELEMETRY",
                    font_family=FONT_DISPLAY,
                    font_size="0.7rem",
                    letter_spacing="0.3em",
                    color=MUTED,
                    line_height="1",
                ),
                gap="0.15rem",
            ),
            align="center",
        ),
        align="center",
        border_bottom=f"1px solid {BORDER}",
        padding="1rem 1.5rem",
        background=PANEL,
        width="100%",
    )


@rx.page(route="/", title="Hermes")
def index() -> rx.Component:
    """Render the main Hermes dashboard page."""
    return rx.vstack(
        # Google Fonts
        rx.html(
            '<link rel="preconnect" href="https://fonts.googleapis.com">'
            '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
            '<link href="https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;600;700&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">'
        ),
        header(),
        rx.moment(interval=HermesState.poll_interval_ms, on_change=HermesState.tick, display="none"),
        rx.moment(interval=5000, on_change=HermesState.refresh_plot, display="none"),
        rx.box(
            # Left column
            rx.vstack(
                connection_panel(),
                telemetry_panel(),
                export_panel(),
                gap="1rem",
                width="100%",
            ),
            # Right column
            rx.vstack(
                telemetry_preview_panel(),
                upload_panel(),
                event_log_panel(),
                gap="1rem",
                width="100%",
            ),
            display="grid",
            grid_template_columns=["1fr", "1fr", "1fr 1fr"],
            gap="1.25rem",
            padding="1.5rem",
            max_width="1560px",
            margin="0 auto",
            width="100%",
            flex="1",
        ),
        footer(),
        align="stretch",
        background=BG,
        min_height="100vh",
        color=TEXT,
        spacing="0",
        width="100%",
    )
