from django.apps import AppConfig


class DjangoFirewallConfig(AppConfig):

    default_auto_field = "django.db.models.BigAutoField"
    name = "django_firewall"
    verbose_name = "Django Firewall"

    def ready(self):
        """Initialize app when Django is ready."""
        # Import conf to validate settings on startup
        from django_firewall import conf  # noqa: F401
