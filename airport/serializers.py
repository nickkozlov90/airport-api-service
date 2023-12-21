from rest_framework import serializers

from airport.models import (
    Airport, Airplane, Crew, Route, Flight, Order, Ticket,
)


class AirportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airport
        fields = ("id", "name", "closest_big_city")


class AirplaneTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airport
        fields = ("id", "name")


class AirplaneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airplane
        fields = (
            "id", "airplane_type", "name", "rows", "seats_in_row", "capacity"
        )


class CrewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Crew
        fields = ("id", "first_name", "last_name", "full_name")


class RouteSerializer(serializers.ModelSerializer):

    class Meta:
        model = Route
        fields = ("id", "source", "destination", "distance")


class RouteListSerializer(RouteSerializer):
    source = serializers.SlugRelatedField(
        read_only=True, slug_field="name"
    )
    destination = serializers.SlugRelatedField(
        read_only=True, slug_field="name"
    )

    class Meta:
        model = Route
        fields = ("id", "source", "destination")


class RouteDetailSerializer(RouteSerializer):
    source = serializers.SlugRelatedField(
        read_only=True, slug_field="name"
    )
    destination = serializers.SlugRelatedField(
        read_only=True, slug_field="name"
    )

    class Meta:
        model = Route
        fields = ("id", "source", "destination", "distance")


class FlightSerializer(serializers.ModelSerializer):
    route = RouteListSerializer(read_only=True)
    departure_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M")
    arrival_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M")

    class Meta:
        model = Flight
        fields = (
            "id",
            "route",
            "airplane",
            "departure_time",
            "arrival_time",
            "crew"
        )


class FlightListSerializer(FlightSerializer):

    class Meta:
        model = Flight
        fields = (
            "id",
            "route",
            "departure_time",
            "arrival_time",
        )


class FlightDetailSerializer(FlightSerializer):
    airplane = AirplaneSerializer(
        read_only=True
    )
    crew = serializers.StringRelatedField(many=True)

    class Meta:
        model = Flight
        fields = (
            "id",
            "route",
            "airplane",
            "departure_time",
            "arrival_time",
            "crew"
        )


class TicketSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ticket
        fields = ("id", "row", "seat", "flight")


class TicketListSerializer(TicketSerializer):
    flight = FlightListSerializer(many=False, read_only=True)


class OrderSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M")
    tickets = TicketSerializer(many=True, read_only=False, allow_empty=False)

    class Meta:
        model = Order
        fields = ("id", "created_at", "tickets")


class OrderListSerializer(OrderSerializer):
    tickets = TicketListSerializer(many=True, read_only=True)
