# Generated by Django 4.2 on 2025-04-16 21:16

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('warehouse', '0003_remove_product_image_remove_productvariation_image_and_more'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='productvariation',
            unique_together=set(),
        ),
        migrations.RemoveField(
            model_name='productvariation',
            name='variation_name',
        ),
    ]
