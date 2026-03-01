from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    IELTSSkill,
    LessonPack,
    IELTSLesson,
    ReadingLessonContent,
    WritingLessonContent,
    SpeakingLessonContent,
    ListeningLessonContent,
    IELTSPracticeExam,
    SpeakingRecordingTask,
    StudentSpeakingRecording,
    StudentLessonPackProgress,
    StudentLessonProgress,
    StudentPracticeExamAttempt,
)

User = get_user_model()


# ============================================
# Basic Serializers
# ============================================

class IELTSSkillSerializer(serializers.ModelSerializer):
    """
    Serializer للمهارات الأربعة
    """
    lesson_packs_count = serializers.SerializerMethodField()
    
    class Meta:
        model = IELTSSkill
        fields = [
            'id',
            'skill_type',
            'title',
            'description',
            'icon',
            'order',
            'is_active',
            'lesson_packs_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_lesson_packs_count(self, obj):
        return obj.get_lesson_packs_count()


class IELTSSkillListSerializer(serializers.ModelSerializer):
    """
    Serializer مبسط للقائمة
    """
    lesson_packs_count = serializers.SerializerMethodField()
    
    class Meta:
        model = IELTSSkill
        fields = ['id', 'skill_type', 'title', 'icon', 'order', 'lesson_packs_count']
    
    def get_lesson_packs_count(self, obj):
        return obj.get_lesson_packs_count()


# ============================================
# Lesson Content Serializers
# ============================================

class ReadingLessonContentSerializer(serializers.ModelSerializer):
    """
    Serializer لمحتوى درس القراءة
    """
    class Meta:
        model = ReadingLessonContent
        fields = [
            'id',
            'lesson',
            'reading_text',
            'explanation',
            'vocabulary_words',
            'examples',
            'video_url',
            'resources',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class WritingLessonContentSerializer(serializers.ModelSerializer):
    """
    Serializer لمحتوى درس الكتابة
    """
    class Meta:
        model = WritingLessonContent
        fields = [
            'id',
            'lesson',
            'sample_texts',
            'writing_instructions',
            'tips',
            'examples',
            'video_url',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class SpeakingLessonContentSerializer(serializers.ModelSerializer):
    """
    Serializer لمحتوى درس التحدث
    """
    class Meta:
        model = SpeakingLessonContent
        fields = [
            'id',
            'lesson',
            'video_file',
            'dialogue_texts',
            'useful_phrases',
            'audio_examples',
            'pronunciation_tips',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class ListeningLessonContentSerializer(serializers.ModelSerializer):
    """
    Serializer لمحتوى درس الاستماع
    """
    class Meta:
        model = ListeningLessonContent
        fields = [
            'id',
            'lesson',
            'audio_file',
            'transcript',
            'vocabulary_explanation',
            'listening_exercises',
            'tips',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


# ============================================
# Lesson Serializers
# ============================================

class IELTSLessonListSerializer(serializers.ModelSerializer):
    """
    Serializer مبسط للدروس (للقائمة)
    """
    skill_type = serializers.CharField(source='lesson_pack.skill.skill_type', read_only=True)
    
    class Meta:
        model = IELTSLesson
        fields = [
            'id',
            'lesson_pack',
            'skill_type',
            'title',
            'description',
            'order',
            'is_active',
        ]


class IELTSLessonDetailSerializer(serializers.ModelSerializer):
    """
    Serializer تفصيلي للدرس (مع المحتوى)
    """
    skill_type = serializers.CharField(source='lesson_pack.skill.skill_type', read_only=True)
    content = serializers.SerializerMethodField()
    
    class Meta:
        model = IELTSLesson
        fields = [
            'id',
            'lesson_pack',
            'skill_type',
            'title',
            'description',
            'order',
            'is_active',
            'content',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_content(self, obj):
        """
        الحصول على المحتوى حسب نوع الـ Skill
        """
        skill_type = obj.lesson_pack.skill.skill_type
        
        if skill_type == 'READING':
            content = getattr(obj, 'reading_content', None)
            if content:
                return ReadingLessonContentSerializer(content).data
        elif skill_type == 'WRITING':
            content = getattr(obj, 'writing_content', None)
            if content:
                return WritingLessonContentSerializer(content).data
        elif skill_type == 'SPEAKING':
            content = getattr(obj, 'speaking_content', None)
            if content:
                return SpeakingLessonContentSerializer(content).data
        elif skill_type == 'LISTENING':
            content = getattr(obj, 'listening_content', None)
            if content:
                return ListeningLessonContentSerializer(content).data
        
        return None


# ============================================
# Lesson Pack Serializers
# ============================================

class LessonPackListSerializer(serializers.ModelSerializer):
    """
    Serializer مبسط لـ Lesson Pack (للقائمة)
    """
    skill_type = serializers.CharField(source='skill.skill_type', read_only=True)
    skill_title = serializers.CharField(source='skill.title', read_only=True)
    lessons_count = serializers.SerializerMethodField()
    has_practice_exam = serializers.SerializerMethodField()
    
    class Meta:
        model = LessonPack
        fields = [
            'id',
            'skill',
            'skill_type',
            'skill_title',
            'title',
            'description',
            'order',
            'is_active',
            'exam_time_limit',
            'exam_passing_score',
            'lessons_count',
            'has_practice_exam',
        ]
    
    def get_lessons_count(self, obj):
        return obj.get_lessons_count()
    
    def get_has_practice_exam(self, obj):
        return obj.get_practice_exam() is not None


class LessonPackDetailSerializer(serializers.ModelSerializer):
    """
    Serializer تفصيلي لـ Lesson Pack (مع الدروس)
    """
    skill_type = serializers.CharField(source='skill.skill_type', read_only=True)
    skill_title = serializers.CharField(source='skill.title', read_only=True)
    lessons = IELTSLessonListSerializer(many=True, read_only=True)
    practice_exam = serializers.SerializerMethodField()
    lessons_count = serializers.SerializerMethodField()
    
    class Meta:
        model = LessonPack
        fields = [
            'id',
            'skill',
            'skill_type',
            'skill_title',
            'title',
            'description',
            'order',
            'is_active',
            'exam_time_limit',
            'exam_passing_score',
            'lessons',
            'lessons_count',
            'practice_exam',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_lessons_count(self, obj):
        return obj.get_lessons_count()
    
    def get_practice_exam(self, obj):
        exam = obj.get_practice_exam()
        if exam:
            return {
                'id': exam.id,
                'title': exam.title,
                'questions_count': exam.get_questions_count(),
            }
        return None


# ============================================
# Practice Exam Serializers
# ============================================
# في ملف serializers.py
class IELTSPracticeExamSerializer(serializers.ModelSerializer):
    """
    Serializer للامتحان
    """
    lesson_pack_title = serializers.CharField(source='lesson_pack.title', read_only=True)
    time_limit = serializers.IntegerField(source='lesson_pack.exam_time_limit', read_only=True)
    passing_score = serializers.IntegerField(source='lesson_pack.exam_passing_score', read_only=True)
    questions_count = serializers.SerializerMethodField()
    vocabulary_count = serializers.SerializerMethodField()
    grammar_count = serializers.SerializerMethodField()  # ✅ إضافة هذا السطر
    reading_count = serializers.SerializerMethodField()
    listening_count = serializers.SerializerMethodField()
    speaking_count = serializers.SerializerMethodField()
    writing_count = serializers.SerializerMethodField()
    
    class Meta:
        model = IELTSPracticeExam
        fields = [
            'id',
            'lesson_pack',
            'lesson_pack_title',
            'title',
            'instructions',
            'time_limit',
            'passing_score',
            'questions_count',
            'vocabulary_count',
            'grammar_count',  # ✅ إضافة هذا السطر
            'reading_count',
            'listening_count',
            'speaking_count',
            'writing_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_questions_count(self, obj):
        return obj.get_questions_count()
    
    def get_vocabulary_count(self, obj):
        from sabr_questions.models import VocabularyQuestion
        return VocabularyQuestion.objects.filter(
            ielts_lesson_pack=obj.lesson_pack,
            usage_type='IELTS',
            is_active=True
        ).count()
    
    def get_grammar_count(self, obj):  # ✅ إضافة هذه الدالة
        from sabr_questions.models import GrammarQuestion
        return GrammarQuestion.objects.filter(
            ielts_lesson_pack=obj.lesson_pack,
            usage_type='IELTS',
            is_active=True
        ).count()
    
    def get_reading_count(self, obj):
        from sabr_questions.models import ReadingPassage
        return ReadingPassage.objects.filter(
            ielts_lesson_pack=obj.lesson_pack,
            usage_type='IELTS',
            is_active=True
        ).count()
    
    def get_listening_count(self, obj):
        from sabr_questions.models import ListeningAudio
        return ListeningAudio.objects.filter(
            ielts_lesson_pack=obj.lesson_pack,
            usage_type='IELTS',
            is_active=True
        ).count()
    
    def get_speaking_count(self, obj):
        from sabr_questions.models import SpeakingVideo
        videos = SpeakingVideo.objects.filter(
            ielts_lesson_pack=obj.lesson_pack,
            usage_type='IELTS',
            is_active=True
        ).count()
        recordings = obj.lesson_pack.speaking_recording_tasks.filter(is_active=True).count()
        return videos + recordings
    
    def get_writing_count(self, obj):
        from sabr_questions.models import WritingQuestion
        return WritingQuestion.objects.filter(
            ielts_lesson_pack=obj.lesson_pack,
            usage_type='IELTS',
            is_active=True
        ).count()

# ============================================
# Speaking Recording Serializers
# ============================================

class SpeakingRecordingTaskSerializer(serializers.ModelSerializer):
    """
    Serializer لمهمة التسجيل الصوتي
    """
    max_total_score = serializers.SerializerMethodField()
    
    class Meta:
        model = SpeakingRecordingTask
        fields = [
            'id',
            'lesson_pack',
            'task_text',
            'task_image',
            'duration_seconds',
            'order',
            'is_active',
            'assess_content',
            'assess_grammar',
            'assess_fluency',
            'assess_pronunciation',
            'max_content_score',
            'max_grammar_score',
            'max_fluency_score',
            'max_pronunciation_score',
            'max_total_score',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_max_total_score(self, obj):
        return obj.get_max_total_score()


class StudentSpeakingRecordingSerializer(serializers.ModelSerializer):
    """
    Serializer لتسجيل الطالب
    """
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    task_text = serializers.CharField(source='task.task_text', read_only=True)
    
    class Meta:
        model = StudentSpeakingRecording
        fields = [
            'id',
            'student',
            'student_name',
            'task',
            'task_text',
            'audio_file',
            'transcribed_text',
            'transcription_model',
            'transcribed_at',
            'content_score',
            'grammar_score',
            'fluency_score',
            'pronunciation_score',
            'total_score',
            'ai_feedback',
            'strengths',
            'improvements',
            'assessed_at',
            'assessment_model',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'transcribed_text',
            'transcription_model',
            'transcribed_at',
            'content_score',
            'grammar_score',
            'fluency_score',
            'pronunciation_score',
            'total_score',
            'ai_feedback',
            'strengths',
            'improvements',
            'assessed_at',
            'assessment_model',
            'created_at',
            'updated_at',
        ]


# ============================================
# Progress Tracking Serializers
# ============================================

class StudentLessonPackProgressSerializer(serializers.ModelSerializer):
    """
    Serializer لتتبع إكمال Lesson Pack
    """
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    lesson_pack_title = serializers.CharField(source='lesson_pack.title', read_only=True)
    skill_type = serializers.CharField(source='lesson_pack.skill.skill_type', read_only=True)
    
    class Meta:
        model = StudentLessonPackProgress
        fields = [
            'id',
            'student',
            'student_name',
            'lesson_pack',
            'lesson_pack_title',
            'skill_type',
            'is_completed',
            'completed_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['completed_at', 'created_at', 'updated_at']


class StudentLessonProgressSerializer(serializers.ModelSerializer):
    """
    Serializer لتتبع إكمال Lesson
    """
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    lesson_title = serializers.CharField(source='lesson.title', read_only=True)
    
    class Meta:
        model = StudentLessonProgress
        fields = [
            'id',
            'student',
            'student_name',
            'lesson',
            'lesson_title',
            'is_completed',
            'completed_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['completed_at', 'created_at', 'updated_at']


class StudentPracticeExamAttemptSerializer(serializers.ModelSerializer):
    """
    Serializer لمحاولات الامتحان
    """
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    exam_title = serializers.CharField(source='practice_exam.title', read_only=True)
    lesson_pack_title = serializers.CharField(source='practice_exam.lesson_pack.title', read_only=True)
    
    class Meta:
        model = StudentPracticeExamAttempt
        fields = [
            'id',
            'student',
            'student_name',
            'practice_exam',
            'exam_title',
            'lesson_pack_title',
            'attempt_number',
            'answers',
            'score',
            'passed',
            'time_taken',
            'started_at',
            'submitted_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['started_at', 'created_at', 'updated_at']


class StudentPracticeExamAttemptCreateSerializer(serializers.ModelSerializer):
    """
    Serializer لإنشاء محاولة امتحان جديدة
    """
    class Meta:
        model = StudentPracticeExamAttempt
        fields = [
            'student',
            'practice_exam',
            'attempt_number',
        ]
    
    def validate(self, data):
        """
        التحقق من عدم تكرار رقم المحاولة
        """
        student = data.get('student')
        practice_exam = data.get('practice_exam')
        attempt_number = data.get('attempt_number')
        
        if StudentPracticeExamAttempt.objects.filter(
            student=student,
            practice_exam=practice_exam,
            attempt_number=attempt_number
        ).exists():
            raise serializers.ValidationError(
                "هذا الطالب قد قام بهذه المحاولة من قبل"
            )
        
        return data

def serialize_cloudinary(value):
    """تحويل CloudinaryResource لـ string"""
    if value is None:
        return None
    if hasattr(value, 'url'):
        return value.url
    return str(value) if value else None

# ============================================
# IELTS Lesson Detail with Questions
# ============================================

class IELTSLessonQuestionSerializer(serializers.Serializer):
    """Serializer للأسئلة المرتبطة بالدرس"""
    id = serializers.IntegerField(read_only=True)
    question_text = serializers.CharField()
    question_image = serializers.SerializerMethodField()
    choice_a = serializers.CharField()
    choice_b = serializers.CharField()
    choice_c = serializers.CharField()
    choice_d = serializers.CharField()
    correct_answer = serializers.CharField()
    explanation = serializers.CharField(allow_null=True)
    points = serializers.IntegerField()
    order = serializers.IntegerField()

    def get_question_image(self, obj):
        if obj.question_image:
            return obj.question_image.url
        return None


class IELTSLessonDetailWithQuestionsSerializer(serializers.ModelSerializer):
    """Serializer تفصيلي للدرس مع المحتوى والأسئلة"""
    skill_type = serializers.CharField(
        source='lesson_pack.skill.skill_type',
        read_only=True
    )
    content = serializers.SerializerMethodField()
    questions = serializers.SerializerMethodField()
    questions_count = serializers.SerializerMethodField()

    class Meta:
        model = IELTSLesson
        fields = [
            'id',
            'lesson_pack',
            'skill_type',
            'title',
            'description',
            'order',
            'is_active',
            'content',
            'questions',
            'questions_count',
            'created_at',
            'updated_at',
        ]

    def get_content(self, obj):
        skill_type = obj.lesson_pack.skill.skill_type

        if skill_type == 'READING':
            content = getattr(obj, 'reading_content', None)
            if content:
                return ReadingLessonContentSerializer(content).data

        elif skill_type == 'WRITING':
            content = getattr(obj, 'writing_content', None)
            if content:
                return WritingLessonContentSerializer(content).data

        elif skill_type == 'SPEAKING':
            content = getattr(obj, 'speaking_content', None)
            if content:
                return SpeakingLessonContentSerializer(content).data

        elif skill_type == 'LISTENING':
            content = getattr(obj, 'listening_content', None)
            if content:
                return ListeningLessonContentSerializer(content).data

        return None

    def get_questions(self, obj):
        from sabr_questions.models import (
            VocabularyQuestion, GrammarQuestion,
            ReadingPassage, ListeningAudio,
            SpeakingVideo
        )

        skill_type = obj.lesson_pack.skill.skill_type

        if skill_type == 'READING':
            # أسئلة القراءة مرتبطة بالـ Passage
            content = getattr(obj, 'reading_content', None)
            if not content or not hasattr(content, 'passage'):
                return []
            questions = content.passage.questions.filter(
                is_active=True
            ).order_by('order', 'id')
            return IELTSLessonQuestionSerializer(questions, many=True).data

        elif skill_type == 'LISTENING':
            # أسئلة الاستماع مرتبطة بالـ Audio
            content = getattr(obj, 'listening_content', None)
            if not content or not hasattr(content, 'audio'):
                return []
            questions = content.audio.questions.filter(
                is_active=True
            ).order_by('order', 'id')
            return IELTSLessonQuestionSerializer(questions, many=True).data

        elif skill_type == 'SPEAKING':
            # أسئلة التحدث مرتبطة بالـ Video
            content = getattr(obj, 'speaking_content', None)
            if not content or not hasattr(content, 'video'):
                return []
            questions = content.video.questions.filter(
                is_active=True
            ).order_by('order', 'id')
            return IELTSLessonQuestionSerializer(questions, many=True).data

        elif skill_type in ['VOCABULARY', 'GRAMMAR']:
            # Vocab & Grammar مرتبطة بـ ielts_lesson مباشرة
            if skill_type == 'VOCABULARY':
                from sabr_questions.models import VocabularyQuestion
                questions = VocabularyQuestion.objects.filter(
                    ielts_lesson=obj,
                    is_active=True
                ).order_by('order', 'id')
            else:
                from sabr_questions.models import GrammarQuestion
                questions = GrammarQuestion.objects.filter(
                    ielts_lesson=obj,
                    is_active=True
                ).order_by('order', 'id')
            return IELTSLessonQuestionSerializer(questions, many=True).data

        return []

    def get_questions_count(self, obj):
        questions = self.get_questions(obj)
        return len(questions)