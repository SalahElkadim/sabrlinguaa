from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model
from django.utils import timezone
from cloudinary.models import CloudinaryField

User = get_user_model()


# ============================================
# Abstract Base Models (مستوردة من sabr_questions)
# ============================================

class TimeStampedModel(models.Model):
    """
    نموذج أساسي للـ timestamps
    """
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")
    
    class Meta:
        abstract = True


class OrderedModel(models.Model):
    """
    نموذج أساسي للترتيب والتفعيل
    """
    order = models.PositiveIntegerField(default=0, verbose_name="الترتيب")
    is_active = models.BooleanField(default=True, verbose_name="نشط")
    
    class Meta:
        abstract = True
        ordering = ['order', 'id']


# ============================================
# IELTS Main Models
# ============================================

class IELTSSkill(TimeStampedModel, OrderedModel):
    """
    المهارات الأربعة الأساسية في IELTS
    """
    SKILL_TYPE_CHOICES = [
        ('READING', 'Reading'),
        ('WRITING', 'Writing'),
        ('SPEAKING', 'Speaking'),
        ('LISTENING', 'Listening'),
    ]
    
    skill_type = models.CharField(
        max_length=20,
        choices=SKILL_TYPE_CHOICES,
        unique=True,
        verbose_name="نوع المهارة"
    )
    title = models.CharField(max_length=200, verbose_name="العنوان")
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="الوصف"
    )
    icon = CloudinaryField(
        verbose_name="الأيقونة",
        blank=True,
        null=True,
        folder='ielts/skill_icons',
    )
    
    class Meta:
        verbose_name = "IELTS Skill"
        verbose_name_plural = "IELTS Skills"
        ordering = ['order', 'skill_type']
    
    def __str__(self):
        return f"{self.get_skill_type_display()}"
    
    def get_lesson_packs_count(self):
        """عدد Lesson Packs تحت هذا الـ Skill"""
        return self.lesson_packs.filter(is_active=True).count()


class LessonPack(TimeStampedModel, OrderedModel):
    """
    مجموعة دروس (Lesson Pack) تحت كل Skill
    """
    skill = models.ForeignKey(
        IELTSSkill,
        on_delete=models.CASCADE,
        related_name='lesson_packs',
        verbose_name="المهارة"
    )
    title = models.CharField(max_length=200, verbose_name="عنوان المجموعة")
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="وصف المجموعة"
    )
    
    # إعدادات الامتحان الثابت
    exam_time_limit = models.PositiveIntegerField(
        default=30,
        verbose_name="وقت الامتحان (دقيقة)"
    )
    exam_passing_score = models.PositiveIntegerField(
        default=70,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="نسبة النجاح (%)"
    )
    
    class Meta:
        verbose_name = "Lesson Pack"
        verbose_name_plural = "Lesson Packs"
        ordering = ['skill', 'order', 'id']
    
    def __str__(self):
        return f"{self.skill.get_skill_type_display()} - {self.title}"
    
    def get_lessons_count(self):
        """عدد الدروس في هذا الـ Pack"""
        return self.lessons.filter(is_active=True).count()
    
    def get_practice_exam(self):
        """الحصول على الامتحان الخاص بهذا الـ Pack"""
        return getattr(self, 'practice_exam', None)


class IELTSLesson(TimeStampedModel, OrderedModel):
    """
    درس واحد تحت Lesson Pack
    """
    lesson_pack = models.ForeignKey(
        LessonPack,
        on_delete=models.CASCADE,
        related_name='lessons',
        verbose_name="Lesson Pack"
    )
    title = models.CharField(max_length=200, verbose_name="عنوان الدرس")
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="وصف الدرس"
    )
    
    class Meta:
        verbose_name = "IELTS Lesson"
        verbose_name_plural = "IELTS Lessons"
        ordering = ['lesson_pack', 'order', 'id']
    
    def __str__(self):
        return f"{self.lesson_pack.title} - {self.title}"
    
    def get_content(self):
        """الحصول على المحتوى حسب نوع الـ Skill"""
        skill_type = self.lesson_pack.skill.skill_type
        
        if skill_type == 'READING':
            return getattr(self, 'reading_content', None)
        elif skill_type == 'WRITING':
            return getattr(self, 'writing_content', None)
        elif skill_type == 'SPEAKING':
            return getattr(self, 'speaking_content', None)
        elif skill_type == 'LISTENING':
            return getattr(self, 'listening_content', None)
        return None


