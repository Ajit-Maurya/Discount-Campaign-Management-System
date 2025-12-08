from django.apps import AppConfig


class AppConfig(AppConfig):
    name = "app"

    def ready(self) -> None:
        import app.signals  # noqa: PLC0415
