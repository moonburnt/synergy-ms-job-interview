# Generated by Django 4.0.5 on 2023-03-11 12:51

from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0004_referalusermodel_affected_parents_deposit_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="referalusermodel",
            name="bonus_deposit",
            field=models.DecimalField(
                decimal_places=2, default=Decimal("0"), max_digits=10
            ),
        ),
    ]
