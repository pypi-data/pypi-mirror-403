"""App config for webshop admin in core tests."""

from django.apps import AppConfig


class WebshopConfig(AppConfig):
    """Configuration for webshop admin in core-only environment."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'webshop'
    label = 'webshop_core'
    verbose_name = 'WebShop Admin (Core Features Only)'

    def ready(self):
        """Import djadmin registrations when app is ready."""
        from . import djadmin  # noqa: F401
