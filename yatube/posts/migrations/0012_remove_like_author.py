# Generated by Django 2.2.16 on 2021-10-25 20:09

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0011_auto_20211025_0315'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='like',
            name='author',
        ),
    ]
