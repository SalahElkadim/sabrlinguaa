# models.py

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model
from django.utils import timezone
from cloudinary.models import CloudinaryField
from sabr_questions.models import SpeakingVideo

User = get_user_model()


# ============================================
# Abstract Base Models
# ============================================

class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")
    
    class Meta:
        abstract = True


class OrderedModel(models.Model):
    order = models.PositiveIntegerField(default=0, verbose_name="الترتيب")
    is_active = models.BooleanField(default=True, verbose_name="نشط")
    
    class Meta:
        abstract = True
        ordering = ['order', 'id']


# ============================================
# IELTS Main Models
# ============================================

class IELTSSkill(TimeStampedModel, OrderedModel):
    SKILL_TYPE_CHOICES = [
        ('VOCABULARY', 'Vocabulary'),
        ('GRAMMAR', 'Grammar'),
        ('READING', 'Reading'),
        ('LISTENING', 'Listening'),
        ('WRITING', 'Writing'),
        ('GENERAL_PATH', 'General path'), 
        ('SPEAKING', 'Speaking'),

    ]
    ORDER_TYPE_CHOICES = [
        ('SEQUENTIAL', 'Sequential (Easy → Medium → Hard)'),
        ('CYCLIC', 'Cyclic (3 Easy, 3 Medium, 3 Hard, repeat)'),
        ('RANDOM', 'Random'),
    ]
    question_order_type = models.CharField(
        max_length=20,
        choices=ORDER_TYPE_CHOICES,
        default='SEQUENTIAL',
        verbose_name="طريقة ترتيب الأسئلة"
    )
    
    skill_type = models.CharField(
        max_length=20,
        choices=SKILL_TYPE_CHOICES,
        verbose_name="نوع المهارة"
    )
    title = models.CharField(max_length=200, verbose_name="العنوان")
    description = models.TextField(blank=True, null=True, verbose_name="الوصف")
    icon = CloudinaryField(
        verbose_name="الأيقونة",
        blank=True,
        null=True,
        folder='ielts/skill_icons',
    )
    child_skills = models.ManyToManyField(
        'self',
        symmetrical=False,
        blank=True,
        related_name='parent_paths',
        verbose_name="المهارات الفرعية"
    )
    class Meta:
        verbose_name = "IELTS Skill"
        verbose_name_plural = "IELTS Skills"
        ordering = ['order', 'skill_type']
    
    def __str__(self):
        return f"{self.get_skill_type_display()}"
    
    def get_total_questions_count(self):
        from sabr_questions.models import (
            VocabularyQuestion, GrammarQuestion,
            ReadingPassage, WritingQuestion, ListeningAudio,
        )
        skill_type = self.skill_type
        if skill_type == 'VOCABULARY':
            return VocabularyQuestion.objects.filter(
                ielts_skill=self, usage_type='IELTS', is_active=True
            ).count()
        elif skill_type == 'GRAMMAR':
            return GrammarQuestion.objects.filter(
                ielts_skill=self, usage_type='IELTS', is_active=True
            ).count()
        elif skill_type == 'READING':
            passages = ReadingPassage.objects.filter(
                ielts_skill=self, usage_type='IELTS', is_active=True
            )
            return sum(p.get_questions_count() for p in passages)
        elif skill_type == 'LISTENING':
            audios = ListeningAudio.objects.filter(
                ielts_skill=self, usage_type='IELTS', is_active=True
            )
            return sum(a.questions.filter(is_active=True).count() for a in audios)
        elif skill_type == 'WRITING':
            return WritingQuestion.objects.filter(
                ielts_skill=self, usage_type='IELTS', is_active=True
            ).count()
        elif skill_type == 'GENERAL_PATH':
            from sabr_questions.models import (
                VocabularyQuestion, GrammarQuestion,
                ReadingPassage, ListeningAudio,
            )
            total = 0
            total += VocabularyQuestion.objects.filter(ielts_skill=self, usage_type='IELTS', is_active=True).count()
            total += GrammarQuestion.objects.filter(ielts_skill=self, usage_type='IELTS', is_active=True).count()
            passages = ReadingPassage.objects.filter(ielts_skill=self, usage_type='IELTS', is_active=True)
            total += sum(p.get_questions_count() for p in passages)
            audios = ListeningAudio.objects.filter(ielts_skill=self, usage_type='IELTS', is_active=True)
            total += sum(a.questions.filter(is_active=True).count() for a in audios)
            videos = SpeakingVideo.objects.filter(ielts_skill=self, usage_type='IELTS', is_active=True)
            total += sum(v.questions.filter(is_active=True).count() for v in videos)
            return total
        elif skill_type == 'SPEAKING':
            videos = SpeakingVideo.objects.filter(
                ielts_skill=self, usage_type='IELTS', is_active=True
            )
            return sum(v.questions.filter(is_active=True).count() for v in videos)
        return 0


# ============================================
# Student Progress Models
# ============================================

class StudentIELTSProgress(TimeStampedModel):
    student = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='ielts_progress', verbose_name="الطالب"
    )
    skill = models.ForeignKey(
        IELTSSkill, on_delete=models.CASCADE,
        related_name='student_progress', verbose_name="المهارة"
    )
    viewed_questions_count = models.PositiveIntegerField(
        default=0, verbose_name="عدد الأسئلة المكتملة"
    )
    total_score = models.PositiveIntegerField(
        default=0, verbose_name="إجمالي النقاط"
    )
    
    class Meta:
        verbose_name = "Student IELTS Progress"
        verbose_name_plural = "Student IELTS Progress"
        unique_together = ['student', 'skill']
        ordering = ['student', 'skill']
    
    def __str__(self):
        return f"{self.student.email} - {self.skill.title}"
    
    def calculate_progress_percentage(self):
        total_questions = self.skill.get_total_questions_count()
        if total_questions == 0:
            return 0
        return round((self.viewed_questions_count / total_questions) * 100, 2)
    
    def add_score(self, points):
        """يضيف نقاط ويزود عداد الأسئلة المكتملة"""
        self.total_score += points
        self.viewed_questions_count += 1
        self.save()


