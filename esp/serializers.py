from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    EspCategory,
    EspSkill,
    StudentEspProgress,
)

User = get_user_model()


# ============================================
# Category Serializers
# ============================================

class EspCategoryListSerializer(serializers.ModelSerializer):
    total_questions = serializers.SerializerMethodField()
    skills_count = serializers.SerializerMethodField()

    class Meta:
        model = EspCategory
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
        return obj.skills.filter(is_active=True).count()


class EspCategoryDetailSerializer(serializers.ModelSerializer):
    total_questions = serializers.SerializerMethodField()
    skills = serializers.SerializerMethodField()

    class Meta:
        model = EspCategory
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
        return EspSkillListSerializer(skills, many=True).data


# ============================================
# Skill Serializers
# ============================================

class EspSkillListSerializer(serializers.ModelSerializer):
    total_questions = serializers.SerializerMethodField()
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = EspSkill
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


class EspSkillDetailSerializer(serializers.ModelSerializer):
    total_questions = serializers.SerializerMethodField()
    category_name = serializers.CharField(source='category.name', read_only=True)
    is_active = serializers.BooleanField()  # أضف السطر ده


    class Meta:
        model = EspSkill
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

class StudentEspProgressSerializer(serializers.ModelSerializer):
    skill_title = serializers.CharField(source='skill.title', read_only=True)
    skill_type = serializers.CharField(source='skill.skill_type', read_only=True)
    category_name = serializers.CharField(source='skill.category.name', read_only=True)
    progress_percentage = serializers.SerializerMethodField()
    total_questions = serializers.SerializerMethodField()

    class Meta:
        model = StudentEspProgress
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

class VocabularyQuestionEspSerializer(serializers.Serializer):
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


class GrammarQuestionEspSerializer(serializers.Serializer):
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


class ReadingQuestionEspSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    question_text = serializers.CharField()
    choice_a = serializers.CharField()
    choice_b = serializers.CharField()
    choice_c = serializers.CharField()
    choice_d = serializers.CharField()
    correct_answer = serializers.CharField()
    explanation = serializers.CharField(required=False, allow_null=True)
    points = serializers.IntegerField()


class ReadingPassageEspSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    passage_text = serializers.CharField()
    passage_image = serializers.URLField(required=False, allow_null=True)
    source = serializers.CharField(required=False, allow_null=True)
    difficulty = serializers.CharField(required=False)
    questions = ReadingQuestionEspSerializer(many=True)


class ListeningQuestionEspSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    question_text = serializers.CharField()
    choice_a = serializers.CharField()
    choice_b = serializers.CharField()
    choice_c = serializers.CharField()
    choice_d = serializers.CharField()
    correct_answer = serializers.CharField()
    explanation = serializers.CharField(required=False, allow_null=True)
    points = serializers.IntegerField()


class ListeningAudioEspSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    audio_file = serializers.URLField(required=False, allow_null=True)
    transcript = serializers.CharField(required=False, allow_null=True)
    duration = serializers.IntegerField(required=False, allow_null=True)
    difficulty = serializers.CharField(required=False)
    questions = ListeningQuestionEspSerializer(many=True)


class WritingQuestionEspSerializer(serializers.Serializer):
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


class SpeakingQuestionEspSerializer(serializers.Serializer):
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


class SpeakingVideoEspSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    video_file = serializers.URLField(required=False, allow_null=True)
    description = serializers.CharField(required=False, allow_null=True)
    duration = serializers.IntegerField(required=False, allow_null=True)
    thumbnail = serializers.URLField(required=False, allow_null=True)
    difficulty = serializers.CharField(required=False)
    questions = SpeakingQuestionEspSerializer(many=True)