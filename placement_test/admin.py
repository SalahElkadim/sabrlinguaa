from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count, Avg
from .models import (
    PlacementTest,
    PlacementTestQuestionBank,
    StudentPlacementTestAttempt,
    StudentPlacementTestAnswer
)


# ============================================
# Inline Admins
# ============================================

class PlacementTestQuestionBankInline(admin.TabularInline):
    """
    عرض الأسئلة المرتبطة بالاختبار
    """
    model = PlacementTestQuestionBank
    extra = 1
    readonly_fields = ['get_question_type', 'created_at']
    fields = ['content_type', 'object_id', 'get_question_type', 'is_active', 'created_at']
    
    def get_question_type(self, obj):
        if obj.id:
            return obj.get_question_type_display()
        return '-'
    get_question_type.short_description = 'نوع السؤال'


class StudentPlacementTestAnswerInline(admin.TabularInline):
    """
    عرض إجابات الطالب
    """
    model = StudentPlacementTestAnswer
    extra = 0
    readonly_fields = ['get_question_type', 'is_correct', 'points_earned', 'answered_at']
    fields = ['get_question_type', 'object_id', 'selected_choice', 'is_correct', 'points_earned', 'answered_at']
    can_delete = False
    
    def get_question_type(self, obj):
        if obj.id:
            return obj.get_question_type_display()
        return '-'
    get_question_type.short_description = 'نوع السؤال'
    
    def has_add_permission(self, request, obj=None):
        return False


# ============================================
# Main Admins
# ============================================

