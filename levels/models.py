from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model
from cloudinary.models import CloudinaryField

User = get_user_model()


# ============================================
# Abstract Base Models (من sabr_questions)
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
# Level System Models
# ============================================

class Level(TimeStampedModel, OrderedModel):
    """
    المستوى التعليمي (A1, A2, B1, B2)
    """
    LEVEL_CHOICES = [
        ('A1', 'A1 - Beginner'),
        ('A2', 'A2 - Elementary'),
        ('B1', 'B1 - Intermediate'),
        ('B2', 'B2 - Upper Intermediate'),
    ]
    
    code = models.CharField(
        max_length=2,
        choices=LEVEL_CHOICES,
        unique=True,
        verbose_name="كود المستوى"
    )
    title = models.CharField(max_length=200, verbose_name="عنوان المستوى")
    description = models.TextField(blank=True, null=True, verbose_name="وصف المستوى")
    
    class Meta:
        verbose_name = "مستوى تعليمي"
        verbose_name_plural = "المستويات التعليمية"
        ordering = ['order', 'code']
    
    def __str__(self):
        return f"{self.code} - {self.title}"
    
    def get_units_count(self):
        """عدد الوحدات"""
        return self.units.filter(is_active=True).count()
    
    def get_total_lessons(self):
        """إجمالي عدد الدروس في المستوى"""
        return sum(unit.get_lessons_count() for unit in self.units.filter(is_active=True))
    
    def save(self, *args, **kwargs):
        """عند إنشاء Level جديد، ننشئ LevelExam تلقائياً"""
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new:
            # إنشاء LevelExam تلقائياً
            LevelExam.objects.get_or_create(
                level=self,
                defaults={
                    'title': f"{self.code} - Level Exam",
                    'time_limit': 60,
                    'vocabulary_count': 12,
                    'grammar_count': 12,
                    'reading_questions_count': 20,
                    'listening_questions_count': 6,
                    'speaking_questions_count': 5,
                    'writing_questions_count': 5
                }
            )


class Unit(TimeStampedModel, OrderedModel):
    """
    الوحدة الدراسية
    """
    level = models.ForeignKey(
        Level,
        on_delete=models.CASCADE,
        related_name='units',
        verbose_name="المستوى"
    )
    title = models.CharField(max_length=200, verbose_name="عنوان الوحدة")
    description = models.TextField(blank=True, null=True, verbose_name="وصف الوحدة")
    
    class Meta:
        verbose_name = "وحدة دراسية"
        verbose_name_plural = "الوحدات الدراسية"
        ordering = ['level', 'order', 'id']
        unique_together = ['level', 'order']
    
    def __str__(self):
        return f"{self.level.code} - {self.title}"
    
    def get_lessons(self):
        """جميع الدروس النشطة"""
        return self.lessons.filter(is_active=True)
    
    def get_lessons_count(self):
        """عدد الدروس"""
        return self.lessons.filter(is_active=True).count()
    
    def save(self, *args, **kwargs):
        """عند إنشاء Unit جديد، ننشئ UnitExam تلقائياً"""
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new:
            # إنشاء UnitExam تلقائياً
            UnitExam.objects.get_or_create(
                unit=self,
                defaults={
                    'title': f"{self.title} - Final Exam",
                    'time_limit': 35,
                    'vocabulary_count': 8,
                    'grammar_count': 8,
                    'reading_questions_count': 10,
                    'listening_questions_count': 3,
                    'speaking_questions_count': 3,
                    'writing_questions_count': 3
                }
            )


class Lesson(TimeStampedModel, OrderedModel):
    """
    الدرس
    """
    LESSON_TYPE_CHOICES = [
        ('READING', 'Reading'),
        ('LISTENING', 'Listening'),
        ('SPEAKING', 'Speaking'),
        ('WRITING', 'Writing'),
    ]
    
    unit = models.ForeignKey(
        Unit,
        on_delete=models.CASCADE,
        related_name='lessons',
        verbose_name="الوحدة"
    )
    lesson_type = models.CharField(
        max_length=20,
        choices=LESSON_TYPE_CHOICES,
        verbose_name="نوع الدرس"
    )
    title = models.CharField(max_length=200, verbose_name="عنوان الدرس")
    
    class Meta:
        verbose_name = "درس"
        verbose_name_plural = "الدروس"
        ordering = ['unit', 'order', 'id']
        unique_together = ['unit', 'order']
    
    def __str__(self):
        return f"{self.unit.title} - {self.get_lesson_type_display()}: {self.title}"
    
    def get_content(self):
        """الحصول على المحتوى حسب نوع الدرس"""
        if self.lesson_type == 'READING':
            return getattr(self, 'reading_content', None)
        elif self.lesson_type == 'LISTENING':
            return getattr(self, 'listening_content', None)
        elif self.lesson_type == 'SPEAKING':
            return getattr(self, 'speaking_content', None)
        elif self.lesson_type == 'WRITING':
            return getattr(self, 'writing_content', None)
        return None


