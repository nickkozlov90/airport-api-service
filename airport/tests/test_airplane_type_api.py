import tempfile
import os

from PIL import Image
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from airport.models import AirplaneType
from airport.serializers import AirplaneTypeSerializer

AIRPLANE_TYPE_URL = reverse("airport:airplanetype-list")


def sample_airplane_type(**params):
    defaults = {
        "name": "Test airplane type",
    }
    defaults.update(params)

    return AirplaneType.objects.create(**defaults)


class UnauthenticatedMovieApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(AIRPLANE_TYPE_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedMovieApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@test.com",
            "testpass",
        )
        self.client.force_authenticate(self.user)

    def test_list_airplane_types(self):
        sample_airplane_type()
        sample_airplane_type(name="Test airplane type 2")

        res = self.client.get(AIRPLANE_TYPE_URL)

        airplane_types = AirplaneType.objects.order_by("id")
        serializer = AirplaneTypeSerializer(airplane_types, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_airplane_type_forbidden(self):
        payload = {
            "name": "Test",
        }
        res = self.client.post(AIRPLANE_TYPE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminAirplaneTypeApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "admin@admin.com", "testpass", is_staff=True
        )
        self.client.force_authenticate(self.user)

    def test_create_airplane_type(self):
        payload = {
            "name": "Test_type",
        }
        res = self.client.post(AIRPLANE_TYPE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        airplane_type = AirplaneType.objects.get(id=res.data["id"])
        self.assertEqual(payload["name"], getattr(airplane_type, "name"))
