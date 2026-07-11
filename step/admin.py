# admin.py

from django.contrib import admin
from django.utils.html import format_html
from .models import (
    STEPSkill,
    StudentSTEPProgress,
    StudentSTEPQuestionAttempt,
    StudentSTEPQuestionView,
    STEPSubscriptionPlan,
    STEPSubscription,
)


# ============================================
# STEP Skill
# ============================================

class ChildSkillInline(admin.TabularInline):
    """يعرض المهارات الفرعية جوه صفحة الـ GENERAL_PATH"""
    model = STEPSkill.child_skills.through
    fk_name = 'from_stepskill'
    extra = 0
    verbose_name = "مهارة فرعية"
    verbose_name_plural = "المهارات الفرعية"


@admin.register(STEPSkill)
class STEPSkillAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'title', 'skill_type', 'question_order_type',
        'order', 'is_active', 'total_questions_display', 'created_at',
    )
    list_display_links = ('id', 'title')
    list_filter = ('skill_type', 'question_order_type', 'is_active')
    search_fields = ('title', 'description')
    ordering = ('order', 'skill_type')
    list_editable = ('order', 'is_active')
    readonly_fields = ('created_at', 'updated_at', 'total_questions_display')
    filter_horizontal = ('child_skills',)

    fieldsets = (
        ('البيانات الأساسية', {
            'fields': ('skill_type', 'title', 'description', 'icon')
        }),
        ('الإعدادات', {
            'fields': ('order', 'is_active', 'question_order_type')
        }),
        ('المسار العام (GENERAL_PATH فقط)', {
            'fields': ('child_skills',),
            'classes': ('collapse',),
        }),
        ('معلومات إضافية', {
            'fields': ('total_questions_display', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def total_questions_display(self, obj):
        return obj.get_total_questions_count()
    total_questions_display.short_description = "إجمالي الأسئلة"


# ============================================
# Student Progress
# ============================================

@admin.register(StudentSTEPProgress)
class StudentSTEPProgressAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'student', 'skill', 'viewed_questions_count',
        'total_score', 'progress_percentage_display', 'updated_at',
    )
    list_filter = ('skill__skill_type', 'skill')
    search_fields = ('student__email', 'student__username', 'skill__title')
    autocomplete_fields = ('student', 'skill')
    readonly_fields = ('created_at', 'updated_at', 'progress_percentage_display')
    list_select_related = ('student', 'skill')

    def progress_percentage_display(self, obj):
        return f"{obj.calculate_progress_percentage()}%"
    progress_percentage_display.short_description = "نسبة التقدم"


# ============================================
# Student Question Attempt
# ============================================

@admin.register(StudentSTEPQuestionAttempt)
class StudentSTEPQuestionAttemptAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'student', 'skill', 'question_type', 'question_id',
        'attempts_count', 'is_solved', 'points_earned',
        'used_show_answer', 'solved_at',
    )
    list_filter = ('question_type', 'is_solved', 'used_show_answer', 'skill')
    search_fields = ('student__email', 'student__username', 'question_id')
    autocomplete_fields = ('student', 'skill')
    readonly_fields = ('created_at', 'updated_at', 'solved_at')
    list_select_related = ('student', 'skill')
    date_hierarchy = 'created_at'


# ============================================
# Student Question View (Legacy)
# ============================================

@admin.register(StudentSTEPQuestionView)
class StudentSTEPQuestionViewAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'student', 'skill', 'question_type',
        'question_id', 'viewed_at',
    )
    list_filter = ('question_type', 'skill')
    search_fields = ('student__email', 'student__username', 'question_id')
    autocomplete_fields = ('student', 'skill')
    readonly_fields = ('viewed_at',)
    list_select_related = ('student', 'skill')
    date_hierarchy = 'viewed_at'


# ============================================
# Subscription Plan
# ============================================

@admin.register(STEPSubscriptionPlan)
class STEPSubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'plan_type', 'price', 'duration_days',
        'is_active', 'description',
    )
    list_filter = ('plan_type', 'is_active')
    list_editable = ('price', 'is_active')
    search_fields = ('description',)
    ordering = ('price',)


# ============================================
# Subscription
# ============================================

@admin.register(STEPSubscription)
class STEPSubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'student', 'plan', 'payment_status_badge',
        'amount', 'starts_at', 'expires_at', 'is_active_display', 'created_at',
    )
    list_filter = ('payment_status', 'plan')
    search_fields = ('student__email', 'student__username', 'payment_id')
    autocomplete_fields = ('student',)
    readonly_fields = ('created_at', 'updated_at', 'is_active_display')
    date_hierarchy = 'created_at'
    list_select_related = ('student', 'plan')

    def is_active_display(self, obj):
        return obj.is_active
    is_active_display.short_description = "نشط الآن؟"
    is_active_display.boolean = True

    def payment_status_badge(self, obj):
        colors = {
            'pending': '#f0ad4e',
            'paid': '#5cb85c',
            'failed': '#d9534f',
        }
        color = colors.get(obj.payment_status, '#777')
        return format_html(
            '<span style="background:{}; color:white; padding:3px 10px; '
            'border-radius:10px; font-size:12px;">{}</span>',
            color, obj.get_payment_status_display()
        )
    payment_status_badge.short_description = "حالة الدفع"