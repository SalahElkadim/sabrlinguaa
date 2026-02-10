from django.contrib import admin
from .models import (
    Level,
    Unit,
    Lesson,
    ReadingLessonContent,
    ListeningLessonContent,
    SpeakingLessonContent,
    WritingLessonContent,
    UnitExam,
    LevelExam,
    StudentLevel,
    StudentUnit,
    StudentLesson,
    StudentUnitExamAttempt,
    StudentLevelExamAttempt,
)


# ============================================
# Core Models Admin
# ============================================

@admin.register(Level)
class LevelAdmin(admin.ModelAdmin):
    list_display = ['code', 'title', 'order', 'is_active', 'created_at']
    list_filter = ['is_active', 'code']
    search_fields = ['title', 'code']
    ordering = ['order', 'code']
    list_editable = ['order', 'is_active']


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ['title', 'level', 'order', 'is_active', 'created_at']
    list_filter = ['level', 'is_active']
    search_fields = ['title', 'level__title']
    ordering = ['level__order', 'order']
    list_editable = ['order', 'is_active']
    raw_id_fields = ['level']


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ['title', 'unit', 'lesson_type', 'order', 'is_active', 'created_at']
    list_filter = ['lesson_type', 'unit__level', 'is_active']
    search_fields = ['title', 'unit__title']
    ordering = ['unit__level__order', 'unit__order', 'order']
    list_editable = ['order', 'is_active']
    raw_id_fields = ['unit']


# ============================================
# Lesson Content Admin
# ============================================

@admin.register(ReadingLessonContent)
class ReadingLessonContentAdmin(admin.ModelAdmin):
    list_display = ['lesson', 'passage', 'created_at']
    search_fields = ['lesson__title', 'passage__title']
    raw_id_fields = ['lesson', 'passage']
    fieldsets = (
        ('الدرس', {
            'fields': ('lesson', 'passage')
        }),
        ('المفردات', {
            'fields': ('vocabulary_words',),
            'description': 'أدخل المفردات بصيغة JSON: [{"english_word": "dog", "translate": "كلب"}]'
        }),
        ('الشرح', {
            'fields': ('explanation',)
        }),
    )


@admin.register(ListeningLessonContent)
class ListeningLessonContentAdmin(admin.ModelAdmin):
    list_display = ['lesson', 'audio', 'created_at']
    search_fields = ['lesson__title', 'audio__title']
    raw_id_fields = ['lesson', 'audio']


@admin.register(SpeakingLessonContent)
class SpeakingLessonContentAdmin(admin.ModelAdmin):
    list_display = ['lesson', 'video', 'created_at']
    search_fields = ['lesson__title', 'video__title']
    raw_id_fields = ['lesson', 'video']


@admin.register(WritingLessonContent)
class WritingLessonContentAdmin(admin.ModelAdmin):
    list_display = ['lesson', 'title', 'created_at']
    search_fields = ['lesson__title', 'title']
    raw_id_fields = ['lesson']


# ============================================
# Exam Admin
# ============================================

@admin.register(UnitExam)
class UnitExamAdmin(admin.ModelAdmin):
    list_display = [
        'unit', 
        'title', 
        'get_total_questions', 
        'time_limit', 
        'passing_score',
        'is_active'
    ]
    list_filter = ['unit__level', 'is_active']
    search_fields = ['unit__title', 'title']
    raw_id_fields = ['unit']
    
    fieldsets = (
        ('معلومات أساسية', {
            'fields': ('unit', 'title', 'description', 'instructions', 'is_active')
        }),
        ('إعدادات الامتحان', {
            'fields': ('time_limit', 'passing_score'),
            'description': 'نسبة النجاح ثابتة 70%'
        }),
        ('عدد الأسئلة', {
            'fields': (
                'vocabulary_count',
                'grammar_count',
                'reading_questions_count',
                'listening_questions_count',
                'speaking_questions_count',
                'writing_questions_count',
            ),
            'description': 'إجمالي: 35 سؤال (افتراضي)'
        }),
    )
    
    readonly_fields = ['passing_score']


