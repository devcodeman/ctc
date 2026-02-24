import reflex as rx

config = rx.Config(
    app_name="command_center",
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ]
)