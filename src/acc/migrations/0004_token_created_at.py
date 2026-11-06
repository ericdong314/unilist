import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('acc', '0003_alter_token_uid'),
    ]

    operations = [
        migrations.AddField(
            model_name='token',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
