from django.urls import path, include
from rest_framework import routers

from airport.views import (
    AirportViewSet,
    AirlineViewSet,
    AirplaneTypeViewSet,
    AirplaneViewSet,
    RouteViewSet,
    CrewViewSet,
    FlightViewSet,
    OrderViewSet,
)

router = routers.DefaultRouter()
router.register("airports", AirportViewSet)
router.register("airlines", AirlineViewSet)
router.register("airplane-types", AirplaneTypeViewSet)
router.register("airplanes", AirplaneViewSet)
router.register("crews", CrewViewSet)
router.register("routes", RouteViewSet)
router.register("flights", FlightViewSet)
router.register("orders", OrderViewSet)


urlpatterns = [path("", include(router.urls))]

app_name = "airport"
