from datetime import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient

from airport.models import (
    Flight, Airport, Route, Airline, Airplane, Crew, AirplaneType, Order,
    Ticket
)


class AuthenticatedTicketApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client = APIClient()
        cls.user = get_user_model().objects.create_user(
            "test@test.com",
            "testpass",
        )
        cls.client.force_authenticate(cls.user)

        airline = Airline.objects.create(name="Test airline")
        cls.airplane = Airplane.objects.create(
            name="Test airplane",
            rows=30,
            seats_in_row=6,
            airplane_type=AirplaneType.objects.create(name="Test type"),
        )
        route = Route.objects.create(
            source=Airport.objects.create(
                name="Heathrow Airport",
                code="LHR",
                closest_big_city="London"
            ),
            destination=Airport.objects.create(
                name="Charles de Gaulle Airport",
                code="CDG",
                closest_big_city="Paris"
            ),
            distance=500
        )
        cls.flight = flight = Flight.objects.create(
            airline=airline,
            airplane=cls.airplane,
            route=route,
            departure_time=datetime(2024, 1, 10, 12, 30, 0),
            arrival_time=datetime(2024, 1, 10, 14, 30, 0),
        )

        crew = Crew.objects.create(first_name="John", last_name="Doe")
        cls.flight.crew.add(crew.id)
        cls.flight.save()

        cls.order = Order.objects.create(user=cls.user)
        cls.ticket = Ticket(
            seat=1, row=1, flight=cls.flight, order=cls.order
        )

    def test_validate_ticket_with_seat_out_of_range(self):
        row = 18
        seat = 7
        message = f"seat number must be in available range: " \
                  f"(1, seats_in_row): (1, {self.airplane.seats_in_row})"

        with self.assertRaisesMessage(ValidationError, message):
            self.ticket.validate_ticket(
                row, seat, self.airplane, ValidationError
            )

    def test_validate_ticket_with_row_out_of_range(self):
        row = 35
        seat = 5
        message = f"row number must be in available range: " \
                  f"(1, rows): (1, {self.airplane.rows})"

        with self.assertRaisesMessage(ValidationError, message):
            self.ticket.validate_ticket(
                row, seat, self.airplane, ValidationError
            )

    def test_validate_ticket_with_valid_row_and_seat(self):
        row = 18
        seat = 5

        self.assertIsNone(
            self.ticket.validate_ticket(
                row, seat, self.airplane, ValidationError
            )
        )
