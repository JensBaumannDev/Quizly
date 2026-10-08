from pathlib import Path
from tempfile import TemporaryDirectory

from django.db import transaction

from quiz_app.models import Question, Quiz
from quiz_app.services.audio import download_audio
from quiz_app.services.quiz_generation import generate_quiz
from quiz_app.services.transcription import transcribe_audio


def create_quiz_from_video(user, video_url, api_key):
    """Create and save a quiz from a YouTube video."""

    with TemporaryDirectory() as temporary_directory:
        audio_path = download_audio(video_url, Path(temporary_directory))
        transcript = transcribe_audio(audio_path)
        quiz_data = generate_quiz(transcript, api_key)
    return save_quiz(user, video_url, quiz_data)


@transaction.atomic
def save_quiz(user, video_url, quiz_data):
    """Persist a quiz and all generated questions atomically."""

    quiz = Quiz.objects.create(
        user=user,
        title=quiz_data["title"],
        description=quiz_data["description"],
        video_url=video_url,
    )
    Question.objects.bulk_create(create_questions(quiz, quiz_data["questions"]))
    return quiz


def create_questions(quiz, question_data):
    """Build unsaved question instances for a quiz."""

    return [Question(quiz=quiz, **data) for data in question_data]
