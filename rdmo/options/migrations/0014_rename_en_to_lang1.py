# -*- coding: utf-8 -*-
# Generated by Django 1.11.18 on 2019-01-29 16:18
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('options', '0013_order'),
    ]

    operations = [
        migrations.RenameField(
            model_name='option',
            old_name='text_en',
            new_name='text_lang1',
        ),
    ]