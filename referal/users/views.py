from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from . import serializers
from . import models


class ReferalUserViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = serializers.SmallReferalUserSerializer
    # Since we didn't get any specific instructions about that.
    # On production, it may be better to use at least IsAuthenticated
    permission_classes = [AllowAny]
    queryset = models.ReferalUserModel.objects.all()
    # Since we decided to don't override the default ID, tinkering with lookup
    # field to retrieve specific model's instanced by referal_id instead of pk
    lookup_field = "referal_id"

    def get_serializer_class(self):
        if self.action == "add_deposit":
            return serializers.AddDepositReferalUserSerializer
        elif self.action == "detailed":
            return serializers.ReferalUserSerializer
        else:
            return self.serializer_class

    # We could allow adding deposits via PATCH requests, but that may be a bit
    # more troublesome to implement
    @action(
        methods=("post",),
        detail=True,
    )
    def add_deposit(self, request, **kwargs) -> Response:
        """Add deposit for to the specific user's wallet"""

        user: models.ReferalUserModel = self.get_object()

        serialized = self.get_serializer(
            instance=user,
            data=request.data,
        )

        serialized.is_valid(raise_exception=True)
        serialized.save()

        return Response(
            data=serialized.data,
            status=status.HTTP_200_OK,
        )

    @action(
        methods=("get",),
        detail=True,
    )
    def detailed(self, request, **kwargs) -> Response:
        """Get detailed info about user"""

        user: models.ReferalUserModel = self.get_object()

        serialized = self.get_serializer(
            instance=user,
        )

        return Response(
            data=serialized.data,
            status=status.HTTP_200_OK,
        )
