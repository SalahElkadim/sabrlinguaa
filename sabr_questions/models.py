from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from cloudinary.models import CloudinaryField


# ============================================
# Abstract Base Models
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


class BaseMCQQuestion(models.Model):
    """
    نموذج أساسي لأسئلة الاختيار من متعدد
    """
    question_text = models.TextField(verbose_name="نص السؤال")
    question_image = CloudinaryField(
        verbose_name="صورة السؤال",
        blank=True,
        null=True
    )
    
    # الاختيارات
    choice_a = models.CharField(max_length=500, verbose_name="الاختيار أ")
    choice_b = models.CharField(max_length=500, verbose_name="الاختيار ب")
    choice_c = models.CharField(max_length=500, verbose_name="الاختيار ج")
    choice_d = models.CharField(max_length=500, verbose_name="الاختيار د")
    
    # الإجابة الصحيحة
    CHOICES = [
        ('A', 'أ'),
        ('B', 'ب'),
        ('C', 'ج'),
        ('D', 'د'),
    ]
    correct_answer = models.CharField(
        max_length=1,
        choices=CHOICES,
        verbose_name="الإجابة الصحيحة"
    )
    
    explanation = models.TextField(
        blank=True,
        null=True,
        verbose_name="شرح الإجابة"
    )
    
    points = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name="النقاط"
    )
    
    class Meta:
        abstract = True
    
    def __str__(self):
        return self.question_text[:50]


# ============================================
# Usage Type Mixin (لإعادة الاستخدام)
# ============================================
class UsageTypeMixin(models.Model):
    """
    Mixin لإضافة usage_type والـ Foreign Keys للاختبارات المختلفة
    """
    USAGE_TYPE_CHOICES = [
        ('QUESTION_BANK', 'Question Bank'),
        ('PLACEMENT', 'Placement Test'),
        ('LESSON', 'Lesson Content'),        # 🆕 للأسئلة المحلولة في الدروس
        ('UNIT_EXAM', 'Unit Exam'),          # 🆕 امتحان الوحدة
        ('LEVEL_EXAM', 'Level Exam'),        # 🆕 امتحان المستوى
        ('IELTS', 'IELTS Exam'),
        ('IELTS_LESSON', 'IELTS Lesson'),   # ✅ جديد
        ('GENERAL', 'General Use'),
    ]
    
    usage_type = models.CharField(
        max_length=20,
        choices=USAGE_TYPE_CHOICES,
        default='QUESTION_BANK',
        verbose_name="نوع الاستخدام",
        db_index=True
    )
    
    # ============================================
    # Foreign Keys للاختبارات المختلفة
    # ============================================
    ielts_lesson = models.ForeignKey(
        'ielts.IELTSLesson',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_questions',
        verbose_name="IELTS Lesson",
    )
    # Existing FK (موجود بالفعل)
    placement_test = models.ForeignKey(
        'placement_test.PlacementTest',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="اختبار تحديد المستوى"
    )
    
    # 🆕 NEW: Foreign Keys للـ Levels System
    lesson = models.ForeignKey(
        'levels.Lesson',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_questions',
        verbose_name="الدرس",
        help_text="للأسئلة المحلولة في الدروس (usage_type=LESSON)"
    )
    
    unit_exam = models.ForeignKey(
        'levels.UnitExam',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_questions',
        verbose_name="امتحان الوحدة",
        help_text="لأسئلة امتحان الوحدة (usage_type=UNIT_EXAM)"
    )
    
    level_exam = models.ForeignKey(
        'levels.LevelExam',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_questions',
        verbose_name="امتحان المستوى",
        help_text="لأسئلة امتحان المستوى (usage_type=LEVEL_EXAM)"
    )
    
    # 🆕 NEW: Foreign Key للـ IELTS System
    ielts_lesson_pack = models.ForeignKey(
        'ielts.LessonPack',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_questions',
        verbose_name="IELTS Lesson Pack",
        help_text="لأسئلة امتحان IELTS (usage_type=IELTS)"
    )
    step_skill = models.ForeignKey(
        'step.STEPSkill',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_questions',
        verbose_name="STEP Skill",
        help_text="لأسئلة STEP (usage_type=STEP)"
    )
    
    class Meta:
        abstract = True

    


# ============================================
# Vocabulary Questions (أسئلة المفردات)
# ============================================