# ============================================
# Lesson Content Models
# ============================================

class ReadingLessonContent(TimeStampedModel):
    """
    محتوى درس القراءة
    """
    lesson = models.OneToOneField(
        IELTSLesson,
        on_delete=models.CASCADE,
        related_name='reading_content',
        verbose_name="الدرس"
    )
    
    reading_text = models.TextField(verbose_name="النص القرائي")
    explanation = models.TextField(
        blank=True,
        null=True,
        verbose_name="شرح الدرس"
    )
    
    vocabulary_words = models.JSONField(
        default=list,
        blank=True,
        verbose_name="المفردات",
        help_text='[{"word": "amazing", "meaning": "مدهش"}]'
    )
    
    examples = models.TextField(
        blank=True,
        null=True,
        verbose_name="أمثلة"
    )
    
    video_url = models.URLField(
        blank=True,
        null=True,
        verbose_name="رابط الفيديو التعليمي"
    )
    
    resources = models.JSONField(
        default=list,
        blank=True,
        verbose_name="ملفات إضافية",
        help_text='[{"title": "PDF Guide", "url": "https://..."}]'
    )
    
    class Meta:
        verbose_name = "Reading Lesson Content"
        verbose_name_plural = "Reading Lesson Contents"
    
    def __str__(self):
        return f"Reading: {self.lesson.title}"


class WritingLessonContent(TimeStampedModel):
    """
    محتوى درس الكتابة
    """
    lesson = models.OneToOneField(
        IELTSLesson,
        on_delete=models.CASCADE,
        related_name='writing_content',
        verbose_name="الدرس"
    )
    
    sample_texts = models.TextField(verbose_name="نصوص نموذجية")
    writing_instructions = models.TextField(verbose_name="تعليمات الكتابة")
    
    tips = models.TextField(
        blank=True,
        null=True,
        verbose_name="نصائح وإرشادات"
    )
    
    examples = models.TextField(
        blank=True,
        null=True,
        verbose_name="أمثلة عملية"
    )
    
    video_url = models.URLField(
        blank=True,
        null=True,
        verbose_name="رابط الفيديو التعليمي"
    )
    
    class Meta:
        verbose_name = "Writing Lesson Content"
        verbose_name_plural = "Writing Lesson Contents"
    
    def __str__(self):
        return f"Writing: {self.lesson.title}"


class SpeakingLessonContent(TimeStampedModel):
    """
    محتوى درس التحدث
    """
    lesson = models.OneToOneField(
        IELTSLesson,
        on_delete=models.CASCADE,
        related_name='speaking_content',
        verbose_name="الدرس"
    )
    
    video_file = CloudinaryField(
        verbose_name="فيديو تعليمي",
        resource_type='video',
        folder='ielts/speaking/lessons',
    )
    
    dialogue_texts = models.JSONField(
        default=list,
        blank=True,
        verbose_name="نصوص حوارية",
        help_text='[{"speaker": "John", "text": "Hello!"}, {"speaker": "Mary", "text": "Hi!"}]'
    )
    
    useful_phrases = models.JSONField(
        default=list,
        blank=True,
        verbose_name="عبارات مفيدة",
        help_text='["Let me think...", "In my opinion..."]'
    )
    
    audio_examples = CloudinaryField(
        verbose_name="أمثلة صوتية",
        resource_type='video',
        blank=True,
        null=True,
        folder='ielts/speaking/audio_examples',
    )
    
    pronunciation_tips = models.TextField(
        blank=True,
        null=True,
        verbose_name="نصائح النطق"
    )
    
    class Meta:
        verbose_name = "Speaking Lesson Content"
        verbose_name_plural = "Speaking Lesson Contents"
    
    def __str__(self):
        return f"Speaking: {self.lesson.title}"


