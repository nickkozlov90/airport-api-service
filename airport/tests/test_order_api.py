import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from airport.models import (
    Flight, Airport, Route, Airline, Airplane, Crew, AirplaneType, Order,
    Ticket
)
from airport.serializers import OrderListSerializer

ORDER_URL = reverse("airport:order-list")


class UnauthenticatedOrderApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required_to_get_order_list(self):
        res = self.client.get(ORDER_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_auth_required_to_create(self):
        user = get_user_model().objects.create_user(
            "test_2@test.com",
            "testpass",
        )
        payload = {
            "user": user.id,
        }

        res = self.client.post(ORDER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedOrderApiTests(TestCase):
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
            distance=400
        )

        Crew.objects.create(first_name="John", last_name="Doe")

        flight = Flight.objects.create(
            airline=Airline.objects.get(id=1),
            airplane=Airplane.objects.get(id=1),
            route=Route.objects.get(id=1),
            departure_time="2022-06-02 14:00",
            arrival_time="2022-06-02 20:00",
        )
        flight.crew.add(1)
        flight.save()

    def test_list_orders(self):
        Order.objects.create(user=self.user)
        Order.objects.create(user=self.user)

        res = self.client.get(ORDER_URL)

        orders = Order.objects.order_by("id")
        serializer = OrderListSerializer(orders, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_filter_list_orders_by_current_user(self):
        user_2 = get_user_model().objects.create_user(
            "test_2@test.com",
            "testpass",
        )

        Order.objects.create(user=self.user)
        Order.objects.create(user=self.user)

        Order.objects.create(user=user_2)
        Order.objects.create(user=user_2)

        res = self.client.get(ORDER_URL)

        orders = Order.objects.filter(user=self.user.id).order_by("id")
        serializer = OrderListSerializer(orders, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_create_order(self):
        payload = {
            "tickets": [
                {
                    "seat": 1,
                    "row": 1,
                    "flight": 1
                }
            ]
        }
        payload = json.dumps(payload)
        res = self.client.post(
            ORDER_URL, data=payload, content_type='application/json'
        )

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_create_order_with_another_user(self):
        user = get_user_model().objects.create_user(
            "test_2@test.com",
            "testpass",
        )
        payload = {
            "user": user.id,
            "tickets": [
                {
                    "seat": 1,
                    "row": 1,
                    "flight": 1
                }
            ]
        }
        payload = json.dumps(payload)
        res = self.client.post(
            ORDER_URL, data=payload, content_type='application/json'
        )
        order = Order.objects.get(id=res.data["id"])

        self.assertEqual(order.user.id, self.user.id)

    def test_ticket_unique_constraint(self):
        flight = Flight.objects.get(id=1)
        order = Order.objects.create(user=self.user)
        Ticket.objects.create(seat=1, row=1, flight=flight, order=order)

        payload = {
            "tickets": [
                {
                    "seat": 1,
                    "row": 1,
                    "flight": flight.id
                }
            ]
        }
        payload = json.dumps(payload)

        res = self.client.post(ORDER_URL, data=payload, content_type='application/json')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            "Seat with entered data has been already booked.",
            res.data["tickets"][0]["non_field_errors"],

        )

    def test_order_pagination(self):
        flight = Flight.objects.get(id=1)
        orders_num = 12
        for num in range(orders_num):
            order = Order.objects.create(user=self.user)
            Ticket.objects.create(seat=1, row=num, flight=flight, order=order)

        res = self.client.get(ORDER_URL)

        self.assertIn("next", res.data)

        res_next = self.client.get(res.data["next"])
        self.assertEqual(len(res_next.data["results"]), orders_num - 10)
