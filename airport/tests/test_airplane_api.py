from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from airport.models import Airplane, AirplaneType
from airport.serializers import AirplaneSerializer

AIRPLANE_URL = reverse("airport:airplane-list")


def sample_airplane(**params):
    airplane_type = AirplaneType.objects.create(
        name="Test type"
    )
    defaults = {
        "name": "Test name",
        "rows": 30,
        "seats_in_row": 6,
        "airplane_type": airplane_type
    }
    defaults.update(params)

    return Airplane.objects.create(**defaults)


class UnauthenticatedAirportApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(AIRPLANE_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedAirportApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@test.com",
            "testpass",
        )
        self.client.force_authenticate(self.user)

    def test_list_airplanes(self):
        sample_airplane()

        airplane_type_2 = AirplaneType.objects.create(
            name="Test type 2"
        )

        data = {
            "name": "Test name 2",
            "rows": 30,
            "seats_in_row": 6,
            "airplane_type": airplane_type_2
        }
        Airplane.objects.create(**data)

        res = self.client.get(AIRPLANE_URL)

        movies = Airplane.objects.order_by("id")
        serializer = AirplaneSerializer(movies, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_airplane_forbidden(self):
        airplane_type = AirplaneType.objects.create(
            name="Test type"
        )
        payload = {
            "name": "test_airplane",
            "rows": 30,
            "seats_in_row": 6,
            "airplane_type": airplane_type.id,
        }
        res = self.client.post(AIRPLANE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminAirplaneApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "admin@admin.com", "testpass", is_staff=True
        )
        self.client.force_authenticate(self.user)

    def test_create_airplane(self):
        airplane_type = AirplaneType.objects.create(
            name="Test type"
        )
        payload = {
            "name": "test_airplane",
            "rows": 30,
            "seats_in_row": 6,
            "airplane_type": airplane_type.id
        }
        res = self.client.post(AIRPLANE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        airplane = Airplane.objects.get(id=res.data["id"])
        for key in payload.keys():
            if key != "airplane_type":
                self.assertEqual(payload[key], getattr(airplane, key))
        self.assertEqual(payload["airplane_type"], airplane.airplane_type.id)