class ListeningLessonContent(TimeStampedModel):
    """
    محتوى درس الاستماع
    """
    lesson = models.OneToOneField(
        IELTSLesson,
        on_delete=models.CASCADE,
        related_name='listening_content',
        verbose_name="الدرس"
    )
    
    audio_file = CloudinaryField(
        verbose_name="التسجيل الصوتي",
        resource_type='video',
        folder='ielts/listening/lessons',
    )
    
    transcript = models.TextField(
        blank=True,
        null=True,
        verbose_name="النص الكتابي"
    )
    
    vocabulary_explanation = models.TextField(
        blank=True,
        null=True,
        verbose_name="شرح المفردات"
    )
    
    listening_exercises = models.JSONField(
        default=list,
        blank=True,
        verbose_name="تمارين استماع",
        help_text='[{"question": "What is the main idea?", "answer": "..."}]'
    )
    
    tips = models.TextField(
        blank=True,
        null=True,
        verbose_name="نصائح الاستماع"
    )
    
    class Meta:
        verbose_name = "Listening Lesson Content"
        verbose_name_plural = "Listening Lesson Contents"
    
    def __str__(self):
        return f"Listening: {self.lesson.title}"


# ============================================
# Practice Exam Models
# ============================================

class IELTSPracticeExam(TimeStampedModel):
    """
    امتحان Practice ثابت لكل Lesson Pack
    """
    lesson_pack = models.OneToOneField(
        LessonPack,
        on_delete=models.CASCADE,
        related_name='practice_exam',
        verbose_name="Lesson Pack"
    )
    
    title = models.CharField(
        max_length=200,
        verbose_name="عنوان الامتحان",
        default="Practice Exam"
    )
    
    instructions = models.TextField(
        blank=True,
        null=True,
        verbose_name="تعليمات الامتحان"
    )
    
    class Meta:
        verbose_name = "IELTS Practice Exam"
        verbose_name_plural = "IELTS Practice Exams"
    
    def __str__(self):
        return f"{self.lesson_pack.title} - Practice Exam"
    
    def get_questions_count(self):
        """
        عدد الأسئلة - يأتي من sabr_questions Models
        عبر ielts_lesson_pack FK
        """
        from sabr_questions.models import (
            VocabularyQuestion,
            GrammarQuestion,
            ReadingPassage,
            ListeningAudio,
            SpeakingVideo,
            WritingQuestion
        )
        
        count = 0
        
        # Vocabulary & Grammar
        count += VocabularyQuestion.objects.filter(
            ielts_lesson_pack=self.lesson_pack,
            usage_type='IELTS',
            is_active=True
        ).count()
        
        count += GrammarQuestion.objects.filter(
            ielts_lesson_pack=self.lesson_pack,
            usage_type='IELTS',
            is_active=True
        ).count()
        
        # Reading
        reading_passages = ReadingPassage.objects.filter(
            ielts_lesson_pack=self.lesson_pack,
            usage_type='IELTS',
            is_active=True
        )
        for passage in reading_passages:
            count += passage.get_questions_count()
        
        # Listening
        listening_audios = ListeningAudio.objects.filter(
            ielts_lesson_pack=self.lesson_pack,
            usage_type='IELTS',
            is_active=True
        )
        for audio in listening_audios:
            count += audio.get_questions_count()
        
        # Speaking (MCQ from Video)
        speaking_videos = SpeakingVideo.objects.filter(
            ielts_lesson_pack=self.lesson_pack,
            usage_type='IELTS',
            is_active=True
        )
        for video in speaking_videos:
            count += video.get_questions_count()
        
        # Speaking Recording Tasks
        count += self.lesson_pack.speaking_recording_tasks.filter(is_active=True).count()        
        # Writing
        count += WritingQuestion.objects.filter(
            ielts_lesson_pack=self.lesson_pack,
            usage_type='IELTS',
            is_active=True
        ).count()
        
        return count


# ============================================
# Speaking Recording Task (Part 2 of Speaking)
# ============================================

