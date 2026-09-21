from django.db import migrations, models

import app.models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='chatroom',
            name='controller_token',
            field=models.CharField(
                default=app.models.generate_controller_token,
                editable=False,
                max_length=86,
            ),
        ),
    ]
