from django.db import models
from cloudinary.models import CloudinaryField


class Teacher(models.Model):
    """
    نموذج المدرس
    """
    name = models.CharField(max_length=255, verbose_name="اسم المعلم")
    profile_picture = CloudinaryField(
    resource_type='image',
    folder='teachers/profiles/',
    null=True,
    blank=True,
    verbose_name="الصورة الشخصية"
)
    subject = models.CharField(max_length=255, verbose_name="المادة")
    years_of_experience = models.PositiveIntegerField(verbose_name="سنوات الخبرة")
    session_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="تكلفة الحصة"
    )
    bio = models.TextField(blank=True, null=True, verbose_name="نبذة مختصرة")
    is_active = models.BooleanField(default=True, verbose_name="نشط")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "مدرس"
        verbose_name_plural = "المدرسون"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - {self.subject}"


class Booking(models.Model):
    """
    نموذج حجز الحصة
    """
    student = models.ForeignKey(
        'sabr_auth.User',
        on_delete=models.CASCADE,
        related_name='bookings',
        verbose_name="الطالب"
    )
    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE,
        related_name='bookings',
        verbose_name="المدرس"
    )
    phone_number = models.CharField(max_length=20, verbose_name="رقم التليفون")
    requested_datetime = models.DateTimeField(verbose_name="التاريخ والوقت المطلوب")
    notes = models.TextField(blank=True, null=True, verbose_name="ملاحظات")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "حجز"
        verbose_name_plural = "الحجوزات"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.student} - {self.teacher.name} - {self.requested_datetime}"