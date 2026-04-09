from django.db import models
from django.contrib.auth import get_user_model
from cloudinary.models import CloudinaryField

User = get_user_model()


class ExtractedBook(models.Model):
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
        folder='ielts/ai/books',
    )
    extracted_text = models.TextField(blank=True, null=True, verbose_name="النص المستخرج")
    page_count = models.PositiveIntegerField(default=0, verbose_name="عدد الصفحات")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    error_message = models.TextField(blank=True, null=True)
    uploaded_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='ielts_extracted_books'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Extracted Book"
        verbose_name_plural = "Extracted Books"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.status})"


class ExtractedMedia(models.Model):
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
        folder='ielts/ai/media',
    )
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPE_CHOICES)
    transcript = models.TextField(blank=True, null=True, verbose_name="الترانسكريبت")
    duration_seconds = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    error_message = models.TextField(blank=True, null=True)
    uploaded_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='ielts_extracted_media'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Extracted Media"
        verbose_name_plural = "Extracted Media"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.media_type} - {self.status})"


class AIGenerationJob(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('DONE', 'Done'),
        ('FAILED', 'Failed'),
    ]

    skill = models.ForeignKey(
        'ielts.IELTSSkill', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='ielts_generation_jobs'
    )
    books = models.ManyToManyField(ExtractedBook, blank=True, related_name='ielts_generation_jobs')
    media = models.ManyToManyField(ExtractedMedia, blank=True, related_name='ielts_generation_jobs')

    skill_type = models.CharField(max_length=20)
    skill_title = models.CharField(max_length=200)
    skill_description = models.TextField(blank=True, null=True)
    no_easy = models.PositiveIntegerField(default=0)
    no_medium = models.PositiveIntegerField(default=0)
    no_hard = models.PositiveIntegerField(default=0)
    additional_notes = models.TextField(blank=True, null=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    error_message = models.TextField(blank=True, null=True)
    questions_created = models.PositiveIntegerField(default=0)

    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='ielts_generation_jobs'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "AI Generation Job"
        verbose_name_plural = "AI Generation Jobs"
        ordering = ['-created_at']

    def __str__(self):
        return f"Job #{self.id} - {self.skill_type} ({self.status})"

    @property
    def total_questions_requested(self):
        return self.no_easy + self.no_medium + self.no_hard