# Generated by Django 4.0.5 on 2023-03-15 19:31

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0006_remove_referalusermodel_affected_parents_deposit_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="referalusermodel",
            name="granted_referal_bonuses_counter",
        ),
    ]
