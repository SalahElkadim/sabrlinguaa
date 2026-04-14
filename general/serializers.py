from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    GeneralCategory,
    GeneralSkill,
    StudentGeneralProgress,
)

User = get_user_model()


# ============================================
# Category Serializers
# ============================================

class GeneralCategoryListSerializer(serializers.ModelSerializer):
    total_questions = serializers.SerializerMethodField()
    skills_count = serializers.SerializerMethodField()

    class Meta:
        model = GeneralCategory
        fields = [
            'id',
            'name',
            'description',
            'icon',
            'order',
            'is_active',
            'total_questions',
            'skills_count',
        ]

    def get_total_questions(self, obj):
        return obj.get_total_questions_count()

    def get_skills_count(self, obj):
        return obj.skills.filter().count()


class GeneralCategoryDetailSerializer(serializers.ModelSerializer):
    total_questions = serializers.SerializerMethodField()
    skills = serializers.SerializerMethodField()

    class Meta:
        model = GeneralCategory
        fields = [
            'id',
            'name',
            'description',
            'icon',
            'order',
            'is_active',
            'total_questions',
            'skills',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_total_questions(self, obj):
        return obj.get_total_questions_count()

    def get_skills(self, obj):
        skills = obj.skills.filter().order_by('order')
        return GeneralSkillListSerializer(skills, many=True).data


# ============================================
# Skill Serializers
# ============================================

class GeneralSkillListSerializer(serializers.ModelSerializer):
    total_questions = serializers.SerializerMethodField()
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = GeneralSkill
        fields = [
            'id',
            'category',
            'category_name',
            'skill_type',
            'title',
            'description',
            'icon',
            'order',
            'is_active',
            'total_questions',
        ]

    def get_total_questions(self, obj):
        return obj.get_total_questions_count()


class GeneralSkillDetailSerializer(serializers.ModelSerializer):
    total_questions = serializers.SerializerMethodField()
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = GeneralSkill
        fields = [
            'id',
            'category',
            'category_name',
            'skill_type',
            'title',
            'description',
            'icon',
            'order',
            'is_active',
            'total_questions',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_total_questions(self, obj):
        return obj.get_total_questions_count()


# ============================================
# Student Progress Serializers
# ============================================

class StudentGeneralProgressSerializer(serializers.ModelSerializer):
    skill_title = serializers.CharField(source='skill.title', read_only=True)
    skill_type = serializers.CharField(source='skill.skill_type', read_only=True)
    category_name = serializers.CharField(source='skill.category.name', read_only=True)
    progress_percentage = serializers.SerializerMethodField()
    total_questions = serializers.SerializerMethodField()

    class Meta:
        model = StudentGeneralProgress
        fields = [
            'id',
            'student',
            'skill',
            'skill_title',
            'skill_type',
            'category_name',
            'viewed_questions_count',
            'total_questions',
            'progress_percentage',
            'total_score',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at', 'viewed_questions_count', 'total_score']

    def get_progress_percentage(self, obj):
        return obj.calculate_progress_percentage()

    def get_total_questions(self, obj):
        return obj.skill.get_total_questions_count()


# ============================================
# Question Serializers (نفس نظام IELTS)
# ============================================

class VocabularyQuestionGeneralSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    difficulty = serializers.CharField(required=False)
    question_text = serializers.CharField()
    question_image = serializers.URLField(required=False, allow_null=True)
    choice_a = serializers.CharField()
    choice_b = serializers.CharField()
    choice_c = serializers.CharField()
    choice_d = serializers.CharField()
    correct_answer = serializers.CharField()
    explanation = serializers.CharField(required=False, allow_null=True)
    points = serializers.IntegerField()


class GrammarQuestionGeneralSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    difficulty = serializers.CharField(required=False)
    question_text = serializers.CharField()
    question_image = serializers.URLField(required=False, allow_null=True)
    choice_a = serializers.CharField()
    choice_b = serializers.CharField()
    choice_c = serializers.CharField()
    choice_d = serializers.CharField()
    correct_answer = serializers.CharField()
    explanation = serializers.CharField(required=False, allow_null=True)
    points = serializers.IntegerField()


class ReadingQuestionGeneralSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    question_text = serializers.CharField()
    choice_a = serializers.CharField()
    choice_b = serializers.CharField()
    choice_c = serializers.CharField()
    choice_d = serializers.CharField()
    correct_answer = serializers.CharField()
    explanation = serializers.CharField(required=False, allow_null=True)
    points = serializers.IntegerField()


class ReadingPassageGeneralSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    passage_text = serializers.CharField()
    passage_image = serializers.URLField(required=False, allow_null=True)
    source = serializers.CharField(required=False, allow_null=True)
    difficulty = serializers.CharField(required=False)
    questions = ReadingQuestionGeneralSerializer(many=True)


class ListeningQuestionGeneralSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    question_text = serializers.CharField()
    choice_a = serializers.CharField()
    choice_b = serializers.CharField()
    choice_c = serializers.CharField()
    choice_d = serializers.CharField()
    correct_answer = serializers.CharField()
    explanation = serializers.CharField(required=False, allow_null=True)
    points = serializers.IntegerField()


class ListeningAudioGeneralSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    audio_file = serializers.URLField(required=False, allow_null=True)
    transcript = serializers.CharField(required=False, allow_null=True)
    duration = serializers.IntegerField(required=False, allow_null=True)
    difficulty = serializers.CharField(required=False)
    questions = ListeningQuestionGeneralSerializer(many=True)


class WritingQuestionGeneralSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    question_text = serializers.CharField()
    question_image = serializers.URLField(required=False, allow_null=True)
    min_words = serializers.IntegerField()
    max_words = serializers.IntegerField()
    sample_answer = serializers.CharField(required=False, allow_null=True)
    rubric = serializers.CharField(required=False, allow_null=True)
    points = serializers.IntegerField()
    difficulty = serializers.CharField(required=False)


class SpeakingQuestionGeneralSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    question_text = serializers.CharField()
    choice_a = serializers.CharField()
    choice_b = serializers.CharField()
    choice_c = serializers.CharField()
    choice_d = serializers.CharField()
    correct_answer = serializers.CharField()
    explanation = serializers.CharField(required=False, allow_null=True)
    points = serializers.IntegerField()
    difficulty = serializers.CharField(required=False)


class SpeakingVideoGeneralSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    video_file = serializers.URLField(required=False, allow_null=True)
    description = serializers.CharField(required=False, allow_null=True)
    duration = serializers.IntegerField(required=False, allow_null=True)
    thumbnail = serializers.URLField(required=False, allow_null=True)
    difficulty = serializers.CharField(required=False)
    questions = SpeakingQuestionGeneralSerializer(many=True)