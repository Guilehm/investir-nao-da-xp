# Generated by Django 2.1.5 on 2019-01-24 01:09

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('communications', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='communication',
            options={'ordering': ('-date_added',)},
        ),
    ]
