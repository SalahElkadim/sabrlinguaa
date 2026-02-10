from rest_framework import serializers
from django.db import transaction
from django.shortcuts import get_object_or_404

from levels.models import (
    Level, Unit, Lesson,
    ReadingLessonContent, ListeningLessonContent,
    SpeakingLessonContent, WritingLessonContent,
    UnitExam, LevelExam,
    StudentLevel, StudentUnit, StudentLesson,
    StudentUnitExamAttempt, StudentLevelExamAttempt,
    QuestionBank
)

from sabr_questions.models import (
    ReadingPassage, ListeningAudio, SpeakingVideo,
    VocabularyQuestion, VocabularyQuestionSet,
    GrammarQuestion, GrammarQuestionSet,
    ReadingQuestion, ListeningQuestion, SpeakingQuestion,
    WritingQuestion
)


# ============================================
# 1. LEVEL SERIALIZERS
# ============================================

class LevelListSerializer(serializers.ModelSerializer):
    """عرض قائمة المستويات (مبسط)"""
    units_count = serializers.SerializerMethodField()
    total_lessons = serializers.SerializerMethodField()
    
    class Meta:
        model = Level
        fields = [
            'id', 'code', 'title', 'description',
            'order', 'is_active',
            'units_count', 'total_lessons',
            'created_at', 'updated_at'
        ]
    
    def get_units_count(self, obj):
        return obj.get_units_count()
    
    def get_total_lessons(self, obj):
        return obj.get_total_lessons()


class UnitNestedSerializer(serializers.ModelSerializer):
    """عرض الوحدات بشكل مبسط داخل Level"""
    lessons_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Unit
        fields = ['id', 'title', 'description', 'order', 'is_active', 'lessons_count']
    
    def get_lessons_count(self, obj):
        return obj.get_lessons_count()


class LevelDetailSerializer(serializers.ModelSerializer):
    """عرض تفاصيل المستوى مع الوحدات"""
    units = UnitNestedSerializer(many=True, read_only=True)
    units_count = serializers.SerializerMethodField()
    total_lessons = serializers.SerializerMethodField()
    has_exam = serializers.SerializerMethodField()
    
    class Meta:
        model = Level
        fields = [
            'id', 'code', 'title', 'description',
            'order', 'is_active',
            'units', 'units_count', 'total_lessons',
            'has_exam',
            'created_at', 'updated_at'
        ]
    
    def get_units_count(self, obj):
        return obj.get_units_count()
    
    def get_total_lessons(self, obj):
        return obj.get_total_lessons()
    
    def get_has_exam(self, obj):
        return hasattr(obj, 'exam')


class LevelCreateUpdateSerializer(serializers.ModelSerializer):
    """إنشاء/تعديل المستوى"""
    class Meta:
        model = Level
        fields = ['code', 'title', 'description', 'order', 'is_active']


# ============================================
# 2. UNIT SERIALIZERS
# ============================================

class LessonNestedSerializer(serializers.ModelSerializer):
    """عرض الدروس بشكل مبسط داخل Unit"""
    class Meta:
        model = Lesson
        fields = ['id', 'title', 'lesson_type', 'order', 'is_active']


class UnitDetailSerializer(serializers.ModelSerializer):
    """عرض تفاصيل الوحدة مع الدروس"""
    level = LevelListSerializer(read_only=True)
    lessons = LessonNestedSerializer(many=True, read_only=True)
    lessons_count = serializers.SerializerMethodField()
    has_exam = serializers.SerializerMethodField()
    has_question_bank = serializers.SerializerMethodField()
    
    class Meta:
        model = Unit
        fields = [
            'id', 'level', 'title', 'description',
            'order', 'is_active',
            'lessons', 'lessons_count',
            'has_exam', 'has_question_bank',
            'created_at', 'updated_at'
        ]
    
    def get_lessons_count(self, obj):
        return obj.get_lessons_count()
    
    def get_has_exam(self, obj):
        return hasattr(obj, 'exam')
    
    def get_has_question_bank(self, obj):
        return obj.question_bank.exists()


