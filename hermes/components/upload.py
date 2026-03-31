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
    selected_files = rx.selected_files("system_file_upload")
    return panel(
        rx.vstack(
            section_title("File Upload"),
            rx.upload(
                rx.vstack(
                    rx.text(
                        "Drop any file here or click to browse",
                        color=MUTED,
                        font_family=FONT_MONO,
                        font_size="0.92rem",
                        text_align="center",
                    ),
                    rx.text(
                        "Use this for binaries, configs, firmware, and other system files.",
                        color=MUTED,
                        font_family=FONT_MONO,
                        font_size="0.8rem",
                        text_align="center",
                    ),
                    align="center",
                    gap="0.35rem",
                ),
                id="system_file_upload",
                multiple=False,
                border=f"1px dashed {BORDER}",
                border_radius="6px",
                padding="1.8rem",
                width="100%",
                background=BG,
                cursor="pointer",
            ),
            rx.cond(
                selected_files.length() > 0,
                rx.box(
                    rx.vstack(
                        rx.text(
                            "Selected for staging",
                            color=WARNING,
                            font_family=FONT_DISPLAY,
                            font_size="0.74rem",
                            font_weight="600",
                            letter_spacing="0.08em",
                        ),
                        rx.foreach(
                            selected_files,
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
                    border=f"1px solid {WARNING}",
                    border_radius="4px",
                    padding="0.95rem",
                    width="100%",
                ),
                rx.box(),
            ),
            rx.hstack(
                rx.button(
                    "Stage File",
                    on_click=HermesState.handle_upload(rx.upload_files(upload_id="system_file_upload")),
                    background="transparent",
                    color=WARNING,
                    border=f"1px solid {WARNING}",
                    border_radius="4px",
                    font_family=FONT_DISPLAY,
                    font_size="0.84rem",
                    font_weight="600",
                    letter_spacing="0.08em",
                    cursor="pointer",
                    padding="0.55rem 1rem",
                ),
                rx.button(
                    "Clear Selection",
                    on_click=rx.clear_selected_files("system_file_upload"),
                    background="transparent",
                    color=MUTED,
                    border=f"1px solid {BORDER}",
                    border_radius="4px",
                    font_family=FONT_DISPLAY,
                    font_size="0.84rem",
                    font_weight="600",
                    letter_spacing="0.08em",
                    cursor="pointer",
                    padding="0.55rem 1rem",
                ),
                gap="0.6rem",
                flex_wrap="wrap",
            ),
            rx.cond(
                HermesState.upload_status != "",
                rx.text(HermesState.upload_status, color=SUCCESS, font_size="0.86rem", font_family=FONT_MONO),
                rx.box(),
            ),
            rx.cond(
                HermesState.uploaded_file_name != "",
                rx.box(
                    rx.vstack(
                        rx.text(
                            HermesState.uploaded_file_name,
                            font_family=FONT_MONO,
                            font_size="0.88rem",
                            color=TEXT,
                        ),
                        align="start",
                        gap="0.35rem",
                    ),
                    background=BG,
                    border=f"1px solid {BORDER}",
                    border_radius="4px",
                    padding="0.95rem",
                    width="100%",
                ),
                rx.box(),
            ),
            rx.cond(
                HermesState.uploaded_file_name != "",
                rx.button(
                    "Clear Staged File",
                    on_click=[HermesState.clear_staged_upload, rx.clear_selected_files("system_file_upload")],
                    background="transparent",
                    color=MUTED,
                    border=f"1px solid {BORDER}",
                    border_radius="4px",
                    font_family=FONT_DISPLAY,
                    font_size="0.8rem",
                    font_weight="600",
                    letter_spacing="0.08em",
                    cursor="pointer",
                    padding="0.45rem 0.9rem",
                    align_self="start",
                ),
                rx.box(),
            ),
            gap="0.8rem",
            width="100%",
        ),
        width="100%",
    )
