from django.contrib.auth.models import User
from django.test import TestCase


class LogoutEndpointTests(TestCase):
    def setUp(self):
        self.url = "/api/logout/"
        self.user = User.objects.create_user(
            username="quiz_user", password="secure-password-123"
        )

    def login_and_set_refresh_cookie(self):
        response = self.client.post(
            "/api/login/",
            {"username": self.user.username, "password": "secure-password-123"},
        )
        self.client.cookies["refresh_token"] = response.cookies["refresh_token"].value

    def assert_successful_logout(self, response):
        response_data = {
            "detail": "Log-Out successfully! All Tokens will be deleted. "
            "Refresh token is now invalid."
        }
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), response_data)
        self.assertEqual(response.cookies["access_token"].value, "")
        self.assertEqual(response.cookies["refresh_token"].value, "")

    def test_logs_out_and_invalidates_refresh_token(self):
        self.login_and_set_refresh_cookie()
        refresh_token = self.client.cookies["refresh_token"].value
        response = self.client.post(self.url)
        self.assert_successful_logout(response)
        self.client.cookies["refresh_token"] = refresh_token
        refresh_response = self.client.post("/api/token/refresh/")
        self.assertEqual(refresh_response.status_code, 401)

    def test_rejects_missing_refresh_token(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 401)

    def test_rejects_invalid_refresh_token(self):
        self.client.cookies["refresh_token"] = "invalid-token"
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 401)

    def test_rejects_blacklisted_refresh_token(self):
        self.login_and_set_refresh_cookie()
        refresh_token = self.client.cookies["refresh_token"].value
        self.client.post(self.url)
        self.client.cookies["refresh_token"] = refresh_token
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 401)
