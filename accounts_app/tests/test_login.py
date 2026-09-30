from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken


class LoginEndpointTests(TestCase):
    def setUp(self):
        self.url = "/api/login/"
        self.user = User.objects.create_user(
            username="quiz_user",
            email="quiz@example.com",
            password="secure-password-123",
        )

    def assert_auth_cookies(self, response):
        access_token = AccessToken(response.cookies["access_token"].value)
        refresh_token = RefreshToken(response.cookies["refresh_token"].value)
        self.assertTrue(response.cookies["access_token"]["httponly"])
        self.assertTrue(response.cookies["refresh_token"]["httponly"])
        self.assertEqual(access_token["user_id"], str(self.user.pk))
        self.assertEqual(refresh_token["user_id"], str(self.user.pk))

    def test_logs_in_user_with_valid_credentials(self):
        data = {"username": self.user.username, "password": "secure-password-123"}
        response = self.client.post(self.url, data, content_type="application/json")
        expected_user = {"id": self.user.pk, "username": self.user.username, "email": self.user.email}
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"detail": "Login successfully!", "user": expected_user})
        self.assert_auth_cookies(response)

    def test_rejects_invalid_credentials(self):
        data = {"username": self.user.username, "password": "invalid-password"}
        response = self.client.post(self.url, data, content_type="application/json")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"detail": "Invalid credentials."})

    def test_rejects_unknown_username(self):
        data = {"username": "unknown_user", "password": "secure-password-123"}
        response = self.client.post(self.url, data, content_type="application/json")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"detail": "Invalid credentials."})

    def test_rejects_missing_required_fields(self):
        for field in ["username", "password"]:
            with self.subTest(field=field):
                data = {"username": self.user.username, "password": "secure-password-123"}
                data.pop(field)
                response = self.client.post(self.url, data, content_type="application/json")
                self.assertEqual(response.status_code, 400)

    def test_rejects_inactive_user(self):
        self.user.is_active = False
        self.user.save(update_fields=["is_active"])
        data = {"username": self.user.username, "password": "secure-password-123"}
        response = self.client.post(self.url, data, content_type="application/json")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"detail": "Invalid credentials."})

    def test_allows_cookie_requests_from_frontend(self):
        data = {"username": self.user.username, "password": "secure-password-123"}
        response = self.client.post(
            self.url, data, content_type="application/json", HTTP_ORIGIN="http://127.0.0.1:5500"
        )
        self.assertEqual(response.headers["Access-Control-Allow-Credentials"], "true")
        self.assertEqual(response.headers["Access-Control-Allow-Origin"], "http://127.0.0.1:5500")
