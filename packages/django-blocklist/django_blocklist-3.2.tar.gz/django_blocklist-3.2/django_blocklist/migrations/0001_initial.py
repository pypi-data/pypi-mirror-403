from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="BlockedIP",
            fields=[
                ("ip", models.GenericIPAddressField(primary_key=True, serialize=False, verbose_name="IP")),
                ("first_seen", models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ("last_seen", models.DateTimeField(blank=True, db_index=True, null=True)),
                ("reason", models.CharField(blank=True, db_index=True, default="", max_length=255)),
                (
                    "tally",
                    models.IntegerField(
                        default=1, help_text="Number of times this IP has been blocked since first_seen"
                    ),
                ),
                (
                    "cooldown",
                    models.IntegerField(
                        default=7,
                        help_text="Cooldown period; number of days with no connections before IP is dropped from blocklist",
                    ),
                ),
            ],
            options={
                "verbose_name": "blocked IP",
                "ordering": ["-last_seen", "ip"],
                "get_latest_by": "first_seen",
            },
        ),
    ]
