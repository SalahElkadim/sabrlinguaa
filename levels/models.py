from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from cloudinary.models import CloudinaryField


# ============================================
# Original Course Models
# ============================================

class Level(models.Model):
    """A1, A2, B1, B2"""
    code = models.CharField(max_length=10)  # A1, A2, B1, B2
    name = models.CharField(max_length=100)
    description = models.TextField()
    
    class Meta:
        verbose_name = "مستوى"
        verbose_name_plural = "المستويات"
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class Unit(models.Model):
    """الوحدات الـ 13"""
    level = models.ForeignKey(Level, on_delete=models.CASCADE, related_name='units')
    title = models.CharField(max_length=200)
    number = models.IntegerField()  # Unit 1, 2, 3...
    
    class Meta:
        verbose_name = "وحدة"
        verbose_name_plural = "الوحدات"
        ordering = ['level', 'number']
    
    def __str__(self):
        return f"{self.level.code} - Unit {self.number}: {self.title}"


class Section(models.Model):
    """الأقسام جوا كل Unit"""
    SECTION_TYPES = [
        ('listening_speaking', 'Listening & Speaking'),
        ('grammar', 'Grammar'),
        ('reading', 'Reading'),
        ('vocabulary', 'Vocabulary'),
        ('writing', 'Writing'),
        ('interactive', 'Interactive Exercises'),
        ('quiz', 'Quiz'),
    ]
    
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='sections')
    section_type = models.CharField(max_length=50, choices=SECTION_TYPES)
    title = models.CharField(max_length=200)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        verbose_name = "قسم"
        verbose_name_plural = "الأقسام"
        ordering = ['unit', 'order']
    
    def __str__(self):
        return f"{self.unit} - {self.get_section_type_display()}"


class Lesson(models.Model):
    """المحتوى جوا كل Section"""
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=200)
    content = models.TextField(blank=True)
    file = CloudinaryField(blank=True, null=True)
    order = models.IntegerField()
    
    class Meta:
        verbose_name = "درس"
        verbose_name_plural = "الدروس"
        ordering = ['section', 'order']
    
    def __str__(self):
        return f"{self.section} - {self.title}"


class Exercise(models.Model):
    """التمارين"""
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='exercises')
    title = models.CharField(max_length=200, verbose_name="عنوان التمرين")
    description = models.TextField(blank=True, null=True, verbose_name="وصف التمرين")
    order = models.PositiveIntegerField(default=0, verbose_name="الترتيب")
    is_active = models.BooleanField(default=True, verbose_name="نشط")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")
    
    class Meta:
        verbose_name = "تمرين"
        verbose_name_plural = "التمارين"
        ordering = ['lesson', 'order']
    
    def __str__(self):
        return f"{self.lesson} - {self.title}"
    
    def get_total_points(self):
        """حساب مجموع النقاط الكلي للتمرين"""
        total = 0
        total += sum(q.points for q in self.mcq_questions.all())
        total += sum(q.points for passage in self.reading_passages.all() for q in passage.questions.all())
        total += sum(q.points for audio in self.listening_audios.all() for q in audio.questions.all())
        total += sum(q.points for video in self.speaking_videos.all() for q in video.questions.all())
        total += sum(q.points for q in self.writing_questions.all())
        return total
    
    def get_questions_count(self):
        """حساب عدد الأسئلة الكلي"""
        count = 0
        count += self.mcq_questions.count()
        count += sum(passage.questions.count() for passage in self.reading_passages.all())
        count += sum(audio.questions.count() for audio in self.listening_audios.all())
        count += sum(video.questions.count() for video in self.speaking_videos.all())
        count += self.writing_questions.count()
        return count


# ============================================
# Exercise MCQ Questions (للـ Grammar, Vocabulary, Quiz)
# ============================================

class ExerciseMCQQuestion(models.Model):
    """
    أسئلة الاختيار من متعدد للتمارين
    مناسبة لـ: Grammar, Vocabulary, Interactive, Quiz
    """
    exercise = models.ForeignKey(
        Exercise,
        on_delete=models.CASCADE,
        related_name='mcq_questions',
        verbose_name="التمرين"
    )
    
    question_text = models.TextField(verbose_name="نص السؤال")
    question_image = CloudinaryField(
        'image', 
        blank=True, 
        null=True,
        folder='exercises/mcq/images'
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
    
    order = models.PositiveIntegerField(default=0, verbose_name="الترتيب")
    is_active = models.BooleanField(default=True, verbose_name="نشط")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")
    
    class Meta:
        verbose_name = "سؤال MCQ للتمرين"
        verbose_name_plural = "أسئلة MCQ للتمارين"
        ordering = ['exercise', 'order', 'created_at']
    
    def __str__(self):
        return f"{self.exercise.title} - {self.question_text[:50]}"


# ============================================
# Exercise Reading Questions (للـ Reading)
# ============================================

class ExerciseReadingPassage(models.Model):
    """
    قطعة القراءة للتمرين
    مناسبة لـ: Reading, Quiz
    """
    exercise = models.ForeignKey(
        Exercise,
        on_delete=models.CASCADE,
        related_name='reading_passages',
        verbose_name="التمرين"
    )
    
    title = models.CharField(max_length=500, verbose_name="عنوان القطعة")
    passage_text = models.TextField(verbose_name="نص القطعة")
    passage_image = CloudinaryField(
        'image',
        blank=True,
        null=True,
        folder='exercises/reading/images'
    )
    source = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="مصدر القطعة"
    )
    
    order = models.PositiveIntegerField(default=0, verbose_name="الترتيب")
    is_active = models.BooleanField(default=True, verbose_name="نشط")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")
    
    class Meta:
        verbose_name = "قطعة قراءة للتمرين"
        verbose_name_plural = "قطع القراءة للتمارين"
        ordering = ['exercise', 'order', 'created_at']
    
    def __str__(self):
        return f"{self.exercise.title} - {self.title}"


