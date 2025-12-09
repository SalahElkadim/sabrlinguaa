from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """Custom user manager"""
    
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('يجب إدخال البريد الإلكتروني'))
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('user_type', 'admin')
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True'))
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Custom User Model"""
    
    USER_TYPE_CHOICES = (
        ('admin', 'Admin'),
        ('student', 'Student'),
    )
    
    email = models.EmailField(_('البريد الإلكتروني'), unique=True)
    full_name = models.CharField(_('الاسم الكامل'), max_length=255)
    user_type = models.CharField(_('نوع المستخدم'), max_length=10, choices=USER_TYPE_CHOICES)
    is_active = models.BooleanField(_('نشط'), default=True)
    is_staff = models.BooleanField(_('موظف'), default=False)
    date_joined = models.DateTimeField(_('تاريخ الانضمام'), auto_now_add=True)
    updated_at = models.DateTimeField(_('تاريخ التحديث'), auto_now=True)
    
    # Fix for groups and user_permissions clash
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name=_('المجموعات'),
        blank=True,
        related_name='sabr_users',
        related_query_name='sabr_user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name=_('الصلاحيات'),
        blank=True,
        related_name='sabr_users',
        related_query_name='sabr_user',
    )
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']
    
    class Meta:
        verbose_name = _('مستخدم')
        verbose_name_plural = _('المستخدمين')
        ordering = ['-date_joined']
    
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        return self.full_name
    
    def get_short_name(self):
        return self.full_name.split()[0] if self.full_name else self.email


class Student(models.Model):
    """Student Profile Model"""
    
    LEVEL_CHOICES = (
        ('not_tested', 'لم يتم الاختبار بعد'),
        ('A1', 'A1 - مبتدئ'),
        ('A2', 'A2 - أساسي'),
        ('B1', 'B1 - متوسط'),
        ('B2', 'B2 - متوسط متقدم'),
    )
    
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='student_profile',
        verbose_name=_('المستخدم')
    )
    profile_picture = models.ImageField(
        _('صورة الملف الشخصي'), 
        upload_to='student_profiles/', 
        blank=True, 
        null=True
    )
    
    # Overall Level based on Placement Test
    overall_level = models.CharField(
        _('المستوى العام'), 
        max_length=20, 
        choices=LEVEL_CHOICES,
        default='not_tested'
    )
    
    # Skill-based levels from Placement Test
    reading_level = models.CharField(
        _('مستوى القراءة'),
        max_length=20,
        choices=LEVEL_CHOICES,
        default='not_tested'
    )
    writing_level = models.CharField(
        _('مستوى الكتابة'),
        max_length=20,
        choices=LEVEL_CHOICES,
        default='not_tested'
    )
    listening_level = models.CharField(
        _('مستوى الاستماع'),
        max_length=20,
        choices=LEVEL_CHOICES,
        default='not_tested'
    )
    speaking_level = models.CharField(
        _('مستوى التحدث'),
        max_length=20,
        choices=LEVEL_CHOICES,
        default='not_tested'
    )
    grammar_level = models.CharField(
        _('مستوى القواعد'),
        max_length=20,
        choices=LEVEL_CHOICES,
        default='not_tested'
    )
    vocabulary_level = models.CharField(
        _('مستوى المفردات'),
        max_length=20,
        choices=LEVEL_CHOICES,
        default='not_tested'
    )
    
    # Placement Test Info
    placement_test_taken = models.BooleanField(_('تم إجراء اختبار تحديد المستوى'), default=False)
    placement_test_date = models.DateTimeField(_('تاريخ اختبار تحديد المستوى'), blank=True, null=True)
    
    # Additional Info
    phone_number = models.CharField(_('رقم الهاتف'), max_length=20, blank=True, null=True)
    birth_date = models.DateField(_('تاريخ الميلاد'), blank=True, null=True)
    bio = models.TextField(_('نبذة عني'), blank=True, null=True)
    
    class Meta:
        verbose_name = _('طالب')
        verbose_name_plural = _('الطلاب')
    
    def __str__(self):
        return f"{self.user.full_name} - {self.get_overall_level_display()}"
    
    def get_skill_levels(self):
        """Return dictionary of all skill levels"""
        return {
            'reading': self.reading_level,
            'writing': self.writing_level,
            'listening': self.listening_level,
            'speaking': self.speaking_level,
            'grammar': self.grammar_level,
            'vocabulary': self.vocabulary_level,
        }