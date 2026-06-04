from django.apps import AppConfig


class fin_aidConfig(AppConfig):
    name = 'fin_aid'

    def ready(self):
        import fin_aid.signals  # noqa: F401
