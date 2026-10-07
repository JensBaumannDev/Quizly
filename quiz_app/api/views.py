import logging

from django.conf import settings
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts_app.api.authentication import CookieJWTAuthentication
from quiz_app.models import Quiz
from quiz_app.services.quiz_creation import create_quiz_from_video

from .permissions import IsQuizOwner
from .serializers import (
    QuizCreateRequestSerializer,
    QuizCreateResponseSerializer,
    QuizSerializer,
    QuizUpdateSerializer,
)


logger = logging.getLogger(__name__)


class QuizListView(generics.ListAPIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = QuizSerializer

    def post(self, request):
        serializer = QuizCreateRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return self.create_quiz_response(
            request.user, serializer.validated_data["url"]
        )

    def create_quiz_response(self, user, video_url):
        try:
            quiz = create_quiz_from_video(
                user, video_url, settings.GEMINI_API_KEY
            )
        except Exception:
            logger.exception("Quiz generation failed.")
            return Response(
                {"detail": "Quiz generation failed."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        response_data = QuizCreateResponseSerializer(quiz).data
        return Response(response_data, status=status.HTTP_201_CREATED)

    def get_queryset(self):
        return (
            Quiz.objects.filter(user=self.request.user)
            .prefetch_related("questions")
        )


class QuizDetailView(generics.RetrieveUpdateDestroyAPIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated, IsQuizOwner]
    queryset = Quiz.objects.prefetch_related("questions")
    serializer_class = QuizSerializer

    def get_serializer_class(self):
        if self.request.method == "PATCH":
            return QuizUpdateSerializer
        return QuizSerializer
