from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet

from airport.models import Airport
from airport.serializers import (
    AirportSerializer,
)


class AirportViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    queryset = Airport.objects.all()
    serializer_class = AirportSerializer
