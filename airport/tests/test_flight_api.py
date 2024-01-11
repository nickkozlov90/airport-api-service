from datetime import datetime

from django.contrib.auth import get_user_model
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
            distance=400
        )
        Route.objects.create(
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
        Crew.objects.create(first_name="John", last_name="Doe")

        flight_1 = Flight.objects.create(
            airline=Airline.objects.get(id=1),
            airplane=Airplane.objects.get(id=1),
            route=Route.objects.get(id=1),
            departure_time="2022-06-02 14:00",
            arrival_time="2022-06-02 20:00",
        )
        flight_1.crew.add(1)
        flight_1.save()

        flight_2 = Flight.objects.create(
            airline=Airline.objects.get(id=1),
            airplane=Airplane.objects.get(id=1),
            route=Route.objects.get(id=2),
            departure_time="2022-07-04 22:00",
            arrival_time="2022-07-05 11:00",
        )
        flight_2.crew.add(1)
        flight_2.save()

    def test_retrieve_flight_detail(self):
        flight = Flight.objects.get(id=1)
        url = detail_url(flight.id)
        res = self.client.get(url)

        serializer = FlightDetailSerializer(flight)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_list_flights(self):
        res = self.client.get(FLIGHT_URL)
        flights = Flight.objects.all()
        serializer = FlightListSerializer(flights)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data["results"]), 2)

    def test_filter_flights_by_source(self):
        target_source = Flight.objects.get(id=1).route.source

        route = Route.objects.create(
            source=target_source,
            destination=Airport.objects.get(id=4),
            distance=1000
        )

        Flight.objects.create(
            airline=Airline.objects.get(id=1),
            airplane=Airplane.objects.get(id=1),
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
        target_destination = Airport.objects.get(closest_big_city="Sydney")

        route = Route.objects.create(
            source=Airport.objects.get(closest_big_city="London"),
            destination=target_destination,
            distance=1000
        )

        Flight.objects.create(
            airline=Airline.objects.get(id=1),
            airplane=Airplane.objects.get(id=1),
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
        tickets_available = Flight.objects.get(id=1).airplane.capacity
        self.assertEqual(
            res.data["results"][0]["tickets_available"],
            tickets_available
        )

    def test_tickets_available_if_one_ticket_ordered(self):
        user = get_user_model().objects.create_user(
            "test@test.com",
            "testpass",
        )
        flight = Flight.objects.get(id=1)
        order = Order.objects.create(user=user)
        Ticket.objects.create(
            flight=flight,
            order=order,
            row=1,
            seat=1,
        )
        tickets_ordered = flight.tickets.count()
        res = self.client.get(FLIGHT_URL)

        tickets_available = Flight.objects.get(id=1).airplane.capacity
        self.assertEqual(
            res.data["results"][0]["tickets_available"],
            tickets_available - tickets_ordered
        )

    def test_tickets_available_if_all_tickets_ordered(self):
        user = get_user_model().objects.create_user(
            "test@test.com",
            "testpass",
        )

        flight = Flight.objects.get(id=1)
        order = Order.objects.create(user=user)
        for row in range(flight.airplane.rows):
            for seat in range(flight.airplane.seats_in_row):
                Ticket.objects.create(
                    flight=flight,
                    order=order,
                    row=row,
                    seat=seat,
                )

        res = self.client.get(FLIGHT_URL)

        self.assertEqual(res.data["results"][0]["tickets_available"], 0)

    def test_create_flight_forbidden(self):
        payload = {
            "airline": Airline.objects.get(id=1),
            "airplane": Airplane.objects.get(id=1),
            "route": Route.objects.get(id=1),
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
            distance=400
        )
        Crew.objects.create(first_name="John", last_name="Doe")

    def test_create_flight(self):
        payload = {
            "airline": 1,  # Airline.objects.get(id=1)
            "airplane": 1,  # Airplane.objects.get(id=1)
            "route": 1,  # Route.objects.get(id=1)
            "departure_time": "2022-07-04 21:00",
            "arrival_time": "2022-07-05 12:00",
            "crew": [1],
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
            airline=Airline.objects.get(id=1),
            airplane=Airplane.objects.get(id=1),
            route=Route.objects.get(id=1),
            departure_time=datetime(2024, 1, 10, 12, 30, 0),
            arrival_time=datetime(2024, 1, 10, 14, 30, 0),
        )
        flight.crew.add(1)
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
            airline=Airline.objects.get(id=1),
            airplane=Airplane.objects.get(id=1),
            route=Route.objects.get(id=1),
            departure_time=datetime(2024, 1, 10, 12, 30, 0),
            arrival_time=datetime(2024, 1, 10, 12, 30, 0),
        )
        flight.crew.add(1)
        flight.save()

        url = detail_url(flight.id)

        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
