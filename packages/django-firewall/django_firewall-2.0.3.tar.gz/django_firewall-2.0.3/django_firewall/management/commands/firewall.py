"""
This command provides CLI tools for managing the firewall:
- Block/unblock IP addresses
- List firewall rules
- Export logs to CSV
- List monitored and whitelisted paths
"""
import ipaddress

from django.core.management.base import BaseCommand, CommandError

from django_firewall import conf, middleware
from django_firewall.endpoint_list import FirewallURLsList, FirewallURLWhiteList
from django_firewall.models import FirewallAPILog


def _validate_ip_address(ip_address: str) -> bool:
    """Validate an IP address."""
    try:
        ipaddress.ip_address(ip_address)
        return True
    except ValueError:
        return False


def _export_csv(csv_file: str, stdout) -> bool:
    """Export the firewall rules to a CSV file."""
    try:
        with open(csv_file, "w") as f:
            f.write("remote_address,server_hostname,url,blocked,created_at,updated_at\n")
            for ip in FirewallAPILog.objects.all():
                f.write(
                    f"{ip.remote_address},{ip.server_hostname},{ip.url},"
                    f"{ip.blocked},{ip.created_at},{ip.updated_at}\n"
                )
        return True
    except Exception as e:
        stdout.write(stdout.style.ERROR(f"Failed to export firewall rules to [{csv_file}]: {e}"))
        return False


def _list(stdout, style) -> bool:
    """List the firewall rules in a table format."""
    try:
        queryset = FirewallAPILog.objects.all()
        headers = [
            "Remote Address",
            "Server Hostname",
            "URL",
            "Blocked",
            "Created At",
            "Updated At",
        ]
        rows = []
        for ip in queryset:
            rows.append([
                str(ip.remote_address or ""),
                str(ip.server_hostname or ""),
                str(ip.url or "")[:50],  # Truncate long URLs
                "yes" if bool(ip.blocked) else "no",
                str(ip.created_at.strftime("%Y-%m-%d %H:%M") if ip.created_at else ""),
                str(ip.updated_at.strftime("%Y-%m-%d %H:%M") if ip.updated_at else ""),
            ])

        # Compute column widths
        if rows:
            widths = [
                max(len(headers[i]), *(len(row[i]) for row in rows))
                for i in range(len(headers))
            ]
        else:
            widths = [len(h) for h in headers]

        # Helper functions to render table
        def sep_line():
            return "+" + "+".join(("-" * (w + 2)) for w in widths) + "+"

        def fmt_line(values):
            return "| " + " | ".join(str(values[i]).ljust(widths[i]) for i in range(len(values))) + " |"

        # Render table
        stdout.write(sep_line())
        stdout.write(fmt_line(headers))
        stdout.write(sep_line())
        for r in rows:
            stdout.write(fmt_line(r))
        stdout.write(sep_line())

        stdout.write(f"\nTotal: {len(rows)} records")
        return True
    except Exception as e:
        stdout.write(style.ERROR(f"Failed to list firewall rules: {e}"))
        return False


def _list_paths(stdout, style) -> bool:
    """List the firewall blacklist and whitelist paths."""
    try:
        # Display whitelist
        stdout.write(style.SUCCESS("\n=== WHITELIST (Allowed Paths) ==="))
        stdout.write(style.WARNING(f"Total: {len(FirewallURLWhiteList)} paths\n"))
        for idx, path in enumerate(FirewallURLWhiteList, 1):
            stdout.write(f"{idx:3d}. {path}")

        # Display blacklist
        stdout.write(style.SUCCESS("\n=== BLACKLIST (Blocked Paths) ==="))
        stdout.write(style.WARNING(f"Total: {len(FirewallURLsList)} paths\n"))
        for idx, path in enumerate(FirewallURLsList, 1):
            stdout.write(f"{idx:3d}. {path}")

        stdout.write("")  # Empty line at the end
        return True
    except Exception as e:
        stdout.write(style.ERROR(f"Failed to list firewall paths: {e}"))
        return False


