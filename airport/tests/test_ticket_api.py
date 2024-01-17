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
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@test.com",
            "testpass",
        )
        self.client.force_authenticate(self.user)

    @classmethod
    def setUpTestData(cls):
        Airline.objects.create(name="Test airline")
        Airplane.objects.create(
            name="Test airplane",
            rows=30,
            seats_in_row=6,
            airplane_type=AirplaneType.objects.create(name="Test type"),
        )
        Route.objects.create(
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
        flight = Flight.objects.create(
            airline=Airline.objects.get(id=1),
            airplane=Airplane.objects.get(id=1),
            route=Route.objects.get(id=1),
            departure_time=datetime(2024, 1, 10, 12, 30, 0),
            arrival_time=datetime(2024, 1, 10, 14, 30, 0),
        )

        Crew.objects.create(first_name="John", last_name="Doe")
        flight.crew.add(1)
        flight.save()

    def test_validate_ticket_with_seat_out_of_range(self):
        user = get_user_model().objects.get(id=1)
        order = Order.objects.create(user=user)
        flight = Flight.objects.get(id=1)
        airplane = Airplane.objects.get(id=1)

        ticket = Ticket(
            seat=1, row=1, flight=flight, order=order
        )

        row = 18
        seat = 7
        message = f"seat number must be in available range: (1, seats_in_row): (1, {airplane.seats_in_row})"

        with self.assertRaisesMessage(ValidationError, message):
            ticket.validate_ticket(row, seat, airplane, ValidationError)

    def test_validate_ticket_with_row_out_of_range(self):
        user = get_user_model().objects.get(id=1)
        order = Order.objects.create(user=user)
        flight = Flight.objects.get(id=1)
        airplane = Airplane.objects.get(id=1)

        ticket = Ticket(
            seat=1, row=1, flight=flight, order=order
        )

        row = 35
        seat = 5
        message = f"row number must be in available range: (1, rows): (1, {airplane.rows})"

        with self.assertRaisesMessage(ValidationError, message):
            ticket.validate_ticket(row, seat, airplane, ValidationError)

    def test_validate_ticket_with_valid_row_and_seat(self):
        user = get_user_model().objects.get(id=1)
        order = Order.objects.create(user=user)
        flight = Flight.objects.get(id=1)
        airplane = Airplane.objects.get(id=1)

        ticket = Ticket(
            seat=1, row=1, flight=flight, order=order
        )

        row = 18
        seat = 5

        self.assertIsNone(ticket.validate_ticket(row, seat, airplane, ValidationError))
