from django.urls import include, path

app_name = "django_firewall"

urlpatterns = []

# Only add API routes if DRF is available
try:
    from rest_framework import routers
    from django_firewall.views import FirewallViewSet

    if FirewallViewSet is not None:
        router = routers.SimpleRouter()
        router.register(r"", FirewallViewSet, basename="firewall")

        urlpatterns = [
            path("", include(router.urls)),
        ]
except ImportError:
    # DRF not installed, no API routes available
    pass
