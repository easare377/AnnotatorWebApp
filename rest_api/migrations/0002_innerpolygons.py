# Generated for storing polygon holes/background patches.

import django.db.models.deletion
import django.utils.timezone
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("rest_api", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="InnerPolygons",
            fields=[
                (
                    "inner_polygon_id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("points", models.JSONField()),
                (
                    "date_created",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                (
                    "polygon_id",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="inner_polygons",
                        to="rest_api.polygons",
                    ),
                ),
            ],
        ),
    ]