class ExerciseReadingQuestion(models.Model):
    """
    سؤال قراءة للتمرين
    """
    passage = models.ForeignKey(
        ExerciseReadingPassage,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name="القطعة"
    )
    
    question_text = models.TextField(verbose_name="نص السؤال")
    question_image = CloudinaryField(
        'image', 
        blank=True, 
        null=True,
        folder='exercises/reading/questions/images'
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
    
    order = models.PositiveIntegerField(default=0, verbose_name="الترتيب")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")
    
    class Meta:
        verbose_name = "سؤال قراءة للتمرين"
        verbose_name_plural = "أسئلة القراءة للتمارين"
        ordering = ['order', 'created_at']
    
    def __str__(self):
        return f"{self.passage.title} - {self.question_text[:50]}"


# ============================================
# Exercise Listening Questions (للـ Listening & Speaking)
# ============================================

class ExerciseListeningAudio(models.Model):
    """
    التسجيل الصوتي للتمرين
    مناسب لـ: Listening & Speaking, Quiz
    """
    exercise = models.ForeignKey(
        Exercise,
        on_delete=models.CASCADE,
        related_name='listening_audios',
        verbose_name="التمرين"
    )
    
    title = models.CharField(max_length=500, verbose_name="عنوان التسجيل")
    audio_file = CloudinaryField(
        'video',
        resource_type='video',
        folder='exercises/listening/audio'
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
    
    order = models.PositiveIntegerField(default=0, verbose_name="الترتيب")
    is_active = models.BooleanField(default=True, verbose_name="نشط")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")
    
    class Meta:
        verbose_name = "تسجيل صوتي للتمرين"
        verbose_name_plural = "التسجيلات الصوتية للتمارين"
        ordering = ['exercise', 'order', 'created_at']
    
    def __str__(self):
        return f"{self.exercise.title} - {self.title}"


class ExerciseListeningQuestion(models.Model):
    """
    سؤال استماع للتمرين
    """
    audio = models.ForeignKey(
        ExerciseListeningAudio,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name="التسجيل الصوتي"
    )
    
    question_text = models.TextField(verbose_name="نص السؤال")
    question_image = CloudinaryField(
        'image', 
        blank=True, 
        null=True,
        folder='exercises/listening/questions/images'
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
    
    order = models.PositiveIntegerField(default=0, verbose_name="الترتيب")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")
    
    class Meta:
        verbose_name = "سؤال استماع للتمرين"
        verbose_name_plural = "أسئلة الاستماع للتمارين"
        ordering = ['order', 'created_at']
    
    def __str__(self):
        return f"{self.audio.title} - {self.question_text[:50]}"


# ============================================
# Exercise Speaking Questions (للـ Listening & Speaking)
# ============================================

class ExerciseSpeakingVideo(models.Model):
    """
    الفيديو التعليمي للتمرين
    مناسب لـ: Listening & Speaking, Quiz
    """
    exercise = models.ForeignKey(
        Exercise,
        on_delete=models.CASCADE,
        related_name='speaking_videos',
        verbose_name="التمرين"
    )
    
    title = models.CharField(max_length=500, verbose_name="عنوان الفيديو")
    video_file = CloudinaryField(
        'video',
        resource_type='video',
        folder='exercises/speaking/videos'
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
        folder='exercises/speaking/thumbnails'
    )
    
    order = models.PositiveIntegerField(default=0, verbose_name="الترتيب")
    is_active = models.BooleanField(default=True, verbose_name="نشط")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")
    
    class Meta:
        verbose_name = "فيديو تحدث للتمرين"
        verbose_name_plural = "فيديوهات التحدث للتمارين"
        ordering = ['exercise', 'order', 'created_at']
    
    def __str__(self):
        return f"{self.exercise.title} - {self.title}"


class ExerciseSpeakingQuestion(models.Model):
    """
    سؤال تحدث للتمرين
    """
    video = models.ForeignKey(
        ExerciseSpeakingVideo,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name="الفيديو"
    )
    
    question_text = models.TextField(verbose_name="نص السؤال")
    question_image = CloudinaryField(
        'image', 
        blank=True, 
        null=True,
        folder='exercises/speaking/questions/images'
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
    
    order = models.PositiveIntegerField(default=0, verbose_name="الترتيب")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")
    
    class Meta:
        verbose_name = "سؤال تحدث للتمرين"
        verbose_name_plural = "أسئلة التحدث للتمارين"
        ordering = ['order', 'created_at']
    
    def __str__(self):
        return f"{self.video.title} - {self.question_text[:50]}"


# ============================================
# Exercise Writing Questions (للـ Writing)
# ============================================

class ExerciseWritingQuestion(models.Model):
    """
    سؤال كتابة للتمرين
    مناسب لـ: Writing, Quiz
    """
    exercise = models.ForeignKey(
        Exercise,
        on_delete=models.CASCADE,
        related_name='writing_questions',
        verbose_name="التمرين"
    )
    
    title = models.CharField(max_length=500, verbose_name="عنوان السؤال")
    question_text = models.TextField(verbose_name="نص السؤال")
    question_image = CloudinaryField(
        'image',
        blank=True,
        null=True,
        folder='exercises/writing/images'
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
        verbose_name = "سؤال كتابة للتمرين"
        verbose_name_plural = "أسئلة الكتابة للتمارين"
        ordering = ['exercise', 'order', 'created_at']
    
    def __str__(self):
        return f"{self.exercise.title} - {self.title}"