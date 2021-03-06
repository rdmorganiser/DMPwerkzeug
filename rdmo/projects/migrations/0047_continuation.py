# Generated by Django 2.2.16 on 2021-01-20 16:47

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('questions', '0054_meta'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('projects', '0046_project_mptt'),
    ]

    operations = [
        migrations.CreateModel(
            name='Continuation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(editable=False, verbose_name='created')),
                ('updated', models.DateTimeField(editable=False, verbose_name='updated')),
                ('project', models.ForeignKey(help_text='The project for this continuation.', on_delete=django.db.models.deletion.CASCADE, related_name='+', to='projects.Project', verbose_name='Project')),
                ('questionset', models.ForeignKey(help_text='The question set for this continuation.', on_delete=django.db.models.deletion.CASCADE, related_name='+', to='questions.QuestionSet', verbose_name='Question set')),
                ('user', models.ForeignKey(help_text='The user for this continuation.', on_delete=django.db.models.deletion.CASCADE, related_name='+', to=settings.AUTH_USER_MODEL, verbose_name='User')),
            ],
            options={
                'verbose_name': 'Continuation',
                'verbose_name_plural': 'Continuations',
                'ordering': ('user', 'project'),
            },
        ),
    ]
