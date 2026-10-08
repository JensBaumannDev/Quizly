import logging

from django.conf import settings
from django.utils.decorators import method_decorator
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts_app.api.authentication import CookieJWTAuthentication
from quiz_app.models import Quiz
from quiz_app.services.quiz_creation import create_quiz_from_video

from .documentation import (
    QUIZ_CREATE_DOCUMENTATION,
    QUIZ_DELETE_DOCUMENTATION,
    QUIZ_DETAIL_DOCUMENTATION,
    QUIZ_LIST_DOCUMENTATION,
    QUIZ_UPDATE_DOCUMENTATION,
)
from .permissions import IsQuizOwner
from .serializers import (
    QuizCreateRequestSerializer,
    QuizCreateResponseSerializer,
    QuizSerializer,
    QuizUpdateSerializer,
)


logger = logging.getLogger(__name__)


@method_decorator(name="get", decorator=QUIZ_LIST_DOCUMENTATION)
class QuizListView(generics.ListAPIView):
    """List owned quizzes and create new AI-generated quizzes."""

    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = QuizSerializer

    @QUIZ_CREATE_DOCUMENTATION
    def post(self, request):
        """Validate a YouTube URL and start quiz generation."""

        serializer = QuizCreateRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return self.create_quiz_response(
            request.user, serializer.validated_data["url"]
        )

    def create_quiz_response(self, user, video_url):
        """Generate, serialize, and return a quiz for the user."""
        try:
            quiz = create_quiz_from_video(
                user, video_url, settings.GEMINI_API_KEY, settings.GEMINI_MODEL
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
        """Return quizzes owned by the authenticated user."""

        return (
            Quiz.objects.filter(user=self.request.user)
            .prefetch_related("questions")
        )


@method_decorator(name="get", decorator=QUIZ_DETAIL_DOCUMENTATION)
@method_decorator(name="patch", decorator=QUIZ_UPDATE_DOCUMENTATION)
@method_decorator(name="delete", decorator=QUIZ_DELETE_DOCUMENTATION)
class QuizDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a quiz owned by the user."""

    http_method_names = ["get", "patch", "delete", "head", "options"]
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated, IsQuizOwner]
    queryset = Quiz.objects.prefetch_related("questions")
    serializer_class = QuizSerializer

    def get_serializer_class(self):
        """Use the restricted serializer for partial updates."""

        if self.request.method == "PATCH":
            return QuizUpdateSerializer
        return QuizSerializer
