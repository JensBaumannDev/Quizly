from drf_yasg import openapi
from drf_yasg.utils import no_body, swagger_auto_schema

from .serializers import (
    QuizCreateRequestSerializer,
    QuizCreateResponseSerializer,
    QuizSerializer,
    QuizUpdateSerializer,
)


COOKIE_SECURITY = [{"CookieAuth": []}]
UNAUTHENTICATED = openapi.Response("Authentication is required.")
FORBIDDEN = openapi.Response("The user does not own this quiz.")
NOT_FOUND = openapi.Response("Quiz not found.")
INTERNAL_ERROR = openapi.Response("Internal server error.")

QUIZ_LIST_DOCUMENTATION = swagger_auto_schema(
    operation_summary="List quizzes",
    operation_description="Return all quizzes owned by the authenticated user.",
    responses={
        200: QuizSerializer(many=True),
        401: UNAUTHENTICATED,
        500: INTERNAL_ERROR,
    },
    security=COOKIE_SECURITY,
    tags=["Quizzes"],
)

QUIZ_CREATE_DOCUMENTATION = swagger_auto_schema(
    operation_summary="Create a quiz",
    operation_description="Generate a quiz from a YouTube video URL.",
    request_body=QuizCreateRequestSerializer,
    responses={
        201: QuizCreateResponseSerializer,
        400: openapi.Response("Invalid URL or request data."),
        401: UNAUTHENTICATED,
        500: INTERNAL_ERROR,
    },
    security=COOKIE_SECURITY,
    tags=["Quizzes"],
)

QUIZ_DETAIL_DOCUMENTATION = swagger_auto_schema(
    operation_summary="Retrieve a quiz",
    operation_description="Return one quiz owned by the authenticated user.",
    responses={
        200: QuizSerializer,
        401: UNAUTHENTICATED,
        403: FORBIDDEN,
        404: NOT_FOUND,
        500: INTERNAL_ERROR,
    },
    security=COOKIE_SECURITY,
    tags=["Quizzes"],
)

QUIZ_UPDATE_DOCUMENTATION = swagger_auto_schema(
    operation_summary="Update a quiz",
    operation_description="Update the title or description of an owned quiz.",
    request_body=QuizUpdateSerializer,
    responses={
        200: QuizSerializer,
        400: openapi.Response("Invalid update data."),
        401: UNAUTHENTICATED,
        403: FORBIDDEN,
        404: NOT_FOUND,
        500: INTERNAL_ERROR,
    },
    security=COOKIE_SECURITY,
    tags=["Quizzes"],
)

QUIZ_DELETE_DOCUMENTATION = swagger_auto_schema(
    operation_summary="Delete a quiz",
    operation_description="Delete one quiz owned by the authenticated user.",
    request_body=no_body,
    responses={
        204: openapi.Response("Quiz deleted successfully."),
        401: UNAUTHENTICATED,
        403: FORBIDDEN,
        404: NOT_FOUND,
        500: INTERNAL_ERROR,
    },
    security=COOKIE_SECURITY,
    tags=["Quizzes"],
)