class UnitCreateUpdateSerializer(serializers.ModelSerializer):
    """إنشاء/تعديل الوحدة"""
    class Meta:
        model = Unit
        fields = ['level', 'title', 'description', 'order', 'is_active']
    
    def create(self, validated_data):
        """
        عند إنشاء Unit جديد، ننشئ QuestionBank تلقائياً
        """
        with transaction.atomic():
            unit = Unit.objects.create(**validated_data)
            
            # ✅ إنشاء QuestionBank تلقائياً
            QuestionBank.objects.create(
                unit=unit,
                title=f"Question Bank - {unit.title}",
                description=f"Automatically created for {unit.title}"
            )
            
            return unit


# ============================================
# 3. LESSON SERIALIZERS
# ============================================

class LessonDetailSerializer(serializers.ModelSerializer):
    """عرض تفاصيل الدرس"""
    unit = UnitNestedSerializer(read_only=True)
    has_content = serializers.SerializerMethodField()
    content_details = serializers.SerializerMethodField()
    
    class Meta:
        model = Lesson
        fields = [
            'id', 'unit', 'lesson_type', 'title',
            'order', 'is_active',
            'has_content', 'content_details',
            'created_at', 'updated_at'
        ]
    
    def get_has_content(self, obj):
        return obj.get_content() is not None
    
    def get_content_details(self, obj):
        """الحصول على تفاصيل المحتوى بناءً على نوع الدرس"""
        content = obj.get_content()
        if not content:
            return None
        
        if obj.lesson_type == 'READING':
            return {
                'id': content.id,
                'passage_title': content.passage.title if content.passage else None,
                'vocabulary_count': len(content.vocabulary_words) if content.vocabulary_words else 0
            }
        elif obj.lesson_type == 'LISTENING':
            return {
                'id': content.id,
                'audio_title': content.audio.title if content.audio else None
            }
        elif obj.lesson_type == 'SPEAKING':
            return {
                'id': content.id,
                'video_title': content.video.title if content.video else None
            }
        elif obj.lesson_type == 'WRITING':
            return {
                'id': content.id,
                'title': content.title
            }
        
        return None


class LessonCreateUpdateSerializer(serializers.ModelSerializer):
    """إنشاء/تعديل الدرس"""
    class Meta:
        model = Lesson
        fields = ['unit', 'lesson_type', 'title', 'order', 'is_active']


# ============================================
# 4. LESSON CONTENT SERIALIZERS
# ============================================

# ---------- 4.1 Reading Lesson Content ----------

class ReadingLessonContentSerializer(serializers.ModelSerializer):
    """عرض محتوى درس القراءة"""
    lesson = LessonDetailSerializer(read_only=True)
    passage_details = serializers.SerializerMethodField()
    
    class Meta:
        model = ReadingLessonContent
        fields = [
            'id', 'lesson', 'passage', 'passage_details',
            'vocabulary_words', 'explanation',
            'created_at', 'updated_at'
        ]
    
    def get_passage_details(self, obj):
        if not obj.passage:
            return None
        return {
            'id': obj.passage.id,
            'title': obj.passage.title,
            'passage_text': obj.passage.passage_text,
            'passage_image': obj.passage.passage_image.url if obj.passage.passage_image else None,
            'questions_count': obj.passage.get_questions_count()
        }


class ReadingLessonContentCreateUpdateSerializer(serializers.ModelSerializer):
    """إنشاء/تعديل محتوى درس القراءة"""
    class Meta:
        model = ReadingLessonContent
        fields = ['lesson', 'passage', 'vocabulary_words', 'explanation']
    
    def validate_lesson(self, value):
        """التحقق من أن الدرس من نوع READING"""
        if value.lesson_type != 'READING':
            raise serializers.ValidationError("الدرس يجب أن يكون من نوع READING")
        return value


# ---------- 4.2 Listening Lesson Content ----------

