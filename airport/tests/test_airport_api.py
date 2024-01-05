from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from airport.models import Airport
from airport.serializers import AirportSerializer

AIRPORT_URL = reverse("airport:airport-list")


def sample_airport(**params):
    defaults = {
        "name": "Test airport",
        "code": "TAP",
        "closest_big_city": "Test city",
    }
    defaults.update(params)

    return Airport.objects.create(**defaults)


class UnauthenticatedAirportApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(AIRPORT_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedAirportApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@test.com",
            "testpass",
        )
        self.client.force_authenticate(self.user)

    def test_list_airports(self):
        sample_airport()
        sample_airport(
            name="Test_2", code="TES", closest_big_city="Closest_city"
        )

        res = self.client.get(AIRPORT_URL)

        airports = Airport.objects.order_by("id")
        serializer = AirportSerializer(airports, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_airport_forbidden(self):
        payload = {
            "name": "Test airport",
            "code": "XYZ",
            "closest_big_city": "Test city",
        }
        res = self.client.post(AIRPORT_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminAirportApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "admin@admin.com", "testpass", is_staff=True
        )
        self.client.force_authenticate(self.user)

    def test_create_airport(self):
        payload = {
            "name": "Test airport",
            "code": "XYZ",
            "closest_big_city": "Test city",
        }
        res = self.client.post(AIRPORT_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        airport = Airport.objects.get(id=res.data["id"])
        for key in payload.keys():
            self.assertEqual(payload[key], getattr(airport, key))
