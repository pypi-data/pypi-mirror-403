from django.db import migrations, models


class Migration(migrations.Migration):
    """Create the FirewallAPILog table."""

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="FirewallAPILog",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "remote_address",
                    models.GenericIPAddressField(
                        verbose_name="Remote Address",
                        help_text="The IP address of the client making the request.",
                    ),
                ),
                (
                    "server_hostname",
                    models.CharField(
                        max_length=255,
                        verbose_name="Server Hostname",
                        help_text="The hostname of the server that received the request.",
                    ),
                ),
                (
                    "url",
                    models.TextField(
                        verbose_name="Request URL",
                        help_text="The URL path that was requested.",
                    ),
                ),
                (
                    "blocked",
                    models.BooleanField(
                        default=True,
                        verbose_name="Blocked",
                        help_text="Whether this IP is currently blocked.",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        verbose_name="Created At",
                        help_text="When this log entry was first created.",
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True,
                        verbose_name="Updated At",
                        help_text="When this log entry was last updated.",
                    ),
                ),
            ],
            options={
                "verbose_name": "Firewall API Log",
                "verbose_name_plural": "Firewall API Logs",
                "ordering": ["-created_at"],
                "unique_together": {("remote_address", "url")},
            },
        ),
        migrations.AddIndex(
            model_name="firewallapilog",
            index=models.Index(
                fields=["remote_address"],
                name="django_fire_remote__idx",
            ),
        ),
        migrations.AddIndex(
            model_name="firewallapilog",
            index=models.Index(
                fields=["blocked"],
                name="django_fire_blocked_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="firewallapilog",
            index=models.Index(
                fields=["-created_at"],
                name="django_fire_created_idx",
            ),
        ),
    ]
