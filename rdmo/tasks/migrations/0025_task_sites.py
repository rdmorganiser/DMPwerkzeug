# Generated by Django 2.2.2 on 2019-06-17 11:29

from django.db import migrations, models
import django.db.models.manager
import rdmo.tasks.managers


class Migration(migrations.Migration):

    dependencies = [
        ('sites', '0002_alter_domain_unique'),
        ('tasks', '0024_require_uri_prefix'),
    ]

    operations = [
        migrations.AlterModelManagers(
            name='task',
            managers=[
                ('objects', django.db.models.manager.Manager()),
                ('on_site', rdmo.tasks.managers.TaskManager()),
            ],
        ),
        migrations.AddField(
            model_name='task',
            name='sites',
            field=models.ManyToManyField(help_text='The sites this task belongs to (in a multi site setup).', to='sites.Site', verbose_name='Sites'),
        ),
    ]
