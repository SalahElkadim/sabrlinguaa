from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    STEPSkill,
    StudentSTEPProgress,
    StudentSTEPQuestionView,
)

User = get_user_model()


# ============================================
# STEP Skill Serializers

class STEPSkillListSerializer(serializers.ModelSerializer):
    total_questions = serializers.SerializerMethodField()
    child_skills = serializers.SerializerMethodField()
    current_question = serializers.SerializerMethodField()  # ← جديد

    class Meta:
        model = STEPSkill
        fields = [
            'id',
            'skill_type',
            'title',
            'description',
            'icon',
            'order',
            'total_questions',
            'child_skills',
            'current_question',  # ← جديد
            'is_active',
            'question_order_type', 
        ]

    def get_total_questions(self, obj):
        return obj.get_total_questions_count()

    def get_child_skills(self, obj):
        if obj.skill_type == 'GENERAL_PATH':
            children = obj.child_skills.filter().order_by('order')
            # ← لازم نبعت الـ context هنا كمان عشان الأولاد ياخدوا current_question صح
            return STEPSkillListSerializer(children, many=True, context=self.context).data
        return None

    # ← الميثود الجديدة (نفسها بالظبط اللي في الـ Detail)
    def get_current_question(self, obj):
        request = self.context.get('request')
        if not request or not request.user or not request.user.is_authenticated:
            return 1

        student = request.user

        try:
            progress = StudentSTEPProgress.objects.get(student=student, skill=obj)
            return progress.viewed_questions_count + 1
        except StudentSTEPProgress.DoesNotExist:
            return 1

class STEPSkillDetailSerializer(serializers.ModelSerializer):
    total_questions = serializers.SerializerMethodField()
    child_skills = serializers.SerializerMethodField()
    current_question = serializers.SerializerMethodField()  # ← السطر الجديد

    class Meta:
        model = STEPSkill
        fields = [
            'id', 'skill_type', 'title', 'description',
            'icon', 'order', 'is_active', 'total_questions',
            'child_skills',
            'current_question',  # ← ضفناه هنا في الليستة
            'created_at', 'updated_at', 'question_order_type',
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_total_questions(self, obj):
        return obj.get_total_questions_count()

    def get_child_skills(self, obj):
        if obj.skill_type == 'GENERAL_PATH':
            children = obj.child_skills.filter().order_by('order')
            return STEPSkillListSerializer(children, many=True, context=self.context).data
        return None

    # ← الميثود الجديدة كلها
    def get_current_question(self, obj):
        request = self.context.get('request')
        if not request or not request.user or not request.user.is_authenticated:
            return 1

        student = request.user

        try:
            progress = StudentSTEPProgress.objects.get(student=student, skill=obj)
            return progress.viewed_questions_count + 1
        except StudentSTEPProgress.DoesNotExist:
            return 1
# ============================================
# Student Progress Serializers
# ============================================

class StudentSTEPProgressSerializer(serializers.ModelSerializer):
    skill_title = serializers.CharField(source='skill.title', read_only=True)
    skill_type = serializers.CharField(source='skill.skill_type', read_only=True)
    progress_percentage = serializers.SerializerMethodField()
    total_questions = serializers.SerializerMethodField()
    
    class Meta:
        model = StudentSTEPProgress
        fields = [
            'id',
            'student',
            'skill',
            'skill_title',
            'skill_type',
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


class StudentSTEPQuestionViewSerializer(serializers.ModelSerializer):
    skill_title = serializers.CharField(source='skill.title', read_only=True)
    
    class Meta:
        model = StudentSTEPQuestionView
        fields = [
            'id',
            'student',
            'skill',
            'skill_title',
            'question_type',
            'question_id',
            'viewed_at',
        ]
        read_only_fields = ['viewed_at']


# ============================================
# Question Serializers
# ============================================

class VocabularyQuestionSTEPSerializer(serializers.Serializer):
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
    english_explanation = serializers.CharField(required=False, allow_null=True)
    points = serializers.IntegerField()


class GrammarQuestionSTEPSerializer(serializers.Serializer):
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
    english_explanation = serializers.CharField(required=False, allow_null=True)
    points = serializers.IntegerField()


class ReadingQuestionSTEPSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    difficulty = serializers.CharField(required=False)
    question_text = serializers.CharField()
    choice_a = serializers.CharField()
    choice_b = serializers.CharField()
    choice_c = serializers.CharField()
    choice_d = serializers.CharField()
    correct_answer = serializers.CharField()
    explanation = serializers.CharField(required=False, allow_null=True)
    english_explanation = serializers.CharField(required=False, allow_null=True)
    points = serializers.IntegerField()


class ReadingPassageSTEPSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    passage_text = serializers.CharField()
    passage_image = serializers.URLField(required=False, allow_null=True)
    source = serializers.CharField(required=False, allow_null=True)
    questions = ReadingQuestionSTEPSerializer(many=True)
    difficulty = serializers.CharField(required=False)  


# ============================================
# Listening Serializers ← جديد
# ============================================

class ListeningQuestionSTEPSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    difficulty = serializers.CharField(required=False)
    question_text = serializers.CharField()
    choice_a = serializers.CharField()
    choice_b = serializers.CharField()
    choice_c = serializers.CharField()
    choice_d = serializers.CharField()
    correct_answer = serializers.CharField()
    explanation = serializers.CharField(required=False, allow_null=True)
    english_explanation = serializers.CharField(required=False, allow_null=True)
    points = serializers.IntegerField()


class ListeningAudioSTEPSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    audio_file = serializers.SerializerMethodField()  # ← غيّر ده
    transcript = serializers.CharField(required=False, allow_null=True)
    duration = serializers.IntegerField(required=False, allow_null=True)
    questions = ListeningQuestionSTEPSerializer(many=True)
    difficulty = serializers.CharField(required=False)

    def get_audio_file(self, obj):  # ← أضف الميثود دي
        if obj.audio_file:
            return obj.audio_file.url  # بيرجع الـ Cloudinary URL الكامل
        return None


# ============================================
# Writing Serializer
# ============================================

class WritingQuestionSTEPSerializer(serializers.Serializer):
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

# SPEAKING

class SpeakingQuestionSTEPSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    question_text = serializers.CharField()
    choice_a = serializers.CharField()
    choice_b = serializers.CharField()
    choice_c = serializers.CharField()
    choice_d = serializers.CharField()
    correct_answer = serializers.CharField()
    explanation = serializers.CharField(required=False, allow_null=True)
    english_explanation = serializers.CharField(required=False, allow_null=True)
    points = serializers.IntegerField()
    difficulty = serializers.CharField(required=False)


class SpeakingVideoSTEPSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    video_file = serializers.SerializerMethodField()  # ← غيّر
    description = serializers.CharField(required=False, allow_null=True)
    duration = serializers.IntegerField(required=False, allow_null=True)
    thumbnail = serializers.SerializerMethodField()  # ← غيّر
    questions = SpeakingQuestionSTEPSerializer(many=True)
    difficulty = serializers.CharField(required=False)

    def get_video_file(self, obj):  # ← أضف
        if obj.video_file:
            return obj.video_file.url
        return None

    def get_thumbnail(self, obj):  # ← أضف
        if obj.thumbnail:
            return obj.thumbnail.url
        return None