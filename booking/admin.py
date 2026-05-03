# admin.py

from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Teacher, Program, ProgramSchedule,
    Subscription, CustomProgram, CustomProgramSchedule,
    Review, Booking
)


# ============================================
# Inlines
# ============================================

class ProgramScheduleInline(admin.TabularInline):
    model = ProgramSchedule
    extra = 1
    fields = ['day_of_week', 'time']


class CustomProgramScheduleInline(admin.TabularInline):
    model = CustomProgramSchedule
    extra = 1
    fields = ['day_of_week', 'time']


class ProgramInline(admin.TabularInline):
    model = Program
    extra = 0
    fields = ['title', 'recurrence', 'duration', 'price', 'is_active']
    show_change_link = True
    readonly_fields = ['title']


class ReviewInline(admin.TabularInline):
    model = Review
    extra = 0
    fields = ['student', 'rating', 'comment', 'created_at']
    readonly_fields = ['student', 'rating', 'comment', 'created_at']
    can_delete = False


# ============================================
# Teacher Admin
# ============================================

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = [
        'teacher_code', 'name', 'subject',
        'years_of_experience', 'get_average_rating',
        'get_reviews_count', 'is_active', 'created_at'
    ]
    list_filter = ['is_active', 'subject']
    search_fields = ['name', 'email', 'teacher_code', 'subject']
    readonly_fields = [
        'teacher_code', 'created_at', 'updated_at',
        'get_average_rating', 'get_reviews_count', 'get_profile_picture_preview'
    ]
    list_editable = ['is_active']
    inlines = [ProgramInline, ReviewInline]

    fieldsets = (
        ('المعلومات الأساسية', {
            'fields': (
                'teacher_code', 'name', 'email',
                'subject', 'years_of_experience', 'is_active'
            )
        }),
        ('الصورة الشخصية', {
            'fields': ('profile_picture', 'get_profile_picture_preview'),
        }),
        ('نبذة مختصرة', {
            'fields': ('bio',),
        }),
        ('التقييمات', {
            'fields': ('get_average_rating', 'get_reviews_count'),
        }),
        ('التواريخ', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='متوسط التقييم')
    def get_average_rating(self, obj):
        rating = obj.average_rating
        if rating:
            return f"{rating} ⭐"
        return "لا يوجد"

    @admin.display(description='عدد التقييمات')
    def get_reviews_count(self, obj):
        return obj.reviews_count

    @admin.display(description='الصورة الشخصية')
    def get_profile_picture_preview(self, obj):
        if obj.profile_picture:
            return format_html(
                '<img src="{}" style="width:80px; height:80px; border-radius:50%; object-fit:cover;" />',
                obj.profile_picture.url
            )
        return "لا توجد صورة"


# ============================================
# Program Admin
# ============================================

@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'teacher', 'recurrence',
        'duration', 'price', 'get_schedules_count',
        'get_subscriptions_count', 'is_active', 'created_at'
    ]
    list_filter = ['is_active', 'recurrence', 'teacher']
    search_fields = ['title', 'teacher__name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['is_active', 'price']
    inlines = [ProgramScheduleInline]

    fieldsets = (
        ('معلومات البرنامج', {
            'fields': ('teacher', 'title', 'description', 'is_active')
        }),
        ('التفاصيل', {
            'fields': ('recurrence', 'duration', 'price')
        }),
        ('التواريخ', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='عدد المواعيد')
    def get_schedules_count(self, obj):
        return obj.schedules.count()

    @admin.display(description='عدد المشتركين')
    def get_subscriptions_count(self, obj):
        return obj.subscriptions.filter(payment_status='paid').count()


# ============================================
# ProgramSchedule Admin
# ============================================

@admin.register(ProgramSchedule)
class ProgramScheduleAdmin(admin.ModelAdmin):
    list_display = ['program', 'get_teacher', 'day_of_week', 'time']
    list_filter = ['day_of_week', 'program__teacher']
    search_fields = ['program__title', 'program__teacher__name']

    @admin.display(description='المدرس')
    def get_teacher(self, obj):
        return obj.program.teacher.name


# ============================================
# Subscription Admin
# ============================================

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = [
        'reference_number', 'student', 'program',
        'amount', 'get_payment_status_badge', 'created_at'
    ]
    list_filter = ['payment_status', 'program__teacher', 'created_at']
    search_fields = [
        'reference_number', 'payment_id',
        'student__username', 'student__email',
        'program__title'
    ]
    readonly_fields = ['reference_number', 'created_at']

    fieldsets = (
        ('بيانات الاشتراك', {
            'fields': ('reference_number', 'student', 'program')
        }),
        ('بيانات الدفع', {
            'fields': ('payment_id', 'payment_status', 'amount')
        }),
        ('التواريخ', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='حالة الدفع')
    def get_payment_status_badge(self, obj):
        colors = {
            'paid':    ('green',  'مدفوع'),
            'failed':  ('red',    'فشل الدفع'),
            'pending': ('orange', 'في الانتظار'),
        }
        color, label = colors.get(obj.payment_status, ('gray', obj.payment_status))
        return format_html(
            '<span style="color:white; background:{}; padding:3px 10px; '
            'border-radius:12px; font-size:12px;">{}</span>',
            color, label
        )


# ============================================
# CustomProgram Admin
# ============================================

@admin.register(CustomProgram)
class CustomProgramAdmin(admin.ModelAdmin):
    list_display = [
        'student', 'teacher', 'recurrence',
        'duration', 'whatsapp_number', 'created_at'
    ]
    list_filter = ['recurrence', 'teacher', 'created_at']
    search_fields = [
        'student__username', 'student__email',
        'teacher__name', 'curriculum', 'whatsapp_number'
    ]
    readonly_fields = ['created_at']
    inlines = [CustomProgramScheduleInline]

    fieldsets = (
        ('بيانات الطلب', {
            'fields': ('student', 'teacher', 'whatsapp_number')
        }),
        ('تفاصيل البرنامج', {
            'fields': ('recurrence', 'duration', 'curriculum')
        }),
        ('التواريخ', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )


# ============================================
# CustomProgramSchedule Admin
# ============================================

@admin.register(CustomProgramSchedule)
class CustomProgramScheduleAdmin(admin.ModelAdmin):
    list_display = ['custom_program', 'get_student', 'get_teacher', 'day_of_week', 'time']
    list_filter = ['day_of_week', 'custom_program__teacher']
    search_fields = ['custom_program__student__username', 'custom_program__teacher__name']

    @admin.display(description='الطالب')
    def get_student(self, obj):
        return obj.custom_program.student

    @admin.display(description='المدرس')
    def get_teacher(self, obj):
        return obj.custom_program.teacher.name


# ============================================
# Review Admin
# ============================================

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = [
        'student', 'teacher', 'get_rating_stars',
        'get_comment_preview', 'created_at'
    ]
    list_filter = ['rating', 'teacher', 'created_at']
    search_fields = ['student__username', 'teacher__name', 'comment']
    readonly_fields = ['created_at']

    @admin.display(description='التقييم')
    def get_rating_stars(self, obj):
        return '⭐' * obj.rating

    @admin.display(description='التعليق')
    def get_comment_preview(self, obj):
        if obj.comment:
            return obj.comment[:60] + '...' if len(obj.comment) > 60 else obj.comment
        return '-'


# ============================================
# Booking Admin
# ============================================

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = [
        'student', 'teacher', 'phone_number',
        'requested_datetime', 'get_notes_preview', 'created_at'
    ]
    list_filter = ['teacher', 'requested_datetime', 'created_at']
    search_fields = [
        'student__username', 'student__email',
        'teacher__name', 'phone_number'
    ]
    readonly_fields = ['created_at']

    fieldsets = (
        ('بيانات الحجز', {
            'fields': ('student', 'teacher', 'phone_number')
        }),
        ('تفاصيل الموعد', {
            'fields': ('requested_datetime', 'notes')
        }),
        ('التواريخ', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='الملاحظات')
    def get_notes_preview(self, obj):
        if obj.notes:
            return obj.notes[:60] + '...' if len(obj.notes) > 60 else obj.notes
        return '-'