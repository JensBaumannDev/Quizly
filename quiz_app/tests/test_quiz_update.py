from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework_simplejwt.tokens import AccessToken

from quiz_app.models import Question, Quiz


class QuizUpdateEndpointTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="quiz_user")
        self.other_user = User.objects.create_user(username="other_user")
        self.quiz = self.create_quiz(self.user, "Python Quiz")
        self.question = self.create_question()
        self.other_quiz = self.create_quiz(self.other_user, "Other Quiz")

    def create_quiz(self, user, title):
        return Quiz.objects.create(
            user=user,
            title=title,
            description="Questions about Python",
            video_url="https://www.youtube.com/watch?v=example",
        )

    def create_question(self):
        return Question.objects.create(
            quiz=self.quiz,
            question_title="What is Python?",
            question_options=["Language", "Framework", "Database", "Browser"],
            answer="Language",
        )

    def authenticate_user(self, user=None):
        authenticated_user = user or self.user
        access_token = AccessToken.for_user(authenticated_user)
        self.client.cookies["access_token"] = str(access_token)

    def get_detail_url(self, quiz):
        return f"/api/quizzes/{quiz.id}/"

    def patch_quiz(self, quiz, data):
        return self.client.patch(
            self.get_detail_url(quiz), data, content_type="application/json"
        )

    def assert_full_response_data(self, response_data):
        expected_fields = {
            "id", "title", "description", "created_at",
            "updated_at", "video_url", "questions",
        }
        expected_question_fields = {
            "id", "question_title", "question_options", "answer"
        }
        self.assertEqual(set(response_data), expected_fields)
        self.assertEqual(set(response_data["questions"][0]), expected_question_fields)
        self.assertEqual(response_data["questions"][0]["id"], self.question.id)

    def test_updates_title_without_changing_description(self):
        previous_updated_at = self.quiz.updated_at
        self.authenticate_user()
        response = self.patch_quiz(self.quiz, {"title": "Updated Python Quiz"})
        self.quiz.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.quiz.title, "Updated Python Quiz")
        self.assertEqual(self.quiz.description, "Questions about Python")
        self.assertNotEqual(self.quiz.updated_at, previous_updated_at)
        self.assert_full_response_data(response.json())

    def test_updates_description_without_changing_title(self):
        self.authenticate_user()
        response = self.patch_quiz(self.quiz, {"description": "Updated description"})
        self.quiz.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.quiz.title, "Python Quiz")
        self.assertEqual(self.quiz.description, "Updated description")

    def test_updates_title_and_description_with_questions(self):
        self.authenticate_user()
        response = self.patch_quiz(
            self.quiz,
            {"title": "Updated Python Quiz", "description": "Updated description"},
        )
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertEqual(response_data["title"], "Updated Python Quiz")
        self.assertEqual(response_data["description"], "Updated description")
        self.assert_full_response_data(response_data)

    def test_rejects_blank_title(self):
        self.authenticate_user()
        response = self.patch_quiz(self.quiz, {"title": ""})
        self.quiz.refresh_from_db()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.quiz.title, "Python Quiz")

    def test_rejects_blank_description(self):
        self.authenticate_user()
        response = self.patch_quiz(self.quiz, {"description": ""})
        self.quiz.refresh_from_db()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.quiz.description, "Questions about Python")

    def test_rejects_empty_update_data(self):
        self.authenticate_user()
        response = self.patch_quiz(self.quiz, {})
        self.assertEqual(response.status_code, 400)

    def test_rejects_read_only_video_url(self):
        self.authenticate_user()
        response = self.patch_quiz(self.quiz, {"video_url": "https://youtube.com"})
        self.quiz.refresh_from_db()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.quiz.video_url, "https://www.youtube.com/watch?v=example")

    def test_rejects_malformed_json(self):
        self.authenticate_user()
        response = self.client.patch(
            self.get_detail_url(self.quiz), "{", content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)

    def test_rejects_missing_access_token(self):
        response = self.patch_quiz(self.quiz, {"title": "Updated Python Quiz"})
        self.assertEqual(response.status_code, 401)

    def test_rejects_invalid_access_token(self):
        self.client.cookies["access_token"] = "invalid-token"
        response = self.patch_quiz(self.quiz, {"title": "Updated Python Quiz"})
        self.assertEqual(response.status_code, 401)

    def test_rejects_expired_access_token(self):
        access_token = AccessToken.for_user(self.user)
        access_token.set_exp(lifetime=timedelta(seconds=-1))
        self.client.cookies["access_token"] = str(access_token)
        response = self.patch_quiz(self.quiz, {"title": "Updated Python Quiz"})
        self.assertEqual(response.status_code, 401)

    def test_rejects_other_users_quiz(self):
        self.authenticate_user()
        response = self.patch_quiz(self.other_quiz, {"title": "Updated Quiz"})
        self.assertEqual(response.status_code, 403)

    def test_returns_not_found_for_missing_quiz(self):
        self.authenticate_user()
        response = self.client.patch("/api/quizzes/999/", {"title": "Updated Quiz"})
        self.assertEqual(response.status_code, 404)