class VocabularyQuestionSet(TimeStampedModel, OrderedModel):
    """
    مجموعة أسئلة المفردات
    """
    title = models.CharField(max_length=200, verbose_name="عنوان المجموعة")
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="وصف المجموعة"
    )
    
    # ✅ إضافة usage_type للـ Set
    USAGE_TYPE_CHOICES = [
        ('QUESTION_BANK', 'Question Bank'),
        ('PLACEMENT', 'Placement Test'),
        ('STEP', 'Learning Step'),
        ('IELTS', 'IELTS Exam'),
        ('LEVEL', 'Level Test'),
        ('GENERAL', 'General Use'),
    ]
    
    usage_type = models.CharField(
        max_length=20,
        choices=USAGE_TYPE_CHOICES,
        default='QUESTION_BANK',
        verbose_name="نوع الاستخدام"
    )
    
    class Meta:
        verbose_name = "مجموعة أسئلة مفردات"
        verbose_name_plural = "مجموعات أسئلة المفردات"
        ordering = ['order', 'created_at']
    
    def __str__(self):
        return self.title
    
    def get_questions_count(self):
        """عدد الأسئلة"""
        return self.questions.count()


class VocabularyQuestion(BaseMCQQuestion, TimeStampedModel, OrderedModel, UsageTypeMixin):
    """
    سؤال مفردات
    """
    question_set = models.ForeignKey(
        VocabularyQuestionSet,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name="مجموعة الأسئلة"
    )
    
    # ✅ إضافة question_bank
    placement_question_bank = models.ForeignKey(
        'placement_test.PlacementQuestionBank',
        on_delete=models.CASCADE,
        related_name='placement_vocabulary_questions',
        null=True,
        blank=True,
        verbose_name="بنك أسئلة Placement"
        )

    levels_units_question_bank = models.ForeignKey(
        'levels.LevelsUnitsQuestionBank',
        on_delete=models.CASCADE,
        related_name='levels_vocabulary_questions',
        null=True,
        blank=True,
        verbose_name="بنك أسئلة Levels/Units"
    )
    
    class Meta:
        verbose_name = "سؤال مفردات"
        verbose_name_plural = "أسئلة المفردات"
        ordering = ['order', 'created_at']
        indexes = [
            models.Index(fields=['usage_type', 'placement_test']),
        ]


# ============================================
# Grammar Questions (أسئلة القواعد)
# ============================================

class GrammarQuestionSet(TimeStampedModel, OrderedModel):
    """
    مجموعة أسئلة القواعد
    """
    title = models.CharField(max_length=200, verbose_name="عنوان المجموعة")
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="وصف المجموعة"
    )
    
    USAGE_TYPE_CHOICES = [
        ('QUESTION_BANK', 'Question Bank'),
        ('PLACEMENT', 'Placement Test'),
        ('STEP', 'Learning Step'),
        ('IELTS', 'IELTS Exam'),
        ('LEVEL', 'Level Test'),
        ('GENERAL', 'General Use'),
    ]
    
    usage_type = models.CharField(
        max_length=20,
        choices=USAGE_TYPE_CHOICES,
        default='QUESTION_BANK',
        verbose_name="نوع الاستخدام"
    )
    
    class Meta:
        verbose_name = "مجموعة أسئلة قواعد"
        verbose_name_plural = "مجموعات أسئلة القواعد"
        ordering = ['order', 'created_at']
    
    def __str__(self):
        return self.title
    
    def get_questions_count(self):
        """عدد الأسئلة"""
        return self.questions.count()


class GrammarQuestion(BaseMCQQuestion, TimeStampedModel, OrderedModel, UsageTypeMixin):
    """
    سؤال قواعد
    """
    question_set = models.ForeignKey(
        GrammarQuestionSet,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name="مجموعة الأسئلة"
    )
    
    # ✅ إضافة question_bank
    placement_question_bank = models.ForeignKey(
        'placement_test.PlacementQuestionBank',
        on_delete=models.CASCADE,
        related_name='placement_grammar_questions',
        null=True,
        blank=True,
        verbose_name="بنك أسئلة Placement"
        )

    levels_units_question_bank = models.ForeignKey(
        'levels.LevelsUnitsQuestionBank',
        on_delete=models.CASCADE,
        related_name='levels_grammar_questions',
        null=True,
        blank=True,
        verbose_name="بنك أسئلة Levels/Units"
    )
    class Meta:
        verbose_name = "سؤال قواعد"
        verbose_name_plural = "أسئلة القواعد"
        ordering = ['order', 'created_at']
        indexes = [
            models.Index(fields=['usage_type', 'placement_test']),
        ]


# ============================================
# Reading Questions (أسئلة القراءة)
# ============================================

