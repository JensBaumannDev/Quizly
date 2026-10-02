from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework_simplejwt.tokens import AccessToken

from quiz_app.models import Question, Quiz


class QuizDetailEndpointTests(TestCase):
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

    def assert_quiz_response_data(self, response_data):
        expected_fields = {
            "id", "title", "description", "created_at",
            "updated_at", "video_url", "questions",
        }
        self.assertEqual(response_data["id"], self.quiz.id)
        self.assertEqual(set(response_data), expected_fields)
        self.assert_question_response_data(response_data["questions"][0])

    def assert_question_response_data(self, question_data):
        expected_options = ["Language", "Framework", "Database", "Browser"]
        expected_fields = {"id", "question_title", "question_options", "answer"}
        self.assertEqual(set(question_data), expected_fields)
        self.assertEqual(question_data["id"], self.question.id)
        self.assertEqual(question_data["question_title"], "What is Python?")
        self.assertEqual(question_data["question_options"], expected_options)
        self.assertEqual(question_data["answer"], "Language")

    def test_retrieves_own_quiz_with_questions(self):
        self.authenticate_user()
        response = self.client.get(self.get_detail_url(self.quiz))
        self.assertEqual(response.status_code, 200)
        self.assert_quiz_response_data(response.json())

    def test_retrieves_own_quiz_without_questions(self):
        empty_quiz = self.create_quiz(self.user, "Empty Quiz")
        self.authenticate_user()
        response = self.client.get(self.get_detail_url(empty_quiz))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["questions"], [])

    def test_rejects_missing_access_token(self):
        response = self.client.get(self.get_detail_url(self.quiz))
        self.assertEqual(response.status_code, 401)

    def test_rejects_invalid_access_token(self):
        self.client.cookies["access_token"] = "invalid-token"
        response = self.client.get(self.get_detail_url(self.quiz))
        self.assertEqual(response.status_code, 401)

    def test_rejects_expired_access_token(self):
        access_token = AccessToken.for_user(self.user)
        access_token.set_exp(lifetime=timedelta(seconds=-1))
        self.client.cookies["access_token"] = str(access_token)
        response = self.client.get(self.get_detail_url(self.quiz))
        self.assertEqual(response.status_code, 401)

    def test_rejects_other_users_quiz(self):
        self.authenticate_user()
        response = self.client.get(self.get_detail_url(self.other_quiz))
        self.assertEqual(response.status_code, 403)

    def test_returns_not_found_for_missing_quiz(self):
        self.authenticate_user()
        response = self.client.get("/api/quizzes/999/")
        self.assertEqual(response.status_code, 404)
