# Generated by Django 5.0.7 on 2024-08-10 06:27

import imagekit.models.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('adminside', '0005_remove_products_img1_remove_products_img2_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='products',
            name='img1',
            field=imagekit.models.fields.ProcessedImageField(null=True, upload_to='media/'),
        ),
        migrations.AddField(
            model_name='products',
            name='img2',
            field=imagekit.models.fields.ProcessedImageField(blank=True, null=True, upload_to='media/'),
        ),
        migrations.AddField(
            model_name='products',
            name='img3',
            field=imagekit.models.fields.ProcessedImageField(blank=True, null=True, upload_to='media/'),
        ),
        migrations.AddField(
            model_name='products',
            name='img4',
            field=imagekit.models.fields.ProcessedImageField(blank=True, null=True, upload_to='media/'),
        ),
    ]