class SpeakingRecordingTask(TimeStampedModel, OrderedModel):
    """
    مهمة تسجيل صوتي - Part 2 من Speaking Exam
    """
    lesson_pack = models.ForeignKey(
        LessonPack,
        on_delete=models.CASCADE,
        related_name='speaking_recording_tasks',
        verbose_name="Lesson Pack"
    )
    
    task_text = models.TextField(verbose_name="نص المهمة")
    task_image = CloudinaryField(
        verbose_name="صورة المهمة",
        blank=True,
        null=True,
        folder='ielts/speaking/tasks',
    )
    
    duration_seconds = models.PositiveIntegerField(
        default=120,
        verbose_name="المدة المطلوبة (ثانية)"
    )
    
    # AI Assessment Configuration
    assess_content = models.BooleanField(
        default=True,
        verbose_name="تقييم المحتوى"
    )
    assess_grammar = models.BooleanField(
        default=True,
        verbose_name="تقييم القواعد"
    )
    assess_fluency = models.BooleanField(
        default=True,
        verbose_name="تقييم الطلاقة"
    )
    assess_pronunciation = models.BooleanField(
        default=False,
        verbose_name="تقييم النطق"
    )
    
    # Max Scores
    max_content_score = models.PositiveIntegerField(
        default=10,
        verbose_name="أقصى درجة للمحتوى"
    )
    max_grammar_score = models.PositiveIntegerField(
        default=10,
        verbose_name="أقصى درجة للقواعد"
    )
    max_fluency_score = models.PositiveIntegerField(
        default=10,
        verbose_name="أقصى درجة للطلاقة"
    )
    max_pronunciation_score = models.PositiveIntegerField(
        default=10,
        verbose_name="أقصى درجة للنطق"
    )
    
    class Meta:
        verbose_name = "Speaking Recording Task"
        verbose_name_plural = "Speaking Recording Tasks"
        ordering = ['lesson_pack', 'order']
    
    def __str__(self):
        return f"{self.lesson_pack.title} - Recording Task #{self.order}"
    
    def get_max_total_score(self):
        """أقصى درجة إجمالية"""
        total = 0
        if self.assess_content:
            total += self.max_content_score
        if self.assess_grammar:
            total += self.max_grammar_score
        if self.assess_fluency:
            total += self.max_fluency_score
        if self.assess_pronunciation:
            total += self.max_pronunciation_score
        return total


class StudentSpeakingRecording(TimeStampedModel):
    """
    تسجيل الطالب + AI Assessment
    """
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='speaking_recordings',
        verbose_name="الطالب"
    )
    task = models.ForeignKey(
        SpeakingRecordingTask,
        on_delete=models.CASCADE,
        related_name='student_recordings',
        verbose_name="المهمة"
    )
    
    audio_file = CloudinaryField(
        verbose_name="تسجيل الطالب",
        resource_type='video',
        folder='ielts/speaking/student_recordings',
    )
    
    # Transcription (Whisper)
    transcribed_text = models.TextField(
        blank=True,
        null=True,
        verbose_name="النص المكتوب (Whisper)"
    )
    transcription_model = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="نموذج التحويل"
    )
    transcribed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="تاريخ التحويل"
    )
    
    # AI Assessment Scores
    content_score = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        verbose_name="درجة المحتوى"
    )
    grammar_score = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        verbose_name="درجة القواعد"
    )
    fluency_score = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        verbose_name="درجة الطلاقة"
    )
    pronunciation_score = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        verbose_name="درجة النطق"
    )
    total_score = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="الدرجة الإجمالية"
    )
    
    # AI Feedback
    ai_feedback = models.TextField(
        blank=True,
        null=True,
        verbose_name="ملاحظات الـ AI"
    )
    strengths = models.JSONField(
        default=list,
        blank=True,
        verbose_name="نقاط القوة",
        help_text='["Good vocabulary", "Clear pronunciation"]'
    )
    improvements = models.JSONField(
        default=list,
        blank=True,
        verbose_name="نقاط التحسين",
        help_text='["Work on past tense", "Speak more slowly"]'
    )
    
    # Meta
    assessed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="تاريخ التقييم"
    )
    assessment_model = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="نموذج التقييم",
        help_text="e.g., gpt-4, claude-3"
    )
    
    class Meta:
        verbose_name = "Student Speaking Recording"
        verbose_name_plural = "Student Speaking Recordings"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.student.username} - {self.task.task_text[:30]}"
    
    def calculate_total_score(self):
        """حساب الدرجة الإجمالية"""
        total = 0
        if self.task.assess_content and self.content_score:
            total += self.content_score
        if self.task.assess_grammar and self.grammar_score:
            total += self.grammar_score
        if self.task.assess_fluency and self.fluency_score:
            total += self.fluency_score
        if self.task.assess_pronunciation and self.pronunciation_score:
            total += self.pronunciation_score
        
        self.total_score = total
        self.save()
        return total