def _show_status(stdout, style) -> bool:
    """Show current firewall configuration status."""
    try:
        stdout.write(style.SUCCESS("\n=== FIREWALL STATUS ===\n"))

        # Basic settings
        stdout.write(f"Enabled: {style.SUCCESS('Yes') if conf.ENABLED else style.ERROR('No')}")
        stdout.write(f"Firewall URL: {conf.URL or style.WARNING('Not configured')}")
        stdout.write(f"Firewall Port: {conf.PORT}")
        stdout.write(f"Request Timeout: {conf.REQUEST_TIMEOUT}s")
        stdout.write(f"Host Script: {conf.GET_HOST_SCRIPT or style.WARNING('Not configured')}")

        # URL lists
        stdout.write(f"\nMonitored URL Patterns: {len(conf.URLS_LIST)}")
        stdout.write(f"Whitelisted URL Patterns: {len(conf.URL_WHITE_LIST)}")

        # Database stats
        total_logs = FirewallAPILog.objects.count()
        blocked_count = FirewallAPILog.objects.filter(blocked=True).count()
        allowed_count = FirewallAPILog.objects.filter(blocked=False).count()

        stdout.write(f"\nTotal Log Entries: {total_logs}")
        stdout.write(f"  - Blocked IPs: {blocked_count}")
        stdout.write(f"  - Allowed IPs: {allowed_count}")

        stdout.write("")
        return True
    except Exception as e:
        stdout.write(style.ERROR(f"Failed to show status: {e}"))
        return False


class Command(BaseCommand):
    """Django management command for firewall operations."""

    help = "Django Firewall management commands for blocking/allowing IPs and viewing logs."

    def add_arguments(self, parser):
        """Add command line arguments."""
        parser.add_argument(
            "--block", "-b",
            type=str,
            required=False,
            metavar="IP",
            help="Block the specified IP address",
        )
        parser.add_argument(
            "--unblock", "-u",
            type=str,
            required=False,
            metavar="IP",
            help="Unblock (allow) the specified IP address",
        )
        parser.add_argument(
            "--csv", "-c",
            type=str,
            required=False,
            metavar="FILE",
            help="Export the firewall logs to a CSV file",
        )
        parser.add_argument(
            "--list", "-l",
            action="store_true",
            required=False,
            help="List all firewall log entries",
        )
        parser.add_argument(
            "--list-paths", "-p",
            action="store_true",
            required=False,
            help="List all blacklist and whitelist URL patterns",
        )
        parser.add_argument(
            "--status", "-s",
            action="store_true",
            required=False,
            help="Show current firewall configuration status",
        )

    # Disable flake8 complexity check
    # flake8: noqa: C901
    def handle(self, *args, **kwargs):
        """Handle the command execution."""
        # Get arguments
        verbose = kwargs.get("verbosity", 1)
        block_ip = kwargs.get("block")
        unblock_ip = kwargs.get("unblock")
        csv_file = kwargs.get("csv")
        list_logs = kwargs.get("list")
        list_paths = kwargs.get("list_paths")
        status = kwargs.get("status")

        # Show verbose info
        if verbose > 1:
            self.stdout.write(self.style.SUCCESS(f"verbose: {verbose}"))
            self.stdout.write(self.style.SUCCESS(f"block_ip: {block_ip}"))
            self.stdout.write(self.style.SUCCESS(f"unblock_ip: {unblock_ip}"))
            self.stdout.write(self.style.SUCCESS(f"csv_file: {csv_file}"))
            self.stdout.write(self.style.SUCCESS(f"list: {list_logs}"))
            self.stdout.write(self.style.SUCCESS(f"list_paths: {list_paths}"))
            self.stdout.write(self.style.SUCCESS(f"status: {status}"))

        # Process commands
        if status:
            _show_status(self.stdout, self.style)
            return

        if list_paths:
            _list_paths(self.stdout, self.style)
            return

        if list_logs:
            _list(self.stdout, self.style)
            return

        if csv_file:
            result = _export_csv(csv_file, self.stdout)
            if result:
                self.stdout.write(self.style.SUCCESS(f"Successfully exported to [{csv_file}]"))
            return

        # Commands that require firewall to be enabled
        if not conf.ENABLED:
            self.stdout.write(self.style.WARNING(
                "Firewall is not enabled. Set DJANGO_FIREWALL_ENABLED=True in settings."
            ))

        if block_ip:
            if not _validate_ip_address(block_ip):
                raise CommandError(f"Invalid IP address: {block_ip}")

            result = middleware.block_ip(block_ip)
            if result:
                self.stdout.write(self.style.SUCCESS(f"Successfully blocked IP: {block_ip}"))
            else:
                self.stdout.write(self.style.ERROR(f"Failed to block IP: {block_ip}"))
            return

        if unblock_ip:
            if not _validate_ip_address(unblock_ip):
                raise CommandError(f"Invalid IP address: {unblock_ip}")

            result = middleware.allow_ip(unblock_ip)
            if result:
                self.stdout.write(self.style.SUCCESS(f"Successfully unblocked IP: {unblock_ip}"))
            else:
                self.stdout.write(self.style.ERROR(f"Failed to unblock IP: {unblock_ip}"))
            return

        # No command specified, show help
        self.stdout.write(self.style.NOTICE("No command specified. Use --help for usage information."))
        _show_status(self.stdout, self.style)
    # flake8: enable all errors
