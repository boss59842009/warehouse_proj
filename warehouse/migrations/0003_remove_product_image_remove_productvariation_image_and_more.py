# Generated by Django 4.2 on 2025-04-16 19:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('warehouse', '0002_product_code'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='image',
        ),
        migrations.RemoveField(
            model_name='productvariation',
            name='image',
        ),
        migrations.AlterField(
            model_name='product',
            name='code',
            field=models.CharField(max_length=50, unique=True, verbose_name='Код товару'),
        ),
    ]
