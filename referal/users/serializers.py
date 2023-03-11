from rest_framework import serializers
from users.models import ReferalUserModel
from decimal import Decimal
import logging

log = logging.getLogger(__name__)


class SmallReferalUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReferalUserModel
        fields = (
            "referal_id",
            "referal_lvl"
        )
        read_only_fields = fields

class ReferalUserSerializer(serializers.ModelSerializer):
    invited_by = serializers.CharField(
        read_only=True,
        source = "invited_by.referal_id",
    )

    class Meta:
        model = ReferalUserModel
        exclude = ("id",)


class AddDepositReferalUserSerializer(serializers.ModelSerializer):
    deposit = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal(0.00),
    )

    class Meta:
        model = ReferalUserModel
        fields = (
            "referal_id",
            "referal_lvl",
            "deposit",
        )
        read_only_fields = (
            "referal_id",
            "referal_lvl",
        )
