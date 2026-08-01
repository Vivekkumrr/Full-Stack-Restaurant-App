from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import Reservation, Table
from .serializers import ReservationSerializer


class ReservationSerializerTests(TestCase):
    def test_reserved_table_is_rejected(self):
        table = Table.objects.create(table_number=1, capacity=4, status=Table.Status.RESERVED)
        serializer = ReservationSerializer(
            data={
                "name": "Test User",
                "email": "test@example.com",
                "phone": "123456789",
                "table": table.id,
                "date": "2026-07-15",
                "time": "18:00:00",
                "guests": 2,
                "notes": "",
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("table", serializer.errors)

    def test_creating_reservation_marks_table_as_reserved(self):
        table = Table.objects.create(table_number=2, capacity=4, status=Table.Status.AVAILABLE)
        serializer = ReservationSerializer(
            data={
                "name": "Test User",
                "email": "test@example.com",
                "phone": "123456789",
                "table": table.id,
                "date": "2026-07-16",
                "time": "19:00:00",
                "guests": 2,
                "notes": "",
            }
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()
        table.refresh_from_db()
        self.assertEqual(table.status, Table.Status.RESERVED)


class LogoutViewTests(TestCase):
    def test_logout_endpoint_clears_session_for_authenticated_user(self):
        User = get_user_model()
        user = User.objects.create_user(username="admin", password="secret123")
        self.client.force_login(user)

        response = self.client.get("/api/logout")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        self.assertNotIn("_auth_user_id", self.client.session)
