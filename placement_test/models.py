from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import random
import json

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


# ============================================
# Placement Test Models
# ============================================

class PlacementTest(TimeStampedModel):
    """
    اختبار تحديد المستوى
    """
    title = models.CharField(max_length=200, verbose_name="عنوان الاختبار")
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="وصف الاختبار"
    )
    
    # إعدادات الاختبار
    duration_minutes = models.PositiveIntegerField(
        default=30,
        verbose_name="المدة بالدقائق"
    )
    total_questions = models.PositiveIntegerField(
        default=50,
        verbose_name="إجمالي الأسئلة"
    )
    
    # توزيع الأسئلة
    vocabulary_count = models.PositiveIntegerField(
        default=10,
        verbose_name="عدد أسئلة المفردات"
    )
    grammar_count = models.PositiveIntegerField(
        default=10,
        verbose_name="عدد أسئلة القواعد"
    )
    reading_count = models.PositiveIntegerField(
        default=6,
        verbose_name="عدد أسئلة القراءة"
    )
    listening_count = models.PositiveIntegerField(
        default=10,
        verbose_name="عدد أسئلة الاستماع"
    )
    speaking_count = models.PositiveIntegerField(
        default=10,
        verbose_name="عدد أسئلة التحدث"
    )
    writing_count = models.PositiveIntegerField(
        default=4,
        verbose_name="عدد أسئلة الكتابة"
    )
    
    # معايير التقييم (CEFR Standards)
    a1_min_score = models.PositiveIntegerField(
        default=0,
        verbose_name="الحد الأدنى لـ A1"
    )
    a1_max_score = models.PositiveIntegerField(
        default=20,
        verbose_name="الحد الأقصى لـ A1"
    )
    
    a2_min_score = models.PositiveIntegerField(
        default=21,
        verbose_name="الحد الأدنى لـ A2"
    )
    a2_max_score = models.PositiveIntegerField(
        default=30,
        verbose_name="الحد الأقصى لـ A2"
    )
    
    b1_min_score = models.PositiveIntegerField(
        default=31,
        verbose_name="الحد الأدنى لـ B1"
    )
    b1_max_score = models.PositiveIntegerField(
        default=40,
        verbose_name="الحد الأقصى لـ B1"
    )
    
    b2_min_score = models.PositiveIntegerField(
        default=41,
        verbose_name="الحد الأدنى لـ B2"
    )
    b2_max_score = models.PositiveIntegerField(
        default=50,
        verbose_name="الحد الأقصى لـ B2"
    )
    
    # حالة الاختبار
    is_active = models.BooleanField(default=True, verbose_name="نشط")
    
    class Meta:
        verbose_name = "اختبار تحديد المستوى"
        verbose_name_plural = "اختبارات تحديد المستوى"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def get_level_from_score(self, score):
        """
        تحديد المستوى بناءً على الدرجة
        """
        if self.a1_min_score <= score <= self.a1_max_score:
            return 'A1'
        elif self.a2_min_score <= score <= self.a2_max_score:
            return 'A2'
        elif self.b1_min_score <= score <= self.b1_max_score:
            return 'B1'
        elif self.b2_min_score <= score <= self.b2_max_score:
            return 'B2'
        else:
            return 'Unknown'
    
    def get_total_questions_in_bank(self):
        """
        إجمالي الأسئلة في البنك
        """
        return self.question_bank.filter(is_active=True).count()
    
    def validate_question_distribution(self):
        """
        التحقق من أن مجموع الأسئلة = total_questions
        """
        total = (
            self.vocabulary_count +
            self.grammar_count +
            self.reading_count +
            self.listening_count +
            self.speaking_count +
            self.writing_count
        )
        return total == self.total_questions


