from django.db import migrations
from django.db import models


class Migration(migrations.Migration):

    dependencies = [
        ("taskqueue", "0003_alter_taskreconstruction_id"),
    ]

    operations = [
        migrations.AddField(
            model_name="taskreconstruction",
            name="callable_name_meta",
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
    ]
