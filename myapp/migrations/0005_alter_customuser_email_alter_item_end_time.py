# Generated by Django 5.1.4 on 2025-07-01 03:08

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0004_alter_item_end_time_passwordresetotp'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='email',
            field=models.EmailField(blank=True, max_length=254, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name='item',
            name='end_time',
            field=models.DateTimeField(default=datetime.datetime(2025, 7, 16, 3, 8, 58, 496560, tzinfo=datetime.timezone.utc)),
        ),
    ]
