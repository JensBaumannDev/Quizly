from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework_simplejwt.tokens import AccessToken


class TokenRefreshEndpointTests(TestCase):
    def setUp(self):
        self.url = "/api/token/refresh/"
        self.user = User.objects.create_user(username="quiz_user", password="secure-password-123")

    def set_refresh_cookie(self, value):
        self.client.cookies["refresh_token"] = value

    def test_refreshes_access_token(self):
        login_data = {"username": self.user.username, "password": "secure-password-123"}
        login_response = self.client.post("/api/login/", login_data)
        self.set_refresh_cookie(login_response.cookies["refresh_token"].value)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)
        access_token = AccessToken(response.cookies["access_token"].value)
        self.assertEqual(response.json(), {"detail": "Token refreshed"})
        self.assertTrue(response.cookies["access_token"]["httponly"])
        self.assertEqual(access_token["user_id"], str(self.user.pk))

    def test_rejects_missing_refresh_token(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 401)

    def test_rejects_invalid_refresh_token(self):
        self.set_refresh_cookie("invalid-token")
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 401)