# ============================================
# Lesson Content Models
# ============================================

class ReadingLessonContent(TimeStampedModel):
    """
    محتوى درس القراءة
    """
    lesson = models.OneToOneField(
        Lesson,
        on_delete=models.CASCADE,
        related_name='reading_content',
        verbose_name="الدرس",
        limit_choices_to={'lesson_type': 'READING'}
    )
    
    # القطعة الأساسية (من sabr_questions)
    passage = models.ForeignKey(
        'sabr_questions.ReadingPassage',
        on_delete=models.CASCADE,
        verbose_name="القطعة",
        help_text="القطعة تحتوي على: العنوان، النص، الصورة، الأسئلة المحلولة"
    )
    
    # المفردات الخاصة بالدرس
    vocabulary_words = models.JSONField(
        default=list,
        blank=True,
        verbose_name="المفردات",
        help_text='مثال: [{"english_word": "dog", "translate": "كلب"}]'
    )
    
    # شرح عام عن الدرس
    explanation = models.TextField(
        blank=True,
        null=True,
        verbose_name="شرح الدرس"
    )
    
    class Meta:
        verbose_name = "محتوى درس قراءة"
        verbose_name_plural = "محتويات دروس القراءة"
    
    def __str__(self):
        return f"Reading Content: {self.lesson.title}"


class ListeningLessonContent(TimeStampedModel):
    """
    محتوى درس الاستماع
    """
    lesson = models.OneToOneField(
        Lesson,
        on_delete=models.CASCADE,
        related_name='listening_content',
        verbose_name="الدرس",
        limit_choices_to={'lesson_type': 'LISTENING'}
    )
    
    # التسجيل الصوتي (من sabr_questions)
    audio = models.ForeignKey(
        'sabr_questions.ListeningAudio',
        on_delete=models.CASCADE,
        verbose_name="التسجيل الصوتي",
        help_text="يحتوي على: العنوان، الملف الصوتي، النص، الأسئلة المحلولة"
    )
    
    # شرح عام عن الدرس
    explanation = models.TextField(
        blank=True,
        null=True,
        verbose_name="شرح الدرس"
    )
    
    class Meta:
        verbose_name = "محتوى درس استماع"
        verbose_name_plural = "محتويات دروس الاستماع"
    
    def __str__(self):
        return f"Listening Content: {self.lesson.title}"


class SpeakingLessonContent(TimeStampedModel):
    """
    محتوى درس التحدث
    """
    lesson = models.OneToOneField(
        Lesson,
        on_delete=models.CASCADE,
        related_name='speaking_content',
        verbose_name="الدرس",
        limit_choices_to={'lesson_type': 'SPEAKING'}
    )
    
    # الفيديو التعليمي (من sabr_questions)
    video = models.ForeignKey(
        'sabr_questions.SpeakingVideo',
        on_delete=models.CASCADE,
        verbose_name="الفيديو",
        help_text="يحتوي على: العنوان، الفيديو، النص، الأسئلة المحلولة"
    )
    
    # شرح عام عن الدرس
    explanation = models.TextField(
        blank=True,
        null=True,
        verbose_name="شرح الدرس"
    )
    
    class Meta:
        verbose_name = "محتوى درس تحدث"
        verbose_name_plural = "محتويات دروس التحدث"
    
    def __str__(self):
        return f"Speaking Content: {self.lesson.title}"


