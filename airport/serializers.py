from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.validators import UniqueTogetherValidator

from airport.models import (
    Airport,
    Airline,
    Airplane,
    Route,
    Flight,
    Order,
    Ticket,
)


class AirportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airport
        fields = ("id", "name", "closest_big_city")


class AirlineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airline
        fields = ("id", "name")


class AirlineListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airline
        fields = ("id", "name", "image")


class AirlineImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airline
        fields = ("id", "image")


class AirplaneTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airport
        fields = ("id", "name")


class AirplaneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airplane
        fields = (
            "id",
            "airplane_type",
            "name",
            "rows",
            "seats_in_row",
            "capacity"
        )


class RouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        fields = ("id", "source", "destination", "distance")


class RouteListSerializer(RouteSerializer):
    source = serializers.SlugRelatedField(
        read_only=True,
        slug_field="name"
    )
    destination = serializers.SlugRelatedField(
        read_only=True,
        slug_field="name"
    )

    class Meta:
        model = Route
        fields = ("id", "source", "destination")


class RouteDetailSerializer(RouteSerializer):
    source = serializers.SlugRelatedField(
        read_only=True,
        slug_field="name"
    )
    destination = serializers.SlugRelatedField(
        read_only=True,
        slug_field="name"
    )

    class Meta:
        model = Route
        fields = ("id", "source", "destination", "distance")


class FlightSerializer(serializers.ModelSerializer):
    route = RouteListSerializer(read_only=True)
    departure_time = serializers.DateTimeField(
        read_only=True, format="%Y-%m-%d %H:%M"
    )
    arrival_time = serializers.DateTimeField(
        read_only=True, format="%Y-%m-%d %H:%M"
    )

    class Meta:
        model = Flight
        fields = (
            "id",
            "route",
            "departure_time",
            "arrival_time",
        )


class FlightListSerializer(FlightSerializer):
    route_source = serializers.CharField(
        source="route.source", read_only=True
    )
    route_destination = serializers.CharField(
        source="route.destination", read_only=True
    )
    airplane_num_seats = serializers.IntegerField(
        source="airplane.capacity",
        read_only=True,
    )
    tickets_available = serializers.IntegerField(read_only=True)
    airline_image = serializers.ImageField(
        source="airline.image",
        read_only=True
    )

    class Meta:
        model = Flight
        fields = (
            "id",
            "route_source",
            "route_destination",
            "departure_time",
            "arrival_time",
            "airplane_num_seats",
            "tickets_available",
            "airline_image",
        )


class TicketSerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        data = super(TicketSerializer, self).validate(attrs=attrs)
        Ticket.validate_ticket(
            attrs["row"],
            attrs["seat"],
            attrs["flight"].airplane,
            ValidationError
        )
        return data

    class Meta:
        model = Ticket
        fields = ("id", "row", "seat", "flight")
        validators = [
            UniqueTogetherValidator(
                queryset=Ticket.objects.all(),
                fields=["flight", "row", "seat"],
                message="Seat with entered data has been already booked."
            )
        ]


class TicketListSerializer(TicketSerializer):
    flight = FlightListSerializer(many=False, read_only=True)


class TicketSeatsSerializer(TicketSerializer):
    class Meta:
        model = Ticket
        fields = ("row", "seat")


class FlightDetailSerializer(FlightSerializer):
    airplane_name = serializers.CharField(
        read_only=True,
        source="airplane.name"
    )
    airplane_type = serializers.CharField(
        read_only=True,
        source="airplane.airplane_type"
    )
    airline = AirlineListSerializer()
    taken_tickets = TicketSeatsSerializer(
        source="tickets",
        many=True,
        read_only=True,
    )

    class Meta:
        model = Flight
        fields = (
            "id",
            "route",
            "departure_time",
            "arrival_time",
            "airline",
            "airplane_name",
            "airplane_type",
            "taken_tickets",
        )


class OrderSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(many=True, read_only=False, allow_empty=False)

    class Meta:
        model = Order
        fields = ("id", "created_at", "tickets")

    def create(self, validated_data):
        with transaction.atomic():
            tickets_data = validated_data.pop("tickets")
            order = Order.objects.create(**validated_data)
            for ticket_data in tickets_data:
                Ticket.objects.create(order=order, **ticket_data)
            return order


class OrderListSerializer(OrderSerializer):
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M")
    tickets = TicketListSerializer(many=True, read_only=True)