class ReadingPassage(TimeStampedModel, OrderedModel, UsageTypeMixin):
    """
    قطعة القراءة
    """
    title = models.CharField(max_length=200, verbose_name="عنوان القطعة")
    passage_text = models.TextField(verbose_name="نص القطعة")
    passage_image = CloudinaryField(
        verbose_name="صورة القطعة",
        blank=True,
        null=True,
    )
    source = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="مصدر القطعة"
    )
    
    # ✅ إضافة question_bank
    placement_question_bank = models.ForeignKey(
        'placement_test.PlacementQuestionBank',
        on_delete=models.CASCADE,
        related_name='placement_reading_passages',
        null=True,
        blank=True,
        verbose_name="بنك أسئلة Placement"
    )

    levels_units_question_bank = models.ForeignKey(
        'levels.LevelsUnitsQuestionBank',
        on_delete=models.CASCADE,
        related_name='levels_reading_passages',
        null=True,
        blank=True,
        verbose_name="بنك أسئلة Levels/Units"
    )
        
    class Meta:
        verbose_name = "قطعة قراءة"
        verbose_name_plural = "قطع القراءة"
        ordering = ['order', 'created_at']
        indexes = [
            models.Index(fields=['usage_type', 'placement_test']),
        ]
    
    def __str__(self):
        return self.title
    
    def get_questions_count(self):
        """عدد الأسئلة"""
        return self.questions.count()


class ReadingQuestion(BaseMCQQuestion, TimeStampedModel, OrderedModel):
    """
    سؤال قراءة
    ملاحظة: لا يحتاج UsageTypeMixin لأنه مرتبط بالـ Passage
    """
    passage = models.ForeignKey(
        ReadingPassage,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name="القطعة"
    )
    
    class Meta:
        verbose_name = "سؤال قراءة"
        verbose_name_plural = "أسئلة القراءة"
        ordering = ['order', 'created_at']
    
    def get_usage_type(self):
        """الحصول على usage_type من الـ Passage"""
        return self.passage.usage_type
    
    def get_placement_test(self):
        """الحصول على placement_test من الـ Passage"""
        return self.passage.placement_test


# ============================================
# Listening Questions (أسئلة الاستماع)
# ============================================

class ListeningAudio(TimeStampedModel, OrderedModel, UsageTypeMixin):
    """
    التسجيل الصوتي
    """
    title = models.CharField(max_length=200, verbose_name="عنوان التسجيل")
    audio_file = CloudinaryField(
        verbose_name="ملف الصوت",
        resource_type='video',
        folder='listening/audio',
    )
    transcript = models.TextField(
        blank=True,
        null=True,
        verbose_name="النص الكتابي للتسجيل"
    )
    duration = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="المدة بالثواني",
        verbose_name="مدة التسجيل"
    )
    
    placement_question_bank = models.ForeignKey(
        'placement_test.PlacementQuestionBank',
        on_delete=models.CASCADE,
        related_name='placement_listening_audios',
        null=True,
        blank=True,
        verbose_name="بنك أسئلة Placement"
    )

    levels_units_question_bank = models.ForeignKey(
        'levels.LevelsUnitsQuestionBank',
        on_delete=models.CASCADE,
        related_name='levels_listening_audios',
        null=True,
        blank=True,
        verbose_name="بنك أسئلة Levels/Units"
    )
    class Meta:
        verbose_name = "تسجيل صوتي"
        verbose_name_plural = "التسجيلات الصوتية"
        ordering = ['order', 'created_at']
        indexes = [
            models.Index(fields=['usage_type', 'placement_test']),
        ]
    
    def __str__(self):
        return self.title
    
    def get_questions_count(self):
        """عدد الأسئلة"""
        return self.questions.count()


class ListeningQuestion(BaseMCQQuestion, TimeStampedModel, OrderedModel):
    """
    سؤال استماع
    """
    audio = models.ForeignKey(
        ListeningAudio,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name="التسجيل الصوتي"
    )
    
    class Meta:
        verbose_name = "سؤال استماع"
        verbose_name_plural = "أسئلة الاستماع"
        ordering = ['order', 'created_at']
    
    def get_usage_type(self):
        """الحصول على usage_type من الـ Audio"""
        return self.audio.usage_type
    
    def get_placement_test(self):
        """الحصول على placement_test من الـ Audio"""
        return self.audio.placement_test


# ============================================
# Speaking Questions (أسئلة التحدث)
# ============================================