class WritingLessonContent(TimeStampedModel):
    """
    محتوى درس الكتابة
    """
    lesson = models.OneToOneField(
        Lesson,
        on_delete=models.CASCADE,
        related_name='writing_content',
        verbose_name="الدرس",
        limit_choices_to={'lesson_type': 'WRITING'}
    )
    
    title = models.CharField(max_length=500, verbose_name="عنوان المحتوى")
    
    # قطعة كتابية (نموذج/مثال)
    writing_passage = models.TextField(
        verbose_name="قطعة كتابية نموذجية",
        help_text="مثال أو نموذج للطالب"
    )
    
    # تعليمات الكتابة
    instructions = models.TextField(
        verbose_name="تعليمات الكتابة",
        help_text="إرشادات وتوجيهات للطالب"
    )
    
    # نموذج إجابة (اختياري)
    sample_answer = models.TextField(
        blank=True,
        null=True,
        verbose_name="نموذج إجابة"
    )
    
    class Meta:
        verbose_name = "محتوى درس كتابة"
        verbose_name_plural = "محتويات دروس الكتابة"
    
    def __str__(self):
        return f"Writing Content: {self.lesson.title}"


# ============================================
# Exam Models
# ============================================

class UnitExam(TimeStampedModel, OrderedModel):
    """
    امتحان نهاية الوحدة
    """
    unit = models.OneToOneField(
        Unit,
        on_delete=models.CASCADE,
        related_name='exam',
        verbose_name="الوحدة"
    )
    
    title = models.CharField(
        max_length=200,
        verbose_name="عنوان الامتحان",
        default="Unit Exam"
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="وصف الامتحان"
    )
    instructions = models.TextField(
        blank=True,
        null=True,
        verbose_name="تعليمات الامتحان"
    )
    
    # ⏱️ الوقت المخصص (بالدقائق)
    time_limit = models.PositiveIntegerField(
        default=35,
        verbose_name="الوقت المخصص (دقيقة)",
        help_text="سؤال واحد = دقيقة واحدة"
    )
    
    # 🎯 نسبة النجاح (ثابتة 70%)
    passing_score = models.PositiveIntegerField(
        default=70,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="نسبة النجاح (%)",
        editable=False
    )
    
    # 📊 عدد الأسئلة من كل نوع (Total = 35)
    vocabulary_count = models.PositiveIntegerField(
        default=8,
        validators=[MinValueValidator(0)],
        verbose_name="عدد أسئلة المفردات"
    )
    grammar_count = models.PositiveIntegerField(
        default=8,
        validators=[MinValueValidator(0)],
        verbose_name="عدد أسئلة القواعد"
    )
    reading_questions_count = models.PositiveIntegerField(
        default=10,
        validators=[MinValueValidator(0)],
        verbose_name="عدد أسئلة القراءة",
        help_text="سيتم اختيار قطع قراءة تحتوي على هذا العدد من الأسئلة تقريباً"
    )
    listening_questions_count = models.PositiveIntegerField(
        default=3,
        validators=[MinValueValidator(0)],
        verbose_name="عدد أسئلة الاستماع"
    )
    speaking_questions_count = models.PositiveIntegerField(
        default=3,
        validators=[MinValueValidator(0)],
        verbose_name="عدد أسئلة التحدث"
    )
    writing_questions_count = models.PositiveIntegerField(
        default=3,
        validators=[MinValueValidator(0)],
        verbose_name="عدد أسئلة الكتابة"
    )
    
    class Meta:
        verbose_name = "امتحان وحدة"
        verbose_name_plural = "امتحانات الوحدات"
        ordering = ['unit__level', 'unit__order']
    
    def __str__(self):
        return f"{self.unit.level.code} - {self.unit.title} - Exam"
    
    def get_total_questions(self):
        """إجمالي عدد الأسئلة"""
        return (
            self.vocabulary_count +
            self.grammar_count +
            self.reading_questions_count +
            self.listening_questions_count +
            self.speaking_questions_count +
            self.writing_questions_count
        )


