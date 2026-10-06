import json
import re

from google import genai


GEMINI_MODEL = "gemini-3.8-flash"
QUIZ_FIELDS = {"title", "description", "questions"}
QUESTION_FIELDS = {"question_title", "question_options", "answer"}
CODE_FENCE_PATTERN = re.compile(
    r"^\s*```(?:json)?\s*(.*?)\s*```\s*$", re.IGNORECASE | re.DOTALL
)
QUIZ_PROMPT_TEMPLATE = """Based on the following transcript, generate a quiz in valid JSON format.
The quiz must follow this exact structure:
{{
  "title": "Create a concise quiz title based on the topic of the transcript.",
  "description": "Summarize the transcript in no more than 150 characters. Do not include any quiz questions or answers.",
  "questions": [
    {{
      "question_title": "The question goes here.",
      "question_options": ["Option A", "Option B", "Option C", "Option D"],
      "answer": "The correct answer from the above options"
    }}
  ]
}}
Requirements:
- Generate exactly 10 questions.
- Each question must have exactly 4 distinct answer options.
- Only one correct answer is allowed per question, and it must be present in "question_options".
- The output must be valid JSON and parsable as-is using Python's json.loads.
- Do not include explanations, comments, or any text outside the JSON.

Transcript:
{transcript}"""
QUIZ_SCHEMA = {
    "type": "object",
    "required": sorted(QUIZ_FIELDS),
    "properties": {
        "title": {"type": "string"},
        "description": {"type": "string", "maxLength": 150},
        "questions": {
            "type": "array",
            "minItems": 10,
            "maxItems": 10,
            "items": {
                "type": "object",
                "required": sorted(QUESTION_FIELDS),
                "properties": {
                    "question_title": {"type": "string"},
                    "question_options": {
                        "type": "array",
                        "minItems": 4,
                        "maxItems": 4,
                        "items": {"type": "string"},
                    },
                    "answer": {"type": "string"},
                },
            },
        },
    },
}


def generate_quiz(transcript, api_key):
    validate_generation_input(transcript, api_key)
    client = genai.Client(api_key=api_key)
    response = request_quiz(client, build_quiz_prompt(transcript.strip()))
    return parse_quiz_response(response)


def validate_generation_input(transcript, api_key):
    if not isinstance(transcript, str) or not transcript.strip():
        raise ValueError("A transcript is required.")
    if not isinstance(api_key, str) or not api_key.strip():
        raise ValueError("A Gemini API key is required.")


def build_quiz_prompt(transcript):
    return QUIZ_PROMPT_TEMPLATE.format(transcript=transcript)


def request_quiz(client, prompt):
    return client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_json_schema": QUIZ_SCHEMA,
        },
    )


def parse_quiz_response(response):
    try:
        quiz_data = json.loads(remove_code_fence(response.text))
    except (AttributeError, TypeError, json.JSONDecodeError) as error:
        raise ValueError("Gemini returned invalid JSON.") from error
    validate_quiz_data(quiz_data)
    return quiz_data


def remove_code_fence(response_text):
    if not isinstance(response_text, str):
        return response_text
    match = CODE_FENCE_PATTERN.fullmatch(response_text)
    return match.group(1).strip() if match else response_text.strip()


def validate_quiz_data(quiz_data):
    if not isinstance(quiz_data, dict) or set(quiz_data) != QUIZ_FIELDS:
        raise ValueError("Gemini returned invalid quiz fields.")
    validate_text(quiz_data["title"], "title")
    validate_text(quiz_data["description"], "description")
    if len(quiz_data["description"]) > 150:
        raise ValueError("The quiz description cannot exceed 150 characters.")
    questions = quiz_data["questions"]
    if not isinstance(questions, list) or len(questions) != 10:
        raise ValueError("A quiz must contain exactly 10 questions.")
    for question in questions:
        validate_question(question)


def validate_question(question):
    if not isinstance(question, dict) or set(question) != QUESTION_FIELDS:
        raise ValueError("Gemini returned invalid question fields.")
    validate_text(question["question_title"], "question title")
    options = question["question_options"]
    if not valid_options(options):
        raise ValueError("A question must contain 4 distinct options.")
    if question["answer"] not in options:
        raise ValueError("The answer must match one question option.")


def valid_options(options):
    return (
        isinstance(options, list)
        and len(options) == 4
        and all(isinstance(option, str) and option.strip() for option in options)
        and len(set(options)) == 4
    )


def validate_text(value, field_name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Gemini returned an invalid {field_name}.")
