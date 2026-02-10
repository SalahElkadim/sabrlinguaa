from rest_framework import serializers
from sabr_questions.models import (
    VocabularyQuestion, VocabularyQuestionSet,
    GrammarQuestion, GrammarQuestionSet,
    ReadingPassage, ReadingQuestion,
    ListeningAudio, ListeningQuestion,
    SpeakingVideo, SpeakingQuestion,
    WritingQuestion
)


# ============================================
# 1. VOCABULARY SERIALIZERS
# ============================================

class VocabularyQuestionSetSerializer(serializers.ModelSerializer):
    """مجموعة أسئلة المفردات"""
    questions_count = serializers.SerializerMethodField()
    
    class Meta:
        model = VocabularyQuestionSet
        fields = [
            'id', 'title', 'description', 'usage_type',
            'order', 'is_active', 'questions_count',
            'created_at', 'updated_at'
        ]
    
    def get_questions_count(self, obj):
        return obj.get_questions_count()


class VocabularyQuestionSerializer(serializers.ModelSerializer):
    """سؤال مفردات - للعرض"""
    question_set_title = serializers.CharField(source='question_set.title', read_only=True)
    
    class Meta:
        model = VocabularyQuestion
        fields = [
            'id', 'question_set', 'question_set_title',
            'question_text', 'question_image',
            'choice_a', 'choice_b', 'choice_c', 'choice_d',
            'correct_answer', 'explanation', 'points',
            'usage_type', 'order', 'is_active',
            'created_at', 'updated_at'
        ]


class CreateVocabularyQuestionSerializer(serializers.ModelSerializer):
    """إنشاء سؤال مفردات"""
    question_set_id = serializers.IntegerField(required=False, write_only=True)
    question_set_title = serializers.CharField(required=False, write_only=True)
    question_set_description = serializers.CharField(required=False, write_only=True, allow_blank=True)
    
    class Meta:
        model = VocabularyQuestion
        fields = [
            'question_set_id', 'question_set_title', 'question_set_description',
            'question_text', 'question_image',
            'choice_a', 'choice_b', 'choice_c', 'choice_d',
            'correct_answer', 'explanation', 'points',
            'order', 'is_active'
        ]


# ============================================
# 2. GRAMMAR SERIALIZERS
# ============================================

class GrammarQuestionSetSerializer(serializers.ModelSerializer):
    """مجموعة أسئلة القواعد"""
    questions_count = serializers.SerializerMethodField()
    
    class Meta:
        model = GrammarQuestionSet
        fields = [
            'id', 'title', 'description', 'usage_type',
            'order', 'is_active', 'questions_count',
            'created_at', 'updated_at'
        ]
    
    def get_questions_count(self, obj):
        return obj.get_questions_count()


class GrammarQuestionSerializer(serializers.ModelSerializer):
    """سؤال قواعد - للعرض"""
    question_set_title = serializers.CharField(source='question_set.title', read_only=True)
    
    class Meta:
        model = GrammarQuestion
        fields = [
            'id', 'question_set', 'question_set_title',
            'question_text', 'question_image',
            'choice_a', 'choice_b', 'choice_c', 'choice_d',
            'correct_answer', 'explanation', 'points',
            'usage_type', 'order', 'is_active',
            'created_at', 'updated_at'
        ]


class CreateGrammarQuestionSerializer(serializers.ModelSerializer):
    """إنشاء سؤال قواعد"""
    question_set_id = serializers.IntegerField(required=False, write_only=True)
    question_set_title = serializers.CharField(required=False, write_only=True)
    question_set_description = serializers.CharField(required=False, write_only=True, allow_blank=True)
    
    class Meta:
        model = GrammarQuestion
        fields = [
            'question_set_id', 'question_set_title', 'question_set_description',
            'question_text', 'question_image',
            'choice_a', 'choice_b', 'choice_c', 'choice_d',
            'correct_answer', 'explanation', 'points',
            'order', 'is_active'
        ]


# ============================================
# 3. READING SERIALIZERS
# ============================================

class ReadingQuestionSerializer(serializers.ModelSerializer):
    """سؤال قراءة - للعرض"""
    class Meta:
        model = ReadingQuestion
        fields = [
            'id', 'passage',
            'question_text', 'question_image',
            'choice_a', 'choice_b', 'choice_c', 'choice_d',
            'correct_answer', 'explanation', 'points',
            'order', 'is_active',
            'created_at', 'updated_at'
        ]


class ReadingPassageSerializer(serializers.ModelSerializer):
    """قطعة قراءة - للعرض"""
    questions = ReadingQuestionSerializer(many=True, read_only=True)
    questions_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ReadingPassage
        fields = [
            'id', 'title', 'passage_text', 'passage_image', 'source',
            'usage_type', 'order', 'is_active',
            'questions', 'questions_count',
            'created_at', 'updated_at'
        ]
    
    def get_questions_count(self, obj):
        return obj.get_questions_count()


class CreateReadingPassageSerializer(serializers.ModelSerializer):
    """إنشاء قطعة قراءة"""
    class Meta:
        model = ReadingPassage
        fields = [
            'title', 'passage_text', 'passage_image', 'source',
            'order', 'is_active'
        ]