class StudentIELTSQuestionAttempt(TimeStampedModel):
    """
    يسجل كل محاولة للإجابة على سؤال معين.
    يحفظ عدد المحاولات، النقاط المكتسبة، وهل استخدم show answer.
    """
    QUESTION_TYPE_CHOICES = [
        ('VOCABULARY', 'Vocabulary'),
        ('GRAMMAR', 'Grammar'),
        ('READING', 'Reading'),
        ('LISTENING', 'Listening'),
        ('WRITING', 'Writing'),
        ('SPEAKING', 'Speaking'),
    ]

    student = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='ielts_question_attempts', verbose_name="الطالب"
    )
    skill = models.ForeignKey(
        IELTSSkill, on_delete=models.CASCADE,
        related_name='question_attempts', verbose_name="المهارة"
    )
    question_type = models.CharField(
        max_length=20, choices=QUESTION_TYPE_CHOICES, verbose_name="نوع السؤال"
    )
    question_id = models.PositiveIntegerField(verbose_name="رقم السؤال")

    attempts_count = models.PositiveIntegerField(
        default=0, verbose_name="عدد المحاولات"
    )
    is_solved = models.BooleanField(
        default=False, verbose_name="تم الحل (إجابة صحيحة أو show answer)"
    )
    points_earned = models.PositiveIntegerField(
        default=0, verbose_name="النقاط المكتسبة"
    )
    used_show_answer = models.BooleanField(
        default=False, verbose_name="استخدم show answer"
    )
    solved_at = models.DateTimeField(
        null=True, blank=True, verbose_name="وقت الحل"
    )

    class Meta:
        verbose_name = "Student IELTS Question Attempt"
        verbose_name_plural = "Student IELTS Question Attempts"
        # كل سؤال له record واحد بس per student
        unique_together = ['student', 'question_type', 'question_id']
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['student', 'skill']),
            models.Index(fields=['question_type', 'question_id']),
        ]
    
    def __str__(self):
        return f"{self.student.email} - {self.question_type} #{self.question_id} - attempts: {self.attempts_count}"

    def get_points_for_attempt(self):
        """
        يحسب النقاط بناءً على عدد المحاولات الحالية:
        محاولة 1 → 20، محاولة 2 → 15، محاولة 3 → 10، محاولة 4+ → 5
        """
        points_map = {1: 20, 2: 15, 3: 10}
        return points_map.get(self.attempts_count, 5)


# نحتفظ بـ StudentIELTSQuestionView للـ backward compatibility
# لكن مش هنستخدمه في النظام الجديد
class StudentIELTSQuestionView(TimeStampedModel):
    QUESTION_TYPE_CHOICES = [
        ('VOCABULARY', 'Vocabulary'),
        ('GRAMMAR', 'Grammar'),
        ('READING', 'Reading'),
        ('LISTENING', 'Listening'),
        ('WRITING', 'Writing'),
        ('SPEAKING', 'Speaking'),

    ]
    
    student = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='ielts_question_views', verbose_name="الطالب"
    )
    skill = models.ForeignKey(
        IELTSSkill, on_delete=models.CASCADE,
        related_name='question_views', verbose_name="المهارة"
    )
    question_type = models.CharField(
        max_length=20, choices=QUESTION_TYPE_CHOICES, verbose_name="نوع السؤال"
    )
    question_id = models.PositiveIntegerField(verbose_name="رقم السؤال")
    viewed_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الفتح")
    
    class Meta:
        verbose_name = "Student IELTS Question View"
        verbose_name_plural = "Student IELTS Question Views"
        unique_together = ['student', 'question_type', 'question_id']
        ordering = ['-viewed_at']
        indexes = [
            models.Index(fields=['student', 'skill']),
            models.Index(fields=['question_type', 'question_id']),
        ]
    
    def __str__(self):
        return f"{self.student.email} - {self.question_type} #{self.question_id}"
    


class IELTSSubscriptionPlan(models.Model):
    PLAN_CHOICES = [
        ('MONTHLY', 'شهر واحد'),
        ('QUARTERLY', 'ثلاثة أشهر'),
    ]
    plan_type = models.CharField(max_length=20, choices=PLAN_CHOICES, unique=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    duration_days = models.PositiveIntegerField()
    description = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.get_plan_type_display()} - {self.price} ريال"


class IELTSSubscription(TimeStampedModel):
    class PaymentStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PAID    = 'paid',    'Paid'
        FAILED  = 'failed',  'Failed'

    student      = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ielts_subscriptions')
    plan         = models.ForeignKey(IELTSSubscriptionPlan, on_delete=models.PROTECT)
    payment_id   = models.CharField(max_length=100, blank=True, null=True, unique=True)
    payment_status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
    amount       = models.DecimalField(max_digits=8, decimal_places=2)
    starts_at    = models.DateTimeField(null=True, blank=True)
    expires_at   = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.student.email} - {self.plan} - {self.payment_status}"

    @property
    def is_active(self):
        from django.utils import timezone
        return (
            self.payment_status == self.PaymentStatus.PAID
            and self.expires_at is not None
            and self.expires_at > timezone.now()
        )
    
# Import AI models عشان يتعمل migrate معاهم
from .ai_models import ExtractedBook, ExtractedMedia, AIGenerationJob