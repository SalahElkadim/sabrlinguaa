from django.db import models
from django.contrib.auth import get_user_model
from cloudinary.models import CloudinaryField

User = get_user_model()


class GeneralExtractedBook(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('DONE', 'Done'),
        ('FAILED', 'Failed'),
    ]

    name = models.CharField(max_length=255, verbose_name="اسم الكتاب")
    pdf_file = CloudinaryField(
        verbose_name="ملف PDF",
        resource_type='raw',
        folder='general/ai/books',
    )
    extracted_text = models.TextField(blank=True, null=True, verbose_name="النص المستخرج")
    page_count = models.PositiveIntegerField(default=0, verbose_name="عدد الصفحات")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    error_message = models.TextField(blank=True, null=True)
    uploaded_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='general_extracted_books'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "General Extracted Book"
        verbose_name_plural = "General Extracted Books"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.status})"


class GeneralExtractedMedia(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('DONE', 'Done'),
        ('FAILED', 'Failed'),
    ]
    MEDIA_TYPE_CHOICES = [
        ('AUDIO', 'Audio'),
        ('VIDEO', 'Video'),
    ]

    name = models.CharField(max_length=255, verbose_name="اسم الميديا")
    media_file = CloudinaryField(
        verbose_name="ملف الميديا",
        resource_type='raw',
        folder='general/ai/media',
    )
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPE_CHOICES)
    transcript = models.TextField(blank=True, null=True, verbose_name="الترانسكريبت")
    duration_seconds = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    error_message = models.TextField(blank=True, null=True)
    uploaded_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='general_extracted_media'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "General Extracted Media"
        verbose_name_plural = "General Extracted Media"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.media_type} - {self.status})"


class GeneralAIGenerationJob(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('DONE', 'Done'),
        ('FAILED', 'Failed'),
    ]

    # الفرق الجوهري عن IELTS: بنربط بـ Category مش بـ Skill مباشرة
    # لأن الـ AI هو اللي بيعمل الـ Skill جوه الكاتيجوري
    category = models.ForeignKey(
        'general.GeneralCategory',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='ai_generation_jobs',
        verbose_name="الكاتيجوري"
    )
    # الـ skill اللي اتعملت بعد ما الـ job خلصت
    skill = models.ForeignKey(
        'general.GeneralSkill',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='generation_jobs',
        verbose_name="المهارة المُنشأة"
    )

    books = models.ManyToManyField(
        GeneralExtractedBook, blank=True,
        related_name='generation_jobs'
    )
    media = models.ManyToManyField(
        GeneralExtractedMedia, blank=True,
        related_name='generation_jobs'
    )

    # بيانات الـ Skill اللي هتتعمل
    skill_type = models.CharField(max_length=20, verbose_name="نوع المهارة")
    skill_title = models.CharField(max_length=200, verbose_name="عنوان المهارة")
    skill_description = models.TextField(blank=True, null=True, verbose_name="وصف المهارة")

    # عدد الأسئلة المطلوبة
    no_easy = models.PositiveIntegerField(default=0, verbose_name="عدد الأسئلة السهلة")
    no_medium = models.PositiveIntegerField(default=0, verbose_name="عدد الأسئلة المتوسطة")
    no_hard = models.PositiveIntegerField(default=0, verbose_name="عدد الأسئلة الصعبة")
    additional_notes = models.TextField(blank=True, null=True, verbose_name="ملاحظات إضافية")

    # حالة الـ job
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    error_message = models.TextField(blank=True, null=True)
    questions_created = models.PositiveIntegerField(default=0, verbose_name="عدد الأسئلة المُنشأة")

    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='general_generation_jobs'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "General AI Generation Job"
        verbose_name_plural = "General AI Generation Jobs"
        ordering = ['-created_at']

    def __str__(self):
        category_name = self.category.name if self.category else 'No Category'
        return f"Job #{self.id} - {category_name} / {self.skill_type} ({self.status})"

    @property
    def total_questions_requested(self):
        return self.no_easy + self.no_medium + self.no_hard