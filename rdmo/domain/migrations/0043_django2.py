# Generated by Django 2.2rc1 on 2019-03-26 13:29

from django.db import migrations
import django.db.models.deletion
import mptt.fields


class Migration(migrations.Migration):

    dependencies = [
        ('domain', '0042_remove_null_true'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='attribute',
            options={'ordering': ('uri',), 'verbose_name': 'Attribute', 'verbose_name_plural': 'Attributes'},
        ),
        migrations.AlterField(
            model_name='attribute',
            name='parent',
            field=mptt.fields.TreeForeignKey(blank=True, help_text='Parent attribute in the domain model.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='children', to='domain.Attribute', verbose_name='Parent attribute'),
        ),
    ]
