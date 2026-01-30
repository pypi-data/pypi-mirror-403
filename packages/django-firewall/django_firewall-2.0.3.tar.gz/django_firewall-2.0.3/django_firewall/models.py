from django.core.cache import cache
from django.db import models
from django.utils.translation import gettext_lazy as _


class FirewallPathRule(models.Model):
    """
    Model to manage firewall path rules (blacklist and whitelist).

    This model allows dynamic management of URL patterns that should be
    blocked or allowed through the Django admin interface.
    """

    RULE_TYPE_CHOICES = [
        ("blacklist", _("Blacklist")),
        ("whitelist", _("Whitelist")),
    ]

    path_pattern = models.TextField(
        verbose_name=_("Path Pattern"),
        help_text=_(
            "Regular expression pattern for the path (e.g., r'/admin/.*' or '/config.json')"
        ),
    )
    rule_type = models.CharField(
        max_length=10,
        choices=RULE_TYPE_CHOICES,
        default="blacklist",
        verbose_name=_("Rule Type"),
        help_text=_("Whether this is a blacklist (block) or whitelist (allow) rule"),
    )
    enabled = models.BooleanField(
        default=True,
        verbose_name=_("Enabled"),
        help_text=_("Whether this rule is active"),
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Description"),
        help_text=_("Optional description of what this rule blocks/allows"),
    )
    priority = models.IntegerField(
        default=100,
        verbose_name=_("Priority"),
        help_text=_(
            "Lower numbers = higher priority. Whitelist rules are always checked first."
        ),
    )
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Created At")
    )
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    class Meta:
        verbose_name = _("Firewall Path Rule")
        verbose_name_plural = _("Firewall Path Rules")
        ordering = ["rule_type", "priority", "path_pattern"]
        indexes = [
            models.Index(fields=["rule_type", "enabled", "priority"]),
        ]

    def __str__(self):
        status = "✓" if self.enabled else "✗"
        return f"{status} [{self.get_rule_type_display()}] {self.path_pattern}"

    def save(self, *args, **kwargs):
        """Clear cache when rules are modified."""
        super().save(*args, **kwargs)
        cache.delete("firewall_blacklist_rules")
        cache.delete("firewall_whitelist_rules")

    def delete(self, *args, **kwargs):
        """Clear cache when rules are deleted."""
        super().delete(*args, **kwargs)
        cache.delete("firewall_blacklist_rules")
        cache.delete("firewall_whitelist_rules")


class FirewallAPILog(models.Model):
    """
    Model to log API requests for firewall purposes.

    This model tracks IP addresses that have been blocked or allowed,
    along with the URL they attempted to access and server information.
    """

    remote_address = models.GenericIPAddressField(
        verbose_name=_("Remote Address"),
        help_text=_("The IP address of the client making the request."),
    )
    server_hostname = models.CharField(
        max_length=255,
        verbose_name=_("Server Hostname"),
        help_text=_("The hostname of the server that received the request."),
    )
    url = models.TextField(
        verbose_name=_("Request URL"),
        help_text=_("The URL path that was requested."),
    )
    blocked = models.BooleanField(
        default=True,
        verbose_name=_("Blocked"),
        help_text=_("Whether this IP is currently blocked."),
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At"),
        help_text=_("When this log entry was first created."),
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Updated At"),
        help_text=_("When this log entry was last updated."),
    )

    def block_ip(self):
        """
        Mark this IP address as blocked.

        This method updates the database record and can be extended
        to call external firewall APIs.
        """
        self.blocked = True
        self.save(update_fields=["blocked", "updated_at"])

    def allow_ip(self):
        """
        Mark this IP address as allowed.

        This method updates the database record and can be extended
        to call external firewall APIs.
        """
        self.blocked = False
        self.save(update_fields=["blocked", "updated_at"])

    class Meta:
        verbose_name = _("Firewall API Log")
        verbose_name_plural = _("Firewall API Logs")
        ordering = ["-created_at"]
        unique_together = ("remote_address", "url")
        indexes = [
            models.Index(fields=["remote_address"]),
            models.Index(fields=["blocked"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self):
        status = "Blocked" if self.blocked else "Allowed"
        return f"{self.remote_address} - {status} - {self.url}"
