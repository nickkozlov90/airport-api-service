from datetime import datetime

from django.contrib.auth import get_user_model
from django.db.models import F, Count
from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from airport.models import (
    Flight, Airport, Route, Airline, Airplane, Crew, AirplaneType, Order, Ticket
)
from airport.serializers import FlightDetailSerializer, FlightListSerializer

FLIGHT_URL = reverse("airport:flight-list")


def detail_url(flight_id):
    return reverse("airport:flight-detail", args=[flight_id])


class UnauthenticatedFlightApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    @classmethod
    def setUpTestData(cls):
        cls.airline = Airline.objects.create(name="Test airline")
        cls.airplane = Airplane.objects.create(
            name="Test airplane",
            rows=30,
            seats_in_row=6,
            airplane_type=AirplaneType.objects.create(name="Test type"),
        )
        cls.route_1 = Route.objects.create(
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
            distance=400
        )
        cls.route_2 = Route.objects.create(
            source=Airport.objects.create(
                name="Dubai International Airport",
                code="DXB",
                closest_big_city="Dubai"
            ),
            destination=Airport.objects.create(
                name="Sydney Airport",
                code="SYD",
                closest_big_city="Sydney"
            ),
            distance=700
        )
        cls.crew = Crew.objects.create(first_name="John", last_name="Doe")

        cls.flight_1 = Flight.objects.create(
            airline=cls.airline,
            airplane=cls.airplane,
            route=cls.route_1,
            departure_time="2022-06-02 14:00",
            arrival_time="2022-06-02 20:00",
        )
        cls.flight_1.crew.add(cls.crew.id)
        cls.flight_1.save()

        cls.flight_2 = Flight.objects.create(
            airline=cls.airline,
            airplane=cls.airplane,
            route=cls.route_2,
            departure_time="2022-07-04 22:00",
            arrival_time="2022-07-05 11:00",
        )
        cls.flight_2.crew.add(cls.crew.id)
        cls.flight_2.save()

    def test_retrieve_flight_detail(self):
        url = detail_url(self.flight_1.id)
        res = self.client.get(url)

        serializer = FlightDetailSerializer(self.flight_1)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_list_flights(self):
        res = self.client.get(FLIGHT_URL)
        flights = Flight.objects.all().annotate(
                tickets_available=F("airplane__rows")
                * F("airplane__seats_in_row")
                - Count("tickets")
            ).order_by("departure_time")
        serializer = FlightListSerializer(flights, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_filter_flights_by_source(self):
        target_source = self.flight_1.route.source

        route = Route.objects.create(
            source=target_source,
            destination=self.route_2.destination,
            distance=1000
        )

        Flight.objects.create(
            airline=self.airline,
            airplane=self.airplane,
            route=route,
            departure_time="2022-07-04 21:00",
            arrival_time="2022-07-05 12:00",
        )

        res = self.client.get(
            FLIGHT_URL, {"source": target_source.name}
        )

        self.assertEqual(len(res.data["results"]), 2)
        for flight in res.data["results"]:
            self.assertEqual(flight["route_source"], str(target_source))

    def test_filter_flights_by_destination(self):
        target_destination = self.flight_2.route.destination

        route = Route.objects.create(
            source=self.route_1.source,
            destination=target_destination,
            distance=1000
        )

        Flight.objects.create(
            airline=self.airline,
            airplane=self.airplane,
            route=route,
            departure_time="2022-07-04 21:00",
            arrival_time="2022-07-05 12:00",
        )

        res = self.client.get(
            FLIGHT_URL, {"destination": target_destination.name}
        )

        self.assertEqual(len(res.data["results"]), 2)
        for flight in res.data["results"]:
            self.assertEqual(flight["route_destination"], str(target_destination))

    def test_tickets_available_if_zero_tickets_ordered(self):
        res = self.client.get(FLIGHT_URL)
        tickets_available = self.flight_1.airplane.capacity
        self.assertEqual(
            res.data["results"][0]["tickets_available"],
            tickets_available
        )

    def test_tickets_available_if_one_ticket_ordered(self):
        user = get_user_model().objects.create_user(
            "test@test.com",
            "testpass",
        )
        order = Order.objects.create(user=user)
        Ticket.objects.create(
            flight=self.flight_1,
            order=order,
            row=1,
            seat=1,
        )
        tickets_ordered = self.flight_1.tickets.count()
        res = self.client.get(FLIGHT_URL)

        tickets_available = self.flight_1.airplane.capacity
        self.assertEqual(
            res.data["results"][0]["tickets_available"],
            tickets_available - tickets_ordered
        )

    def test_tickets_available_if_all_tickets_ordered(self):
        user = get_user_model().objects.create_user(
            "test@test.com",
            "testpass",
        )
        order = Order.objects.create(user=user)
        for row in range(self.flight_1.airplane.rows):
            for seat in range(self.flight_1.airplane.seats_in_row):
                Ticket.objects.create(
                    flight=self.flight_1,
                    order=order,
                    row=row,
                    seat=seat,
                )

        res = self.client.get(FLIGHT_URL)

        self.assertEqual(res.data["results"][0]["tickets_available"], 0)

    def test_create_flight_by_not_admin_is_forbidden(self):
        payload = {
            "airline": self.airline.id,
            "airplane": self.airplane.id,
            "route": self.route_1.id,
            "departure_time": "2022-07-04 21:00",
            "arrival_time": "2022-07-05 12:00",
        }

        res = self.client.post(FLIGHT_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@test.com",
            "testpass",
        )
        self.client.force_authenticate(self.user)

        res = self.client.post(FLIGHT_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminFlightApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "admin@admin.com", "testpass", is_staff=True
        )
        self.client.force_authenticate(self.user)

    @classmethod
    def setUpTestData(cls):
        cls.airline = Airline.objects.create(name="Test airline")
        cls.airplane = Airplane.objects.create(
            name="Test airplane",
            rows=30,
            seats_in_row=6,
            airplane_type=AirplaneType.objects.create(name="Test type"),
        )
        cls.route = Route.objects.create(
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
            distance=400
        )
        cls.crew = Crew.objects.create(first_name="John", last_name="Doe")

    def test_create_flight(self):
        payload = {
            "airline": self.airline.id,
            "airplane": self.airplane.id,
            "route": self.route.id,
            "departure_time": "2022-07-04 21:00",
            "arrival_time": "2022-07-05 12:00",
            "crew": [self.crew.id],
        }

        res = self.client.post(FLIGHT_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        flight = Flight.objects.get(id=res.data["id"])
        for key in ("airline", "airplane", "route"):
            self.assertEqual(payload[key], getattr(flight, key).id)
        for key in ("departure_time", "arrival_time"):
            self.assertEqual(payload[key], getattr(flight, key).strftime("%Y-%m-%d %H:%M"))

    def test_update_flight(self):
        flight = Flight.objects.create(
            airline=self.airline,
            airplane=self.airplane,
            route=self.route,
            departure_time=datetime(2024, 1, 10, 12, 30, 0),
            arrival_time=datetime(2024, 1, 10, 14, 30, 0),
        )
        flight.crew.add(self.crew.id)
        flight.save()

        airline_2 = Airline.objects.create(name="Another airline")
        payload = {
            "airline": airline_2.id,
            "departure_time": "2022-06-02 14:00"
        }

        res = self.client.patch(
            detail_url(flight.id),
            data=payload
        )
        flight.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.assertEqual(
            payload["departure_time"],
            flight.departure_time.strftime('%Y-%m-%d %H:%M')
        )
        self.assertEqual(payload["airline"], flight.airline.id)

    def test_delete_flight_not_allowed(self):
        flight = Flight.objects.create(
            airline=self.airline,
            airplane=self.airplane,
            route=self.route,
            departure_time=datetime(2024, 1, 10, 12, 30, 0),
            arrival_time=datetime(2024, 1, 10, 14, 30, 0),
        )
        flight.crew.add(self.crew.id)
        flight.save()

        url = detail_url(flight.id)

        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
