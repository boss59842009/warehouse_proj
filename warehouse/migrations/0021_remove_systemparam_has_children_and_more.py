# Generated by Django 4.2 on 2025-04-23 19:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('warehouse', '0020_systemparam_has_children'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='systemparam',
            name='has_children',
        ),
        migrations.AddField(
            model_name='systemparam',
            name='has_parent',
            field=models.BooleanField(default=False, verbose_name='Має батьківський параметр'),
        ),
    ]