class ListeningLessonContentSerializer(serializers.ModelSerializer):
    """عرض محتوى درس الاستماع"""
    lesson = LessonDetailSerializer(read_only=True)
    audio_details = serializers.SerializerMethodField()
    
    class Meta:
        model = ListeningLessonContent
        fields = [
            'id', 'lesson', 'audio', 'audio_details',
            'explanation',
            'created_at', 'updated_at'
        ]
    
    def get_audio_details(self, obj):
        if not obj.audio:
            return None
        return {
            'id': obj.audio.id,
            'title': obj.audio.title,
            'audio_file': obj.audio.audio_file.url if obj.audio.audio_file else None,
            'transcript': obj.audio.transcript,
            'duration': obj.audio.duration,
            'questions_count': obj.audio.get_questions_count()
        }


class ListeningLessonContentCreateUpdateSerializer(serializers.ModelSerializer):
    """إنشاء/تعديل محتوى درس الاستماع"""
    class Meta:
        model = ListeningLessonContent
        fields = ['lesson', 'audio', 'explanation']
    
    def validate_lesson(self, value):
        if value.lesson_type != 'LISTENING':
            raise serializers.ValidationError("الدرس يجب أن يكون من نوع LISTENING")
        return value


# ---------- 4.3 Speaking Lesson Content ----------

class SpeakingLessonContentSerializer(serializers.ModelSerializer):
    """عرض محتوى درس التحدث"""
    lesson = LessonDetailSerializer(read_only=True)
    video_details = serializers.SerializerMethodField()
    
    class Meta:
        model = SpeakingLessonContent
        fields = [
            'id', 'lesson', 'video', 'video_details',
            'explanation',
            'created_at', 'updated_at'
        ]
    
    def get_video_details(self, obj):
        if not obj.video:
            return None
        return {
            'id': obj.video.id,
            'title': obj.video.title,
            'video_file': obj.video.video_file.url if obj.video.video_file else None,
            'description': obj.video.description,
            'duration': obj.video.duration,
            'thumbnail': obj.video.thumbnail.url if obj.video.thumbnail else None,
            'questions_count': obj.video.get_questions_count()
        }


class SpeakingLessonContentCreateUpdateSerializer(serializers.ModelSerializer):
    """إنشاء/تعديل محتوى درس التحدث"""
    class Meta:
        model = SpeakingLessonContent
        fields = ['lesson', 'video', 'explanation']
    
    def validate_lesson(self, value):
        if value.lesson_type != 'SPEAKING':
            raise serializers.ValidationError("الدرس يجب أن يكون من نوع SPEAKING")
        return value


# ---------- 4.4 Writing Lesson Content ----------

class WritingLessonContentSerializer(serializers.ModelSerializer):
    """عرض محتوى درس الكتابة"""
    lesson = LessonDetailSerializer(read_only=True)
    
    class Meta:
        model = WritingLessonContent
        fields = [
            'id', 'lesson', 'title',
            'writing_passage', 'instructions', 'sample_answer',
            'created_at', 'updated_at'
        ]


class WritingLessonContentCreateUpdateSerializer(serializers.ModelSerializer):
    """إنشاء/تعديل محتوى درس الكتابة"""
    class Meta:
        model = WritingLessonContent
        fields = ['lesson', 'title', 'writing_passage', 'instructions', 'sample_answer']
    
    def validate_lesson(self, value):
        if value.lesson_type != 'WRITING':
            raise serializers.ValidationError("الدرس يجب أن يكون من نوع WRITING")
        return value


# ============================================
# 5. EXAM SERIALIZERS
# ============================================

# ---------- 5.1 Unit Exam ----------

