import tempfile
import os

from PIL import Image
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from airport.models import (
    Airline, Flight, Airplane, AirplaneType, Airport, Route
)
from airport.serializers import AirlineListSerializer

AIRLINE_URL = reverse("airport:airline-list")
FLIGHT_URL = reverse("airport:flight-list")


def sample_airline(**params):
    defaults = {
        "name": "Test airline",
    }
    defaults.update(params)

    return Airline.objects.create(**defaults)


def sample_flight(**params):
    airplane_type = AirplaneType.objects.create(name="Test Type")
    airplane = Airplane.objects.create(
        name="Blue", rows=20, seats_in_row=20, airplane_type=airplane_type
    )
    source = Airport.objects.create(name="Source airport", code="SAP")
    destination = Airport.objects.create(
        name="Destination airport", code="DAP"
    )
    route = Route.objects.create(
        source=source, destination=destination, distance=1200
    )

    defaults = {
        "departure_time": "2022-06-02 14:00:00",
        "arrival_time": "2022-06-02 20:00:00",
        "airplane": airplane,
        "route": route,
    }
    defaults.update(params)

    return Flight.objects.create(**defaults)


def image_upload_url(airline_id):
    """Return URL for recipe image upload"""
    return reverse("airport:airline-upload-image", args=[airline_id])


def detail_url(airline_id):
    return reverse("airport:airline-detail", args=[airline_id])


class UnauthenticatedAirlineApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(AIRLINE_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedAirlineApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@test.com",
            "testpass",
        )
        self.client.force_authenticate(self.user)

    def test_list_airlines(self):
        sample_airline()
        sample_airline(name="Test airline 2")

        res = self.client.get(AIRLINE_URL)

        airlines = Airline.objects.order_by("id")
        serializer = AirlineListSerializer(airlines, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_airline_forbidden(self):
        payload = {
            "name": "Airline",
        }
        res = self.client.post(AIRLINE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminAirlineApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "admin@admin.com", "testpass", is_staff=True
        )
        self.client.force_authenticate(self.user)

    def test_create_airline(self):
        payload = {
            "name": "Airline",
        }
        res = self.client.post(AIRLINE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        airline = Airline.objects.get(id=res.data["id"])
        for key in payload.keys():
            self.assertEqual(payload[key], getattr(airline, key))


class AirlineImageUploadTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_superuser(
            "admin@myproject.com", "password"
        )
        self.client.force_authenticate(self.user)
        self.airline = sample_airline()
        self.flight = sample_flight()
        self.flight.airline = self.airline
        self.flight.save()

    def tearDown(self):
        self.airline.image.delete()

    def test_upload_image_to_airline(self):
        """Test uploading an image to airline"""
        url = image_upload_url(self.airline.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            res = self.client.post(url, {"image": ntf}, format="multipart")
        self.airline.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("image", res.data)
        self.assertTrue(os.path.exists(self.airline.image.path))

    def test_upload_image_bad_request(self):
        """Test uploading an invalid image"""
        url = image_upload_url(self.airline.id)
        res = self.client.post(url, {"image": "not image"}, format="multipart")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_image_to_airline_list_should_not_work(self):
        url = AIRLINE_URL
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            res = self.client.post(
                url,
                {
                    "name": "Airline",
                    "image": ntf,
                },
                format="multipart",
            )

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        airline = Airline.objects.get(name="Airline")
        self.assertFalse(airline.image)

    def test_image_url_is_shown_on_airline_list(self):
        url = image_upload_url(self.airline.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            self.client.post(url, {"image": ntf}, format="multipart")
        res = self.client.get(AIRLINE_URL)

        self.assertIn("image", res.data[0].keys())

    def test_image_url_is_shown_on_flight_list(self):
        url = image_upload_url(self.airline.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            self.client.post(url, {"image": ntf}, format="multipart")
        res = self.client.get(FLIGHT_URL)

        self.assertIn("airline_image", res.data["results"][0].keys())

    def test_image_url_is_shown_on_flight_detail(self):
        url = image_upload_url(self.airline.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            self.client.post(url, {"image": ntf}, format="multipart")
        res = self.client.get(FLIGHT_URL + "1/")

        self.assertIn("image", res.data["airline"].keys())
