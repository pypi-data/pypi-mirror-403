import csv
import logging

from django.conf import settings as django_settings
from django.contrib import admin
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import path, reverse
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from django_firewall import conf
from django_firewall.middleware import allow_ip, block_ip
from django_firewall.models import FirewallAPILog, FirewallPathRule

logger = logging.getLogger(__name__)


@admin.register(FirewallPathRule)
class FirewallPathRuleAdmin(admin.ModelAdmin):
    """Admin configuration for FirewallPathRule model."""

    list_display = (
        "path_pattern",
        "enabled_icon",
        "rule_type",
        "priority",
        "description_short",
        "updated_at",
    )
    list_filter = ("rule_type", "enabled", "created_at", "updated_at")
    search_fields = ("path_pattern", "description")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("rule_type", "priority", "path_pattern")
    list_editable = ("priority",)
    list_display_links = ("path_pattern",)

    fieldsets = (
        (
            _("Rule Configuration"),
            {
                "fields": ("path_pattern", "rule_type", "enabled", "priority"),
            },
        ),
        (
            _("Description"),
            {
                "fields": ("description",),
            },
        ),
        (
            _("Timestamps"),
            {
                "classes": ("collapse",),
                "fields": ("created_at", "updated_at"),
            },
        ),
    )

    def has_add_permission(self, request):
        """Only superusers can add new rules."""
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        """Only superusers can change rules."""
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        """Only superusers can delete rules."""
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        """Only superusers can view rules."""
        return request.user.is_superuser

    def enabled_icon(self, obj):
        """Display a visual indicator for enabled/disabled status."""
        if obj.enabled:
            return format_html('<span style="color: green; font-size: 16px;">✓</span>')
        return format_html('<span style="color: red; font-size: 16px;">✗</span>')

    enabled_icon.short_description = _("Status")
    enabled_icon.admin_order_field = "enabled"

    def description_short(self, obj):
        """Display a shortened description."""
        if obj.description:
            return (
                obj.description[:50] + "..."
                if len(obj.description) > 50
                else obj.description
            )
        return "-"

    description_short.short_description = _("Description")


