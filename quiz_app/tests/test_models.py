from django.contrib import admin
from django.contrib.auth.models import User
from django.test import TestCase

from quiz_app.models import Question, Quiz


class QuizModelsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="quiz_user", password="secure-password-123"
        )

    def create_quiz(self):
        return Quiz.objects.create(
            user=self.user,
            title="Python Quiz",
            description="Questions about Python",
            video_url="https://www.youtube.com/watch?v=example",
        )

    def test_quiz_belongs_to_user(self):
        quiz = self.create_quiz()
        self.assertEqual(quiz.user, self.user)
        self.assertEqual(self.user.quizzes.get(), quiz)

    def test_question_belongs_to_quiz(self):
        quiz = self.create_quiz()
        question = Question.objects.create(
            quiz=quiz,
            question_title="What is Python?",
            question_options=["Language", "Framework", "Database", "Browser"],
            answer="Language",
        )
        self.assertEqual(quiz.questions.get(), question)
        self.assertEqual(question.question_options[0], "Language")

    def test_models_are_registered_in_admin(self):
        self.assertIn(Quiz, admin.site._registry)
        self.assertIn(Question, admin.site._registry)
