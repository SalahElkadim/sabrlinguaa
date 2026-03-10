from django.contrib import admin
from django.utils.html import format_html
from .models import STEPSkill, StudentSTEPProgress, StudentSTEPQuestionView


# ============================================
# STEP Skill Admin
# ============================================

@admin.register(STEPSkill)
class STEPSkillAdmin(admin.ModelAdmin):
    list_display = ['skill_icon', 'skill_type_badge', 'title', 'total_questions', 'order', 'is_active']
    list_filter = ['skill_type', 'is_active']
    search_fields = ['title', 'skill_type']
    ordering = ['order', 'skill_type']
    list_editable = ['order', 'is_active']

    fieldsets = (
        ('معلومات المهارة', {
            'fields': ('skill_type', 'title', 'description', 'icon')
        }),
        ('الترتيب والتفعيل', {
            'fields': ('order', 'is_active')
        }),
    )

    def skill_icon(self, obj):
        if obj.icon:
            return format_html(
                '<img src="{}" style="width:36px;height:36px;border-radius:8px;object-fit:cover;" />',
                obj.icon.url
            )
        icons = {
            'VOCABULARY': '📚',
            'GRAMMAR': '📝',
            'READING': '📖',
            'WRITING': '✏️',
        }
        icon = icons.get(obj.skill_type, '❓')
        colors = {
            'VOCABULARY': '#6366f1',
            'GRAMMAR': '#8b5cf6',
            'READING': '#0ea5e9',
            'WRITING': '#10b981',
        }
        color = colors.get(obj.skill_type, '#94a3b8')
        return format_html(
            '<div style="width:36px;height:36px;border-radius:8px;background:{};'
            'display:flex;align-items:center;justify-content:center;font-size:18px;">{}</div>',
            color, icon
        )
    skill_icon.short_description = ''

    def skill_type_badge(self, obj):
        colors = {
            'VOCABULARY': ('#6366f1', '📚 Vocabulary'),
            'GRAMMAR':    ('#8b5cf6', '📝 Grammar'),
            'READING':    ('#0ea5e9', '📖 Reading'),
            'WRITING':    ('#10b981', '✏️ Writing'),
        }
        color, label = colors.get(obj.skill_type, ('#94a3b8', obj.skill_type))
        return format_html(
            '<span style="background:{};color:#fff;padding:3px 12px;'
            'border-radius:20px;font-size:11px;font-weight:600;">{}</span>',
            color, label
        )
    skill_type_badge.short_description = 'النوع'

    def total_questions(self, obj):
        count = obj.get_total_questions_count()
        color = '#10b981' if count > 0 else '#ef4444'
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 10px;'
            'border-radius:12px;font-size:12px;font-weight:600;">{} سؤال</span>',
            color, count
        )
    total_questions.short_description = 'عدد الأسئلة'


# ============================================
# Student STEP Progress Admin
# ============================================

