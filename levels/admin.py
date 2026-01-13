from django.contrib import admin
from .models import (
    Level, Unit, Section, Lesson, Exercise,

    ExerciseMCQQuestion,

    ExerciseReadingPassage, ExerciseReadingQuestion,

    ExerciseListeningAudio, ExerciseListeningQuestion,

    ExerciseSpeakingVideo, ExerciseSpeakingQuestion,

    ExerciseWritingQuestion
)

# ============================================
# Base Course Structure
# ============================================

@admin.register(Level)
class LevelAdmin(admin.ModelAdmin):
    list_display = ('code', 'name')
    search_fields = ('code', 'name')
    ordering = ('code',)


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ('level', 'number', 'title')
    list_filter = ('level',)
    ordering = ('level', 'number')
    search_fields = ('title',)


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ('unit', 'section_type', 'title', 'order')
    list_filter = ('section_type', 'unit__level')
    ordering = ('unit', 'order')
    search_fields = ('title',)


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('section', 'title', 'order')
    list_filter = ('section__unit__level', 'section__section_type')
    ordering = ('section', 'order')
    search_fields = ('title',)


# ============================================
# Exercise
# ============================================

@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ('lesson', 'title', 'order', 'is_active')
    list_filter = ('is_active', 'lesson__section__section_type')
    search_fields = ('title',)
    ordering = ('lesson', 'order')


# ============================================
# MCQ Questions
# ============================================

@admin.register(ExerciseMCQQuestion)
class ExerciseMCQQuestionAdmin(admin.ModelAdmin):
    list_display = ('exercise', 'question_text', 'correct_answer', 'points', 'order', 'is_active')
    list_filter = ('is_active', 'exercise')
    search_fields = ('question_text',)
    ordering = ('exercise', 'order')


# ============================================
# Reading
# ============================================

@admin.register(ExerciseReadingPassage)
class ExerciseReadingPassageAdmin(admin.ModelAdmin):
    list_display = ('exercise', 'title', 'order', 'is_active')
    list_filter = ('is_active', 'exercise')
    search_fields = ('title',)
    ordering = ('exercise', 'order')


@admin.register(ExerciseReadingQuestion)
class ExerciseReadingQuestionAdmin(admin.ModelAdmin):
    list_display = ('passage', 'question_text', 'correct_answer', 'points', 'order')
    search_fields = ('question_text',)
    ordering = ('order',)


# ============================================
# Listening
# ============================================

@admin.register(ExerciseListeningAudio)
class ExerciseListeningAudioAdmin(admin.ModelAdmin):
    list_display = ('exercise', 'title', 'duration', 'order', 'is_active')
    list_filter = ('is_active', 'exercise')
    search_fields = ('title',)
    ordering = ('exercise', 'order')


@admin.register(ExerciseListeningQuestion)
class ExerciseListeningQuestionAdmin(admin.ModelAdmin):
    list_display = ('audio', 'question_text', 'correct_answer', 'points', 'order')
    search_fields = ('question_text',)
    ordering = ('order',)


# ============================================
# Speaking
# ============================================

@admin.register(ExerciseSpeakingVideo)
class ExerciseSpeakingVideoAdmin(admin.ModelAdmin):
    list_display = ('exercise', 'title', 'duration', 'order', 'is_active')
    list_filter = ('is_active', 'exercise')
    search_fields = ('title',)
    ordering = ('exercise', 'order')


@admin.register(ExerciseSpeakingQuestion)
class ExerciseSpeakingQuestionAdmin(admin.ModelAdmin):
    list_display = ('video', 'question_text', 'correct_answer', 'points', 'order')
    search_fields = ('question_text',)
    ordering = ('order',)


# ============================================
# Writing
# ============================================

@admin.register(ExerciseWritingQuestion)
class ExerciseWritingQuestionAdmin(admin.ModelAdmin):
    list_display = ('exercise', 'title', 'min_words', 'max_words', 'points', 'order', 'is_active')
    list_filter = ('is_active', 'exercise')
    search_fields = ('title', 'question_text')
    ordering = ('exercise', 'order')
