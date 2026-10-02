from rest_framework import serializers

from quiz_app.models import Question, Quiz


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ["id", "question_title", "question_options", "answer"]


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
