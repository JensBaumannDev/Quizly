from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework_simplejwt.tokens import AccessToken

from quiz_app.models import Question, Quiz


class QuizDeleteEndpointTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="quiz_user")
        self.other_user = User.objects.create_user(username="other_user")
        self.quiz = self.create_quiz(self.user, "Python Quiz")
        self.question = self.create_question(self.quiz)
        self.other_quiz = self.create_quiz(self.other_user, "Other Quiz")

    def create_quiz(self, user, title):
        return Quiz.objects.create(
            user=user,
            title=title,
            description="Questions about Python",
            video_url="https://www.youtube.com/watch?v=example",
        )

    def create_question(self, quiz):
        return Question.objects.create(
            quiz=quiz,
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

    def assert_quiz_exists(self, quiz):
        self.assertTrue(Quiz.objects.filter(id=quiz.id).exists())

    def test_deletes_own_quiz_and_its_questions(self):
        self.authenticate_user()
        response = self.client.delete(self.get_detail_url(self.quiz))
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.content, b"")
        self.assertFalse(Quiz.objects.filter(id=self.quiz.id).exists())
        self.assertFalse(Question.objects.filter(id=self.question.id).exists())

    def test_rejects_missing_access_token(self):
        response = self.client.delete(self.get_detail_url(self.quiz))
        self.assertEqual(response.status_code, 401)
        self.assert_quiz_exists(self.quiz)

    def test_rejects_invalid_access_token(self):
        self.client.cookies["access_token"] = "invalid-token"
        response = self.client.delete(self.get_detail_url(self.quiz))
        self.assertEqual(response.status_code, 401)
        self.assert_quiz_exists(self.quiz)

    def test_rejects_expired_access_token(self):
        access_token = AccessToken.for_user(self.user)
        access_token.set_exp(lifetime=timedelta(seconds=-1))
        self.client.cookies["access_token"] = str(access_token)
        response = self.client.delete(self.get_detail_url(self.quiz))
        self.assertEqual(response.status_code, 401)
        self.assert_quiz_exists(self.quiz)

    def test_rejects_other_users_quiz(self):
        self.authenticate_user()
        response = self.client.delete(self.get_detail_url(self.other_quiz))
        self.assertEqual(response.status_code, 403)
        self.assert_quiz_exists(self.other_quiz)

    def test_returns_not_found_for_missing_quiz(self):
        self.authenticate_user()
        response = self.client.delete("/api/quizzes/999/")
        self.assertEqual(response.status_code, 404)