class LevelExam(TimeStampedModel, OrderedModel):
    """
    امتحان نهاية المستوى
    """
    level = models.OneToOneField(
        Level,
        on_delete=models.CASCADE,
        related_name='exam',
        verbose_name="المستوى"
    )
    
    title = models.CharField(
        max_length=200,
        verbose_name="عنوان الامتحان",
        default="Level Exam"
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="وصف الامتحان"
    )
    instructions = models.TextField(
        blank=True,
        null=True,
        verbose_name="تعليمات الامتحان"
    )
    
    # ⏱️ الوقت المخصص (بالدقائق)
    time_limit = models.PositiveIntegerField(
        default=60,
        verbose_name="الوقت المخصص (دقيقة)"
    )
    
    # 🎯 نسبة النجاح (ثابتة 70%)
    passing_score = models.PositiveIntegerField(
        default=70,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="نسبة النجاح (%)",
        editable=False
    )
    
    # 📊 عدد الأسئلة من كل نوع (Total = 60)
    vocabulary_count = models.PositiveIntegerField(
        default=12,
        validators=[MinValueValidator(0)],
        verbose_name="عدد أسئلة المفردات"
    )
    grammar_count = models.PositiveIntegerField(
        default=12,
        validators=[MinValueValidator(0)],
        verbose_name="عدد أسئلة القواعد"
    )
    reading_questions_count = models.PositiveIntegerField(
        default=20,
        validators=[MinValueValidator(0)],
        verbose_name="عدد أسئلة القراءة"
    )
    listening_questions_count = models.PositiveIntegerField(
        default=6,
        validators=[MinValueValidator(0)],
        verbose_name="عدد أسئلة الاستماع"
    )
    speaking_questions_count = models.PositiveIntegerField(
        default=5,
        validators=[MinValueValidator(0)],
        verbose_name="عدد أسئلة التحدث"
    )
    writing_questions_count = models.PositiveIntegerField(
        default=5,
        validators=[MinValueValidator(0)],
        verbose_name="عدد أسئلة الكتابة"
    )
    
    class Meta:
        verbose_name = "امتحان مستوى"
        verbose_name_plural = "امتحانات المستويات"
        ordering = ['level__order']
    
    def __str__(self):
        return f"{self.level.code} - Level Exam"
    
    def get_total_questions(self):
        """إجمالي عدد الأسئلة"""
        return (
            self.vocabulary_count +
            self.grammar_count +
            self.reading_questions_count +
            self.listening_questions_count +
            self.speaking_questions_count +
            self.writing_questions_count
        )


# ============================================
# Student Progress Models
# ============================================

class StudentLevel(TimeStampedModel):
    """
    تتبع تقدم الطالب في المستوى
    """
    STATUS_CHOICES = [
        ('LOCKED', 'Locked'),           # مقفل
        ('IN_PROGRESS', 'In Progress'), # جاري
        ('COMPLETED', 'Completed'),     # مكتمل
    ]
    
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='student_levels',
        verbose_name="الطالب"
    )
    level = models.ForeignKey(
        Level,
        on_delete=models.CASCADE,
        related_name='student_progress',
        verbose_name="المستوى"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='LOCKED',
        verbose_name="الحالة"
    )
    
    # الوحدة الحالية
    current_unit = models.ForeignKey(
        Unit,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="الوحدة الحالية"
    )
    
    started_at = models.DateTimeField(null=True, blank=True, verbose_name="تاريخ البدء")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="تاريخ الإكمال")
    
    class Meta:
        verbose_name = "تقدم الطالب في المستوى"
        verbose_name_plural = "تقدم الطلاب في المستويات"
        unique_together = ['student', 'level']
        ordering = ['student', 'level__order']
    
    def __str__(self):
        return f"{self.student.email} - {self.level.code} ({self.get_status_display()})"


class StudentUnit(TimeStampedModel):
    """
    تتبع تقدم الطالب في الوحدة
    """
    STATUS_CHOICES = [
        ('LOCKED', 'Locked'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
    ]
    
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='student_units',
        verbose_name="الطالب"
    )
    unit = models.ForeignKey(
        Unit,
        on_delete=models.CASCADE,
        related_name='student_progress',
        verbose_name="الوحدة"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='LOCKED',
        verbose_name="الحالة"
    )
    
    # عدد الدروس المكتملة
    lessons_completed = models.PositiveIntegerField(
        default=0,
        verbose_name="الدروس المكتملة"
    )
    
    # هل نجح في امتحان الوحدة؟
    exam_passed = models.BooleanField(
        default=False,
        verbose_name="نجح في الامتحان"
    )
    
    started_at = models.DateTimeField(null=True, blank=True, verbose_name="تاريخ البدء")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="تاريخ الإكمال")
    
    class Meta:
        verbose_name = "تقدم الطالب في الوحدة"
        verbose_name_plural = "تقدم الطلاب في الوحدات"
        unique_together = ['student', 'unit']
        ordering = ['student', 'unit__level', 'unit__order']
    
    def __str__(self):
        return f"{self.student.email} - {self.unit.title} ({self.get_status_display()})"


