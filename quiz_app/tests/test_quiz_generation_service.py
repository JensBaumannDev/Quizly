import json
from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from quiz_app.services.quiz_generation import generate_quiz


class QuizGenerationTests(SimpleTestCase):
    def setUp(self):
        self.quiz_data = {
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

    def create_response(self, quiz_data=None):
        response = Mock()
        data = self.quiz_data if quiz_data is None else quiz_data
        response.text = json.dumps(data)
        return response

    def assert_generation_request(self, client):
        request = client.models.generate_content.call_args.kwargs
        self.assertEqual(request["model"], "gemini-3.8-flash")
        self.assertIn("Python transcript", request["contents"])
        self.assertEqual(request["config"]["response_mime_type"], "application/json")
        schema = request["config"]["response_json_schema"]
        questions = schema["properties"]["questions"]
        self.assertEqual(questions["minItems"], 10)
        self.assertEqual(questions["maxItems"], 10)
        options = questions["items"]["properties"]["question_options"]
        self.assertEqual(options["minItems"], 4)
        self.assertEqual(options["maxItems"], 4)
        self.assertEqual(schema["properties"]["description"]["maxLength"], 150)

    @patch("quiz_app.services.quiz_generation.genai.Client")
    def test_generates_validated_quiz(self, client_class):
        client = client_class.return_value
        client.models.generate_content.return_value = self.create_response()
        result = generate_quiz("Python transcript", "api-key")
        self.assertEqual(result, self.quiz_data)
        client_class.assert_called_once_with(api_key="api-key")
        self.assert_generation_request(client)

    @patch("quiz_app.services.quiz_generation.genai.Client")
    def test_prompt_contains_da_requirements_and_ends_with_transcript(self, client_class):
        client = client_class.return_value
        client.models.generate_content.return_value = self.create_response()
        generate_quiz("Python transcript", "api-key")
        prompt = client.models.generate_content.call_args.kwargs["contents"]
        self.assertIn("exactly 10 questions", prompt)
        self.assertIn("exactly 4 distinct answer options", prompt)
        self.assertIn("no more than 150 characters", prompt)
        self.assertIn("Do not include explanations", prompt)
        self.assertTrue(prompt.endswith("Transcript:\nPython transcript"))

    @patch("quiz_app.services.quiz_generation.genai.Client")
    def test_removes_markdown_json_code_fences(self, client_class):
        client = client_class.return_value
        quiz_json = json.dumps(self.quiz_data)
        for opening_fence in ["```", "```json", "```JSON"]:
            with self.subTest(opening_fence=opening_fence):
                client.models.generate_content.return_value.text = (
                    f"{opening_fence}\n{quiz_json}\n```"
                )
                result = generate_quiz("Python transcript", "api-key")
                self.assertEqual(result, self.quiz_data)

    @patch("quiz_app.services.quiz_generation.genai.Client")
    def test_rejects_blank_transcript(self, client_class):
        for transcript in ["  ", None, 123, []]:
            with self.subTest(transcript=transcript), self.assertRaises(ValueError):
                generate_quiz(transcript, "api-key")
        client_class.assert_not_called()

    @patch("quiz_app.services.quiz_generation.genai.Client")
    def test_rejects_missing_api_key(self, client_class):
        for api_key in ["", "  ", None, 123]:
            with self.subTest(api_key=api_key), self.assertRaises(ValueError):
                generate_quiz("Python transcript", api_key)
        client_class.assert_not_called()

    @patch("quiz_app.services.quiz_generation.genai.Client")
    def test_rejects_invalid_or_empty_response(self, client_class):
        client = client_class.return_value
        for response_text in ["not-json", "", None]:
            with self.subTest(response_text=response_text):
                client.models.generate_content.return_value.text = response_text
                with self.assertRaises(ValueError):
                    generate_quiz("Python transcript", "api-key")

    def assert_rejects_quiz_data(self, quiz_data):
        with patch("quiz_app.services.quiz_generation.genai.Client") as client_class:
            client = client_class.return_value
            client.models.generate_content.return_value = self.create_response(quiz_data)
            with self.assertRaises(ValueError):
                generate_quiz("Python transcript", "api-key")

    def test_rejects_missing_quiz_fields(self):
        for field in ["title", "description", "questions"]:
            with self.subTest(field=field):
                quiz_data = self.quiz_data.copy()
                quiz_data.pop(field)
                self.assert_rejects_quiz_data(quiz_data)

    def test_rejects_invalid_quiz_structure(self):
        invalid_quizzes = [[], "quiz", {}, {**self.quiz_data, "extra": "value"}]
        for quiz_data in invalid_quizzes:
            with self.subTest(quiz_data=quiz_data):
                self.assert_rejects_quiz_data(quiz_data)

    def test_rejects_empty_quiz_text(self):
        for field in ["title", "description"]:
            with self.subTest(field=field):
                quiz_data = json.loads(json.dumps(self.quiz_data))
                quiz_data[field] = "  "
                self.assert_rejects_quiz_data(quiz_data)

    def test_rejects_non_string_quiz_text(self):
        for field in ["title", "description"]:
            with self.subTest(field=field):
                quiz_data = json.loads(json.dumps(self.quiz_data))
                quiz_data[field] = 123
                self.assert_rejects_quiz_data(quiz_data)

    def test_rejects_description_longer_than_150_characters(self):
        self.quiz_data["description"] = "a" * 151
        self.assert_rejects_quiz_data(self.quiz_data)

    def test_rejects_wrong_question_count(self):
        for question_count in [0, 9, 11]:
            with self.subTest(question_count=question_count):
                quiz_data = self.quiz_data.copy()
                question = self.quiz_data["questions"][0]
                quiz_data["questions"] = [question] * question_count
                self.assert_rejects_quiz_data(quiz_data)

    def test_rejects_non_list_questions(self):
        for questions in [None, "questions", {}]:
            with self.subTest(questions=questions):
                quiz_data = self.quiz_data.copy()
                quiz_data["questions"] = questions
                self.assert_rejects_quiz_data(quiz_data)

    def test_rejects_invalid_options(self):
        invalid_options = [
            ["A", "B", "C"],
            ["A", "B", "C", "C"],
            ["A", "B", "C", "  "],
            ["A", "B", "C", 4],
            "A, B, C, D",
        ]
        for options in invalid_options:
            with self.subTest(options=options):
                quiz_data = json.loads(json.dumps(self.quiz_data))
                quiz_data["questions"][0]["question_options"] = options
                self.assert_rejects_quiz_data(quiz_data)

    def test_rejects_answer_outside_options(self):
        self.quiz_data["questions"][0]["answer"] = "E"
        self.assert_rejects_quiz_data(self.quiz_data)

    def test_rejects_missing_question_fields(self):
        for field in ["question_title", "question_options", "answer"]:
            with self.subTest(field=field):
                quiz_data = json.loads(json.dumps(self.quiz_data))
                quiz_data["questions"][0].pop(field)
                self.assert_rejects_quiz_data(quiz_data)

    def test_rejects_extra_question_fields(self):
        self.quiz_data["questions"][0]["extra"] = "value"
        self.assert_rejects_quiz_data(self.quiz_data)

    def test_rejects_invalid_question_structure(self):
        invalid_questions = [None, "question"]
        for question in invalid_questions:
            with self.subTest(question=question):
                quiz_data = json.loads(json.dumps(self.quiz_data))
                quiz_data["questions"][0] = question
                self.assert_rejects_quiz_data(quiz_data)

    def test_rejects_empty_question_title(self):
        self.quiz_data["questions"][0]["question_title"] = "  "
        self.assert_rejects_quiz_data(self.quiz_data)

    def test_rejects_non_string_question_title(self):
        self.quiz_data["questions"][0]["question_title"] = 123
        self.assert_rejects_quiz_data(self.quiz_data)

    @patch("quiz_app.services.quiz_generation.genai.Client")
    def test_propagates_client_creation_errors(self, client_class):
        client_class.side_effect = RuntimeError("Failed")
        with self.assertRaises(RuntimeError):
            generate_quiz("Python transcript", "api-key")

    @patch("quiz_app.services.quiz_generation.genai.Client")
    def test_propagates_gemini_errors(self, client_class):
        client = client_class.return_value
        client.models.generate_content.side_effect = RuntimeError("Failed")
        with self.assertRaises(RuntimeError):
            generate_quiz("Python transcript", "api-key")
