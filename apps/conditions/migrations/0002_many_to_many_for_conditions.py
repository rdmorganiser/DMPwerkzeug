# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-07-26 15:00
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('conditions', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='condition',
            name='content_type',
        ),
        migrations.RemoveField(
            model_name='condition',
            name='object_id',
        ),
    ]
