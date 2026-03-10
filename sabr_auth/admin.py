from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.utils import timezone
from .models import User, Student, EmailVerification


# ============================================================
# EMAIL VERIFICATION INLINE
# ============================================================

class EmailVerificationInline(admin.TabularInline):
    model = EmailVerification
    extra = 0
    readonly_fields = ('code', 'created_at', 'expires_at', 'is_verified', 'status_badge')
    fields = ('code', 'created_at', 'expires_at', 'is_verified', 'status_badge')
    can_delete = False
    max_num = 5
    verbose_name = _('رمز التحقق')
    verbose_name_plural = _('رموز التحقق')

    def status_badge(self, obj):
        if obj.is_verified:
            return format_html(
                '<span style="background:#10b981;color:#fff;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:600;">✓ تم التحقق</span>'
            )
        elif obj.is_expired():
            return format_html(
                '<span style="background:#ef4444;color:#fff;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:600;">✗ منتهي</span>'
            )
        else:
            return format_html(
                '<span style="background:#f59e0b;color:#fff;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:600;">⏳ معلّق</span>'
            )
    status_badge.short_description = _('الحالة')


# ============================================================
# STUDENT INLINE
# ============================================================

class StudentInline(admin.StackedInline):
    model = Student
    can_delete = False
    extra = 0
    verbose_name = _('ملف الطالب')
    verbose_name_plural = _('ملف الطالب')
    readonly_fields = ('placement_test_date', 'level_summary')
    fields = (
        'profile_picture',
        'overall_level',
        'level_summary',
        ('reading_level', 'writing_level'),
        ('listening_level', 'speaking_level'),
        ('grammar_level', 'vocabulary_level'),
        'placement_test_taken',
        'placement_test_date',
        'phone_number',
        'birth_date',
        'bio',
    )

    def level_summary(self, obj):
        if not obj.pk:
            return '-'
        levels = obj.get_skill_levels()
        colors = {
            'not_tested': '#94a3b8',
            'A1': '#f87171',
            'A2': '#fb923c',
            'B1': '#facc15',
            'B2': '#34d399',
        }
        badges = ''
        labels = {
            'reading': 'قراءة',
            'writing': 'كتابة',
            'listening': 'استماع',
            'speaking': 'تحدث',
            'grammar': 'قواعد',
            'vocabulary': 'مفردات',
        }
        for skill, level in levels.items():
            color = colors.get(level, '#94a3b8')
            badges += format_html(
                '<span style="background:{};color:#fff;padding:2px 8px;border-radius:12px;font-size:11px;margin:2px;display:inline-block;">{}: {}</span>',
                color, labels.get(skill, skill), level
            )
        return format_html('<div style="line-height:2">{}</div>', badges)
    level_summary.short_description = _('ملخص المستويات')


# ============================================================
# USER ADMIN
# ============================================================

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        'avatar_and_name', 'email', 'user_type_badge',
        'is_active_badge', 'is_email_verified_badge', 'date_joined'
    )
    list_filter = ('user_type', 'is_active', 'is_email_verified', 'is_staff', 'date_joined')
    search_fields = ('email', 'full_name')
    ordering = ('-date_joined',)
    readonly_fields = ('date_joined', 'updated_at')
    list_per_page = 25

    fieldsets = (
        (_('بيانات الدخول'), {
            'fields': ('email', 'password'),
            'classes': ('wide',),
        }),
        (_('المعلومات الشخصية'), {
            'fields': ('full_name', 'user_type'),
        }),
        (_('الصلاحيات'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'is_email_verified', 'groups', 'user_permissions'),
            'classes': ('collapse',),
        }),
        (_('التواريخ'), {
            'fields': ('date_joined', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'full_name', 'user_type', 'password1', 'password2'),
        }),
    )

    inlines = [StudentInline, EmailVerificationInline]

    def avatar_and_name(self, obj):
        initials = obj.full_name[:2].upper() if obj.full_name else obj.email[:2].upper()
        colors = ['#6366f1', '#8b5cf6', '#ec4899', '#14b8a6', '#f59e0b', '#10b981']
        color = colors[hash(obj.email) % len(colors)]
        return format_html(
            '<div style="display:flex;align-items:center;gap:10px;">'
            '<div style="width:36px;height:36px;border-radius:50%;background:{};'
            'display:flex;align-items:center;justify-content:center;'
            'color:#fff;font-weight:700;font-size:13px;flex-shrink:0;">{}</div>'
            '<span style="font-weight:600;">{}</span>'
            '</div>',
            color, initials, obj.full_name or obj.email
        )
    avatar_and_name.short_description = _('المستخدم')

    def user_type_badge(self, obj):
        styles = {
            'admin': ('background:#6366f1;color:#fff', '👑 مدير'),
            'student': ('background:#0ea5e9;color:#fff', '🎓 طالب'),
        }
        style, label = styles.get(obj.user_type, ('background:#94a3b8;color:#fff', obj.user_type))
        return format_html(
            '<span style="{};padding:3px 10px;border-radius:20px;font-size:11px;font-weight:600;">{}</span>',
            style, label
        )
    user_type_badge.short_description = _('النوع')

    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html('<span style="color:#10b981;font-size:18px;">●</span>')
        return format_html('<span style="color:#ef4444;font-size:18px;">●</span>')
    is_active_badge.short_description = _('نشط')

    def is_email_verified_badge(self, obj):
        if obj.is_email_verified:
            return format_html('<span style="color:#10b981;">✓ محقق</span>')
        return format_html('<span style="color:#f59e0b;">✗ غير محقق</span>')
    is_email_verified_badge.short_description = _('البريد')


