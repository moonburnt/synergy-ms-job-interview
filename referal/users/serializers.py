from rest_framework import serializers
from users.models import ReferalUserModel
import logging

log = logging.getLogger(__name__)


class ReferalUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReferalUserModel
        fields = (
            "referal_id",
            "referal_lvl"
        )
        read_only_fields = fields
