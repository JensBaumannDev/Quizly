from rest_framework import serializers

from quiz_app.models import Question, Quiz
from quiz_app.services.audio import is_valid_youtube_url


class QuizCreateRequestSerializer(serializers.Serializer):
    """Validate requests for generating a quiz from YouTube."""

    url = serializers.URLField()

    def validate(self, attributes):
        """Reject request fields other than the video URL."""

        if set(self.initial_data) != {"url"}:
            raise serializers.ValidationError("Only a YouTube URL is allowed.")
        return attributes

    def validate_url(self, video_url):
        """Ensure that the supplied URL identifies a YouTube video."""

        if not is_valid_youtube_url(video_url):
            raise serializers.ValidationError(
                "A valid YouTube URL is required."
            )
        return video_url


class QuestionSerializer(serializers.ModelSerializer):
    """Serialize question data for quiz responses."""

    class Meta:
        """Configure fields exposed for a question."""

        model = Question
        fields = ["id", "question_title", "question_options", "answer"]


class QuestionCreateResponseSerializer(QuestionSerializer):
    """Serialize questions with creation and update timestamps."""

    class Meta(QuestionSerializer.Meta):
        """Add timestamps to generated question responses."""

        fields = QuestionSerializer.Meta.fields + ["created_at", "updated_at"]


class QuizSerializer(serializers.ModelSerializer):
    """Serialize quizzes together with their questions."""

    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        """Configure fields exposed for a quiz."""

        model = Quiz
        fields = [
            "id",
            "title",
            "description",
            "created_at",
            "updated_at",
            "video_url",
            "questions",
        ]


class QuizCreateResponseSerializer(QuizSerializer):
    """Serialize a newly generated quiz with complete question data."""

    questions = QuestionCreateResponseSerializer(many=True, read_only=True)


class QuizUpdateSerializer(QuizSerializer):
    """Restrict quiz updates to title and description."""

    class Meta(QuizSerializer.Meta):
        """Configure fields that cannot be changed on a quiz."""

        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "video_url",
            "questions",
        ]

    def validate(self, attributes):
        """Reject empty updates and changes to read-only quiz fields."""

        editable_fields = {"title", "description"}
        invalid_fields = set(self.initial_data) - editable_fields
        if invalid_fields or not attributes:
            raise serializers.ValidationError(
                "Only title and description can be updated."
            )
        return attributes
