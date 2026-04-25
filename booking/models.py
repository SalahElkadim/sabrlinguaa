# ============================================
# التعديلات على models.py
# ============================================

from django.db import models
from cloudinary.models import CloudinaryField
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Avg


class Teacher(models.Model):
    name = models.CharField(max_length=255, verbose_name="اسم المعلم")
    profile_picture = CloudinaryField(
        resource_type='image',
        folder='teachers/profiles/',
        null=True,
        blank=True,
        verbose_name="الصورة الشخصية"
    )
    email = models.EmailField(verbose_name="البريد الالكتروني", unique=True)
    subject = models.CharField(max_length=255, verbose_name="المادة")
    years_of_experience = models.PositiveIntegerField(verbose_name="سنوات الخبرة")
    # ✅ تم حذف session_price
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

    @property
    def average_rating(self):
        result = self.reviews.aggregate(Avg('rating'))['rating__avg']
        return round(result, 1) if result else None

    @property
    def reviews_count(self):
        return self.reviews.count()


# ============================================
# 1. البرنامج التعليمي
# ============================================

class Program(models.Model):

    class RecurrenceType(models.TextChoices):
        WEEKLY = 'weekly', 'أسبوعي'
        MONTHLY = 'monthly', 'شهري'
        ONCE = 'once', 'مرة واحدة'

    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE,
        related_name='programs',
        verbose_name="المدرس"
    )
    title = models.CharField(max_length=255, verbose_name="عنوان البرنامج")
    description = models.TextField(verbose_name="وصف البرنامج")
    recurrence = models.CharField(
        max_length=10,
        choices=RecurrenceType.choices,
        verbose_name="نظام التكرار"
    )
    duration = models.CharField(
        max_length=100,
        verbose_name="مدة البرنامج",
        help_text="مثال: شهرين، 3 أشهر"
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="تكلفة البرنامج"
    )
    is_active = models.BooleanField(default=True, verbose_name="نشط")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "برنامج تعليمي"
        verbose_name_plural = "البرامج التعليمية"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.teacher.name}"


# ============================================
# 2. جدول البرنامج (يوم + ساعة)
# ============================================

class ProgramSchedule(models.Model):

    class DayOfWeek(models.IntegerChoices):
        MONDAY = 0, 'الاثنين'
        TUESDAY = 1, 'الثلاثاء'
        WEDNESDAY = 2, 'الأربعاء'
        THURSDAY = 3, 'الخميس'
        FRIDAY = 4, 'الجمعة'
        SATURDAY = 5, 'السبت'
        SUNDAY = 6, 'الأحد'

    program = models.ForeignKey(
        Program,
        on_delete=models.CASCADE,
        related_name='schedules',
        verbose_name="البرنامج"
    )
    day_of_week = models.IntegerField(
        choices=DayOfWeek.choices,
        verbose_name="اليوم"
    )
    time = models.TimeField(verbose_name="الساعة")

    class Meta:
        verbose_name = "موعد البرنامج"
        verbose_name_plural = "مواعيد البرنامج"
        ordering = ['day_of_week', 'time']
        constraints = [
            models.UniqueConstraint(
                fields=['program', 'day_of_week', 'time'],
                name='unique_program_schedule'
            )
        ]

    def __str__(self):
        return f"{self.program.title} - {self.get_day_of_week_display()} {self.time}"


# ============================================
# 3. الاشتراك
# ============================================

class Subscription(models.Model):

    class PaymentStatus(models.TextChoices):
        PAID = 'paid', 'مدفوع'
        FAILED = 'failed', 'فشل الدفع'
        PENDING = 'pending', 'في الانتظار'

    student = models.ForeignKey(
        'sabr_auth.User',
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name="الطالب"
    )
    program = models.ForeignKey(
        Program,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name="البرنامج"
    )
    payment_id = models.CharField(
        max_length=255,
        unique=True,
        verbose_name="معرف الدفع من Moyasar"
    )
    payment_status = models.CharField(
        max_length=10,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        verbose_name="حالة الدفع"
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="المبلغ المدفوع"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    reference_number = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        verbose_name="الرقم المرجعي"
    )
    def save(self, *args, **kwargs):
        if not self.reference_number:
            year = self.created_at.year if self.created_at else __import__('datetime').date.today().year
            # save مؤقت عشان نجيب الـ id
            super().save(*args, **kwargs)
            self.reference_number = f"SBR-{year}-{self.id:05d}"
            kwargs['force_insert'] = False
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "اشتراك"
        verbose_name_plural = "الاشتراكات"
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['student', 'program'],
                name='unique_subscription'
            )
        ]

    def __str__(self):
        return f"{self.student} - {self.program.title} - {self.payment_status}"


# ============================================
# 4. تخصيص برنامج
# ============================================

class CustomProgram(models.Model):

    class RecurrenceType(models.TextChoices):
        WEEKLY = 'weekly', 'أسبوعي'
        MONTHLY = 'monthly', 'شهري'
        ONCE = 'once', 'مرة واحدة'

    class DayOfWeek(models.IntegerChoices):
        MONDAY = 0, 'الاثنين'
        TUESDAY = 1, 'الثلاثاء'
        WEDNESDAY = 2, 'الأربعاء'
        THURSDAY = 3, 'الخميس'
        FRIDAY = 4, 'الجمعة'
        SATURDAY = 5, 'السبت'
        SUNDAY = 6, 'الأحد'

    student = models.ForeignKey(
        'sabr_auth.User',
        on_delete=models.CASCADE,
        related_name='custom_programs',
        verbose_name="الطالب"
    )
    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE,
        related_name='custom_programs',
        verbose_name="المدرس"
    )
    whatsapp_number = models.CharField(
        max_length=20,
        verbose_name="رقم واتساب الطالب"
    )
    recurrence = models.CharField(
        max_length=10,
        choices=RecurrenceType.choices,
        verbose_name="نظام التكرار"
    )
    duration = models.CharField(
        max_length=100,
        verbose_name="المدة المطلوبة",
        help_text="مثال: شهرين، 3 أشهر"
    )
    curriculum = models.TextField(
        verbose_name="المادة أو المنهج المطلوب"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "تخصيص برنامج"
        verbose_name_plural = "طلبات تخصيص البرامج"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.student} → {self.teacher.name}"


# ============================================
# 5. جدول التخصيص (يوم + ساعة)
# ============================================

class CustomProgramSchedule(models.Model):

    custom_program = models.ForeignKey(
        CustomProgram,
        on_delete=models.CASCADE,
        related_name='schedules',
        verbose_name="طلب التخصيص"
    )
    day_of_week = models.IntegerField(
        choices=CustomProgram.DayOfWeek.choices,
        verbose_name="اليوم"
    )
    time = models.TimeField(verbose_name="الساعة")

    class Meta:
        verbose_name = "موعد التخصيص"
        verbose_name_plural = "مواعيد التخصيص"
        ordering = ['day_of_week', 'time']

    def __str__(self):
        return f"{self.custom_program} - {self.get_day_of_week_display()} {self.time}"


# ============================================
# نماذج Review و Booking زي ما هي
# ============================================

class Review(models.Model):
    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name="المدرس"
    )
    student = models.ForeignKey(
        'sabr_auth.User',
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name="الطالب"
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="التقييم"
    )
    comment = models.TextField(blank=True, null=True, verbose_name="تعليق")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "تقييم"
        verbose_name_plural = "التقييمات"
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['teacher', 'student'],
                name='unique_review_per_student'
            )
        ]

    def __str__(self):
        return f"{self.student} → {self.teacher.name}: {self.rating}⭐"


class Booking(models.Model):
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