class StudentLesson(TimeStampedModel):
    """
    تتبع إكمال الدروس
    """
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='student_lessons',
        verbose_name="الطالب"
    )
    lesson = models.ForeignKey(
        Lesson,
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
        verbose_name = "تقدم الطالب في الدرس"
        verbose_name_plural = "تقدم الطلاب في الدروس"
        unique_together = ['student', 'lesson']
        ordering = ['student', 'lesson__unit', 'lesson__order']
    
    def __str__(self):
        status = "✓" if self.is_completed else "✗"
        return f"{status} {self.student.email} - {self.lesson.title}"


class StudentUnitExamAttempt(TimeStampedModel):
    """
    محاولات الطالب في امتحان الوحدة
    """
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='unit_exam_attempts',
        verbose_name="الطالب"
    )
    unit_exam = models.ForeignKey(
        UnitExam,
        on_delete=models.CASCADE,
        related_name='attempts',
        verbose_name="امتحان الوحدة"
    )
    
    attempt_number = models.PositiveIntegerField(
        verbose_name="رقم المحاولة",
        validators=[MinValueValidator(1)]
    )
    
    # الأسئلة المولّدة للطالب (IDs)
    generated_questions = models.JSONField(
        default=dict,
        verbose_name="الأسئلة المولّدة",
        help_text="""
        {
            "vocabulary_questions": [1, 5, 8, ...],
            "grammar_questions": [2, 4, 9, ...],
            "reading_passages": [3, 7],
            "listening_audios": [6],
            "speaking_videos": [10],
            "writing_questions": [11]
        }
        """
    )
    
    # إجابات الطالب
    answers = models.JSONField(
        default=dict,
        verbose_name="الإجابات",
        help_text="""
        {
            "vocabulary_1": "A",
            "grammar_2": "B",
            "reading_3_1": "C",
            "writing_11": "text of student answer..."
        }
        """
    )
    
    # النتيجة
    score = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="الدرجة (من 100)"
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
        verbose_name = "محاولة امتحان وحدة"
        verbose_name_plural = "محاولات امتحانات الوحدات"
        unique_together = ['student', 'unit_exam', 'attempt_number']
        ordering = ['-started_at']
    
    def __str__(self):
        status = "✓ Passed" if self.passed else "✗ Failed" if self.score is not None else "In Progress"
        return f"{self.student.email} - {self.unit_exam.unit.title} - Attempt #{self.attempt_number} ({status})"


class StudentLevelExamAttempt(TimeStampedModel):
    """
    محاولات الطالب في امتحان المستوى
    """
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='level_exam_attempts',
        verbose_name="الطالب"
    )
    level_exam = models.ForeignKey(
        LevelExam,
        on_delete=models.CASCADE,
        related_name='attempts',
        verbose_name="امتحان المستوى"
    )
    
    attempt_number = models.PositiveIntegerField(
        verbose_name="رقم المحاولة",
        validators=[MinValueValidator(1)]
    )
    
    # الأسئلة المولّدة للطالب (IDs)
    generated_questions = models.JSONField(
        default=dict,
        verbose_name="الأسئلة المولّدة"
    )
    
    # إجابات الطالب
    answers = models.JSONField(
        default=dict,
        verbose_name="الإجابات"
    )
    
    # النتيجة
    score = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="الدرجة (من 100)"
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
        verbose_name = "محاولة امتحان مستوى"
        verbose_name_plural = "محاولات امتحانات المستويات"
        unique_together = ['student', 'level_exam', 'attempt_number']
        ordering = ['-started_at']
    
    def __str__(self):
        status = "✓ Passed" if self.passed else "✗ Failed" if self.score is not None else "In Progress"
        return f"{self.student.email} - {self.level_exam.level.code} Exam - Attempt #{self.attempt_number} ({status})"
    
# ============================================
# ADD THIS TO THE END OF levels/models.py
# ============================================

# بعد StudentLevelExamAttempt Model

# ============================================
# Question Bank for Units & Levels
# ============================================

