import os
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify


class Airport(models.Model):
    name = models.CharField(max_length=255, unique=True)
    code = models.CharField(max_length=255, unique=True)
    closest_big_city = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.name}, {self.closest_big_city} ({self.code})"


def airline_image_file_path(instance, filename):
    _, extension = os.path.splitext(filename)
    filename = f"{slugify(instance.name)}-{uuid.uuid4()}.{extension}"

    return os.path.join("uploads/airlines/", filename)


class Airline(models.Model):
    name = models.CharField(max_length=255, unique=True)
    image = models.ImageField(null=True, upload_to=airline_image_file_path)

    def __str__(self):
        return f"{self.name}"


class AirplaneType(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return f"{self.name}"


class Airplane(models.Model):
    name = models.CharField(max_length=255, unique=True)
    rows = models.IntegerField()
    seats_in_row = models.IntegerField()
    airplane_type = models.ForeignKey(AirplaneType, on_delete=models.CASCADE)

    @property
    def capacity(self) -> int:
        return self.rows * self.seats_in_row

    def __str__(self):
        return self.name


class Route(models.Model):
    source = models.ForeignKey(
        Airport, on_delete=models.CASCADE, related_name="route_sources"
    )
    destination = models.ForeignKey(
        Airport, on_delete=models.CASCADE, related_name="route_destinations"
    )
    distance = models.IntegerField()

    def __str__(self):
        return (
            f"{self.source.short_name}"
            f"({self.source.closest_big_city})"
            f" - {self.destination.short_name}"
            f"({self.destination.closest_big_city})"
        )


class Flight(models.Model):
    route = models.ForeignKey(Route, on_delete=models.CASCADE)
    airline = models.ForeignKey(Airline, related_name="flights", on_delete=models.CASCADE, null=True)
    airplane = models.ForeignKey(Airplane, on_delete=models.CASCADE)
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()

    class Meta:
        ordering = ["departure_time"]

    def __str__(self):
        return (
            f"{self.route}, Departure time: "
            f"{str(self.departure_time.strftime('%Y-%m-%d %H:%M'))}"
        )


class Order(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{str(self.created_at.strftime('%Y-%m-%d %H:%M'))}"


class Ticket(models.Model):
    flight = models.ForeignKey(
        Flight,
        on_delete=models.CASCADE,
        related_name="tickets"
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="tickets"
    )
    row = models.IntegerField()
    seat = models.IntegerField()

    @staticmethod
    def validate_ticket(row, seat, airplane, error_to_raise):
        for ticket_attr_value, ticket_attr_name, airplane_attr_name in [
            (row, "row", "rows"),
            (seat, "seat", "seats_in_row"),
        ]:
            count_attrs = getattr(airplane, airplane_attr_name)
            if not (1 <= ticket_attr_value <= count_attrs):
                raise error_to_raise(
                    {
                        ticket_attr_name: f"{ticket_attr_name} "
                        f"number must be in available range: "
                        f"(1, {airplane_attr_name}): "
                        f"(1, {count_attrs})"
                    }
                )

    def clean(self):
        Ticket.validate_ticket(
            self.row,
            self.seat,
            self.flight.airplane,
            ValidationError,
        )
        self.validate_unique()

    def __str__(self):
        return f"{str(self.flight)} (row: {self.row}, seat: {self.seat})"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["flight", "row", "seat"],
                name="validate_unique"
            )
        ]
        ordering = ["flight__departure_time", "row", "seat"]


