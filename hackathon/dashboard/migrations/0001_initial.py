# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2019-03-02 17:16
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Input',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(max_length=200)),
                ('value', models.FloatField(default=0)),
                ('timestamp', models.DateTimeField(verbose_name='timestamp')),
            ],
        ),
    ]
