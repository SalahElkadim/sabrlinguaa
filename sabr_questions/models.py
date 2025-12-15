from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from cloudinary.models import CloudinaryField


# ============================================
# Placement Test Model
# ============================================

class PlacementTest(models.Model):
    """
    نموذج امتحان تحديد المستوى
    """
    title = models.CharField(max_length=200, verbose_name="عنوان الامتحان")
    description = models.TextField(blank=True, null=True, verbose_name="وصف الامتحان")
    
    # المدة الزمنية
    duration_minutes = models.PositiveIntegerField(
        verbose_name="مدة الامتحان (بالدقائق)",
        help_text="المدة الزمنية المحددة لإنهاء الامتحان"
    )
    
    # درجات النجاح للمستويات
    a1_min_score = models.PositiveIntegerField(
        default=0,
        verbose_name="الحد الأدنى لمستوى A1",
        help_text="من 0 إلى هذه الدرجة = A1"
    )
    a2_min_score = models.PositiveIntegerField(
        verbose_name="الحد الأدنى لمستوى A2",
        help_text="من الدرجة السابقة إلى هذه الدرجة = A2"
    )
    b1_min_score = models.PositiveIntegerField(
        verbose_name="الحد الأدنى لمستوى B1",
        help_text="من الدرجة السابقة إلى هذه الدرجة = B1"
    )
    b2_min_score = models.PositiveIntegerField(
        verbose_name="الحد الأدنى لمستوى B2",
        help_text="من الدرجة السابقة فما فوق = B2"
    )
    
    # الحالة
    is_active = models.BooleanField(default=False, verbose_name="نشط")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")
    
    class Meta:
        verbose_name = "امتحان تحديد المستوى"
        verbose_name_plural = "امتحانات تحديد المستوى"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def get_total_points(self):
        """حساب مجموع النقاط الكلي للامتحان"""
        total = 0
        
        # MCQ Questions
        for mcq_set in self.mcq_sets.all():
            total += sum(q.points for q in mcq_set.questions.all())
        
        # Reading Questions
        for passage in self.reading_passages.all():
            total += sum(q.points for q in passage.questions.all())
        
        # Listening Questions
        for audio in self.listening_audios.all():
            total += sum(q.points for q in audio.questions.all())
        
        # Speaking Questions
        for video in self.speaking_videos.all():
            total += sum(q.points for q in video.questions.all())
        
        # Writing Questions
        total += sum(q.points for q in self.writing_questions.all())
        
        return total
    
    def get_questions_count(self):
        """حساب عدد الأسئلة الكلي"""
        count = 0
        count += sum(mcq_set.questions.count() for mcq_set in self.mcq_sets.all())
        count += sum(passage.questions.count() for passage in self.reading_passages.all())
        count += sum(audio.questions.count() for audio in self.listening_audios.all())
        count += sum(video.questions.count() for video in self.speaking_videos.all())
        count += self.writing_questions.count()
        return count


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
    placement_test = models.ForeignKey(
        PlacementTest,
        on_delete=models.CASCADE,
        related_name='mcq_sets',
        verbose_name="امتحان تحديد المستوى"
    )
    description = models.TextField(
        blank=True, 
        null=True,
        verbose_name="وصف المجموعة"
    )
    
    class Meta:
        verbose_name = "مجموعة أسئلة MCQ"
        verbose_name_plural = "مجموعات أسئلة MCQ"
        ordering = ['placement_test', 'order', 'created_at']


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
    placement_test = models.ForeignKey(
        PlacementTest,
        on_delete=models.CASCADE,
        related_name='reading_passages',
        verbose_name="امتحان تحديد المستوى",
        blank=True,
        null=True
    )
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
    
    class Meta:
        verbose_name = "قطعة قراءة"
        verbose_name_plural = "قطع القراءة"
        ordering = ['placement_test', 'order', 'created_at']


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
    placement_test = models.ForeignKey(
        PlacementTest,
        on_delete=models.CASCADE,
        related_name='listening_audios',
        verbose_name="امتحان تحديد المستوى",
        blank=True,
        null=True
    )
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
    
    class Meta:
        verbose_name = "تسجيل صوتي"
        verbose_name_plural = "التسجيلات الصوتية"
        ordering = ['placement_test', 'order', 'created_at']


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
    placement_test = models.ForeignKey(
        PlacementTest,
        on_delete=models.CASCADE,
        related_name='speaking_videos',
        verbose_name="امتحان تحديد المستوى",
        blank=True,
        null=True
    )
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
        ordering = ['placement_test', 'order', 'created_at']


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
    placement_test = models.ForeignKey(
        PlacementTest,
        on_delete=models.CASCADE,
        related_name='writing_questions',
        verbose_name="امتحان تحديد المستوى",
        blank=True,
        null=True
    )
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
    
    order = models.PositiveIntegerField(default=0, verbose_name="الترتيب")
    is_active = models.BooleanField(default=True, verbose_name="نشط")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")
    
    class Meta:
        verbose_name = "سؤال كتابة"
        verbose_name_plural = "أسئلة الكتابة"
        ordering = ['placement_test', 'order', 'created_at']
    
    def __str__(self):
        return self.title