# ============================================
# Student Progress Tracking
# ============================================

class StudentLessonPackProgress(TimeStampedModel):
    """
    تتبع إكمال Lesson Pack
    """
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='ielts_lesson_pack_progress',
        verbose_name="الطالب"
    )
    lesson_pack = models.ForeignKey(
        LessonPack,
        on_delete=models.CASCADE,
        related_name='student_progress',
        verbose_name="Lesson Pack"
    )
    
    is_completed = models.BooleanField(
        default=False,
        verbose_name="مكتمل"
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="تاريخ الإكمال"
    )
    
    class Meta:
        verbose_name = "Student Lesson Pack Progress"
        verbose_name_plural = "Student Lesson Pack Progress"
        unique_together = ['student', 'lesson_pack']
        ordering = ['student', 'lesson_pack']
    
    def __str__(self):
        status = "✓" if self.is_completed else "✗"
        return f"{status} {self.student.username} - {self.lesson_pack.title}"
    
    def mark_completed(self):
        """تحديد كمكتمل"""
        self.is_completed = True
        self.completed_at = timezone.now()
        self.save()


class StudentLessonProgress(TimeStampedModel):
    """
    تتبع إكمال Lesson (اختياري)
    """
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='ielts_lesson_progress',
        verbose_name="الطالب"
    )
    lesson = models.ForeignKey(
        IELTSLesson,
        on_delete=models.CASCADE,
        related_name='student_progress',
        verbose_name="الدرس"
    )
    
    is_completed = models.BooleanField(
        default=False,
        verbose_name="مكتمل"
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="تاريخ الإكمال"
    )
    
    class Meta:
        verbose_name = "Student Lesson Progress"
        verbose_name_plural = "Student Lesson Progress"
        unique_together = ['student', 'lesson']
        ordering = ['student', 'lesson']
    
    def __str__(self):
        status = "✓" if self.is_completed else "✗"
        return f"{status} {self.student.username} - {self.lesson.title}"


class StudentPracticeExamAttempt(TimeStampedModel):
    """
    محاولات الطالب في Practice Exam
    """
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='ielts_exam_attempts',
        verbose_name="الطالب"
    )
    practice_exam = models.ForeignKey(
        IELTSPracticeExam,
        on_delete=models.CASCADE,
        related_name='attempts',
        verbose_name="Practice Exam"
    )
    
    attempt_number = models.PositiveIntegerField(
        verbose_name="رقم المحاولة",
        validators=[MinValueValidator(1)]
    )
    
    # الإجابات (JSONField)
    answers = models.JSONField(
        default=dict,
        verbose_name="الإجابات",
        help_text="""
        {
            "vocabulary_1": "A",
            "reading_passage_1_q1": "B",
            "writing_1": "text of answer...",
            "speaking_recording_1": "recording_id"
        }
        """
    )
    
    # النتيجة
    score = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="الدرجة (%)"
    )
    
    passed = models.BooleanField(
        default=False,
        verbose_name="نجح"
    )
    
    # الوقت
    time_taken = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="الوقت المستغرق (ثانية)"
    )
    
    # Timestamps
    started_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاريخ البدء"
    )
    submitted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="تاريخ التسليم"
    )
    
    class Meta:
        verbose_name = "Student Practice Exam Attempt"
        verbose_name_plural = "Student Practice Exam Attempts"
        unique_together = ['student', 'practice_exam', 'attempt_number']
        ordering = ['-started_at']
    
    def __str__(self):
        status = "✓ Passed" if self.passed else "✗ Failed" if self.score is not None else "In Progress"
        return f"{self.student.username} - {self.practice_exam.title} - Attempt #{self.attempt_number} ({status})"
    
    def mark_submitted(self):
        """تحديد كمسلّم"""
        self.submitted_at = timezone.now()
        if self.started_at:
            delta = self.submitted_at - self.started_at
            self.time_taken = int(delta.total_seconds())
        self.save()