@admin.register(FirewallAPILog)
class FirewallAPILogAdmin(admin.ModelAdmin):
    """Admin configuration for FirewallAPILog model."""

    list_display = (
        "remote_address",
        "server_hostname",
        "url",
        "blocked",
        "actions_html",
        "created_at",
        "updated_at",
    )
    search_fields = ("remote_address", "server_hostname", "url")
    list_filter = ("created_at", "blocked")
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
    show_full_result_count = False
    list_per_page = 50

    # CSV export configuration
    exclude_csv_fields = ("actions_html",)
    header_list = {}
    extra_header_list = ()
    extra_csv_fields = ()

    actions = [
        "export_selected_objects_via_csv",
        "export_filtered_objects_via_csv",
        "export_all_objects_via_csv",
    ]

    fieldsets = (
        (_("Main Information"), {
            "fields": ("remote_address", "server_hostname", "url", "blocked"),
        }),
        (_("Timestamps"), {
            "fields": ("created_at", "updated_at"),
        }),
    )

    def has_add_permission(self, request):
        """Only superusers can add new logs."""
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        """Only superusers can change logs."""
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        """Only superusers can delete logs."""
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        """Only superusers can view logs."""
        return request.user.is_superuser

    def process_block_ip(self, request, ip_pk):
        """
        Process the blocking of an IP address.

        Args:
            request: The HTTP request object.
            ip_pk: The primary key of the IP to be blocked.

        Returns:
            HttpResponseRedirect to the log list page.
        """
        if not conf.ENABLED:
            self.message_user(
                request,
                _("Firewall is not enabled. Please enable it in settings."),
                level="error",
            )
            return HttpResponseRedirect(
                reverse("admin:django_firewall_firewallapilog_changelist")
            )

        try:
            ip_log = FirewallAPILog.objects.get(pk=ip_pk)
            logger.debug(f"Blocking IP address: {ip_log.remote_address}")

            result = block_ip(ip_log.remote_address)
            if not result:
                raise Exception("Failed to block IP address via firewall service.")

            ip_log.block_ip()
            self.message_user(
                request,
                _("IP address %(ip)s has been blocked.") % {"ip": ip_log.remote_address},
                level="success",
            )
        except FirewallAPILog.DoesNotExist:
            self.message_user(
                request,
                _("Log entry not found."),
                level="error",
            )
        except Exception as e:
            self.message_user(
                request,
                _("Failed to block IP address: %(error)s") % {"error": str(e)},
                level="error",
            )

        return HttpResponseRedirect(
            reverse("admin:django_firewall_firewallapilog_changelist")
        )

    def process_allow_ip(self, request, ip_pk):
        """
        Process the allowing of an IP address.

        Args:
            request: The HTTP request object.
            ip_pk: The primary key of the IP to be allowed.

        Returns:
            HttpResponseRedirect to the log list page.
        """
        if not conf.ENABLED:
            self.message_user(
                request,
                _("Firewall is not enabled. Please enable it in settings."),
                level="error",
            )
            return HttpResponseRedirect(
                reverse("admin:django_firewall_firewallapilog_changelist")
            )

        try:
            ip_log = FirewallAPILog.objects.get(pk=ip_pk)
            logger.debug(f"Allowing IP address: {ip_log.remote_address}")

            result = allow_ip(ip_log.remote_address)
            if not result:
                raise Exception("Failed to allow IP address via firewall service.")

            ip_log.allow_ip()
            self.message_user(
                request,
                _("IP address %(ip)s has been allowed.") % {"ip": ip_log.remote_address},
                level="success",
            )
        except FirewallAPILog.DoesNotExist:
            self.message_user(
                request,
                _("Log entry not found."),
                level="error",
            )
        except Exception as e:
            self.message_user(
                request,
                _("Failed to allow IP address: %(error)s") % {"error": str(e)},
                level="error",
            )

        return HttpResponseRedirect(
            reverse("admin:django_firewall_firewallapilog_changelist")
        )

    def get_urls(self):
        """Add custom URLs for block/allow actions."""
        urls = super().get_urls()
        custom_urls = [
            path(
                "block-ip/<int:ip_pk>/",
                self.admin_site.admin_view(self.process_block_ip),
                name="django_firewall_block_ip",
            ),
            path(
                "allow-ip/<int:ip_pk>/",
                self.admin_site.admin_view(self.process_allow_ip),
                name="django_firewall_allow_ip",
            ),
        ]
        return custom_urls + urls

    def actions_html(self, obj):
        """Generate HTML for action buttons to block or allow an IP address."""
        if conf.ENABLED:
            buttons = (
                '<a class="button" href="{}">Block</a>&nbsp;'
                '<a class="button" href="{}">Allow</a>'
            )
            return format_html(
                '<div style="white-space: nowrap;">' + buttons + "</div>",
                reverse("admin:django_firewall_block_ip", args=[obj.pk]),
                reverse("admin:django_firewall_allow_ip", args=[obj.pk]),
            )
        else:
            return format_html(
                '<div style="white-space: nowrap;">'
                '<span class="button" style="opacity: 0.5;">Block</span>&nbsp;'
                '<span class="button" style="opacity: 0.5;">Allow</span>'
                "</div>"
            )

    actions_html.short_description = _("Actions")
    actions_html.allow_tags = True

    def export_selected_objects_via_csv(self, request, queryset):
        """Export selected records to CSV."""
        return self.export_objects_via_csv(request, queryset)

    export_selected_objects_via_csv.short_description = _("Export selected to CSV")

    def export_filtered_objects_via_csv(self, request, queryset):
        """Export filtered records to CSV."""
        cl = self.get_changelist_instance(request)
        records = cl.get_queryset(request)
        return self.export_objects_via_csv(request, records)

    export_filtered_objects_via_csv.short_description = _("Export filtered to CSV")

    def export_all_objects_via_csv(self, request, queryset):
        """Export all records to CSV."""
        records = self.get_queryset(request)
        return self.export_objects_via_csv(request, records)

    export_all_objects_via_csv.short_description = _("Export all to CSV")

    def export_objects_via_csv(self, request, records):
        """
        Export records to CSV file.

        Args:
            request: The HTTP request.
            records: QuerySet of records to export.

        Returns:
            HttpResponse with CSV file attachment.
        """
        file_name = f"{self.model.__name__.lower()}-{timezone.now().date()}"
        response = HttpResponse(content_type="text/csv", charset="utf-8")
        response["Content-Disposition"] = f'attachment; filename="{file_name}.csv"'

        writer = csv.writer(response, delimiter=";", quoting=csv.QUOTE_ALL)

        # Write header
        headers = [
            header if header not in self.header_list else self.header_list[header]
            for header in self.list_display
            if header not in self.exclude_csv_fields
        ]
        for header in self.extra_header_list:
            headers.append(header)
        writer.writerow(headers)

        # Write data
        for record in records:
            values = []
            for field in self.list_display:
                if field not in self.exclude_csv_fields:
                    value = getattr(record, field, "")
                    if value is not None and isinstance(value, list):
                        value = ", ".join(str(v) for v in value)
                    values.append(value)
            for field in self.extra_csv_fields:
                method = getattr(record, field, None)
                if callable(method):
                    values.append(method())
                else:
                    values.append("")
            writer.writerow(values)

        # User feedback
        count = len(records) if hasattr(records, "__len__") else records.count()
        message = _("%(count)d record(s) exported successfully.") % {"count": count}
        self.message_user(request, message)

        return response
