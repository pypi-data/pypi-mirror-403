try:
    from rest_framework import serializers
    HAS_DRF = True
except ImportError:
    HAS_DRF = False
    serializers = None


if HAS_DRF:
    from django_firewall.models import FirewallAPILog

    class FirewallAPILogSerializer(serializers.ModelSerializer):
        """
        Provides JSON serialization for the firewall log entries,
        suitable for REST API responses.
        """

        class Meta:
            model = FirewallAPILog
            fields = "__all__"
            read_only_fields = ("created_at", "updated_at")

        @staticmethod
        def validate_remote_address(value):
            """Validate that the remote address is not empty."""
            if not value:
                raise serializers.ValidationError("Remote address cannot be empty.")
            return value

        @staticmethod
        def validate_url(value):
            """Validate that the URL is not empty."""
            if not value:
                raise serializers.ValidationError("URL cannot be empty.")
            return value
else:
    # Placeholder when DRF is not installed
    FirewallAPILogSerializer = None
