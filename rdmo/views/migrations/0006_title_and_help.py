# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2017-01-27 15:42
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('views', '0005_meta'),
    ]

    operations = [
        migrations.AddField(
            model_name='view',
            name='help_de',
            field=models.TextField(blank=True, help_text='The German help text for this view.', null=True, verbose_name='Help (de)'),
        ),
        migrations.AddField(
            model_name='view',
            name='help_en',
            field=models.TextField(blank=True, help_text='The English help text for this view.', null=True, verbose_name='Help (en)'),
        ),
        migrations.AddField(
            model_name='view',
            name='title_de',
            field=models.CharField(blank=True, help_text='The German title for this view.', max_length=256, null=True, verbose_name='Title (de)'),
        ),
        migrations.AddField(
            model_name='view',
            name='title_en',
            field=models.CharField(blank=True, help_text='The English title for this view.', max_length=256, null=True, verbose_name='Title (en)'),
        ),
    ]