class LevelsUnitsQuestionBank(TimeStampedModel):
    """
    بنك الأسئلة - يمكن ربطه بـ Unit أو Level
    """
    # الربط (واحد من الاثنين فقط)
    unit = models.ForeignKey(
        Unit,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='question_banks',
        verbose_name="الوحدة"
    )
    level = models.ForeignKey(
        Level,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='question_banks',
        verbose_name="المستوى"
    )
    
    title = models.CharField(max_length=200, verbose_name="عنوان البنك")
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="وصف البنك"
    )
    
    class Meta:
        verbose_name = "بنك أسئلة"
        verbose_name_plural = "بنوك الأسئلة"
        ordering = ['-created_at']
    
    def __str__(self):
        if self.unit:
            return f"Question Bank - {self.unit.title}"
        elif self.level:
            return f"Question Bank - {self.level.code}"
        return self.title
    
    def clean(self):
        """التحقق من أن البنك مربوط بـ Unit أو Level فقط (ليس الاثنين)"""
        from django.core.exceptions import ValidationError
        if self.unit and self.level:
            raise ValidationError("لا يمكن ربط البنك بـ Unit و Level في نفس الوقت")
        if not self.unit and not self.level:
            raise ValidationError("يجب ربط البنك بـ Unit أو Level")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    def get_vocabulary_count(self):
        """عدد أسئلة المفردات"""
        from sabr_questions.models import VocabularyQuestion
        return VocabularyQuestion.objects.filter(
            levels_units_question_bank=self,  # ✅ 
            is_active=True
        ).count()
    
    def get_grammar_count(self):
        """عدد أسئلة القواعد"""
        from sabr_questions.models import GrammarQuestion
        return GrammarQuestion.objects.filter(
            levels_units_question_bank=self,  # ✅
            is_active=True
        ).count()
    
    def get_reading_count(self):
        """عدد أسئلة القراءة"""
        from sabr_questions.models import ReadingPassage, ReadingQuestion
        passages = ReadingPassage.objects.filter(
            levels_units_question_bank=self,  # ✅
            is_active=True
        )
        if not passages.exists():
            return 0
        
        total = ReadingQuestion.objects.filter(
            passage__in=passages,
            is_active=True
        ).count()
        return total
    
    def get_listening_count(self):
        """عدد أسئلة الاستماع"""
        from sabr_questions.models import ListeningAudio, ListeningQuestion
        audios = ListeningAudio.objects.filter(
            levels_units_question_bank=self,  # ✅
            is_active=True
        )
        if not audios.exists():
            return 0
        
        total = ListeningQuestion.objects.filter(
            audio__in=audios,
            is_active=True
        ).count()
        return total
    
    def get_speaking_count(self):
        """عدد أسئلة التحدث"""
        from sabr_questions.models import SpeakingVideo, SpeakingQuestion
        videos = SpeakingVideo.objects.filter(
            levels_units_question_bank=self,  # ✅
            is_active=True
        )
        if not videos.exists():
            return 0
        
        total = SpeakingQuestion.objects.filter(
            video__in=videos,
            is_active=True
        ).count()
        return total
    
    def get_writing_count(self):
        """عدد أسئلة الكتابة"""
        from sabr_questions.models import WritingQuestion
        return WritingQuestion.objects.filter(
            levels_units_question_bank=self,  # ✅
            is_active=True
        ).count()
    
    def get_total_questions(self):
        return (
            self.get_vocabulary_count() +
            self.get_grammar_count() +
            self.get_reading_count() +
            self.get_listening_count() +
            self.get_speaking_count() +
            self.get_writing_count()
        )
    def is_ready_for_unit_exam(self):
        
        return (
            self.get_vocabulary_count() >= 8 and
            self.get_grammar_count() >= 8 and
            self.get_reading_count() >= 10 and
            self.get_listening_count() >= 3 and
            self.get_speaking_count() >= 3 and
            self.get_writing_count() >= 3
        )

    def is_ready_for_level_exam(self):
        
        return (
            self.get_vocabulary_count() >= 12 and
            self.get_grammar_count() >= 12 and
            self.get_reading_count() >= 20 and
            self.get_listening_count() >= 6 and
            self.get_speaking_count() >= 5 and
            self.get_writing_count() >= 5
        )