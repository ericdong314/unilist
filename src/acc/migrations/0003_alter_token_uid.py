import uuid

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('acc', '0002_token'),
    ]

    operations = [
        migrations.AlterField(
            model_name='token',
            name='uid',
            field=models.CharField(default=uuid.uuid4, max_length=40, unique=True),
        ),
    ]
