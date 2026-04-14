from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    IELTSSkill,
    StudentIELTSProgress,
    StudentIELTSQuestionView,
)

User = get_user_model()


# ============================================
# IELTS Skill Serializers
# ============================================
class IELTSSkillListSerializer(serializers.ModelSerializer):
    total_questions = serializers.SerializerMethodField()
    child_skills = serializers.SerializerMethodField()  # ← جديد

    class Meta:
        model = IELTSSkill
        fields = [
            'id',
            'skill_type',
            'title',
            'description',
            'icon',
            'order',
            'total_questions',
            'child_skills', 
            'is_active', # ← جديد
            'question_order_type', 
        ]

    def get_total_questions(self, obj):
        return obj.get_total_questions_count()

    # ← جديد
    def get_child_skills(self, obj):
        if obj.skill_type == 'GENERAL_PATH':
            children = obj.child_skills.filter().order_by('order')
            return IELTSSkillListSerializer(children, many=True).data
        return None

class IELTSSkillDetailSerializer(serializers.ModelSerializer):
    total_questions = serializers.SerializerMethodField()
    child_skills = serializers.SerializerMethodField()  # ← جديد

    class Meta:
        model = IELTSSkill
        fields = [
            'id', 'skill_type', 'title', 'description',
            'icon', 'order', 'is_active', 'total_questions',
            'child_skills',  # ← جديد
            'created_at', 'updated_at','question_order_type', 
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_total_questions(self, obj):
        return obj.get_total_questions_count()

    # ← جديد
    def get_child_skills(self, obj):
        if obj.skill_type == 'GENERAL_PATH':
            children = obj.child_skills.filter().order_by('order')
            return IELTSSkillListSerializer(children, many=True).data
        return None


# ============================================
# Student Progress Serializers
# ============================================

class StudentIELTSProgressSerializer(serializers.ModelSerializer):
    skill_title = serializers.CharField(source='skill.title', read_only=True)
    skill_type = serializers.CharField(source='skill.skill_type', read_only=True)
    progress_percentage = serializers.SerializerMethodField()
    total_questions = serializers.SerializerMethodField()
    
    class Meta:
        model = StudentIELTSProgress
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


class StudentIELTSQuestionViewSerializer(serializers.ModelSerializer):
    skill_title = serializers.CharField(source='skill.title', read_only=True)
    
    class Meta:
        model = StudentIELTSQuestionView
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

class VocabularyQuestionIELTSSerializer(serializers.Serializer):
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


class GrammarQuestionIELTSSerializer(serializers.Serializer):
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


class ReadingQuestionIELTSSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    difficulty = serializers.CharField(required=False)
    question_text = serializers.CharField()
    choice_a = serializers.CharField()
    choice_b = serializers.CharField()
    choice_c = serializers.CharField()
    choice_d = serializers.CharField()
    correct_answer = serializers.CharField()
    explanation = serializers.CharField(required=False, allow_null=True)
    points = serializers.IntegerField()


class ReadingPassageIELTSSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    passage_text = serializers.CharField()
    passage_image = serializers.URLField(required=False, allow_null=True)
    source = serializers.CharField(required=False, allow_null=True)
    questions = ReadingQuestionIELTSSerializer(many=True)
    difficulty = serializers.CharField(required=False)  


# ============================================
# Listening Serializers ← جديد
# ============================================

class ListeningQuestionIELTSSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    difficulty = serializers.CharField(required=False)
    question_text = serializers.CharField()
    choice_a = serializers.CharField()
    choice_b = serializers.CharField()
    choice_c = serializers.CharField()
    choice_d = serializers.CharField()
    correct_answer = serializers.CharField()
    explanation = serializers.CharField(required=False, allow_null=True)
    points = serializers.IntegerField()


class ListeningAudioIELTSSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    audio_file = serializers.URLField(required=False, allow_null=True)
    transcript = serializers.CharField(required=False, allow_null=True)
    duration = serializers.IntegerField(required=False, allow_null=True)
    questions = ListeningQuestionIELTSSerializer(many=True)
    difficulty = serializers.CharField(required=False)  


# ============================================
# Writing Serializer
# ============================================

class WritingQuestionIELTSSerializer(serializers.Serializer):
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

class SpeakingQuestionIELTSSerializer(serializers.Serializer):
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


class SpeakingVideoIELTSSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    video_file = serializers.URLField(required=False, allow_null=True)
    description = serializers.CharField(required=False, allow_null=True)
    duration = serializers.IntegerField(required=False, allow_null=True)
    thumbnail = serializers.URLField(required=False, allow_null=True)
    questions = SpeakingQuestionIELTSSerializer(many=True)
    difficulty = serializers.CharField(required=False)