class PlacementTestQuestionBank(TimeStampedModel):
    """
    بنك أسئلة اختبار تحديد المستوى (Many-to-Many مع GenericForeignKey)
    """
    placement_test = models.ForeignKey(
        PlacementTest,
        on_delete=models.CASCADE,
        related_name='question_bank',
        verbose_name="اختبار تحديد المستوى"
    )
    
    # GenericForeignKey للربط مع أي نوع سؤال
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        verbose_name="نوع السؤال",
        limit_choices_to={
            'model__in': [
                'vocabularyquestion',
                'grammarquestion',
                'readingquestion',
                'listeningquestion',
                'speakingquestion',
                'writingquestion'
            ]
        }
    )
    object_id = models.PositiveIntegerField(verbose_name="معرف السؤال")
    question = GenericForeignKey('content_type', 'object_id')
    
    # معلومات إضافية
    is_active = models.BooleanField(default=True, verbose_name="نشط")
    added_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='added_placement_questions',
        verbose_name="أضيف بواسطة"
    )
    
    class Meta:
        verbose_name = "سؤال في بنك الاختبار"
        verbose_name_plural = "أسئلة بنك الاختبار"
        ordering = ['-created_at']
        # منع التكرار (نفس السؤال لا يضاف مرتين لنفس الاختبار)
        unique_together = ['placement_test', 'content_type', 'object_id']
    
    def __str__(self):
        return f"{self.placement_test.title} - {self.get_question_type_display()} - Q{self.object_id}"
    
    def get_question_type_display(self):
        """
        عرض نوع السؤال بالعربي
        """
        model_name = self.content_type.model
        types = {
            'vocabularyquestion': 'مفردات',
            'grammarquestion': 'قواعد',
            'readingquestion': 'قراءة',
            'listeningquestion': 'استماع',
            'speakingquestion': 'تحدث',
            'writingquestion': 'كتابة'
        }
        return types.get(model_name, model_name)



class QuestionBank(models.Model):
    """
    بنك الأسئلة
    """
    title = models.CharField(max_length=200, verbose_name="عنوان البنك")
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="وصف البنك"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")
    
    class Meta:
        verbose_name = "بنك أسئلة"
        verbose_name_plural = "بنوك الأسئلة"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def get_vocabulary_count(self):
        """عدد أسئلة المفردات"""
        from sabr_questions.models import VocabularyQuestion
        return VocabularyQuestion.objects.filter(
            question_bank=self,
            is_active=True
        ).count()
    
    def get_grammar_count(self):
        """عدد أسئلة القواعد"""
        from sabr_questions.models import GrammarQuestion
        return GrammarQuestion.objects.filter(
            question_bank=self,
            is_active=True
        ).count()
    
    def get_reading_count(self):
        """عدد أسئلة القراءة"""
        from sabr_questions.models import ReadingPassage
        passages = ReadingPassage.objects.filter(
            question_bank=self,
            is_active=True
        )
        return sum(p.get_questions_count() for p in passages)
    
    def get_listening_count(self):
        """عدد أسئلة الاستماع"""
        from sabr_questions.models import ListeningAudio
        audios = ListeningAudio.objects.filter(
            question_bank=self,
            is_active=True
        )
        return sum(a.get_questions_count() for a in audios)
    
    def get_speaking_count(self):
        """عدد أسئلة التحدث"""
        from sabr_questions.models import SpeakingVideo
        videos = SpeakingVideo.objects.filter(
            question_bank=self,
            is_active=True
        )
        return sum(v.get_questions_count() for v in videos)
    
    def get_writing_count(self):
        """عدد أسئلة الكتابة"""
        from sabr_questions.models import WritingQuestion
        return WritingQuestion.objects.filter(
            question_bank=self,
            is_active=True
        ).count()
    
    def get_total_questions(self):
        """إجمالي الأسئلة في البنك"""
        return (
            self.get_vocabulary_count() +
            self.get_grammar_count() +
            self.get_reading_count() +
            self.get_listening_count() +
            self.get_speaking_count() +
            self.get_writing_count()
        )
    
    def is_ready_for_exam(self):
        """
        التحقق من جاهزية البنك لإنشاء امتحان
        يجب أن يكون فيه على الأقل:
        - 10 vocabulary
        - 10 grammar
        - 6 reading
        - 10 listening
        - 10 speaking
        - 4 writing
        """
        return (
            self.get_vocabulary_count() >= 10 and
            self.get_grammar_count() >= 10 and
            self.get_reading_count() >= 6 and
            self.get_listening_count() >= 10 and
            self.get_speaking_count() >= 10 and
            self.get_writing_count() >= 4
        )


