from rest_framework import serializers
from placement_test.models import PlacementQuestionBank , StudentPlacementTestAnswer, StudentPlacementTestAttempt
from sabr_questions.models import (
    VocabularyQuestionSet,
    VocabularyQuestion,
    GrammarQuestionSet,
    GrammarQuestion,
    ReadingPassage,
    ReadingQuestion,
    ListeningAudio,
    ListeningQuestion,
    SpeakingVideo,
    SpeakingQuestion,
    WritingQuestion
)


# ============================================
# Question Bank Serializers
# ============================================

class PlacementQuestionBankSerializer(serializers.ModelSerializer):
    """
    Serializer بسيط لعرض قائمة البنوك
    """
    total_questions = serializers.IntegerField(source='get_total_questions', read_only=True)
    is_ready = serializers.BooleanField(source='is_ready_for_exam', read_only=True)
    
    class Meta:
        model = PlacementQuestionBank 
        fields = [
            'id',
            'title',
            'description',
            'total_questions',
            'is_ready',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class PlacementQuestionBankCreateSerializer(serializers.ModelSerializer):
    """
    Serializer لإنشاء بنك أسئلة جديد
    """
    class Meta:
        model = PlacementQuestionBank 
        fields = [
            'title',
            'description'
        ]
    
    def validate_title(self, value):
        """
        التحقق من عدم تكرار العنوان
        """
        if PlacementQuestionBank .objects.filter(title=value).exists():
            raise serializers.ValidationError(
                "يوجد بنك أسئلة بهذا العنوان بالفعل"
            )
        return value


class PlacementQuestionBankDetailSerializer(serializers.ModelSerializer):
    """
    Serializer مفصل لعرض تفاصيل البنك
    """
    vocabulary_count = serializers.IntegerField(source='get_vocabulary_count', read_only=True)
    grammar_count = serializers.IntegerField(source='get_grammar_count', read_only=True)
    reading_count = serializers.IntegerField(source='get_reading_count', read_only=True)
    listening_count = serializers.IntegerField(source='get_listening_count', read_only=True)
    speaking_count = serializers.IntegerField(source='get_speaking_count', read_only=True)
    writing_count = serializers.IntegerField(source='get_writing_count', read_only=True)
    total_questions = serializers.IntegerField(source='get_total_questions', read_only=True)
    is_ready = serializers.BooleanField(source='is_ready_for_exam', read_only=True)
    
    class Meta:
        model = PlacementQuestionBank 
        fields = [
            'id',
            'title',
            'description',
            'vocabulary_count',
            'grammar_count',
            'reading_count',
            'listening_count',
            'speaking_count',
            'writing_count',
            'total_questions',
            'is_ready',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class PlacementQuestionBankUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer لتعديل بنك موجود
    """
    class Meta:
        model = PlacementQuestionBank 
        fields = [
            'title',
            'description'
        ]
    
    def validate_title(self, value):
        """
        التحقق من عدم تكرار العنوان (مع استثناء البنك الحالي)
        """
        instance = self.instance
        if PlacementQuestionBank.objects.filter(title=value).exclude(id=instance.id).exists():
            raise serializers.ValidationError(
                "يوجد بنك أسئلة آخر بهذا العنوان"
            )
        return value


# ============================================
# Vocabulary Question Serializers
# ============================================

class VocabularyQuestionSetSerializer(serializers.ModelSerializer):
    """
    Serializer لمجموعات أسئلة المفردات
    """
    questions_count = serializers.IntegerField(source='get_questions_count', read_only=True)
    
    class Meta:
        model = VocabularyQuestionSet
        fields = [
            'id',
            'title',
            'description',
            'usage_type',
            'order',
            'is_active',
            'questions_count',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CreateVocabularyQuestionSerializer(serializers.ModelSerializer):
    """
    Serializer لإنشاء سؤال مفردات جديد
    """
    # إنشاء Set جديد أو اختيار موجود
    question_set_id = serializers.IntegerField(required=False, allow_null=True)
    question_set_title = serializers.CharField(required=False, allow_blank=True)
    question_set_description = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = VocabularyQuestion
        fields = [
            'question_set_id',
            'question_set_title',
            'question_set_description',
            'question_text',
            'question_image',
            'choice_a',
            'choice_b',
            'choice_c',
            'choice_d',
            'correct_answer',
            'explanation',
            'points',
            'order',
            'is_active',
        ]
    
    def validate(self, data):
        """
        التحقق من وجود question_set_id أو question_set_title
        """
        question_set_id = data.get('question_set_id')
        question_set_title = data.get('question_set_title')
        
        if not question_set_id and not question_set_title:
            raise serializers.ValidationError(
                "يجب تحديد question_set_id أو question_set_title"
            )
        
        return data


class VocabularyQuestionSerializer(serializers.ModelSerializer):
    """
    Serializer لعرض سؤال المفردات
    """
    question_set_title = serializers.CharField(source='question_set.title', read_only=True)
    usage_type_display = serializers.CharField(source='get_usage_type_display', read_only=True)
    
    class Meta:
        model = VocabularyQuestion
        fields = [
            'id',
            'question_set',
            'question_set_title',
            'question_text',
            'question_image',
            'choice_a',
            'choice_b',
            'choice_c',
            'choice_d',
            'correct_answer',
            'explanation',
            'points',
            'usage_type',
            'usage_type_display',
            'placement_test',
            'order',
            'is_active',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# ============================================
# Grammar Question Serializers
# ============================================

class GrammarQuestionSetSerializer(serializers.ModelSerializer):
    """
    Serializer لمجموعات أسئلة القواعد
    """
    questions_count = serializers.IntegerField(source='get_questions_count', read_only=True)
    
    class Meta:
        model = GrammarQuestionSet
        fields = [
            'id',
            'title',
            'description',
            'usage_type',
            'order',
            'is_active',
            'questions_count',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CreateGrammarQuestionSerializer(serializers.ModelSerializer):
    """
    Serializer لإنشاء سؤال قواعد جديد
    """
    question_set_id = serializers.IntegerField(required=False, allow_null=True)
    question_set_title = serializers.CharField(required=False, allow_blank=True)
    question_set_description = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = GrammarQuestion
        fields = [
            'question_set_id',
            'question_set_title',
            'question_set_description',
            'question_text',
            'question_image',
            'choice_a',
            'choice_b',
            'choice_c',
            'choice_d',
            'correct_answer',
            'explanation',
            'points',
            'order',
            'is_active',
        ]
    
    def validate(self, data):
        question_set_id = data.get('question_set_id')
        question_set_title = data.get('question_set_title')
        
        if not question_set_id and not question_set_title:
            raise serializers.ValidationError(
                "يجب تحديد question_set_id أو question_set_title"
            )
        
        return data


class GrammarQuestionSerializer(serializers.ModelSerializer):
    """
    Serializer لعرض سؤال القواعد
    """
    question_set_title = serializers.CharField(source='question_set.title', read_only=True)
    usage_type_display = serializers.CharField(source='get_usage_type_display', read_only=True)
    
    class Meta:
        model = GrammarQuestion
        fields = [
            'id',
            'question_set',
            'question_set_title',
            'question_text',
            'question_image',
            'choice_a',
            'choice_b',
            'choice_c',
            'choice_d',
            'correct_answer',
            'explanation',
            'points',
            'usage_type',
            'usage_type_display',
            'placement_test',
            'order',
            'is_active',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# ============================================
# Reading Question Serializers
# ============================================

class ReadingQuestionSerializer(serializers.ModelSerializer):
    """
    Serializer لعرض سؤال القراءة
    """
    passage_title = serializers.CharField(source='passage.title', read_only=True)
    
    class Meta:
        model = ReadingQuestion
        fields = [
            'id',
            'passage',
            'passage_title',
            'question_text',
            'question_image',
            'choice_a',
            'choice_b',
            'choice_c',
            'choice_d',
            'correct_answer',
            'explanation',
            'points',
            'order',
            'is_active',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CreateReadingQuestionSerializer(serializers.ModelSerializer):
    """
    Serializer لإنشاء سؤال قراءة جديد
    """
    class Meta:
        model = ReadingQuestion
        fields = [
            'question_text',
            'question_image',
            'choice_a',
            'choice_b',
            'choice_c',
            'choice_d',
            'correct_answer',
            'explanation',
            'points',
            'order',
            'is_active',
        ]


class ReadingPassageSerializer(serializers.ModelSerializer):
    """
    Serializer لقطعة القراءة مع الأسئلة
    """
    questions_count = serializers.IntegerField(source='get_questions_count', read_only=True)
    usage_type_display = serializers.CharField(source='get_usage_type_display', read_only=True)
    questions = ReadingQuestionSerializer(many=True, read_only=True)
    
    class Meta:
        model = ReadingPassage
        fields = [
            'id',
            'title',
            'passage_text',
            'passage_image',
            'source',
            'usage_type',
            'usage_type_display',
            'placement_test',
            'order',
            'is_active',
            'questions_count',
            'questions',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# ============================================
# Listening Question Serializers
# ============================================

class ListeningQuestionSerializer(serializers.ModelSerializer):
    """
    Serializer لعرض سؤال الاستماع
    """
    audio_title = serializers.CharField(source='audio.title', read_only=True)
    
    class Meta:
        model = ListeningQuestion
        fields = [
            'id',
            'audio',
            'audio_title',
            'question_text',
            'question_image',
            'choice_a',
            'choice_b',
            'choice_c',
            'choice_d',
            'correct_answer',
            'explanation',
            'points',
            'order',
            'is_active',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CreateListeningQuestionSerializer(serializers.ModelSerializer):
    """
    Serializer لإنشاء سؤال استماع جديد
    """
    class Meta:
        model = ListeningQuestion
        fields = [
            'question_text',
            'question_image',
            'choice_a',
            'choice_b',
            'choice_c',
            'choice_d',
            'correct_answer',
            'explanation',
            'points',
            'order',
            'is_active',
        ]


class ListeningAudioSerializer(serializers.ModelSerializer):
    """
    Serializer للتسجيل الصوتي مع الأسئلة
    """
    questions_count = serializers.IntegerField(source='get_questions_count', read_only=True)
    usage_type_display = serializers.CharField(source='get_usage_type_display', read_only=True)
    questions = ListeningQuestionSerializer(many=True, read_only=True)
    
    class Meta:
        model = ListeningAudio
        fields = [
            'id',
            'title',
            'audio_file',
            'transcript',
            'duration',
            'usage_type',
            'usage_type_display',
            'placement_test',
            'order',
            'is_active',
            'questions_count',
            'questions',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# ============================================
# Speaking Question Serializers
# ============================================

class SpeakingQuestionSerializer(serializers.ModelSerializer):
    """
    Serializer لعرض سؤال التحدث
    """
    video_title = serializers.CharField(source='video.title', read_only=True)
    
    class Meta:
        model = SpeakingQuestion
        fields = [
            'id',
            'video',
            'video_title',
            'question_text',
            'question_image',
            'choice_a',
            'choice_b',
            'choice_c',
            'choice_d',
            'correct_answer',
            'explanation',
            'points',
            'order',
            'is_active',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CreateSpeakingQuestionSerializer(serializers.ModelSerializer):
    """
    Serializer لإنشاء سؤال تحدث جديد
    """
    class Meta:
        model = SpeakingQuestion
        fields = [
            'question_text',
            'question_image',
            'choice_a',
            'choice_b',
            'choice_c',
            'choice_d',
            'correct_answer',
            'explanation',
            'points',
            'order',
            'is_active',
        ]


class SpeakingVideoSerializer(serializers.ModelSerializer):
    """
    Serializer للفيديو التعليمي مع الأسئلة
    """
    questions_count = serializers.IntegerField(source='get_questions_count', read_only=True)
    usage_type_display = serializers.CharField(source='get_usage_type_display', read_only=True)
    questions = SpeakingQuestionSerializer(many=True, read_only=True)
    
    class Meta:
        model = SpeakingVideo
        fields = [
            'id',
            'title',
            'video_file',
            'description',
            'duration',
            'thumbnail',
            'usage_type',
            'usage_type_display',
            'placement_test',
            'order',
            'is_active',
            'questions_count',
            'questions',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# ============================================
# Writing Question Serializers
# ============================================

class CreateWritingQuestionSerializer(serializers.ModelSerializer):
    """
    Serializer لإنشاء سؤال كتابة جديد
    """
    class Meta:
        model = WritingQuestion
        fields = [
            'title',
            'question_text',
            'question_image',
            'min_words',
            'max_words',
            'sample_answer',
            'rubric',
            'points',
            'order',
            'is_active',
        ]


class WritingQuestionSerializer(serializers.ModelSerializer):
    """
    Serializer لعرض سؤال الكتابة
    """
    usage_type_display = serializers.CharField(source='get_usage_type_display', read_only=True)
    
    class Meta:
        model = WritingQuestion
        fields = [
            'id',
            'title',
            'question_text',
            'question_image',
            'min_words',
            'max_words',
            'sample_answer',
            'rubric',
            'points',
            'usage_type',
            'usage_type_display',
            'placement_test',
            'order',
            'is_active',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# ============================================
# Student Answer Serializers
# ============================================

class MCQAnswerInputSerializer(serializers.Serializer):
    """
    Serializer لإجابة سؤال MCQ
    """
    question_id = serializers.IntegerField(min_value=1)
    selected_choice = serializers.ChoiceField(choices=['A', 'B', 'C', 'D'])


class WritingAnswerInputSerializer(serializers.Serializer):
    """
    Serializer لإجابة سؤال Writing
    """
    question_id = serializers.IntegerField(min_value=1)
    text_answer = serializers.CharField(
        min_length=10,
        max_length=5000,
        error_messages={
            'min_length': 'الإجابة قصيرة جداً (الحد الأدنى 10 حروف)',
            'max_length': 'الإجابة طويلة جداً (الحد الأقصى 5000 حرف)'
        }
    )


class SubmitExamSerializer(serializers.Serializer):
    """
    Serializer لتقديم إجابات الامتحان
    """
    answers = serializers.DictField(
        child=serializers.ListField(),
        required=True,
        error_messages={
            'required': 'يجب إرسال الإجابات'
        }
    )
    
    def validate_answers(self, value):
        """
        التحقق من صحة بنية الإجابات
        """
        required_keys = ['vocabulary', 'grammar', 'reading', 'listening', 'speaking', 'writing']
        
        for key in required_keys:
            if key not in value:
                raise serializers.ValidationError(
                    f'يجب تضمين إجابات {key}'
                )
            
            if not isinstance(value[key], list):
                raise serializers.ValidationError(
                    f'إجابات {key} يجب أن تكون قائمة (list)'
                )
        
        # التحقق من MCQ answers
        mcq_types = ['vocabulary', 'grammar', 'reading', 'listening', 'speaking']
        for q_type in mcq_types:
            for answer in value[q_type]:
                serializer = MCQAnswerInputSerializer(data=answer)
                if not serializer.is_valid():
                    raise serializers.ValidationError(
                        f'خطأ في إجابات {q_type}: {serializer.errors}'
                    )
        
        # التحقق من Writing answers
        for answer in value['writing']:
            serializer = WritingAnswerInputSerializer(data=answer)
            if not serializer.is_valid():
                raise serializers.ValidationError(
                    f'خطأ في إجابات الكتابة: {serializer.errors}'
                )
        
        return value


class StudentAnswerDetailSerializer(serializers.ModelSerializer):
    """
    Serializer لعرض تفاصيل إجابة الطالب
    """
    question_type = serializers.CharField(source='get_question_type_display', read_only=True)
    
    class Meta:
        model = StudentPlacementTestAnswer
        fields = [
            'id',
            'question_type',
            'object_id',
            'selected_choice',
            'text_answer',
            'is_correct',
            'points_earned',
            'ai_feedback',
            'strengths',
            'improvements',
            'answered_at',
            'time_spent_seconds'
        ]
        read_only_fields = fields


class ExamResultSerializer(serializers.ModelSerializer):
    """
    Serializer لعرض نتيجة الامتحان
    """
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    student_username = serializers.CharField(source='student.username', read_only=True)
    question_bank_title = serializers.CharField(source='question_bank.title', read_only=True)
    placement_test_title = serializers.CharField(source='placement_test.title', read_only=True)
    duration_minutes = serializers.SerializerMethodField()
    total_questions = serializers.IntegerField(source='placement_test.total_questions', read_only=True)
    percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = StudentPlacementTestAttempt
        fields = [
            'id',
            'student_name',
            'student_username',
            'placement_test_title',
            'question_bank_title',
            'started_at',
            'completed_at',
            'duration_minutes',
            'score',
            'total_questions',
            'percentage',
            'level_achieved',
            'status'
        ]
        read_only_fields = fields
    
    def get_duration_minutes(self, obj):
        """حساب المدة بالدقائق"""
        duration = obj.get_duration()
        return round(duration, 2) if duration else None
    
    def get_percentage(self, obj):
        """حساب النسبة المئوية"""
        total = obj.placement_test.total_questions
        if total > 0:
            return round((obj.score / total) * 100, 2)
        return 0


class StudentAttemptListSerializer(serializers.ModelSerializer):
    """
    Serializer لعرض قائمة محاولات الطالب
    """
    question_bank_title = serializers.CharField(source='question_bank.title', read_only=True)
    placement_test_title = serializers.CharField(source='placement_test.title', read_only=True)
    duration_minutes = serializers.SerializerMethodField()
    percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = StudentPlacementTestAttempt
        fields = [
            'id',
            'placement_test_title',
            'question_bank_title',
            'started_at',
            'completed_at',
            'duration_minutes',
            'score',
            'percentage',
            'level_achieved',
            'status'
        ]
        read_only_fields = fields
    
    def get_duration_minutes(self, obj):
        duration = obj.get_duration()
        return round(duration, 2) if duration else None
    
    def get_percentage(self, obj):
        total = obj.placement_test.total_questions
        if total > 0:
            return round((obj.score / total) * 100, 2)
        return 0