class UnitExamSerializer(serializers.ModelSerializer):
    """عرض امتحان الوحدة"""
    unit_details = serializers.SerializerMethodField()
    total_questions = serializers.SerializerMethodField()
    
    class Meta:
        model = UnitExam
        fields = [
            'id', 'unit', 'unit_details', 'title', 'description', 'instructions',
            'time_limit', 'passing_score',
            'vocabulary_count', 'grammar_count', 'reading_questions_count',
            'listening_questions_count', 'speaking_questions_count', 'writing_questions_count',
            'total_questions',
            'order', 'is_active',
            'created_at', 'updated_at'
        ]
    
    def get_unit_details(self, obj):
        return {
            'id': obj.unit.id,
            'title': obj.unit.title,
            'level_code': obj.unit.level.code
        }
    
    def get_total_questions(self, obj):
        return obj.get_total_questions()


class UnitExamCreateUpdateSerializer(serializers.ModelSerializer):
    """إنشاء/تعديل امتحان الوحدة"""
    class Meta:
        model = UnitExam
        fields = [
            'unit', 'title', 'description', 'instructions',
            'time_limit',
            'vocabulary_count', 'grammar_count', 'reading_questions_count',
            'listening_questions_count', 'speaking_questions_count', 'writing_questions_count',
            'order', 'is_active'
        ]


# ---------- 5.2 Level Exam ----------

class LevelExamSerializer(serializers.ModelSerializer):
    """عرض امتحان المستوى"""
    level_details = serializers.SerializerMethodField()
    total_questions = serializers.SerializerMethodField()
    
    class Meta:
        model = LevelExam
        fields = [
            'id', 'level', 'level_details', 'title', 'description', 'instructions',
            'time_limit', 'passing_score',
            'vocabulary_count', 'grammar_count', 'reading_questions_count',
            'listening_questions_count', 'speaking_questions_count', 'writing_questions_count',
            'total_questions',
            'order', 'is_active',
            'created_at', 'updated_at'
        ]
    
    def get_level_details(self, obj):
        return {
            'id': obj.level.id,
            'code': obj.level.code,
            'title': obj.level.title
        }
    
    def get_total_questions(self, obj):
        return obj.get_total_questions()


class LevelExamCreateUpdateSerializer(serializers.ModelSerializer):
    """إنشاء/تعديل امتحان المستوى"""
    class Meta:
        model = LevelExam
        fields = [
            'level', 'title', 'description', 'instructions',
            'time_limit',
            'vocabulary_count', 'grammar_count', 'reading_questions_count',
            'listening_questions_count', 'speaking_questions_count', 'writing_questions_count',
            'order', 'is_active'
        ]


# ============================================
# 6. STUDENT PROGRESS SERIALIZERS
# ============================================

