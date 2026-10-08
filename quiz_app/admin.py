from django.contrib import admin

from .models import Question, Quiz


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    """Configure quiz management in the Django admin panel."""

    list_display = ["title", "user", "created_at", "updated_at"]
    search_fields = ["title", "user__username"]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    """Configure question management in the Django admin panel."""

    list_display = ["question_title", "quiz", "answer"]
    search_fields = ["question_title", "quiz__title"]
