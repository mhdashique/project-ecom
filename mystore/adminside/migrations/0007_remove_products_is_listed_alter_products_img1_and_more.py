# Generated by Django 5.0.7 on 2024-08-21 08:50

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('adminside', '0006_products_img1_products_img2_products_img3_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='products',
            name='is_listed',
        ),
        migrations.AlterField(
            model_name='products',
            name='img1',
            field=models.ImageField(blank=True, null=True, upload_to='media/', validators=[django.core.validators.FileExtensionValidator(['jpg', 'jpeg', 'png'])]),
        ),
        migrations.AlterField(
            model_name='products',
            name='img2',
            field=models.ImageField(blank=True, null=True, upload_to='media/', validators=[django.core.validators.FileExtensionValidator(['jpg', 'jpeg', 'png'])]),
        ),
        migrations.AlterField(
            model_name='products',
            name='img3',
            field=models.ImageField(blank=True, null=True, upload_to='media/', validators=[django.core.validators.FileExtensionValidator(['jpg', 'jpeg', 'png'])]),
        ),
        migrations.AlterField(
            model_name='products',
            name='img4',
            field=models.ImageField(blank=True, null=True, upload_to='media/', validators=[django.core.validators.FileExtensionValidator(['jpg', 'jpeg', 'png'])]),
        ),
    ]