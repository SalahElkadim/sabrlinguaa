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
    is_favorite = serializers.SerializerMethodField()

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
            'is_favorite',
        ]

    def get_total_questions(self, obj):
        return obj.get_total_questions_count()

    def get_skills_count(self, obj):
        return obj.skills.filter().count()
    
    def get_is_favorite(self, obj):
        from .models import StudentFavoriteCategory  # ← أو استورده فوق
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return StudentFavoriteCategory.objects.filter(
            student=request.user, category=obj
        ).exists()


# serializers.py
from cloudinary.uploader import upload as cloudinary_upload

class GeneralCategoryDetailSerializer(serializers.ModelSerializer):
    icon = serializers.ImageField(write_only=True, required=False)
    icon_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = GeneralCategory
        fields = [
            'id', 'name', 'description',
            'icon',      # write only
            'icon_url',  # read only
            'order', 'is_active',
            'total_questions', 'skills',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_icon_url(self, obj):
        if obj.icon:
            return obj.icon.url
        return None

    def get_total_questions(self, obj):
        return obj.get_total_questions_count()

    def get_skills(self, obj):
        skills = obj.skills.filter().order_by('order')
        return GeneralSkillListSerializer(skills, many=True).data

    def _upload_icon(self, icon_file):
        result = cloudinary_upload(
            icon_file,
            folder='general/category_icons'
        )
        return result['public_id']

    def create(self, validated_data):
        icon_file = validated_data.pop('icon', None)
        instance = super().create(validated_data)
        if icon_file:
            instance.icon = self._upload_icon(icon_file)
            instance.save()
        return instance

    def update(self, instance, validated_data):
        icon_file = validated_data.pop('icon', None)
        instance = super().update(instance, validated_data)
        if icon_file:
            instance.icon = self._upload_icon(icon_file)
            instance.save()
        return instance
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
            'question_order_type', 
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
            'question_order_type', 
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

from .models import GeneralCategory, GeneralSkill, StudentGeneralProgress, StudentFavoriteCategory

class StudentFavoriteCategorySerializer(serializers.ModelSerializer):
    category = GeneralCategoryListSerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=GeneralCategory.objects.all(),
        source='category',
        write_only=True
    )

    class Meta:
        model = StudentFavoriteCategory
        fields = ['id', 'category', 'category_id', 'created_at']
        read_only_fields = ['id', 'created_at']