from django.db import models
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
# Esp Category
# ============================================

class EspCategory(TimeStampedModel, OrderedModel):
    """
    الكاتيجوري اللي بيضيفها الأدمن من الداشبورد.
    كل كاتيجوري هي بمثابة "تطبيق" مستقل جوه Esp.
    """
    name = models.CharField(max_length=200, verbose_name="اسم الكاتيجوري")
    description = models.TextField(blank=True, null=True, verbose_name="الوصف")
    icon = CloudinaryField(
        verbose_name="الأيقونة",
        blank=True,
        null=True,
        folder='esp/category_icons',
    )

    class Meta:
        verbose_name = "Esp Category"
        verbose_name_plural = "Esp Categories"
        ordering = ['order', 'id']

    def __str__(self):
        return self.name

    def get_total_questions_count(self):
        total = 0
        for skill in self.skills.filter():
            total += skill.get_total_questions_count()
        return total


# ============================================
# Esp Skill
# ============================================

class EspSkill(TimeStampedModel, OrderedModel):
    """
    المهارة جوه الكاتيجوري - ديناميكية بالكامل.
    كل skill بيتحدد نوعها بالـ skill_type.
    """
    SKILL_TYPE_CHOICES = [
        ('VOCABULARY', 'Vocabulary'),
        ('GRAMMAR', 'Grammar'),
        ('READING', 'Reading'),
        ('LISTENING', 'Listening'),
        ('WRITING', 'Writing'),
        ('SPEAKING', 'Speaking'),
        ('GENERAL_PATH', 'General path'),

    ]
    ORDER_TYPE_CHOICES = [
        ('SEQUENTIAL', 'Sequential (Easy → Medium → Hard)'),
        ('CYCLIC', 'Cyclic (3 Easy, 3 Medium, 3 Hard, repeat)'),
        ('RANDOM', 'Random'),
    ]

    # ... الـ fields الموجودة ...
    
    question_order_type = models.CharField(
        max_length=20,
        choices=ORDER_TYPE_CHOICES,
        default='SEQUENTIAL',
        verbose_name="طريقة ترتيب الأسئلة"
    )

    category = models.ForeignKey(
        EspCategory,
        on_delete=models.CASCADE,
        related_name='skills',
        verbose_name="الكاتيجوري"
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
        folder='esp/skill_icons',
    )

    class Meta:
        verbose_name = "Esp Skill"
        verbose_name_plural = "Esp Skills"
        ordering = ['order', 'skill_type']

    def __str__(self):
        return f"{self.category.name} - {self.get_skill_type_display()}"

    def get_total_questions_count(self):
        from sabr_questions.models import (
            VocabularyQuestion, GrammarQuestion,
            ReadingPassage, WritingQuestion, ListeningAudio,
        )
        skill_type = self.skill_type

        if skill_type == 'VOCABULARY':
            return VocabularyQuestion.objects.filter(
                esp_skill=self, usage_type='ESP', is_active=True
            ).count()

        elif skill_type == 'GRAMMAR':
            return GrammarQuestion.objects.filter(
                esp_skill=self, usage_type='ESP', is_active=True
            ).count()

        elif skill_type == 'READING':
            passages = ReadingPassage.objects.filter(
                esp_skill=self, usage_type='ESP', is_active=True
            )
            return sum(p.get_questions_count() for p in passages)

        elif skill_type == 'LISTENING':
            audios = ListeningAudio.objects.filter(
                esp_skill=self, usage_type='ESP', is_active=True
            )
            return sum(a.questions.filter(is_active=True).count() for a in audios)

        elif skill_type == 'WRITING':
            return WritingQuestion.objects.filter(
                esp_skill=self, usage_type='ESP', is_active=True
            ).count()

        elif skill_type == 'SPEAKING':
            videos = SpeakingVideo.objects.filter(
                esp_skill=self, usage_type='ESP', is_active=True
            )
            return sum(v.questions.filter(is_active=True).count() for v in videos)

        elif skill_type == 'GENERAL_PATH':
            from sabr_questions.models import (
                VocabularyQuestion, GrammarQuestion,
                ReadingPassage, ListeningAudio,
            )
            total = 0
            total += VocabularyQuestion.objects.filter(esp_skill=self, usage_type='ESP', is_active=True).count()
            total += GrammarQuestion.objects.filter(esp_skill=self, usage_type='ESP', is_active=True).count()
            passages = ReadingPassage.objects.filter(esp_skill=self, usage_type='ESP', is_active=True)
            total += sum(p.get_questions_count() for p in passages)
            audios = ListeningAudio.objects.filter(esp_skill=self, usage_type='ESP', is_active=True)
            total += sum(a.questions.filter(is_active=True).count() for a in audios)
            videos = SpeakingVideo.objects.filter(esp_skill=self, usage_type='ESP', is_active=True)
            total += sum(v.questions.filter(is_active=True).count() for v in videos)
            return total
        
        return 0


# ============================================
# Student Progress Models
# ============================================

class StudentEspProgress(TimeStampedModel):
    """
    تتبع تقدم الطالب في كل skill جوه Esp.
    """
    student = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='esp_progress', verbose_name="الطالب"
    )
    skill = models.ForeignKey(
        EspSkill, on_delete=models.CASCADE,
        related_name='student_progress', verbose_name="المهارة"
    )
    viewed_questions_count = models.PositiveIntegerField(
        default=0, verbose_name="عدد الأسئلة المكتملة"
    )
    total_score = models.PositiveIntegerField(
        default=0, verbose_name="إجمالي النقاط"
    )

    class Meta:
        verbose_name = "Student Esp Progress"
        verbose_name_plural = "Student Esp Progress"
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
        self.total_score += points
        self.viewed_questions_count += 1
        self.save()


class StudentEspQuestionAttempt(TimeStampedModel):
    """
    يسجل كل محاولة للإجابة على سؤال في Esp.
    نفس نظام IELTS بالظبط: 4 محاولات، نقاط تنازلية.
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
        related_name='esp_question_attempts', verbose_name="الطالب"
    )
    skill = models.ForeignKey(
        EspSkill, on_delete=models.CASCADE,
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
        default=False, verbose_name="تم الحل"
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
        verbose_name = "Student Esp Question Attempt"
        verbose_name_plural = "Student Esp Question Attempts"
        unique_together = ['student', 'question_type', 'question_id']
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['student', 'skill']),
            models.Index(fields=['question_type', 'question_id']),
        ]

    def __str__(self):
        return f"{self.student.email} - {self.question_type} #{self.question_id} - attempts: {self.attempts_count}"

    def get_points_for_attempt(self):
        points_map = {1: 20, 2: 15, 3: 10}
        return points_map.get(self.attempts_count, 5)
    
class StudentEspFavoriteCategory(TimeStampedModel):
    """
    المفضلة — الكاتيجوريز اللي اختارها الطالب
    """
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorite_esp_categories',
        verbose_name="الطالب"
    )
    category = models.ForeignKey(
        EspCategory,
        on_delete=models.CASCADE,
        related_name='favorited_by_esp',
        verbose_name="الكاتيجوري"
    )

    class Meta:
        verbose_name = "Favorite Category"
        verbose_name_plural = "Favorite Categories"
        unique_together = ['student', 'category']  # مينفعش يضيفها أكتر من مرة
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.student.email} ♥ {self.category.name}"
    

from .ai_models import EspExtractedBook, EspExtractedMedia, EspAIGenerationJob