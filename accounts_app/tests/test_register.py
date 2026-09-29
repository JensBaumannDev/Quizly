from django.contrib.auth.models import User
from django.test import TestCase


class RegisterEndpointTests(TestCase):
    def setUp(self):
        self.url = "/api/register/"
        self.data = {
            "username": "quiz_user",
            "email": "quiz@example.com",
            "password": "secure-password-123",
            "confirmed_password": "secure-password-123",
        }

    def test_registers_user_with_valid_data(self):
        response = self.client.post(self.url, self.data, content_type="application/json")
        user = User.objects.get(username=self.data["username"])
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json(), {"detail": "User created successfully!"})
        self.assertEqual(user.email, self.data["email"])
        self.assertTrue(user.check_password(self.data["password"]))

    def test_rejects_mismatched_passwords(self):
        self.data["confirmed_password"] = "different-password"
        response = self.client.post(self.url, self.data, content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertFalse(User.objects.filter(email=self.data["email"]).exists())

    def test_rejects_existing_email(self):
        User.objects.create_user(
            username=self.data["username"],
            email=self.data["email"],
            password=self.data["password"],
        )
        response = self.client.post(self.url, self.data, content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(User.objects.filter(email=self.data["email"]).count(), 1)
