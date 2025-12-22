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
    """Serializer لأسئلة MCQ الفردية"""
    
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
    """Serializer لمجموعة أسئلة MCQ مع الأسئلة"""
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


class MCQQuestionSetCreateSerializer(serializers.ModelSerializer):
    """Serializer لإنشاء مجموعة MCQ بدون الأسئلة"""
    
    class Meta:
        model = MCQQuestionSet
        fields = [
            'id', 'placement_test', 'title', 'description',
            'order', 'is_active'
        ]
        read_only_fields = ['id']


# ============================================
# Reading Serializers
# ============================================

class ReadingQuestionSerializer(serializers.ModelSerializer):
    """Serializer لأسئلة القراءة"""
    
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
    """Serializer لقطعة القراءة مع الأسئلة"""
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


class ReadingPassageCreateSerializer(serializers.ModelSerializer):
    """Serializer لإنشاء قطعة قراءة بدون الأسئلة"""
    
    class Meta:
        model = ReadingPassage
        fields = [
            'id', 'placement_test', 'title', 'passage_text',
            'passage_image', 'source', 'order', 'is_active'
        ]
        read_only_fields = ['id']


# ============================================
# Listening Serializers
# ============================================

class ListeningQuestionSerializer(serializers.ModelSerializer):
    """Serializer لأسئلة الاستماع"""
    
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
    """Serializer للتسجيل الصوتي مع الأسئلة"""
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


class ListeningAudioCreateSerializer(serializers.ModelSerializer):
    """Serializer لإنشاء تسجيل صوتي بدون الأسئلة"""
    
    class Meta:
        model = ListeningAudio
        fields = [
            'id', 'placement_test', 'title', 'audio_file',
            'transcript', 'duration', 'order', 'is_active'
        ]
        read_only_fields = ['id']


# ============================================
# Speaking Serializers
# ============================================

class SpeakingQuestionSerializer(serializers.ModelSerializer):
    """Serializer لأسئلة التحدث"""
    
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
    """Serializer لفيديو التحدث مع الأسئلة"""
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


class SpeakingVideoCreateSerializer(serializers.ModelSerializer):
    """Serializer لإنشاء فيديو تحدث بدون الأسئلة"""
    
    class Meta:
        model = SpeakingVideo
        fields = [
            'id', 'placement_test', 'title', 'video_file',
            'description', 'duration', 'thumbnail', 'order',
            'is_active'
        ]
        read_only_fields = ['id']


# ============================================
# Writing Serializers
# ============================================

class WritingQuestionSerializer(serializers.ModelSerializer):
    """Serializer لأسئلة الكتابة"""
    
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

class PlacementTestListSerializer(serializers.ModelSerializer):
    """Serializer لقائمة الامتحانات (مختصر)"""
    total_points = serializers.SerializerMethodField()
    questions_count = serializers.SerializerMethodField()
    
    class Meta:
        model = PlacementTest
        fields = [
            'id', 'title', 'description', 'duration_minutes',
            'a1_min_score', 'a2_min_score', 'b1_min_score', 'b2_min_score',  # أضف دول
            'is_active', 'total_points', 'questions_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_total_points(self, obj):
        return obj.get_total_points()
    
    def get_questions_count(self, obj):
        return obj.get_questions_count()

class PlacementTestDetailSerializer(serializers.ModelSerializer):
    """Serializer لتفاصيل الامتحان الكاملة"""
    mcq_sets = MCQQuestionSetSerializer(many=True, read_only=True)
    reading_passages = ReadingPassageSerializer(many=True, read_only=True)
    listening_audios = ListeningAudioSerializer(many=True, read_only=True)
    speaking_videos = SpeakingVideoSerializer(many=True, read_only=True)
    writing_questions = WritingQuestionSerializer(many=True, read_only=True)
    
    total_points = serializers.SerializerMethodField()
    questions_count = serializers.SerializerMethodField()
    
    class Meta:
        model = PlacementTest
        fields = [
            'id', 'title', 'description', 'duration_minutes',
            'a1_min_score', 'a2_min_score', 'b1_min_score', 'b2_min_score',
            'is_active', 'mcq_sets', 'reading_passages',
            'listening_audios', 'speaking_videos', 'writing_questions',
            'total_points', 'questions_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_total_points(self, obj):
        return obj.get_total_points()
    
    def get_questions_count(self, obj):
        return obj.get_questions_count()


class PlacementTestCreateSerializer(serializers.ModelSerializer):
    """Serializer لإنشاء امتحان جديد"""
    
    class Meta:
        model = PlacementTest
        fields = [
            'id', 'title', 'description', 'duration_minutes',
            'a1_min_score', 'a2_min_score', 'b1_min_score', 'b2_min_score',
            'is_active'
        ]
        read_only_fields = ['id']
    
    def validate(self, data):
        """التحقق من صحة درجات المستويات"""
        scores = [
            data.get('a1_min_score', 0),
            data.get('a2_min_score'),
            data.get('b1_min_score'),
            data.get('b2_min_score')
        ]
        
        # التأكد أن الدرجات متصاعدة
        for i in range(len(scores) - 1):
            if scores[i] >= scores[i + 1]:
                raise serializers.ValidationError(
                    "يجب أن تكون درجات المستويات متصاعدة (A1 < A2 < B1 < B2)"
                )
        
        return data