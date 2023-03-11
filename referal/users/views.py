from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from . import serializers
from . import models


class ReferalUserViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = serializers.ReferalUserSerializer
    # Since we didn't get any specific instructions about that.
    # On production, it may be better to use at least IsAuthenticated
    permission_classes = [AllowAny]
    queryset = models.ReferalUserModel.objects.all()
    # Since we decided to don't override the default ID, tinkering with lookup
    # field to retrieve specific model's instanced by referal_id instead of pk
    lookup_field = "referal_id"
