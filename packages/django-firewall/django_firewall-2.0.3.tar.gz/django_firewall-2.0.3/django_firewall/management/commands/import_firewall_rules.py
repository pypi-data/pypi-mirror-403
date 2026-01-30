"""
Management command to import hardcoded firewall rules into the database.

This command imports the hardcoded firewall rules from endpoint_list.py
into the FirewallPathRule model, making them manageable via Django admin.
"""
import logging

from django.core.management.base import BaseCommand
from django.db import transaction

from django_firewall.endpoint_list import FirewallURLsList, FirewallURLWhiteList
from django_firewall.models import FirewallPathRule

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Import hardcoded firewall rules from endpoint_list.py into the database."""

    help = "Import hardcoded firewall rules from endpoint_list.py into the database"

    def add_arguments(self, parser):
        """Add command line arguments."""
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing rules before importing",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be imported without actually importing",
        )

    def handle(self, *args, **options):
        """Execute the command."""
        clear_existing = options["clear"]
        dry_run = options["dry_run"]

        if dry_run:
            self.stdout.write(
                self.style.WARNING("DRY RUN MODE - No changes will be made")
            )

        # Count existing rules
        existing_blacklist = FirewallPathRule.objects.filter(
            rule_type="blacklist"
        ).count()
        existing_whitelist = FirewallPathRule.objects.filter(
            rule_type="whitelist"
        ).count()

        self.stdout.write("Existing rules in database:")
        self.stdout.write(f"  - Blacklist: {existing_blacklist}")
        self.stdout.write(f"  - Whitelist: {existing_whitelist}")

        if clear_existing:
            if dry_run:
                self.stdout.write(
                    self.style.WARNING("Would delete all existing rules")
                )
            else:
                with transaction.atomic():
                    deleted_count, _ = FirewallPathRule.objects.all().delete()
                    self.stdout.write(
                        self.style.SUCCESS(f"Deleted {deleted_count} existing rules")
                    )

        # Import blacklist rules
        self.stdout.write(f"\nImporting {len(FirewallURLsList)} blacklist rules...")
        blacklist_created = 0
        blacklist_skipped = 0

        for idx, path_pattern in enumerate(FirewallURLsList, start=1):
            # Check if rule already exists
            exists = FirewallPathRule.objects.filter(
                path_pattern=path_pattern, rule_type="blacklist"
            ).exists()

            if exists and not clear_existing:
                blacklist_skipped += 1
                self.stdout.write(
                    f"  [{idx}/{len(FirewallURLsList)}] SKIP: {path_pattern}"
                )
                continue

            if dry_run:
                self.stdout.write(
                    f"  [{idx}/{len(FirewallURLsList)}] Would create: {path_pattern}"
                )
            else:
                FirewallPathRule.objects.create(
                    path_pattern=path_pattern,
                    rule_type="blacklist",
                    enabled=True,
                    priority=idx * 10,  # Space out priorities for easy reordering
                    description="Imported from hardcoded blacklist",
                )
                blacklist_created += 1
                self.stdout.write(
                    f"  [{idx}/{len(FirewallURLsList)}] CREATE: {path_pattern}"
                )

        # Import whitelist rules
        self.stdout.write(
            f"\nImporting {len(FirewallURLWhiteList)} whitelist rules..."
        )
        whitelist_created = 0
        whitelist_skipped = 0

        for idx, path_pattern in enumerate(FirewallURLWhiteList, start=1):
            # Check if rule already exists
            exists = FirewallPathRule.objects.filter(
                path_pattern=path_pattern, rule_type="whitelist"
            ).exists()

            if exists and not clear_existing:
                whitelist_skipped += 1
                self.stdout.write(
                    f"  [{idx}/{len(FirewallURLWhiteList)}] SKIP: {path_pattern}"
                )
                continue

            if dry_run:
                self.stdout.write(
                    f"  [{idx}/{len(FirewallURLWhiteList)}] Would create: {path_pattern}"
                )
            else:
                FirewallPathRule.objects.create(
                    path_pattern=path_pattern,
                    rule_type="whitelist",
                    enabled=True,
                    priority=idx * 10,  # Space out priorities for easy reordering
                    description="Imported from hardcoded whitelist",
                )
                whitelist_created += 1
                self.stdout.write(
                    f"  [{idx}/{len(FirewallURLWhiteList)}] CREATE: {path_pattern}"
                )

        # Summary
        self.stdout.write("\n" + "=" * 60)
        if dry_run:
            self.stdout.write(self.style.SUCCESS("DRY RUN SUMMARY:"))
            self.stdout.write(f"Would create {len(FirewallURLsList)} blacklist rules")
            self.stdout.write(
                f"Would create {len(FirewallURLWhiteList)} whitelist rules"
            )
        else:
            self.stdout.write(self.style.SUCCESS("IMPORT SUMMARY:"))
            self.stdout.write(
                f"Blacklist: {blacklist_created} created, {blacklist_skipped} skipped"
            )
            self.stdout.write(
                f"Whitelist: {whitelist_created} created, {whitelist_skipped} skipped"
            )
            self.stdout.write(self.style.SUCCESS("\nImport completed successfully!"))
            self.stdout.write(
                "\nYou can now manage these rules via the Django admin interface."
            )