@admin.register(LevelExam)
class LevelExamAdmin(admin.ModelAdmin):
    list_display = [
        'level',
        'title',
        'get_total_questions',
        'time_limit',
        'passing_score',
        'is_active'
    ]
    list_filter = ['level', 'is_active']
    search_fields = ['level__title', 'title']
    raw_id_fields = ['level']
    
    fieldsets = (
        ('معلومات أساسية', {
            'fields': ('level', 'title', 'description', 'instructions', 'is_active')
        }),
        ('إعدادات الامتحان', {
            'fields': ('time_limit', 'passing_score'),
            'description': 'نسبة النجاح ثابتة 70%'
        }),
        ('عدد الأسئلة', {
            'fields': (
                'vocabulary_count',
                'grammar_count',
                'reading_questions_count',
                'listening_questions_count',
                'speaking_questions_count',
                'writing_questions_count',
            ),
            'description': 'إجمالي: 60 سؤال (افتراضي)'
        }),
    )
    
    readonly_fields = ['passing_score']


# ============================================
# Student Progress Admin (Read-Only)
# ============================================

@admin.register(StudentLevel)
class StudentLevelAdmin(admin.ModelAdmin):
    list_display = ['student', 'level', 'status', 'current_unit', 'started_at', 'completed_at']
    list_filter = ['status', 'level']
    search_fields = ['student__username', 'level__title']
    raw_id_fields = ['student', 'level', 'current_unit']
    readonly_fields = [
        'student', 'level', 'status', 'current_unit', 
        'started_at', 'completed_at', 'created_at', 'updated_at'
    ]
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(StudentUnit)
class StudentUnitAdmin(admin.ModelAdmin):
    list_display = [
        'student', 'unit', 'status', 
        'lessons_completed', 'exam_passed', 
        'started_at', 'completed_at'
    ]
    list_filter = ['status', 'exam_passed', 'unit__level']
    search_fields = ['student__username', 'unit__title']
    raw_id_fields = ['student', 'unit']
    readonly_fields = [
        'student', 'unit', 'status', 'lessons_completed', 
        'exam_passed', 'started_at', 'completed_at', 'created_at', 'updated_at'
    ]
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(StudentLesson)
class StudentLessonAdmin(admin.ModelAdmin):
    list_display = ['student', 'lesson', 'is_completed', 'completed_at', 'created_at']
    list_filter = ['is_completed', 'lesson__lesson_type', 'lesson__unit__level']
    search_fields = ['student__username', 'lesson__title']
    raw_id_fields = ['student', 'lesson']
    readonly_fields = [
        'student', 'lesson', 'is_completed', 
        'completed_at', 'created_at', 'updated_at'
    ]
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(StudentUnitExamAttempt)
class StudentUnitExamAttemptAdmin(admin.ModelAdmin):
    list_display = [
        'student', 'unit_exam', 'attempt_number', 
        'score', 'passed', 'started_at', 'submitted_at'
    ]
    list_filter = ['passed', 'unit_exam__unit__level']
    search_fields = ['student__username', 'unit_exam__unit__title']
    raw_id_fields = ['student', 'unit_exam']
    readonly_fields = [
        'student', 'unit_exam', 'attempt_number', 
        'generated_questions', 'answers', 'score', 'passed',
        'time_taken', 'started_at', 'submitted_at', 
        'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('معلومات المحاولة', {
            'fields': ('student', 'unit_exam', 'attempt_number', 'started_at', 'submitted_at')
        }),
        ('النتيجة', {
            'fields': ('score', 'passed', 'time_taken')
        }),
        ('التفاصيل', {
            'fields': ('generated_questions', 'answers'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(StudentLevelExamAttempt)
class StudentLevelExamAttemptAdmin(admin.ModelAdmin):
    list_display = [
        'student', 'level_exam', 'attempt_number',
        'score', 'passed', 'started_at', 'submitted_at'
    ]
    list_filter = ['passed', 'level_exam__level']
    search_fields = ['student__username', 'level_exam__level__title']
    raw_id_fields = ['student', 'level_exam']
    readonly_fields = [
        'student', 'level_exam', 'attempt_number',
        'generated_questions', 'answers', 'score', 'passed',
        'time_taken', 'started_at', 'submitted_at',
        'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('معلومات المحاولة', {
            'fields': ('student', 'level_exam', 'attempt_number', 'started_at', 'submitted_at')
        }),
        ('النتيجة', {
            'fields': ('score', 'passed', 'time_taken')
        }),
        ('التفاصيل', {
            'fields': ('generated_questions', 'answers'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False