class StudentPlacementTestAttempt(TimeStampedModel):
    """
    محاولة الطالب في اختبار تحديد المستوى
    """
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='placement_test_attempts',
        verbose_name="الطالب"
    )
    placement_test = models.ForeignKey(
        PlacementTest,
        on_delete=models.CASCADE,
        related_name='student_attempts',
        verbose_name="اختبار تحديد المستوى"
    )
    question_bank = models.ForeignKey(
        QuestionBank,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bank_attempts',
        verbose_name="بنك الأسئلة"
    )
    
    # توقيتات
    started_at = models.DateTimeField(auto_now_add=True, verbose_name="بدأ في")
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="انتهى في"
    )
    
    # النتائج
    score = models.PositiveIntegerField(
        default=0,
        verbose_name="الدرجة"
    )
    
    LEVEL_CHOICES = [
        ('A1', 'A1 - Beginner'),
        ('A2', 'A2 - Elementary'),
        ('B1', 'B1 - Intermediate'),
        ('B2', 'B2 - Upper Intermediate'),
    ]
    level_achieved = models.CharField(
        max_length=2,
        choices=LEVEL_CHOICES,
        null=True,
        blank=True,
        verbose_name="المستوى المحقق"
    )
    
    # الأسئلة المختارة (JSON) - لحفظ IDs الأسئلة
    selected_questions_json = models.TextField(
        blank=True,
        null=True,
        verbose_name="الأسئلة المختارة (JSON)",
        help_text="يحفظ معرفات الأسئلة المختارة عشوائياً"
    )
    
    # حالة الاختبار
    STATUS_CHOICES = [
        ('IN_PROGRESS', 'جاري'),
        ('COMPLETED', 'مكتمل'),
        ('ABANDONED', 'متروك'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='IN_PROGRESS',
        verbose_name="الحالة"
    )
    
    class Meta:
        verbose_name = "محاولة طالب"
        verbose_name_plural = "محاولات الطلاب"
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.student.username} - {self.placement_test.title} - {self.started_at.strftime('%Y-%m-%d %H:%M')}"
    
    def set_selected_questions(self, questions_dict):
        """
        حفظ الأسئلة المختارة في JSON
        questions_dict = {
            'vocabulary': [1, 5, 9, ...],
            'grammar': [2, 7, 11, ...],
            ...
        }
        """
        self.selected_questions_json = json.dumps(questions_dict)
        self.save()
    
    def get_selected_questions(self):
        """
        استرجاع الأسئلة المختارة من JSON
        """
        if self.selected_questions_json:
            return json.loads(self.selected_questions_json)
        return {}
    
    def calculate_score(self):
        """
        حساب الدرجة النهائية
        """
        total_score = 0
        answers = self.answers.all()
        
        for answer in answers:
            if answer.is_correct:
                total_score += answer.points_earned
        
        self.score = total_score
        self.level_achieved = self.placement_test.get_level_from_score(total_score)
        self.save()
        
        return total_score
    
    def mark_completed(self):
        """
        تحديد الاختبار كمكتمل
        """
        self.completed_at = timezone.now()
        self.status = 'COMPLETED'
        self.calculate_score()
        self.save()
    
    def get_duration(self):
        """
        حساب المدة الفعلية للاختبار
        """
        if self.completed_at:
            delta = self.completed_at - self.started_at
            return delta.total_seconds() / 60  # بالدقائق
        return None
    
    def is_time_up(self):
        """
        التحقق من انتهاء الوقت
        """
        if self.status == 'COMPLETED':
            return True
        
        elapsed = timezone.now() - self.started_at
        elapsed_minutes = elapsed.total_seconds() / 60
        return elapsed_minutes >= self.placement_test.duration_minutes

