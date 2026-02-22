from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model
from django.utils import timezone
from cloudinary.models import CloudinaryField

User = get_user_model()


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


# ============================================
# STEP Main Models
# ============================================

class STEPSkill(TimeStampedModel, OrderedModel):
    """
    المهارات الأربعة في STEP: Reading, Writing, Vocabulary, Grammar
    """
    SKILL_TYPE_CHOICES = [
        ('VOCABULARY', 'Vocabulary'),
        ('GRAMMAR', 'Grammar'),
        ('READING', 'Reading'),
        ('WRITING', 'Writing'),
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
        folder='step/skill_icons',
    )
    
    class Meta:
        verbose_name = "STEP Skill"
        verbose_name_plural = "STEP Skills"
        ordering = ['order', 'skill_type']
    
    def __str__(self):
        return f"{self.get_skill_type_display()}"
    
    def get_total_questions_count(self):
        """
        عدد جميع الأسئلة في هذه المهارة
        """
        from sabr_questions.models import (
            VocabularyQuestion,
            GrammarQuestion,
            ReadingPassage,
            WritingQuestion
        )
        
        skill_type = self.skill_type
        
        if skill_type == 'VOCABULARY':
            return VocabularyQuestion.objects.filter(
                step_skill=self,
                usage_type='STEP',
                is_active=True
            ).count()
        
        elif skill_type == 'GRAMMAR':
            return GrammarQuestion.objects.filter(
                step_skill=self,
                usage_type='STEP',
                is_active=True
            ).count()
        
        elif skill_type == 'READING':
            passages = ReadingPassage.objects.filter(
                step_skill=self,
                usage_type='STEP',
                is_active=True
            )
            total = 0
            for passage in passages:
                total += passage.get_questions_count()
            return total
        
        elif skill_type == 'WRITING':
            return WritingQuestion.objects.filter(
                step_skill=self,
                usage_type='STEP',
                is_active=True
            ).count()
        
        return 0


# ============================================
# Student Progress Models
# ============================================

class StudentSTEPProgress(TimeStampedModel):
    """
    تقدم الطالب في مهارة معينة
    """
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='step_progress',
        verbose_name="الطالب"
    )
    skill = models.ForeignKey(
        STEPSkill,
        on_delete=models.CASCADE,
        related_name='student_progress',
        verbose_name="المهارة"
    )
    
    # Statistics
    viewed_questions_count = models.PositiveIntegerField(
        default=0,
        verbose_name="عدد الأسئلة المفتوحة"
    )
    total_score = models.PositiveIntegerField(
        default=0,
        verbose_name="إجمالي النقاط"
    )
    
    class Meta:
        verbose_name = "Student STEP Progress"
        verbose_name_plural = "Student STEP Progress"
        unique_together = ['student', 'skill']
        ordering = ['student', 'skill']
    
    def __str__(self):
        return f"{self.student.username} - {self.skill.title}"
    
    def calculate_progress_percentage(self):
        """
        حساب نسبة التقدم (%)
        """
        total_questions = self.skill.get_total_questions_count()
        if total_questions == 0:
            return 0
        
        percentage = (self.viewed_questions_count / total_questions) * 100
        return round(percentage, 2)
    
    def increment_score(self):
        """
        زيادة النقاط والأسئلة المفتوحة
        """
        self.viewed_questions_count += 1
        self.total_score += 1
        self.save()


class StudentSTEPQuestionView(TimeStampedModel):
    """
    سجل الأسئلة التي فتحها الطالب (unique per student)
    """
    QUESTION_TYPE_CHOICES = [
        ('VOCABULARY', 'Vocabulary'),
        ('GRAMMAR', 'Grammar'),
        ('READING', 'Reading'),
        ('WRITING', 'Writing'),
    ]
    
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='step_question_views',
        verbose_name="الطالب"
    )
    skill = models.ForeignKey(
        STEPSkill,
        on_delete=models.CASCADE,
        related_name='question_views',
        verbose_name="المهارة"
    )
    
    question_type = models.CharField(
        max_length=20,
        choices=QUESTION_TYPE_CHOICES,
        verbose_name="نوع السؤال"
    )
    question_id = models.PositiveIntegerField(verbose_name="رقم السؤال")
    
    # Meta
    viewed_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الفتح")
    
    class Meta:
        verbose_name = "Student STEP Question View"
        verbose_name_plural = "Student STEP Question Views"
        unique_together = ['student', 'question_type', 'question_id']
        ordering = ['-viewed_at']
        indexes = [
            models.Index(fields=['student', 'skill']),
            models.Index(fields=['question_type', 'question_id']),
        ]
    
    def __str__(self):
        return f"{self.student.username} - {self.question_type} #{self.question_id}"