class CreateReadingQuestionSerializer(serializers.ModelSerializer):
    """إنشاء سؤال قراءة"""
    class Meta:
        model = ReadingQuestion
        fields = [
            'question_text', 'question_image',
            'choice_a', 'choice_b', 'choice_c', 'choice_d',
            'correct_answer', 'explanation', 'points',
            'order', 'is_active'
        ]


# ============================================
# 4. LISTENING SERIALIZERS
# ============================================

class ListeningQuestionSerializer(serializers.ModelSerializer):
    """سؤال استماع - للعرض"""
    class Meta:
        model = ListeningQuestion
        fields = [
            'id', 'audio',
            'question_text', 'question_image',
            'choice_a', 'choice_b', 'choice_c', 'choice_d',
            'correct_answer', 'explanation', 'points',
            'order', 'is_active',
            'created_at', 'updated_at'
        ]


class ListeningAudioSerializer(serializers.ModelSerializer):
    """تسجيل صوتي - للعرض"""
    questions = ListeningQuestionSerializer(many=True, read_only=True)
    questions_count = serializers.SerializerMethodField()
    audio_file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = ListeningAudio
        fields = [
            'id', 'title', 'audio_file', 'audio_file_url',
            'transcript', 'duration',
            'usage_type', 'order', 'is_active',
            'questions', 'questions_count',
            'created_at', 'updated_at'
        ]
    
    def get_questions_count(self, obj):
        return obj.get_questions_count()
    
    def get_audio_file_url(self, obj):
        if obj.audio_file:
            return obj.audio_file.url
        return None


class CreateListeningAudioSerializer(serializers.ModelSerializer):
    """إنشاء تسجيل صوتي"""
    class Meta:
        model = ListeningAudio
        fields = [
            'title', 'audio_file', 'transcript', 'duration',
            'order', 'is_active'
        ]


class CreateListeningQuestionSerializer(serializers.ModelSerializer):
    """إنشاء سؤال استماع"""
    class Meta:
        model = ListeningQuestion
        fields = [
            'question_text', 'question_image',
            'choice_a', 'choice_b', 'choice_c', 'choice_d',
            'correct_answer', 'explanation', 'points',
            'order', 'is_active'
        ]


# ============================================
# 5. SPEAKING SERIALIZERS
# ============================================

class SpeakingQuestionSerializer(serializers.ModelSerializer):
    """سؤال تحدث - للعرض"""
    class Meta:
        model = SpeakingQuestion
        fields = [
            'id', 'video',
            'question_text', 'question_image',
            'choice_a', 'choice_b', 'choice_c', 'choice_d',
            'correct_answer', 'explanation', 'points',
            'order', 'is_active',
            'created_at', 'updated_at'
        ]


class SpeakingVideoSerializer(serializers.ModelSerializer):
    """فيديو تحدث - للعرض"""
    questions = SpeakingQuestionSerializer(many=True, read_only=True)
    questions_count = serializers.SerializerMethodField()
    video_file_url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    
    class Meta:
        model = SpeakingVideo
        fields = [
            'id', 'title', 'video_file', 'video_file_url',
            'description', 'duration', 'thumbnail', 'thumbnail_url',
            'usage_type', 'order', 'is_active',
            'questions', 'questions_count',
            'created_at', 'updated_at'
        ]
    
    def get_questions_count(self, obj):
        return obj.get_questions_count()
    
    def get_video_file_url(self, obj):
        if obj.video_file:
            return obj.video_file.url
        return None
    
    def get_thumbnail_url(self, obj):
        if obj.thumbnail:
            return obj.thumbnail.url
        return None


class CreateSpeakingVideoSerializer(serializers.ModelSerializer):
    """إنشاء فيديو تحدث"""
    class Meta:
        model = SpeakingVideo
        fields = [
            'title', 'video_file', 'description', 'duration', 'thumbnail',
            'order', 'is_active'
        ]


class CreateSpeakingQuestionSerializer(serializers.ModelSerializer):
    """إنشاء سؤال تحدث"""
    class Meta:
        model = SpeakingQuestion
        fields = [
            'question_text', 'question_image',
            'choice_a', 'choice_b', 'choice_c', 'choice_d',
            'correct_answer', 'explanation', 'points',
            'order', 'is_active'
        ]


# ============================================
# 6. WRITING SERIALIZERS
# ============================================

class WritingQuestionSerializer(serializers.ModelSerializer):
    """سؤال كتابة - للعرض"""
    class Meta:
        model = WritingQuestion
        fields = [
            'id', 'title', 'question_text', 'question_image',
            'min_words', 'max_words', 'sample_answer', 'rubric',
            'points', 'pass_threshold',
            'usage_type', 'order', 'is_active',
            'created_at', 'updated_at'
        ]


class CreateWritingQuestionSerializer(serializers.ModelSerializer):
    """إنشاء سؤال كتابة"""
    class Meta:
        model = WritingQuestion
        fields = [
            'title', 'question_text', 'question_image',
            'min_words', 'max_words', 'sample_answer', 'rubric',
            'pass_threshold', 'order', 'is_active'
        ]