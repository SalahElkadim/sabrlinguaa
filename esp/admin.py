# esp/admin.py
from django.contrib import admin
from .models import (
    EspCategory, EspSkill,
    StudentEspProgress, StudentEspQuestionAttempt,
)
from .ai_models import EspExtractedBook, EspExtractedMedia, EspAIGenerationJob


@admin.register(EspCategory)
class EspCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'order', 'is_active', 'created_at']
    list_editable = ['order', 'is_active']
    search_fields = ['name']


@admin.register(EspSkill)
class EspSkillAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'skill_type', 'order', 'is_active']
    list_editable = ['order', 'is_active']
    list_filter = ['skill_type', 'category']
    search_fields = ['title']


@admin.register(StudentEspProgress)
class StudentEspProgressAdmin(admin.ModelAdmin):
    list_display = ['student', 'skill', 'viewed_questions_count', 'total_score']
    list_filter = ['skill__skill_type']
    search_fields = ['student__email']


@admin.register(StudentEspQuestionAttempt)
class StudentEspQuestionAttemptAdmin(admin.ModelAdmin):
    list_display = ['student', 'question_type', 'question_id', 'attempts_count', 'is_solved', 'points_earned']
    list_filter = ['question_type', 'is_solved']
    search_fields = ['student__email']


@admin.register(EspExtractedBook)
class EspExtractedBookAdmin(admin.ModelAdmin):
    list_display = ['name', 'status', 'page_count', 'uploaded_by', 'created_at']
    list_filter = ['status']
    search_fields = ['name']


@admin.register(EspExtractedMedia)
class EspExtractedMediaAdmin(admin.ModelAdmin):
    list_display = ['name', 'media_type', 'status', 'duration_seconds', 'uploaded_by']
    list_filter = ['media_type', 'status']
    search_fields = ['name']


@admin.register(EspAIGenerationJob)
class EspAIGenerationJobAdmin(admin.ModelAdmin):
    list_display = ['id', 'category', 'skill_type', 'status', 'questions_created', 'created_at']
    list_filter = ['status', 'skill_type']
    search_fields = ['category__name']
    readonly_fields = ['questions_created', 'created_at', 'updated_at']