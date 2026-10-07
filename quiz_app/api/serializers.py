from rest_framework import serializers

from quiz_app.models import Question, Quiz
from quiz_app.services.audio import is_valid_youtube_url


class QuizCreateRequestSerializer(serializers.Serializer):
    url = serializers.URLField()

    def validate(self, attributes):
        if set(self.initial_data) != {"url"}:
            raise serializers.ValidationError("Only a YouTube URL is allowed.")
        return attributes

    def validate_url(self, video_url):
        if not is_valid_youtube_url(video_url):
            raise serializers.ValidationError(
                "A valid YouTube URL is required."
            )
        return video_url


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ["id", "question_title", "question_options", "answer"]


class QuestionCreateResponseSerializer(QuestionSerializer):
    class Meta(QuestionSerializer.Meta):
        fields = QuestionSerializer.Meta.fields + ["created_at", "updated_at"]


class QuizSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
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
    questions = QuestionCreateResponseSerializer(many=True, read_only=True)


class QuizUpdateSerializer(QuizSerializer):
    class Meta(QuizSerializer.Meta):
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "video_url",
            "questions",
        ]

    def validate(self, attributes):
        editable_fields = {"title", "description"}
        invalid_fields = set(self.initial_data) - editable_fields
        if invalid_fields or not attributes:
            raise serializers.ValidationError("Only title and description can be updated.")
        return attributes
