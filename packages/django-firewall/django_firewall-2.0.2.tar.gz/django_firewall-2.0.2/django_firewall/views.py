import logging

logger = logging.getLogger(__name__)

# Check if Django REST Framework is available
try:
    from rest_framework import viewsets
    from rest_framework.permissions import IsAdminUser, IsAuthenticated
    HAS_DRF = True
except ImportError:
    HAS_DRF = False
    viewsets = None
    logger.debug("Django REST Framework not installed. API views will not be available.")


if HAS_DRF:
    from django_firewall.models import FirewallAPILog
    from django_firewall.serializers import FirewallAPILogSerializer

    class FirewallViewSet(viewsets.ReadOnlyModelViewSet):
        """
        A viewset for viewing firewall log entries.

        This is a read-only viewset that allows authenticated admin users
        to view the firewall logs via REST API.

        Endpoints:
            GET /api/firewall/ - List all firewall logs
            GET /api/firewall/{id}/ - Retrieve a specific firewall log
        """

        queryset = FirewallAPILog.objects.all()
        serializer_class = FirewallAPILogSerializer
        permission_classes = [IsAuthenticated, IsAdminUser]

        # Allow filtering and ordering
        filterset_fields = ["blocked", "remote_address", "server_hostname"]
        ordering_fields = ["created_at", "updated_at", "remote_address"]
        ordering = ["-created_at"]
        search_fields = ["remote_address", "url", "server_hostname"]
else:
    # Placeholder when DRF is not installed
    FirewallViewSet = None