# ============================================================
# STUDENT ADMIN
# ============================================================

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = (
        'student_info', 'overall_level_badge', 'placement_test_taken',
        'placement_test_date', 'phone_number'
    )
    list_filter = (
        'overall_level', 'placement_test_taken',
        'reading_level', 'writing_level'
    )
    search_fields = ('user__email', 'user__full_name', 'phone_number')
    readonly_fields = ('placement_test_date', 'level_radar')
    list_per_page = 25
    ordering = ('-user__date_joined',)

    fieldsets = (
        (_('معلومات الطالب'), {
            'fields': ('user', 'profile_picture', 'phone_number', 'birth_date', 'bio'),
        }),
        (_('المستوى العام'), {
            'fields': ('overall_level', 'placement_test_taken', 'placement_test_date', 'level_radar'),
        }),
        (_('المستويات التفصيلية'), {
            'fields': (
                ('reading_level', 'writing_level'),
                ('listening_level', 'speaking_level'),
                ('grammar_level', 'vocabulary_level'),
            ),
            'classes': ('collapse',),
        }),
    )

    def student_info(self, obj):
        initials = obj.user.full_name[:2].upper() if obj.user.full_name else '??'
        colors = ['#6366f1', '#8b5cf6', '#ec4899', '#14b8a6']
        color = colors[hash(obj.user.email) % len(colors)]
        return format_html(
            '<div style="display:flex;align-items:center;gap:10px;">'
            '<div style="width:36px;height:36px;border-radius:50%;background:{};'
            'display:flex;align-items:center;justify-content:center;'
            'color:#fff;font-weight:700;font-size:13px;">{}</div>'
            '<div><div style="font-weight:600;">{}</div>'
            '<div style="font-size:11px;color:#64748b;">{}</div></div>'
            '</div>',
            color, initials, obj.user.full_name, obj.user.email
        )
    student_info.short_description = _('الطالب')

    def overall_level_badge(self, obj):
        colors = {
            'not_tested': ('#94a3b8', '⬜ لم يختبر'),
            'A1': ('#f87171', '🔴 A1'),
            'A2': ('#fb923c', '🟠 A2'),
            'B1': ('#facc15', '🟡 B1'),
            'B2': ('#34d399', '🟢 B2'),
        }
        color, label = colors.get(obj.overall_level, ('#94a3b8', obj.overall_level))
        return format_html(
            '<span style="background:{};color:#fff;padding:3px 12px;'
            'border-radius:20px;font-size:12px;font-weight:600;">{}</span>',
            color, label
        )
    overall_level_badge.short_description = _('المستوى')

    def level_radar(self, obj):
        if not obj.pk:
            return '-'
        levels = obj.get_skill_levels()
        level_order = ['not_tested', 'A1', 'A2', 'B1', 'B2']
        colors = {
            'not_tested': '#e2e8f0',
            'A1': '#fca5a5',
            'A2': '#fdba74',
            'B1': '#fde68a',
            'B2': '#6ee7b7',
        }
        labels_ar = {
            'reading': 'قراءة',
            'writing': 'كتابة',
            'listening': 'استماع',
            'speaking': 'تحدث',
            'grammar': 'قواعد',
            'vocabulary': 'مفردات',
        }
        bars = ''
        for skill, level in levels.items():
            pct = (level_order.index(level) / (len(level_order) - 1)) * 100 if level in level_order else 0
            color = colors.get(level, '#e2e8f0')
            bars += format_html(
                '<div style="margin:6px 0;">'
                '<div style="display:flex;justify-content:space-between;font-size:12px;margin-bottom:3px;">'
                '<span>{}</span><span style="font-weight:600;">{}</span></div>'
                '<div style="background:#f1f5f9;border-radius:4px;height:8px;">'
                '<div style="background:{};width:{}%;height:8px;border-radius:4px;transition:width 0.3s;"></div>'
                '</div></div>',
                labels_ar.get(skill, skill), level, color, pct
            )
        return format_html('<div style="min-width:300px">{}</div>', bars)
    level_radar.short_description = _('تفاصيل المستويات')


# ============================================================
# EMAIL VERIFICATION ADMIN
# ============================================================

@admin.register(EmailVerification)
class EmailVerificationAdmin(admin.ModelAdmin):
    list_display = ('user_email', 'code', 'status_badge', 'created_at', 'expires_at')
    list_filter = ('is_verified',)
    search_fields = ('user__email', 'code')
    readonly_fields = ('code', 'created_at', 'expires_at', 'is_verified')
    ordering = ('-created_at',)
    list_per_page = 30

    def user_email(self, obj):
        return format_html('<span style="font-weight:600;">{}</span>', obj.user.email)
    user_email.short_description = _('البريد الإلكتروني')

    def status_badge(self, obj):
        if obj.is_verified:
            return format_html(
                '<span style="background:#10b981;color:#fff;padding:3px 10px;'
                'border-radius:20px;font-size:11px;font-weight:600;">✓ تم التحقق</span>'
            )
        elif not obj.expires_at or obj.is_expired():
            return format_html(
                '<span style="background:#ef4444;color:#fff;padding:3px 10px;'
                'border-radius:20px;font-size:11px;font-weight:600;">✗ منتهي الصلاحية</span>'
            )
        else:
            return format_html(
                '<span style="background:#f59e0b;color:#fff;padding:3px 10px;'
                'border-radius:20px;font-size:11px;font-weight:600;">⏳ في الانتظار</span>'
            )
    status_badge.short_description = _('الحالة')

    def has_add_permission(self, request):
        return False