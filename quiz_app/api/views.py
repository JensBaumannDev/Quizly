from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from accounts_app.api.authentication import CookieJWTAuthentication
from quiz_app.models import Quiz

from .permissions import IsQuizOwner
from .serializers import QuizSerializer


class QuizListView(generics.ListAPIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = QuizSerializer

    def get_queryset(self):
        return (
            Quiz.objects.filter(user=self.request.user)
            .prefetch_related("questions")
        )


class QuizDetailView(generics.RetrieveAPIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated, IsQuizOwner]
    queryset = Quiz.objects.prefetch_related("questions")
    serializer_class = QuizSerializer