@admin.register(StudentSTEPProgress)
class StudentSTEPProgressAdmin(admin.ModelAdmin):
    list_display = ['student_info', 'skill_badge', 'viewed_questions_count', 'total_score', 'progress_bar']
    list_filter = ['skill__skill_type']
    search_fields = ['student__email', 'student__full_name']
    ordering = ['-total_score']
    readonly_fields = [
        'student', 'skill', 'viewed_questions_count',
        'total_score', 'progress_display', 'created_at', 'updated_at'
    ]

    fieldsets = (
        ('معلومات الطالب', {
            'fields': ('student', 'skill')
        }),
        ('الإحصائيات', {
            'fields': ('viewed_questions_count', 'total_score', 'progress_display')
        }),
        ('التواريخ', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def student_info(self, obj):
        initials = obj.student.full_name[:2].upper() if obj.student.full_name else obj.student.email[:2].upper()
        colors = ['#6366f1', '#8b5cf6', '#ec4899', '#14b8a6', '#f59e0b', '#10b981']
        color = colors[hash(obj.student.email) % len(colors)]
        return format_html(
            '<div style="display:flex;align-items:center;gap:8px;">'
            '<div style="width:32px;height:32px;border-radius:50%;background:{};'
            'display:flex;align-items:center;justify-content:center;'
            'color:#fff;font-weight:700;font-size:12px;">{}</div>'
            '<div><div style="font-weight:600;font-size:13px;">{}</div>'
            '<div style="font-size:11px;color:#64748b;">{}</div></div>'
            '</div>',
            color, initials,
            obj.student.full_name or '', obj.student.email
        )
    student_info.short_description = 'الطالب'

    def skill_badge(self, obj):
        colors = {
            'VOCABULARY': ('#6366f1', '📚 Vocabulary'),
            'GRAMMAR':    ('#8b5cf6', '📝 Grammar'),
            'READING':    ('#0ea5e9', '📖 Reading'),
            'WRITING':    ('#10b981', '✏️ Writing'),
        }
        color, label = colors.get(obj.skill.skill_type, ('#94a3b8', obj.skill.title))
        return format_html(
            '<span style="background:{};color:#fff;padding:3px 10px;'
            'border-radius:20px;font-size:11px;font-weight:600;">{}</span>',
            color, label
        )
    skill_badge.short_description = 'المهارة'

    def progress_bar(self, obj):
        pct = obj.calculate_progress_percentage()
        color = '#10b981' if pct >= 70 else '#f59e0b' if pct >= 30 else '#6366f1'
        return format_html(
            '<div style="display:flex;align-items:center;gap:8px;min-width:150px;">'
            '<div style="flex:1;background:#f1f5f9;border-radius:4px;height:8px;">'
            '<div style="background:{};width:{}%;height:8px;border-radius:4px;"></div>'
            '</div>'
            '<span style="font-size:11px;font-weight:600;color:{}">{:.0f}%</span>'
            '</div>',
            color, min(pct, 100), color, pct
        )
    progress_bar.short_description = 'التقدم'

    def progress_display(self, obj):
        pct = obj.calculate_progress_percentage()
        total = obj.skill.get_total_questions_count()
        color = '#10b981' if pct >= 70 else '#f59e0b' if pct >= 30 else '#6366f1'
        return format_html(
            '<div style="max-width:400px;">'
            '<div style="display:flex;justify-content:space-between;margin-bottom:6px;">'
            '<span style="font-weight:600;">التقدم الكلي</span>'
            '<span style="font-weight:700;color:{}">{:.1f}%</span>'
            '</div>'
            '<div style="background:#f1f5f9;border-radius:6px;height:12px;">'
            '<div style="background:{};width:{}%;height:12px;border-radius:6px;"></div>'
            '</div>'
            '<div style="margin-top:6px;font-size:12px;color:#64748b;">'
            '{} من {} سؤال</div>'
            '</div>',
            color, pct, color, min(pct, 100),
            obj.viewed_questions_count, total
        )
    progress_display.short_description = 'تفاصيل التقدم'



# ============================================
# Student STEP Question View Admin
# ============================================

@admin.register(StudentSTEPQuestionView)
class StudentSTEPQuestionViewAdmin(admin.ModelAdmin):
    list_display = ['student_email', 'skill_badge', 'question_type_badge', 'question_id', 'viewed_at']
    list_filter = ['question_type', 'skill__skill_type']
    search_fields = ['student__email', 'student__full_name']
    ordering = ['-viewed_at']
    readonly_fields = ['student', 'skill', 'question_type', 'question_id', 'viewed_at', 'created_at', 'updated_at']
    date_hierarchy = 'viewed_at'

    def student_email(self, obj):
        return format_html('<span style="font-weight:600;">{}</span>', obj.student.email)
    student_email.short_description = 'الطالب'

    def skill_badge(self, obj):
        colors = {
            'VOCABULARY': ('#6366f1', '📚'),
            'GRAMMAR':    ('#8b5cf6', '📝'),
            'READING':    ('#0ea5e9', '📖'),
            'WRITING':    ('#10b981', '✏️'),
        }
        color, icon = colors.get(obj.skill.skill_type, ('#94a3b8', '❓'))
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 10px;'
            'border-radius:12px;font-size:11px;">{} {}</span>',
            color, icon, obj.skill.title
        )
    skill_badge.short_description = 'المهارة'

    def question_type_badge(self, obj):
        colors = {
            'VOCABULARY': ('#6366f1', 'Vocabulary'),
            'GRAMMAR':    ('#8b5cf6', 'Grammar'),
            'READING':    ('#0ea5e9', 'Reading'),
            'WRITING':    ('#10b981', 'Writing'),
        }
        color, label = colors.get(obj.question_type, ('#94a3b8', obj.question_type))
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 10px;'
            'border-radius:12px;font-size:11px;font-weight:600;">{}</span>',
            color, label
        )
    question_type_badge.short_description = 'نوع السؤال'
