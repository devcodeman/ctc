"""Connection panel component."""

import reflex as rx
from hermes.state import HermesState
from hermes.utilities.constants import (
    BG, BORDER, ACCENT, TEXT, MUTED, SUCCESS, DANGER,
    FONT_MONO, FONT_DISPLAY,
)
from hermes.components.panel import panel
from hermes.components.ui_helpers import label, section_title, status_dot


def connection_panel() -> rx.Component:
    return panel(
        rx.vstack(
            section_title("Connection"),
            # Mode selector
            rx.hstack(
                rx.button(
                    "IP / TCP",
                    on_click=HermesState.set_conn_mode("ip"),
                    background=rx.cond(HermesState.conn_mode == "ip", ACCENT, "transparent"),
                    color=rx.cond(HermesState.conn_mode == "ip", BG, TEXT),
                    border=f"1px solid {BORDER}",
                    border_radius="4px",
                    font_family=FONT_DISPLAY,
                    font_size="0.88rem",
                    font_weight="600",
                    letter_spacing="0.08em",
                    cursor="pointer",
                    padding="0.5rem 0.95rem",
                ),
                rx.button(
                    "Serial",
                    on_click=HermesState.set_conn_mode("serial"),
                    background=rx.cond(HermesState.conn_mode == "serial", ACCENT, "transparent"),
                    color=rx.cond(HermesState.conn_mode == "serial", BG, TEXT),
                    border=f"1px solid {BORDER}",
                    border_radius="4px",
                    font_family=FONT_DISPLAY,
                    font_size="0.88rem",
                    font_weight="600",
                    letter_spacing="0.08em",
                    cursor="pointer",
                    padding="0.5rem 0.95rem",
                ),
                gap="0.65rem",
                margin_bottom="1.15rem",
            ),
            # IP fields
            rx.cond(
                HermesState.conn_mode == "ip",
                rx.vstack(
                    rx.hstack(
                        rx.vstack(
                            label("IP Address"),
                            rx.input(
                                value=HermesState.ip_address,
                                on_change=HermesState.set_ip_address,
                                placeholder="127.0.0.1",
                                background=BG,
                                border=f"1px solid {BORDER}",
                                color=TEXT,
                                font_family=FONT_MONO,
                                font_size="0.95rem",
                                border_radius="4px",
                                padding="0rem 0.75rem",
                                width="100%",
                            ),
                            width="100%",
                            gap="0",
                        ),
                        rx.vstack(
                            label("Port"),
                            rx.input(
                                value=HermesState.ip_port,
                                on_change=HermesState.set_ip_port,
                                placeholder="5001",
                                background=BG,
                                border=f"1px solid {BORDER}",
                                color=TEXT,
                                font_family=FONT_MONO,
                                font_size="0.95rem",
                                border_radius="4px",
                                padding="0rem 0.75rem",
                                width="110px",
                            ),
                            gap="0",
                        ),
                        gap="0.5rem",
                        width="100%",
                    ),
                    rx.vstack(
                        label("Poll Interval (s)"),
                        rx.input(
                            value=HermesState.poll_interval,
                            on_change=HermesState.set_poll_interval,
                            placeholder="1",
                            background=BG,
                            border=f"1px solid {BORDER}",
                            color=TEXT,
                            font_family=FONT_MONO,
                            font_size="0.95rem",
                            border_radius="4px",
                            padding="0.55rem 0.75rem",
                            width="110px",
                        ),
                        gap="0",
                    ),
                    gap="0.75rem",
                    width="100%",
                ),
                # Serial fields
                rx.vstack(
                    label("Serial Port"),
                    rx.input(
                        value=HermesState.serial_port,
                        on_change=HermesState.set_serial_port,
                        placeholder="/dev/ttyUSB0",
                        background=BG,
                        border=f"1px solid {BORDER}",
                        color=TEXT,
                        font_family=FONT_MONO,
                        font_size="0.95rem",
                        border_radius="4px",
                        padding="0.55rem 0.75rem",
                        width="100%",
                    ),
                    rx.text("Baud: 115200 (fixed)", color=MUTED, font_size="0.82rem", font_family=FONT_MONO),
                    gap="0.35rem",
                    width="100%",
                ),
            ),
            # Connect / Disconnect
            rx.hstack(
                rx.button(
                    rx.cond(HermesState.connected, "Disconnect", "Connect"),
                    on_click=rx.cond(
                        HermesState.connected,
                        HermesState.disconnect,
                        HermesState.connect,
                    ),
                    background=rx.cond(HermesState.connected, DANGER, ACCENT),
                    color=BG,
                    border="none",
                    border_radius="4px",
                    font_family=FONT_DISPLAY,
                    font_size="0.9rem",
                    font_weight="700",
                    letter_spacing="0.1em",
                    cursor="pointer",
                    padding="0.6rem 1.4rem",
                ),
                rx.hstack(
                    status_dot(HermesState.connected),
                    rx.text(
                        rx.cond(HermesState.connected, "CONNECTED", "OFFLINE"),
                        font_family=FONT_DISPLAY,
                        font_size="0.78rem",
                        font_weight="700",
                        letter_spacing="0.15em",
                        color=rx.cond(HermesState.connected, SUCCESS, MUTED),
                    ),
                    align="center",
                    gap="0.4rem",
                ),
                gap="1.15rem",
                align="center",
                margin_top="0.95rem",
            ),
            gap="0",
            width="100%",
        ),
        width="100%",
    )