class StudentLevelSerializer(serializers.ModelSerializer):
    """تقدم الطالب في المستوى"""
    level_details = LevelListSerializer(source='level', read_only=True)
    current_unit_details = UnitNestedSerializer(source='current_unit', read_only=True)
    
    class Meta:
        model = StudentLevel
        fields = [
            'id', 'student', 'level', 'level_details',
            'status', 'current_unit', 'current_unit_details',
            'started_at', 'completed_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['student', 'started_at', 'completed_at']


class StudentUnitSerializer(serializers.ModelSerializer):
    """تقدم الطالب في الوحدة"""
    unit_details = UnitNestedSerializer(source='unit', read_only=True)
    
    class Meta:
        model = StudentUnit
        fields = [
            'id', 'student', 'unit', 'unit_details',
            'status', 'lessons_completed', 'exam_passed',
            'started_at', 'completed_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['student', 'lessons_completed', 'exam_passed', 'started_at', 'completed_at']


class StudentLessonSerializer(serializers.ModelSerializer):
    """تقدم الطالب في الدرس"""
    lesson_details = LessonNestedSerializer(source='lesson', read_only=True)
    
    class Meta:
        model = StudentLesson
        fields = [
            'id', 'student', 'lesson', 'lesson_details',
            'is_completed', 'completed_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['student', 'completed_at']


# ============================================
# 7. QUESTION BANK SERIALIZERS
# ============================================

class QuestionBankListSerializer(serializers.ModelSerializer):
    """عرض قائمة بنوك الأسئلة (مبسط)"""
    unit_title = serializers.CharField(source='unit.title', read_only=True)
    level_code = serializers.CharField(source='level.code', read_only=True)
    total_questions = serializers.SerializerMethodField()
    
    class Meta:
        model = QuestionBank
        fields = [
            'id', 'title', 'description',
            'unit', 'unit_title',
            'level', 'level_code',
            'total_questions',
            'created_at', 'updated_at'
        ]
    
    def get_total_questions(self, obj):
        return obj.get_total_questions()


class QuestionBankDetailSerializer(serializers.ModelSerializer):
    """عرض تفاصيل بنك الأسئلة"""
    unit_details = UnitNestedSerializer(source='unit', read_only=True)
    level_details = LevelListSerializer(source='level', read_only=True)
    statistics = serializers.SerializerMethodField()
    readiness = serializers.SerializerMethodField()
    
    class Meta:
        model = QuestionBank
        fields = [
            'id', 'title', 'description',
            'unit', 'unit_details',
            'level', 'level_details',
            'statistics', 'readiness',
            'created_at', 'updated_at'
        ]
    
    def get_statistics(self, obj):
        return {
            'vocabulary': obj.get_vocabulary_count(),
            'grammar': obj.get_grammar_count(),
            'reading': obj.get_reading_count(),
            'listening': obj.get_listening_count(),
            'speaking': obj.get_speaking_count(),
            'writing': obj.get_writing_count(),
            'total': obj.get_total_questions()
        }
    
    def get_readiness(self, obj):
        if obj.unit:
            required = {
                'vocabulary': 8,
                'grammar': 8,
                'reading': 10,
                'listening': 3,
                'speaking': 3,
                'writing': 3
            }
            is_ready = obj.is_ready_for_unit_exam()
        elif obj.level:
            required = {
                'vocabulary': 12,
                'grammar': 12,
                'reading': 20,
                'listening': 6,
                'speaking': 5,
                'writing': 5
            }
            is_ready = obj.is_ready_for_level_exam()
        else:
            return None
        
        stats = self.get_statistics(obj)
        
        return {
            'is_ready': is_ready,
            'required': required,
            'current': stats,
            'missing': {
                key: max(0, required[key] - stats[key])
                for key in required.keys()
            }
        }


class QuestionBankCreateUpdateSerializer(serializers.ModelSerializer):
    """إنشاء/تعديل بنك الأسئلة"""
    class Meta:
        model = QuestionBank
        fields = ['unit', 'level', 'title', 'description']
    
    def validate(self, data):
        """التحقق من أن البنك مربوط بـ Unit أو Level فقط"""
        unit = data.get('unit')
        level = data.get('level')
        
        if unit and level:
            raise serializers.ValidationError("لا يمكن ربط البنك بـ Unit و Level في نفس الوقت")
        if not unit and not level:
            raise serializers.ValidationError("يجب ربط البنك بـ Unit أو Level")
        
        return data


# ============================================
# 8. EXAM ATTEMPT SERIALIZERS
# ============================================

class StudentUnitExamAttemptSerializer(serializers.ModelSerializer):
    """محاولة امتحان الوحدة"""
    unit_exam_details = UnitExamSerializer(source='unit_exam', read_only=True)
    
    class Meta:
        model = StudentUnitExamAttempt
        fields = [
            'id', 'student', 'unit_exam', 'unit_exam_details',
            'attempt_number', 'generated_questions', 'answers',
            'score', 'passed', 'time_taken',
            'started_at', 'submitted_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['student', 'generated_questions', 'score', 'passed', 'submitted_at']


class StudentLevelExamAttemptSerializer(serializers.ModelSerializer):
    """محاولة امتحان المستوى"""
    level_exam_details = LevelExamSerializer(source='level_exam', read_only=True)
    
    class Meta:
        model = StudentLevelExamAttempt
        fields = [
            'id', 'student', 'level_exam', 'level_exam_details',
            'attempt_number', 'generated_questions', 'answers',
            'score', 'passed', 'time_taken',
            'started_at', 'submitted_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['student', 'generated_questions', 'score', 'passed', 'submitted_at']