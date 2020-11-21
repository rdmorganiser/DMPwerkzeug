# Generated by Django 2.2.16 on 2020-11-10 14:32

import django.db.models.deletion
from django.db import migrations, models

import rdmo.projects.models.value


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0043_meta'),
    ]

    operations = [
        migrations.AddField(
            model_name='value',
            name='file',
            field=models.FileField(help_text='The file stored for this value.', null=True, upload_to=rdmo.projects.models.value.get_file_upload_to, verbose_name='File'),
        ),
        migrations.AlterField(
            model_name='value',
            name='option',
            field=models.ForeignKey(blank=True, help_text='The option stored for this value.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='values', to='options.Option', verbose_name='Option'),
        ),
        migrations.AlterField(
            model_name='value',
            name='value_type',
            field=models.CharField(choices=[('text', 'Text'), ('url', 'URL'), ('integer', 'Integer'), ('float', 'Float'), ('boolean', 'Boolean'), ('datetime', 'Datetime'), ('option', 'Option'), ('file', 'File')], default='text', help_text='Type of this value.', max_length=8, verbose_name='Value type'),
        ),
    ]