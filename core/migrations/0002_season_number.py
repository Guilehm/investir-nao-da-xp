# Generated by Django 2.1.5 on 2019-01-23 23:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='season',
            name='number',
            field=models.SmallIntegerField(blank=True, null=True),
        ),
    ]
