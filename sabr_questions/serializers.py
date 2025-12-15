from rest_framework import serializers
from .models import (
    PlacementTest, MCQQuestionSet, MCQQuestion,
    ReadingPassage, ReadingQuestion,
    ListeningAudio, ListeningQuestion,
    SpeakingVideo, SpeakingQuestion,
    WritingQuestion
)


# ============================================
# MCQ Serializers
# ============================================

class MCQQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MCQQuestion
        fields = [
            'id', 'question_set', 'question_text', 'question_image',
            'choice_a', 'choice_b', 'choice_c', 'choice_d',
            'correct_answer', 'explanation', 'points', 'order',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class MCQQuestionSetSerializer(serializers.ModelSerializer):
    questions = MCQQuestionSerializer(many=True, read_only=True)
    questions_count = serializers.SerializerMethodField()
    total_points = serializers.SerializerMethodField()

    class Meta:
        model = MCQQuestionSet
        fields = [
            'id', 'placement_test', 'title', 'description',
            'order', 'is_active', 'questions', 'questions_count',
            'total_points', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_questions_count(self, obj):
        return obj.questions.count()

    def get_total_points(self, obj):
        return sum(q.points for q in obj.questions.all())


# ============================================
# Reading Serializers
# ============================================

class ReadingQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReadingQuestion
        fields = [
            'id', 'passage', 'question_text', 'question_image',
            'choice_a', 'choice_b', 'choice_c', 'choice_d',
            'correct_answer', 'explanation', 'points', 'order',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ReadingPassageSerializer(serializers.ModelSerializer):
    questions = ReadingQuestionSerializer(many=True, read_only=True)
    questions_count = serializers.SerializerMethodField()
    total_points = serializers.SerializerMethodField()

    class Meta:
        model = ReadingPassage
        fields = [
            'id', 'placement_test', 'title', 'passage_text',
            'passage_image', 'source', 'order', 'is_active',
            'questions', 'questions_count', 'total_points',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_questions_count(self, obj):
        return obj.questions.count()

    def get_total_points(self, obj):
        return sum(q.points for q in obj.questions.all())


# ============================================
# Listening Serializers
# ============================================

class ListeningQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ListeningQuestion
        fields = [
            'id', 'audio', 'question_text', 'question_image',
            'choice_a', 'choice_b', 'choice_c', 'choice_d',
            'correct_answer', 'explanation', 'points', 'order',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ListeningAudioSerializer(serializers.ModelSerializer):
    questions = ListeningQuestionSerializer(many=True, read_only=True)
    questions_count = serializers.SerializerMethodField()
    total_points = serializers.SerializerMethodField()

    class Meta:
        model = ListeningAudio
        fields = [
            'id', 'placement_test', 'title', 'audio_file',
            'transcript', 'duration', 'order', 'is_active',
            'questions', 'questions_count', 'total_points',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_questions_count(self, obj):
        return obj.questions.count()

    def get_total_points(self, obj):
        return sum(q.points for q in obj.questions.all())


# ============================================
# Speaking Serializers
# ============================================

class SpeakingQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpeakingQuestion
        fields = [
            'id', 'video', 'question_text', 'question_image',
            'choice_a', 'choice_b', 'choice_c', 'choice_d',
            'correct_answer', 'explanation', 'points', 'order',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class SpeakingVideoSerializer(serializers.ModelSerializer):
    questions = SpeakingQuestionSerializer(many=True, read_only=True)
    questions_count = serializers.SerializerMethodField()
    total_points = serializers.SerializerMethodField()

    class Meta:
        model = SpeakingVideo
        fields = [
            'id', 'placement_test', 'title', 'video_file',
            'description', 'duration', 'thumbnail', 'order',
            'is_active', 'questions', 'questions_count',
            'total_points', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_questions_count(self, obj):
        return obj.questions.count()

    def get_total_points(self, obj):
        return sum(q.points for q in obj.questions.all())


# ============================================
# Writing Serializer
# ============================================

class WritingQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WritingQuestion
        fields = [
            'id', 'placement_test', 'title', 'question_text',
            'question_image', 'min_words', 'max_words',
            'sample_answer', 'rubric', 'points', 'order',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# ============================================
# Placement Test Serializers
# ============================================

class PlacementTestDetailSerializer(serializers.ModelSerializer):
    mcq_sets = MCQQuestionSetSerializer(many=True, read_only=True)
    reading_passages = ReadingPassageSerializer(many=True, read_only=True)
    listening_audios = ListeningAudioSerializer(many=True, read_only=True)
    speaking_videos = SpeakingVideoSerializer(many=True, read_only=True)
    writing_questions = WritingQuestionSerializer(many=True, read_only=True)
    total_points = serializers.IntegerField(source='get_total_points', read_only=True)
    questions_count = serializers.IntegerField(source='get_questions_count', read_only=True)

    class Meta:
        model = PlacementTest
        fields = [
            'id', 'title', 'description', 'duration_minutes',
            'a1_min_score', 'a2_min_score', 'b1_min_score', 'b2_min_score',
            'is_active', 'created_at', 'updated_at',
            'mcq_sets', 'reading_passages', 'listening_audios',
            'speaking_videos', 'writing_questions',
            'total_points', 'questions_count'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class PlacementTestListSerializer(serializers.ModelSerializer):
    total_points = serializers.IntegerField(source='get_total_points', read_only=True)
    questions_count = serializers.IntegerField(source='get_questions_count', read_only=True)

    class Meta:
        model = PlacementTest
        fields = [
            'id', 'title', 'description', 'duration_minutes',
            'is_active', 'total_points', 'questions_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']