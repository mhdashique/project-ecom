# Generated by Django 5.0.7 on 2024-09-14 19:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0006_alter_coupon_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='discount',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='order',
            name='sub_total',
            field=models.DecimalField(blank=True, decimal_places=2, default=0.0, max_digits=10, null=True),
        ),
    ]
