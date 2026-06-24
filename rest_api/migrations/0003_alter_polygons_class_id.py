# Generated for preserving polygons when object classes are removed.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("rest_api", "0002_innerpolygons"),
    ]

    operations = [
        migrations.AlterField(
            model_name="polygons",
            name="class_id",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="rest_api.objectclass",
            ),
        ),
    ]