class SpeakingVideo(TimeStampedModel, OrderedModel, UsageTypeMixin):
    """
    الفيديو التعليمي
    """
    title = models.CharField(max_length=200, verbose_name="عنوان الفيديو")
    video_file = CloudinaryField(
        verbose_name="ملف الفيديو",
        resource_type='video',
        folder='speaking/videos',
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="وصف الفيديو"
    )
    duration = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="المدة بالثواني",
        verbose_name="مدة الفيديو"
    )
    thumbnail = CloudinaryField(
        verbose_name="صورة مصغرة",
        blank=True,
        null=True,
        folder='speaking/thumbnails',
    )
    
    placement_question_bank = models.ForeignKey(
        'placement_test.PlacementQuestionBank',
        on_delete=models.CASCADE,
        related_name='placement_speaking_videos',
        null=True,
        blank=True,
        verbose_name="بنك أسئلة Placement"
    )

    levels_units_question_bank = models.ForeignKey(
        'levels.LevelsUnitsQuestionBank',
        on_delete=models.CASCADE,
        related_name='levels_speaking_videos',
        null=True,
        blank=True,
        verbose_name="بنك أسئلة Levels/Units")
    
    
    class Meta:
        verbose_name = "فيديو تحدث"
        verbose_name_plural = "فيديوهات التحدث"
        ordering = ['order', 'created_at']
        indexes = [
            models.Index(fields=['usage_type', 'placement_test']),
        ]
    
    def __str__(self):
        return self.title
    
    def get_questions_count(self):
        """عدد الأسئلة"""
        return self.questions.count()


class SpeakingQuestion(BaseMCQQuestion, TimeStampedModel, OrderedModel):
    """
    سؤال تحدث
    """
    video = models.ForeignKey(
        SpeakingVideo,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name="الفيديو"
    )
    
    class Meta:
        verbose_name = "سؤال تحدث"
        verbose_name_plural = "أسئلة التحدث"
        ordering = ['order', 'created_at']
    
    def get_usage_type(self):
        """الحصول على usage_type من الـ Video"""
        return self.video.usage_type
    
    def get_placement_test(self):
        """الحصول على placement_test من الـ Video"""
        return self.video.placement_test


# ============================================
# Writing Questions (أسئلة الكتابة)
# ============================================

class WritingQuestion(TimeStampedModel, OrderedModel, UsageTypeMixin):
    """
    سؤال كتابة
    """
    title = models.CharField(max_length=500, verbose_name="عنوان السؤال")
    question_text = models.TextField(verbose_name="نص السؤال")
    question_image = CloudinaryField(
        verbose_name="صورة السؤال",
        blank=True,
        null=True,
        folder='writing/images',
    )
    
    # متطلبات الإجابة
    min_words = models.PositiveIntegerField(
        default=100,
        verbose_name="الحد الأدنى للكلمات"
    )
    max_words = models.PositiveIntegerField(
        default=500,
        verbose_name="الحد الأقصى للكلمات"
    )
    
    # نموذج إجابة مقترح
    sample_answer = models.TextField(
        blank=True,
        null=True,
        verbose_name="نموذج إجابة"
    )
    
    # معايير التقييم
    rubric = models.TextField(
        blank=True,
        null=True,
        verbose_name="معايير التقييم",
        help_text="معايير تقييم الإجابة"
    )
    
    points = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name="النقاط",
        editable=False
    )
    
    # ✅ إضافة: نسبة النجاح (Pass Threshold)
    pass_threshold = models.PositiveIntegerField(
        default=60,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="نسبة النجاح المطلوبة (%)",
        help_text="النسبة المئوية المطلوبة لاعتبار الإجابة صحيحة (default: 60%)"
    )
    
    placement_question_bank = models.ForeignKey(
        'placement_test.PlacementQuestionBank',
        on_delete=models.CASCADE,
        related_name='placement_writing_questions',
        null=True,
        blank=True,
        verbose_name="بنك أسئلة Placement"
    )

    levels_units_question_bank = models.ForeignKey(
        'levels.LevelsUnitsQuestionBank',
        on_delete=models.CASCADE,
        related_name='levels_writing_questions',
        null=True,
        blank=True,
        verbose_name="بنك أسئلة Levels/Units")
    
    class Meta:
        verbose_name = "سؤال كتابة"
        verbose_name_plural = "أسئلة الكتابة"
        ordering = ['order', 'created_at']
        indexes = [
            models.Index(fields=['usage_type', 'placement_test']),
        ]
    
    def __str__(self):
        return self.title