# Generated by Django 4.0.5 on 2023-03-15 17:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0005_referalusermodel_bonus_deposit"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="referalusermodel",
            name="affected_parents_deposit",
        ),
        migrations.AddField(
            model_name="referalusermodel",
            name="granted_referal_bonuses_counter",
            field=models.IntegerField(default=0),
        ),
    ]