class StudentPlacementTestAnswer(TimeStampedModel):
    """
    إجابة الطالب على سؤال في اختبار تحديد المستوى
    """
    attempt = models.ForeignKey(
        StudentPlacementTestAttempt,
        on_delete=models.CASCADE,
        related_name='answers',
        verbose_name="المحاولة"
    )
    
    # السؤال (GenericForeignKey)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        verbose_name="نوع السؤال"
    )
    object_id = models.PositiveIntegerField(verbose_name="معرف السؤال")
    question = GenericForeignKey('content_type', 'object_id')
    
    # الإجابة (للأسئلة MCQ)
    CHOICE_OPTIONS = [
        ('A', 'أ'),
        ('B', 'ب'),
        ('C', 'ج'),
        ('D', 'د'),
    ]
    selected_choice = models.CharField(
        max_length=1,
        choices=CHOICE_OPTIONS,
        null=True,
        blank=True,
        verbose_name="الاختيار المحدد"
    )
    
    # الإجابة (لأسئلة Writing)
    text_answer = models.TextField(
        blank=True,
        null=True,
        verbose_name="الإجابة النصية"
    )
    
    # التقييم
    is_correct = models.BooleanField(default=False, verbose_name="صحيحة")
    points_earned = models.PositiveIntegerField(default=0, verbose_name="النقاط المكتسبة")
    
    # ✅ حقول جديدة للـ AI Grading
    ai_feedback = models.TextField(
        blank=True,
        null=True,
        verbose_name="ملاحظات الـ AI"
    )
    
    ai_grading_model = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Model المستخدم"
    )
    
    ai_grading_cost = models.DecimalField(
        max_digits=10,
        decimal_places=6,
        default=0,
        verbose_name="تكلفة التصحيح ($)"
    )
    
    strengths = models.JSONField(
        blank=True,
        null=True,
        default=list,
        verbose_name="نقاط القوة"
    )
    
    improvements = models.JSONField(
        blank=True,
        null=True,
        default=list,
        verbose_name="نقاط التحسين"
    )
    
    # معلومات إضافية
    answered_at = models.DateTimeField(auto_now_add=True, verbose_name="تم الإجابة في")
    time_spent_seconds = models.PositiveIntegerField(
        default=0,
        verbose_name="الوقت المستغرق (بالثواني)"
    )
    
    class Meta:
        verbose_name = "إجابة طالب"
        verbose_name_plural = "إجابات الطلاب"
        ordering = ['answered_at']
        unique_together = ['attempt', 'content_type', 'object_id']
    
    def __str__(self):
        return f"{self.attempt.student.username} - Q{self.object_id} - {'✓' if self.is_correct else '✗'}"
    
    def check_answer(self):
        """
        التحقق من صحة الإجابة
        """
        question_obj = self.question
        
        # للأسئلة MCQ (Vocabulary, Grammar, Reading, Listening, Speaking)
        if hasattr(question_obj, 'correct_answer'):
            if self.selected_choice == question_obj.correct_answer:
                self.is_correct = True
                self.points_earned = getattr(question_obj, 'points', 1)
            else:
                self.is_correct = False
                self.points_earned = 0
        
        self.save()
        return self.is_correct
    
    def get_question_type_display(self):
        """
        عرض نوع السؤال بالعربي
        """
        model_name = self.content_type.model
        types = {
            'vocabularyquestion': 'مفردات',
            'grammarquestion': 'قواعد',
            'readingquestion': 'قراءة',
            'listeningquestion': 'استماع',
            'speakingquestion': 'تحدث',
            'writingquestion': 'كتابة'
        }
        return types.get(model_name, model_name)

# ============================================
# Helper Functions
# ============================================

def select_random_questions_for_attempt(placement_test):
    """
    اختيار أسئلة عشوائية من بنك الاختبار بناءً على التوزيع المحدد
    
    Returns:
        dict: {
            'vocabulary': [list of question IDs],
            'grammar': [list of question IDs],
            ...
        }
    """
    from django.contrib.contenttypes.models import ContentType
    
    selected_questions = {
        'vocabulary': [],
        'grammar': [],
        'reading': [],
        'listening': [],
        'speaking': [],
        'writing': []
    }
    
    # Get ContentTypes
    content_types = {
        'vocabulary': ContentType.objects.get(model='vocabularyquestion'),
        'grammar': ContentType.objects.get(model='grammarquestion'),
        'reading': ContentType.objects.get(model='readingquestion'),
        'listening': ContentType.objects.get(model='listeningquestion'),
        'speaking': ContentType.objects.get(model='speakingquestion'),
        'writing': ContentType.objects.get(model='writingquestion'),
    }
    
    # Select random questions for each type
    question_counts = {
        'vocabulary': placement_test.vocabulary_count,
        'grammar': placement_test.grammar_count,
        'reading': placement_test.reading_count,
        'listening': placement_test.listening_count,
        'speaking': placement_test.speaking_count,
        'writing': placement_test.writing_count,
    }
    
    for q_type, count in question_counts.items():
        # Get all active questions of this type from the bank
        questions = PlacementTestQuestionBank.objects.filter(
            placement_test=placement_test,
            content_type=content_types[q_type],
            is_active=True
        ).values_list('object_id', flat=True)
        
        # Convert to list and shuffle
        questions_list = list(questions)
        
        # Select random questions
        if len(questions_list) >= count:
            selected = random.sample(questions_list, count)
        else:
            # If not enough questions, take all available
            selected = questions_list
        
        selected_questions[q_type] = selected
    
    return selected_questions