@admin.register(PlacementTest)
class PlacementTestAdmin(admin.ModelAdmin):
    """
    إدارة اختبارات تحديد المستوى
    """
    list_display = [
        'title',
        'total_questions',
        'duration_minutes',
        'get_questions_distribution',
        'get_total_in_bank',
        'get_attempts_count',
        'is_active',
        'created_at'
    ]
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'description']
    readonly_fields = ['created_at', 'updated_at', 'get_total_in_bank', 'get_attempts_count']
    
    fieldsets = [
        ('معلومات عامة', {
            'fields': ['title', 'description', 'is_active']
        }),
        ('إعدادات الاختبار', {
            'fields': ['duration_minutes', 'total_questions']
        }),
        ('توزيع الأسئلة', {
            'fields': [
                'vocabulary_count',
                'grammar_count',
                'reading_count',
                'listening_count',
                'speaking_count',
                'writing_count'
            ],
            'description': 'يجب أن يكون مجموع الأسئلة = إجمالي الأسئلة'
        }),
        ('معايير المستويات (CEFR)', {
            'fields': [
                ('a1_min_score', 'a1_max_score'),
                ('a2_min_score', 'a2_max_score'),
                ('b1_min_score', 'b1_max_score'),
                ('b2_min_score', 'b2_max_score'),
            ],
            'classes': ['collapse']
        }),
        ('إحصائيات', {
            'fields': ['get_total_in_bank', 'get_attempts_count', 'created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]
    
    inlines = [PlacementTestQuestionBankInline]
    
    def get_questions_distribution(self, obj):
        """
        عرض توزيع الأسئلة
        """
        return format_html(
            '<span title="المفردات: {} | القواعد: {} | القراءة: {} | الاستماع: {} | التحدث: {} | الكتابة: {}">'
            'V:{} G:{} R:{} L:{} S:{} W:{}'
            '</span>',
            obj.vocabulary_count, obj.grammar_count, obj.reading_count,
            obj.listening_count, obj.speaking_count, obj.writing_count,
            obj.vocabulary_count, obj.grammar_count, obj.reading_count,
            obj.listening_count, obj.speaking_count, obj.writing_count
        )
    get_questions_distribution.short_description = 'توزيع الأسئلة'
    
    def get_total_in_bank(self, obj):
        """
        إجمالي الأسئلة في البنك
        """
        total = obj.get_total_questions_in_bank()
        if total > 0:
            return format_html(
                '<span style="color: green; font-weight: bold;">{} سؤال</span>',
                total
            )
        return format_html('<span style="color: red;">0 سؤال</span>')
    get_total_in_bank.short_description = 'أسئلة البنك'
    
    def get_attempts_count(self, obj):
        """
        عدد المحاولات
        """
        count = obj.student_attempts.count()
        if count > 0:
            url = reverse('admin:placement_test_studentplacementtestatempt_changelist') + f'?placement_test__id__exact={obj.id}'
            return format_html(
                '<a href="{}">{} محاولة</a>',
                url, count
            )
        return '0 محاولة'
    get_attempts_count.short_description = 'عدد المحاولات'
    
    def save_model(self, request, obj, form, change):
        """
        التحقق من صحة توزيع الأسئلة قبل الحفظ
        """
        if not obj.validate_question_distribution():
            from django.contrib import messages
            messages.error(
                request,
                f'خطأ: مجموع الأسئلة ({obj.vocabulary_count + obj.grammar_count + obj.reading_count + obj.listening_count + obj.speaking_count + obj.writing_count}) '
                f'لا يساوي إجمالي الأسئلة ({obj.total_questions})'
            )
        super().save_model(request, obj, form, change)


@admin.register(PlacementTestQuestionBank)
class PlacementTestQuestionBankAdmin(admin.ModelAdmin):
    """
    إدارة بنك أسئلة اختبار تحديد المستوى
    """
    list_display = [
        'placement_test',
        'get_question_type',
        'object_id',
        'is_active',
        'added_by',
        'created_at'
    ]
    list_filter = ['placement_test', 'content_type', 'is_active', 'created_at']
    search_fields = ['placement_test__title', 'object_id']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = [
        (None, {
            'fields': ['placement_test', 'content_type', 'object_id']
        }),
        ('معلومات إضافية', {
            'fields': ['is_active', 'added_by', 'created_at', 'updated_at']
        })
    ]
    
    def get_question_type(self, obj):
        """
        عرض نوع السؤال
        """
        return obj.get_question_type_display()
    get_question_type.short_description = 'نوع السؤال'
    
    def save_model(self, request, obj, form, change):
        """
        حفظ المستخدم الذي أضاف السؤال
        """
        if not change:  # إذا كان سؤال جديد
            obj.added_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(StudentPlacementTestAttempt)
class StudentPlacementTestAttemptAdmin(admin.ModelAdmin):
    """
    إدارة محاولات الطلاب
    """
    list_display = [
        'student',
        'placement_test',
        'score',
        'level_achieved',
        'status',
        'get_duration_display',
        'started_at',
        'completed_at'
    ]
    list_filter = ['status', 'level_achieved', 'placement_test', 'started_at']
    search_fields = ['student__username', 'student__email', 'placement_test__title']
    readonly_fields = [
        'started_at',
        'created_at',
        'updated_at',
        'get_duration_display',
        'get_answers_count',
        'get_correct_answers',
        'get_accuracy'
    ]
    
    fieldsets = [
        ('معلومات عامة', {
            'fields': ['student', 'placement_test', 'status']
        }),
        ('النتائج', {
            'fields': ['score', 'level_achieved']
        }),
        ('التوقيتات', {
            'fields': ['started_at', 'completed_at', 'get_duration_display']
        }),
        ('الأسئلة المختارة', {
            'fields': ['selected_questions_json'],
            'classes': ['collapse']
        }),
        ('إحصائيات', {
            'fields': ['get_answers_count', 'get_correct_answers', 'get_accuracy'],
            'classes': ['collapse']
        }),
        ('معلومات إضافية', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]
    
    inlines = [StudentPlacementTestAnswerInline]
    
    def get_duration_display(self, obj):
        """
        عرض المدة الفعلية
        """
        duration = obj.get_duration()
        if duration:
            return f"{duration:.1f} دقيقة"
        return '-'
    get_duration_display.short_description = 'المدة الفعلية'
    
    def get_answers_count(self, obj):
        """
        عدد الإجابات
        """
        return obj.answers.count()
    get_answers_count.short_description = 'عدد الإجابات'
    
    def get_correct_answers(self, obj):
        """
        عدد الإجابات الصحيحة
        """
        return obj.answers.filter(is_correct=True).count()
    get_correct_answers.short_description = 'الإجابات الصحيحة'
    
    def get_accuracy(self, obj):
        """
        نسبة الدقة
        """
        total = obj.answers.count()
        if total == 0:
            return '0%'
        correct = obj.answers.filter(is_correct=True).count()
        accuracy = (correct / total) * 100
        
        color = 'green' if accuracy >= 70 else 'orange' if accuracy >= 50 else 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.1f}%</span>',
            color, accuracy
        )
    get_accuracy.short_description = 'نسبة الدقة'


@admin.register(StudentPlacementTestAnswer)
class StudentPlacementTestAnswerAdmin(admin.ModelAdmin):
    """
    إدارة إجابات الطلاب
    """
    list_display = [
        'attempt',
        'get_question_type',
        'object_id',
        'selected_choice',
        'is_correct',
        'points_earned',
        'answered_at'
    ]
    list_filter = ['is_correct', 'content_type', 'answered_at']
    search_fields = ['attempt__student__username', 'object_id']
    readonly_fields = ['answered_at', 'created_at', 'updated_at']
    
    fieldsets = [
        ('معلومات عامة', {
            'fields': ['attempt', 'content_type', 'object_id']
        }),
        ('الإجابة', {
            'fields': ['selected_choice', 'text_answer']
        }),
        ('التقييم', {
            'fields': ['is_correct', 'points_earned']
        }),
        ('معلومات إضافية', {
            'fields': ['time_spent_seconds', 'answered_at', 'created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]
    
    def get_question_type(self, obj):
        """
        عرض نوع السؤال
        """
        return obj.get_question_type_display()
    get_question_type.short_description = 'نوع السؤال'


# ============================================
# Custom Admin Actions
# ============================================

@admin.action(description='تفعيل الاختبارات المحددة')
def activate_tests(modeladmin, request, queryset):
    """
    تفعيل اختبارات متعددة
    """
    queryset.update(is_active=True)

@admin.action(description='إلغاء تفعيل الاختبارات المحددة')
def deactivate_tests(modeladmin, request, queryset):
    """
    إلغاء تفعيل اختبارات متعددة
    """
    queryset.update(is_active=False)

# إضافة الـ actions للـ PlacementTestAdmin
PlacementTestAdmin.actions = [activate_tests, deactivate_tests]