# Generated by Django 5.0.7 on 2024-10-17 04:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0010_orderedproducts_return_request'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='payment_status',
            field=models.CharField(choices=[('Paid', 'Paid'), ('Pending', 'Pending')], null=True),
        ),
    ]