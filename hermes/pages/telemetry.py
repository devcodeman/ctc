"""Telemetry viewer page – full-screen plotting view."""

import reflex as rx
from hermes.state import HermesState
from hermes.utilities.constants import (
    BG, PANEL, BORDER, ACCENT, ACCENT2, TEXT, MUTED,
    FONT_MONO, FONT_DISPLAY,
)
from hermes.components.ui_helpers import status_dot


def _uploaded_plot_key_badge(key: str) -> rx.Component:
    """Render a selectable telemetry channel badge for uploaded datasets."""
    selected = HermesState.uploaded_selected_keys.contains(key)
    return rx.button(
        key,
        on_click=HermesState.toggle_uploaded_plot_key(key),
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
    """Render the telemetry viewer page header."""
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
                "TELEMETRY VIEWER",
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


@rx.page(route="/telemetry", title="Hermes — Telemetry Viewer")
def telemetry_page() -> rx.Component:
    """Render the full-screen telemetry analysis page."""
    selected_telemetry_files = rx.selected_files("telemetry_file_upload")
    return rx.box(
        rx.html(
            '<link rel="preconnect" href="https://fonts.googleapis.com">'
            '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
            '<link href="https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;600;700&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">'
        ),
        _header(),
        rx.moment(interval=HermesState.poll_interval_ms, on_change=HermesState.tick, display="none"),
        rx.vstack(
            rx.vstack(
                rx.hstack(
                    rx.text(
                        "TELEMETRY ANALYSIS FILE",
                        font_family=FONT_DISPLAY,
                        font_size="0.7rem",
                        font_weight="600",
                        letter_spacing="0.12em",
                        color=MUTED,
                    ),
                    rx.text(
                        "Accepts .json and .jsonl files that match the telemetry schema.",
                        color=MUTED,
                        font_size="0.78rem",
                        font_family=FONT_MONO,
                    ),
                    align="center",
                    justify="between",
                    width="100%",
                ),
                rx.upload(
                    rx.vstack(
                        rx.text(
                            "Drop telemetry JSON/JSONL here or click to browse",
                            color=MUTED,
                            font_family=FONT_MONO,
                            font_size="0.88rem",
                            text_align="center",
                        ),
                        rx.text(
                            "Schema: timestamp plus at least one numeric telemetry field per record.",
                            color=MUTED,
                            font_family=FONT_MONO,
                            font_size="0.76rem",
                            text_align="center",
                        ),
                        align="center",
                        gap="0.35rem",
                    ),
                    id="telemetry_file_upload",
                    accept={
                        ".json": "application/json",
                        ".jsonl": "application/x-ndjson",
                    },
                    multiple=False,
                    border=f"1px dashed {BORDER}",
                    border_radius="6px",
                    padding="1.25rem",
                    width="100%",
                    background=BG,
                    cursor="pointer",
                ),
                rx.cond(
                    selected_telemetry_files.length() > 0,
                    rx.box(
                        rx.vstack(
                            rx.text(
                                "Selected for analysis",
                                color=ACCENT,
                                font_family=FONT_DISPLAY,
                                font_size="0.74rem",
                                font_weight="600",
                                letter_spacing="0.08em",
                            ),
                            rx.foreach(
                                selected_telemetry_files,
                                lambda file_name: rx.text(
                                    file_name,
                                    font_family=FONT_MONO,
                                    font_size="0.84rem",
                                    color=TEXT,
                                ),
                            ),
                            align="start",
                            gap="0.35rem",
                        ),
                        background=BG,
                        border=f"1px solid {ACCENT}",
                        border_radius="4px",
                        padding="0.95rem",
                        width="100%",
                    ),
                    rx.box(),
                ),
                rx.hstack(
                    rx.button(
                        "Load Telemetry File",
                        on_click=HermesState.handle_telemetry_upload(
                            rx.upload_files(upload_id="telemetry_file_upload")
                        ),
                        background="transparent",
                        color=ACCENT,
                        border=f"1px solid {ACCENT}",
                        border_radius="4px",
                        font_family=FONT_DISPLAY,
                        font_size="0.82rem",
                        font_weight="600",
                        letter_spacing="0.08em",
                        cursor="pointer",
                        padding="0.5rem 0.95rem",
                    ),
                    rx.button(
                        "Clear File",
                        on_click=[
                            HermesState.clear_telemetry_upload,
                            rx.clear_selected_files("telemetry_file_upload"),
                        ],
                        background="transparent",
                        color=MUTED,
                        border=f"1px solid {BORDER}",
                        border_radius="4px",
                        font_family=FONT_DISPLAY,
                        font_size="0.82rem",
                        font_weight="600",
                        letter_spacing="0.08em",
                        cursor="pointer",
                        padding="0.5rem 0.95rem",
                    ),
                    rx.cond(
                        HermesState.telemetry_upload_name != "",
                        rx.text(
                            HermesState.telemetry_upload_name,
                            color=MUTED,
                            font_size="0.76rem",
                            font_family=FONT_MONO,
                        ),
                        rx.box(),
                    ),
                    align="center",
                    gap="0.75rem",
                    width="100%",
                ),
                rx.cond(
                    HermesState.telemetry_upload_status != "",
                    rx.text(
                        HermesState.telemetry_upload_status,
                        color=rx.cond(
                            HermesState.telemetry_upload_status.contains("error"),
                            "#ffab00",
                            ACCENT,
                        ),
                        font_size="0.8rem",
                        font_family=FONT_MONO,
                    ),
                    rx.box(),
                ),
                gap="0.75rem",
                padding="0.9rem 1.25rem",
                background=PANEL,
                border=f"1px solid {BORDER}",
                border_radius="6px",
                width="100%",
            ),
            # Key selector bar
            rx.vstack(
                rx.hstack(
                    rx.text(
                        "FILE DATA CHANNELS",
                        font_family=FONT_DISPLAY,
                        font_size="0.7rem",
                        font_weight="600",
                        letter_spacing="0.12em",
                        color=MUTED,
                    ),
                    rx.text(
                        "Full view uses uploaded telemetry files only.",
                        color=MUTED,
                        font_size="0.78rem",
                        font_family=FONT_MONO,
                    ),
                    align="center",
                    justify="between",
                    width="100%",
                ),
                rx.cond(
                    HermesState.uploaded_telemetry_keys.length() == 0,
                    rx.text(
                        "Upload a telemetry JSON or JSONL file above to analyze it here.",
                        color=MUTED,
                        font_size="0.8rem",
                        font_family=FONT_MONO,
                    ),
                    rx.flex(
                        rx.foreach(HermesState.uploaded_telemetry_keys, _uploaded_plot_key_badge),
                        flex_wrap="wrap",
                        gap="0.4rem",
                    ),
                ),
                gap="0.75rem",
                padding="0.9rem 1.25rem",
                background=PANEL,
                border=f"1px solid {BORDER}",
                border_radius="6px",
                width="100%",
            ),
            # Full-height plot
            rx.cond(
                HermesState.uploaded_selected_keys.length() > 0,
                rx.box(
                    rx.plotly(
                        data=HermesState.uploaded_plot_figure,
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
                            rx.cond(
                                HermesState.uploaded_telemetry_keys.length() > 0,
                                "SELECT FILE DATA CHANNELS ABOVE TO BEGIN PLOTTING",
                                "UPLOAD A TELEMETRY FILE ABOVE TO BEGIN ANALYSIS",
                            ),
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
