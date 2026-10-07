import json
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.test import TestCase
from rest_framework_simplejwt.tokens import AccessToken

from quiz_app.models import Question, Quiz


class QuizCreateEndpointTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="quiz_user")
        self.video_url = "https://www.youtube.com/watch?v=video123"
        self.quiz_data = self.create_quiz_data()
        self.authenticate_user()
        self.start_service_patches()

    def create_quiz_data(self):
        return {
            "title": "Python Basics",
            "description": "A quiz about Python fundamentals.",
            "questions": [
                {
                    "question_title": f"Question {index}",
                    "question_options": ["A", "B", "C", "D"],
                    "answer": "A",
                }
                for index in range(1, 11)
            ],
        }

    def authenticate_user(self):
        self.client.cookies["access_token"] = str(AccessToken.for_user(self.user))

    def start_service_patches(self):
        targets = {
            "download_audio": "quiz_app.services.quiz_creation.download_audio",
            "transcribe_audio": "quiz_app.services.quiz_creation.transcribe_audio",
            "generate_quiz": "quiz_app.services.quiz_creation.generate_quiz",
        }
        for attribute, target in targets.items():
            patcher = patch(target)
            mocked_service = patcher.start()
            setattr(self, attribute, mocked_service)
            self.addCleanup(patcher.stop)
        self.download_audio.return_value = Path("video123.mp3")
        self.transcribe_audio.return_value = "Python transcript"
        self.generate_quiz.return_value = self.quiz_data

    def post_quiz(self, data=None):
        payload = {"url": self.video_url} if data is None else data
        return self.client.post("/api/quizzes/", payload, content_type="application/json")

    def assert_quiz_response(self, response_data):
        expected_fields = {
            "id", "title", "description", "created_at",
            "updated_at", "video_url", "questions",
        }
        self.assertEqual(set(response_data), expected_fields)
        self.assertEqual(response_data["title"], self.quiz_data["title"])
        self.assertEqual(response_data["description"], self.quiz_data["description"])
        self.assertEqual(response_data["video_url"], self.video_url)
        self.assertEqual(len(response_data["questions"]), 10)
        self.assert_question_response(response_data["questions"][0])

    def assert_question_response(self, question_data):
        expected_fields = {
            "id", "question_title", "question_options",
            "answer", "created_at", "updated_at",
        }
        self.assertEqual(set(question_data), expected_fields)
        self.assertEqual(question_data["question_title"], "Question 1")
        self.assertEqual(question_data["question_options"], ["A", "B", "C", "D"])
        self.assertEqual(question_data["answer"], "A")
        self.assertTrue(question_data["created_at"])
        self.assertTrue(question_data["updated_at"])

    def assert_saved_quiz(self):
        quiz = Quiz.objects.get()
        self.assertEqual(quiz.user, self.user)
        self.assertEqual(quiz.video_url, self.video_url)
        self.assertEqual(quiz.title, self.quiz_data["title"])
        self.assertEqual(quiz.questions.count(), 10)
        self.assert_saved_question(quiz.questions.order_by("id").first())

    def assert_saved_question(self, question):
        self.assertEqual(question.question_title, "Question 1")
        self.assertEqual(question.question_options, ["A", "B", "C", "D"])
        self.assertEqual(question.answer, "A")

    def assert_pipeline_calls(self):
        audio_directory = self.download_audio.call_args.args[1]
        self.download_audio.assert_called_once_with(self.video_url, audio_directory)
        self.transcribe_audio.assert_called_once_with(Path("video123.mp3"))
        self.generate_quiz.assert_called_once_with(
            "Python transcript", settings.GEMINI_API_KEY
        )
        self.assertFalse(audio_directory.exists())

    def assert_generation_failure(self, response):
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json(), {"detail": "Quiz generation failed."})
        self.assertFalse(Quiz.objects.exists())
        self.assertFalse(Question.objects.exists())
        audio_directory = self.download_audio.call_args.args[1]
        self.assertFalse(audio_directory.exists())

    def invalid_payloads(self):
        return [
            {},
            {"url": ""},
            {"url": "   "},
            {"url": "not-a-url"},
            {"url": "https://vimeo.com/video123"},
            {"url": None},
            {"url": 123},
            [],
        ]

    def test_creates_quiz_with_questions(self):
        response = self.post_quiz()
        self.assertEqual(response.status_code, 201)
        self.assert_quiz_response(response.json())
        self.assert_saved_quiz()
        self.assert_pipeline_calls()

    def test_rejects_invalid_request_data(self):
        for payload in self.invalid_payloads():
            with self.subTest(payload=payload):
                response = self.post_quiz(payload)
                self.assertEqual(response.status_code, 400)
        self.download_audio.assert_not_called()
        self.assertFalse(Quiz.objects.exists())

    def test_rejects_malformed_json(self):
        response = self.client.post(
            "/api/quizzes/", "{", content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        self.download_audio.assert_not_called()

    def test_rejects_non_object_json(self):
        for payload in ["null", "[]", '"url"']:
            with self.subTest(payload=payload):
                response = self.client.post(
                    "/api/quizzes/", payload, content_type="application/json"
                )
                self.assertEqual(response.status_code, 400)
        self.download_audio.assert_not_called()

    def test_rejects_missing_access_token(self):
        self.client.cookies.clear()
        response = self.post_quiz()
        self.assertEqual(response.status_code, 401)
        self.download_audio.assert_not_called()

    def test_rejects_invalid_access_token(self):
        self.client.cookies["access_token"] = "invalid-token"
        response = self.post_quiz()
        self.assertEqual(response.status_code, 401)
        self.download_audio.assert_not_called()

    def test_rejects_expired_access_token(self):
        access_token = AccessToken.for_user(self.user)
        access_token.set_exp(lifetime=timedelta(seconds=-1))
        self.client.cookies["access_token"] = str(access_token)
        response = self.post_quiz()
        self.assertEqual(response.status_code, 401)
        self.download_audio.assert_not_called()

    def test_rejects_unsupported_method(self):
        response = self.client.put(
            "/api/quizzes/",
            {"url": self.video_url},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 405)
        self.download_audio.assert_not_called()

    def test_returns_500_when_audio_download_fails(self):
        self.download_audio.side_effect = RuntimeError("Download failed")
        self.assert_generation_failure(self.post_quiz())
        self.transcribe_audio.assert_not_called()
        self.generate_quiz.assert_not_called()

    def test_returns_500_when_transcription_fails(self):
        self.transcribe_audio.side_effect = RuntimeError("Transcription failed")
        self.assert_generation_failure(self.post_quiz())
        self.generate_quiz.assert_not_called()

    def test_returns_500_when_gemini_fails(self):
        self.generate_quiz.side_effect = RuntimeError("Gemini failed")
        with self.assertLogs("quiz_app.api.views", level="ERROR") as logs:
            self.assert_generation_failure(self.post_quiz())
        self.assertIn("Quiz generation failed.", logs.output[0])
        self.assertIn("Gemini failed", logs.output[0])

    @patch("quiz_app.services.quiz_creation.Question.objects.bulk_create")
    def test_rolls_back_quiz_when_questions_cannot_be_saved(self, bulk_create):
        bulk_create.side_effect = IntegrityError("Database failed")
        self.assert_generation_failure(self.post_quiz())

    def test_rejects_unknown_request_fields(self):
        response = self.post_quiz({"url": self.video_url, "unknown": "value"})
        self.assertEqual(response.status_code, 400)
        self.download_audio.assert_not_called()
