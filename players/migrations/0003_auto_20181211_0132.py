# Generated by Django 2.1.4 on 2018-12-11 01:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('players', '0002_auto_20181211_0131'),
    ]

    operations = [
        migrations.AlterField(
            model_name='player',
            name='platforms',
            field=models.ManyToManyField(blank=True, related_name='players', to='core.Platform'),
        ),
        migrations.AlterField(
            model_name='player',
            name='seasons',
            field=models.ManyToManyField(blank=True, related_name='players', to='core.Season'),
        ),
    ]
