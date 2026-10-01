from django.contrib import admin

from .models import Question, Quiz


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ["title", "user", "created_at", "updated_at"]
    search_fields = ["title", "user__username"]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ["question_title", "quiz", "answer"]
    search_fields = ["question_title", "quiz__title"]

# Register your models here.
