# Generated by Django 4.2 on 2025-04-19 21:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('warehouse', '0010_alter_movementtype_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='productincome',
            name='movement_type',
            field=models.CharField(choices=[('incoming', 'Оприбуткування')], max_length=100, verbose_name='Тип руху'),
        ),
        migrations.DeleteModel(
            name='MovementType',
        ),
    ]
