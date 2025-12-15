from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from cloudinary.models import CloudinaryField


# ============================================
# Abstract Base Models (النماذج الأساسية)
# ============================================

class BaseQuestion(models.Model):
    """
    نموذج أساسي مشترك لكل الأسئلة
    """
    title = models.CharField(max_length=500, verbose_name="عنوان السؤال")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")
    order = models.PositiveIntegerField(default=0, verbose_name="الترتيب")
    is_active = models.BooleanField(default=True, verbose_name="نشط")
    
    class Meta:
        abstract = True
        ordering = ['order', 'created_at']
    
    def __str__(self):
        return self.title


class BaseMCQQuestion(models.Model):
    """
    نموذج أساسي لأسئلة الاختيار من متعدد
    """
    question_text = models.TextField(verbose_name="نص السؤال")
    question_image = CloudinaryField(
        'image', 
        blank=True, 
        null=True,
        folder='questions/images'
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
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True
    
    def __str__(self):
        return self.question_text[:50]


# ============================================
# MCQ Questions (أسئلة الاختيار من متعدد المستقلة)
# ============================================

class MCQQuestionSet(BaseQuestion):
    """
    مجموعة أسئلة MCQ (النموذج الأب)
    """
    description = models.TextField(
        blank=True, 
        null=True,
        verbose_name="وصف المجموعة"
    )
    
    class Meta:
        verbose_name = "مجموعة أسئلة MCQ"
        verbose_name_plural = "مجموعات أسئلة MCQ"


class MCQQuestion(BaseMCQQuestion):
    """
    سؤال MCQ فردي (النموذج الابن)
    """
    question_set = models.ForeignKey(
        MCQQuestionSet,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name="مجموعة الأسئلة"
    )
    order = models.PositiveIntegerField(default=0, verbose_name="الترتيب")
    
    class Meta:
        verbose_name = "سؤال MCQ"
        verbose_name_plural = "أسئلة MCQ"
        ordering = ['order', 'created_at']


# ============================================
# Reading Questions (أسئلة القراءة)
# ============================================

class ReadingPassage(BaseQuestion):
    """
    قطعة القراءة (النموذج الأب)
    """
    passage_text = models.TextField(verbose_name="نص القطعة")
    passage_image = CloudinaryField(
        'image',
        blank=True,
        null=True,
        folder='reading/images'
    )
    source = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="مصدر القطعة"
    )
    difficulty_level = models.CharField(
        max_length=20,
        choices=[
            ('beginner', 'مبتدئ'),
            ('intermediate', 'متوسط'),
            ('advanced', 'متقدم'),
        ],
        default='intermediate',
        verbose_name="مستوى الصعوبة"
    )
    
    class Meta:
        verbose_name = "قطعة قراءة"
        verbose_name_plural = "قطع القراءة"


class ReadingQuestion(BaseMCQQuestion):
    """
    سؤال قراءة (النموذج الابن)
    """
    passage = models.ForeignKey(
        ReadingPassage,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name="القطعة"
    )
    order = models.PositiveIntegerField(default=0, verbose_name="الترتيب")
    
    class Meta:
        verbose_name = "سؤال قراءة"
        verbose_name_plural = "أسئلة القراءة"
        ordering = ['order', 'created_at']


# ============================================
# Listening Questions (أسئلة الاستماع)
# ============================================

class ListeningAudio(BaseQuestion):
    """
    التسجيل الصوتي (النموذج الأب)
    """
    audio_file = CloudinaryField(
        'video',
        resource_type='video',
        folder='listening/audio'
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
    difficulty_level = models.CharField(
        max_length=20,
        choices=[
            ('beginner', 'مبتدئ'),
            ('intermediate', 'متوسط'),
            ('advanced', 'متقدم'),
        ],
        default='intermediate',
        verbose_name="مستوى الصعوبة"
    )
    
    class Meta:
        verbose_name = "تسجيل صوتي"
        verbose_name_plural = "التسجيلات الصوتية"


class ListeningQuestion(BaseMCQQuestion):
    """
    سؤال استماع (النموذج الابن)
    """
    audio = models.ForeignKey(
        ListeningAudio,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name="التسجيل الصوتي"
    )
    order = models.PositiveIntegerField(default=0, verbose_name="الترتيب")
    
    class Meta:
        verbose_name = "سؤال استماع"
        verbose_name_plural = "أسئلة الاستماع"
        ordering = ['order', 'created_at']


# ============================================
# Speaking Questions (أسئلة التحدث)
# ============================================

class SpeakingVideo(BaseQuestion):
    """
    الفيديو التعليمي (النموذج الأب)
    """
    video_file = CloudinaryField(
        'video',
        resource_type='video',
        folder='speaking/videos'
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
        'image',
        blank=True,
        null=True,
        folder='speaking/thumbnails'
    )
    
    class Meta:
        verbose_name = "فيديو تحدث"
        verbose_name_plural = "فيديوهات التحدث"


class SpeakingQuestion(BaseMCQQuestion):
    """
    سؤال تحدث (النموذج الابن)
    """
    video = models.ForeignKey(
        SpeakingVideo,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name="الفيديو"
    )
    order = models.PositiveIntegerField(default=0, verbose_name="الترتيب")
    
    class Meta:
        verbose_name = "سؤال تحدث"
        verbose_name_plural = "أسئلة التحدث"
        ordering = ['order', 'created_at']


# ============================================
# Writing Questions (أسئلة الكتابة)
# ============================================

class WritingQuestion(models.Model):
    """
    سؤال كتابة (نموذج مستقل بدون أب)
    """
    title = models.CharField(max_length=500, verbose_name="عنوان السؤال")
    question_text = models.TextField(verbose_name="نص السؤال")
    question_image = CloudinaryField(
        'image',
        blank=True,
        null=True,
        folder='writing/images'
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
        default=10,
        validators=[MinValueValidator(1)],
        verbose_name="النقاط"
    )
    
    difficulty_level = models.CharField(
        max_length=20,
        choices=[
            ('beginner', 'مبتدئ'),
            ('intermediate', 'متوسط'),
            ('advanced', 'متقدم'),
        ],
        default='intermediate',
        verbose_name="مستوى الصعوبة"
    )
    
    order = models.PositiveIntegerField(default=0, verbose_name="الترتيب")
    is_active = models.BooleanField(default=True, verbose_name="نشط")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")
    
    class Meta:
        verbose_name = "سؤال كتابة"
        verbose_name_plural = "أسئلة الكتابة"
        ordering = ['order', 'created_at']
    
    def __str__(self):
        return self.title