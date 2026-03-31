"""File upload & parse panel component."""

import reflex as rx
from hermes.state import HermesState
from hermes.utilities.constants import (
    BG, BORDER, TEXT, MUTED, SUCCESS, WARNING,
    FONT_MONO, FONT_DISPLAY,
)
from hermes.components.panel import panel
from hermes.components.ui_helpers import section_title


def upload_panel() -> rx.Component:
    return panel(
        rx.vstack(
            section_title("File Upload & Parse"),
            rx.upload(
                rx.vstack(
                    rx.text(
                        "Drop JSON file here or click to browse",
                        color=MUTED,
                        font_family=FONT_MONO,
                        font_size="0.78rem",
                        text_align="center",
                    ),
                    align="center",
                ),
                id="json_upload",
                accept={".json": "application/json"},
                multiple=False,
                border=f"1px dashed {BORDER}",
                border_radius="6px",
                padding="1.5rem",
                width="100%",
                background=BG,
                cursor="pointer",
            ),
            rx.button(
                "Parse File",
                on_click=HermesState.handle_upload(rx.upload_files(upload_id="json_upload")),
                background="transparent",
                color=WARNING,
                border=f"1px solid {WARNING}",
                border_radius="4px",
                font_family=FONT_DISPLAY,
                font_size="0.7rem",
                font_weight="600",
                letter_spacing="0.08em",
                cursor="pointer",
                padding="0.4rem 0.9rem",
            ),
            rx.cond(
                HermesState.upload_status != "",
                rx.text(HermesState.upload_status, color=SUCCESS, font_size="0.72rem", font_family=FONT_MONO),
                rx.box(),
            ),
            rx.cond(
                HermesState.uploaded_json_preview != "",
                rx.box(
                    rx.text(
                        HermesState.uploaded_json_preview,
                        font_family=FONT_MONO,
                        font_size="0.68rem",
                        color=TEXT,
                        white_space="pre",
                        overflow_x="auto",
                    ),
                    background=BG,
                    border=f"1px solid {BORDER}",
                    border_radius="4px",
                    padding="0.75rem",
                    max_height="200px",
                    overflow_y="auto",
                    width="100%",
                ),
                rx.box(),
            ),
            gap="0.6rem",
            width="100%",
        ),
        width="100%",
    )
