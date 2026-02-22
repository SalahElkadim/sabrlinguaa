from django.contrib import admin
from .models import (
    IELTSSkill,
    LessonPack,
    IELTSLesson,
    ReadingLessonContent,
    WritingLessonContent,
    SpeakingLessonContent,
    ListeningLessonContent,
    IELTSPracticeExam,
    SpeakingRecordingTask,
    StudentSpeakingRecording,
    StudentLessonPackProgress,
    StudentLessonProgress,
    StudentPracticeExamAttempt,
)


# ============================================
# Inline Admin Classes
# ============================================

class LessonPackInline(admin.TabularInline):
    model = LessonPack
    extra = 0
    fields = ['title', 'order', 'is_active']
    show_change_link = True


class IELTSLessonInline(admin.TabularInline):
    model = IELTSLesson
    extra = 0
    fields = ['title', 'order', 'is_active']
    show_change_link = True


class SpeakingRecordingTaskInline(admin.TabularInline):
    model = SpeakingRecordingTask
    extra = 0
    fields = ['task_text', 'duration_seconds', 'order', 'is_active']
    show_change_link = True


# ============================================
# Admin Classes
# ============================================

@admin.register(IELTSSkill)
class IELTSSkillAdmin(admin.ModelAdmin):
    list_display = ['skill_type', 'title', 'order', 'is_active', 'get_lesson_packs_count', 'created_at']
    list_filter = ['skill_type', 'is_active']
    search_fields = ['title', 'description']
    ordering = ['order', 'skill_type']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('skill_type', 'title', 'description', 'icon')
        }),
        ('Display Settings', {
            'fields': ('order', 'is_active')
        }),
    )
    
    inlines = [LessonPackInline]
    
    def get_lesson_packs_count(self, obj):
        return obj.get_lesson_packs_count()
    get_lesson_packs_count.short_description = 'Lesson Packs'


@admin.register(LessonPack)
class LessonPackAdmin(admin.ModelAdmin):
    list_display = ['title', 'skill', 'order', 'is_active', 'exam_time_limit', 'exam_passing_score', 'get_lessons_count']
    list_filter = ['skill', 'is_active']
    search_fields = ['title', 'description']
    ordering = ['skill__order', 'order']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('skill', 'title', 'description')
        }),
        ('Exam Settings', {
            'fields': ('exam_time_limit', 'exam_passing_score')
        }),
        ('Display Settings', {
            'fields': ('order', 'is_active')
        }),
    )
    
    inlines = [IELTSLessonInline, SpeakingRecordingTaskInline]
    
    def get_lessons_count(self, obj):
        return obj.get_lessons_count()
    get_lessons_count.short_description = 'Lessons'


@admin.register(IELTSLesson)
class IELTSLessonAdmin(admin.ModelAdmin):
    list_display = ['title', 'lesson_pack', 'get_skill_type', 'order', 'is_active', 'created_at']
    list_filter = ['lesson_pack__skill', 'is_active']
    search_fields = ['title', 'description']
    ordering = ['lesson_pack__order', 'order']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('lesson_pack', 'title', 'description')
        }),
        ('Display Settings', {
            'fields': ('order', 'is_active')
        }),
    )
    
    def get_skill_type(self, obj):
        return obj.lesson_pack.skill.get_skill_type_display()
    get_skill_type.short_description = 'Skill'


@admin.register(ReadingLessonContent)
class ReadingLessonContentAdmin(admin.ModelAdmin):
    list_display = ['lesson', 'get_lesson_pack', 'created_at']
    list_filter = ['lesson__lesson_pack']
    search_fields = ['lesson__title', 'reading_text']
    
    fieldsets = (
        ('Lesson', {
            'fields': ('lesson',)
        }),
        ('Content', {
            'fields': ('reading_text', 'explanation', 'vocabulary_words', 'examples')
        }),
        ('Resources', {
            'fields': ('video_url', 'resources')
        }),
    )
    
    def get_lesson_pack(self, obj):
        return obj.lesson.lesson_pack.title
    get_lesson_pack.short_description = 'Lesson Pack'


@admin.register(WritingLessonContent)
class WritingLessonContentAdmin(admin.ModelAdmin):
    list_display = ['lesson', 'get_lesson_pack', 'created_at']
    list_filter = ['lesson__lesson_pack']
    search_fields = ['lesson__title', 'sample_texts']
    
    fieldsets = (
        ('Lesson', {
            'fields': ('lesson',)
        }),
        ('Content', {
            'fields': ('sample_texts', 'writing_instructions', 'tips', 'examples')
        }),
        ('Resources', {
            'fields': ('video_url',)
        }),
    )
    
    def get_lesson_pack(self, obj):
        return obj.lesson.lesson_pack.title
    get_lesson_pack.short_description = 'Lesson Pack'


@admin.register(SpeakingLessonContent)
class SpeakingLessonContentAdmin(admin.ModelAdmin):
    list_display = ['lesson', 'get_lesson_pack', 'created_at']
    list_filter = ['lesson__lesson_pack']
    search_fields = ['lesson__title']
    
    fieldsets = (
        ('Lesson', {
            'fields': ('lesson',)
        }),
        ('Media', {
            'fields': ('video_file', 'audio_examples')
        }),
        ('Content', {
            'fields': ('dialogue_texts', 'useful_phrases', 'pronunciation_tips')
        }),
    )
    
    def get_lesson_pack(self, obj):
        return obj.lesson.lesson_pack.title
    get_lesson_pack.short_description = 'Lesson Pack'


@admin.register(ListeningLessonContent)
class ListeningLessonContentAdmin(admin.ModelAdmin):
    list_display = ['lesson', 'get_lesson_pack', 'created_at']
    list_filter = ['lesson__lesson_pack']
    search_fields = ['lesson__title', 'transcript']
    
    fieldsets = (
        ('Lesson', {
            'fields': ('lesson',)
        }),
        ('Audio', {
            'fields': ('audio_file',)
        }),
        ('Content', {
            'fields': ('transcript', 'vocabulary_explanation', 'listening_exercises', 'tips')
        }),
    )
    
    def get_lesson_pack(self, obj):
        return obj.lesson.lesson_pack.title
    get_lesson_pack.short_description = 'Lesson Pack'


@admin.register(IELTSPracticeExam)
class IELTSPracticeExamAdmin(admin.ModelAdmin):
    list_display = ['title', 'lesson_pack', 'get_questions_count', 'created_at']
    list_filter = ['lesson_pack__skill']
    search_fields = ['title', 'instructions']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('lesson_pack', 'title', 'instructions')
        }),
    )
    
    def get_questions_count(self, obj):
        return obj.get_questions_count()
    get_questions_count.short_description = 'Questions'


@admin.register(SpeakingRecordingTask)
class SpeakingRecordingTaskAdmin(admin.ModelAdmin):
    list_display = ['get_short_task', 'lesson_pack', 'duration_seconds', 'order', 'is_active', 'get_max_total_score']
    list_filter = ['lesson_pack', 'is_active']
    search_fields = ['task_text']
    ordering = ['lesson_pack', 'order']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('lesson_pack', 'task_text', 'task_image', 'duration_seconds')
        }),
        ('Assessment Configuration', {
            'fields': (
                'assess_content', 'max_content_score',
                'assess_grammar', 'max_grammar_score',
                'assess_fluency', 'max_fluency_score',
                'assess_pronunciation', 'max_pronunciation_score'
            )
        }),
        ('Display Settings', {
            'fields': ('order', 'is_active')
        }),
    )
    
    def get_short_task(self, obj):
        return obj.task_text[:50] + '...' if len(obj.task_text) > 50 else obj.task_text
    get_short_task.short_description = 'Task'
    
    def get_max_total_score(self, obj):
        return obj.get_max_total_score()
    get_max_total_score.short_description = 'Max Score'


@admin.register(StudentSpeakingRecording)
class StudentSpeakingRecordingAdmin(admin.ModelAdmin):
    list_display = ['student', 'get_short_task', 'total_score', 'assessed_at', 'created_at']
    list_filter = ['task__lesson_pack', 'assessed_at']
    search_fields = ['student__username', 'student__email', 'task__task_text']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('student', 'task', 'audio_file')
        }),
        ('Transcription', {
            'fields': ('transcribed_text', 'transcription_model', 'transcribed_at')
        }),
        ('Assessment Scores', {
            'fields': (
                'content_score', 'grammar_score',
                'fluency_score', 'pronunciation_score',
                'total_score'
            )
        }),
        ('Feedback', {
            'fields': ('ai_feedback', 'strengths', 'improvements')
        }),
        ('Meta', {
            'fields': ('assessment_model', 'assessed_at', 'created_at', 'updated_at')
        }),
    )
    
    def get_short_task(self, obj):
        return obj.task.task_text[:30] + '...' if len(obj.task.task_text) > 30 else obj.task.task_text
    get_short_task.short_description = 'Task'


@admin.register(StudentLessonPackProgress)
class StudentLessonPackProgressAdmin(admin.ModelAdmin):
    list_display = ['student', 'lesson_pack', 'is_completed', 'completed_at', 'created_at']
    list_filter = ['lesson_pack__skill', 'is_completed']
    search_fields = ['student__username', 'student__email', 'lesson_pack__title']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('student', 'lesson_pack')
        }),
        ('Progress', {
            'fields': ('is_completed', 'completed_at')
        }),
    )


@admin.register(StudentLessonProgress)
class StudentLessonProgressAdmin(admin.ModelAdmin):
    list_display = ['student', 'lesson', 'is_completed', 'completed_at', 'created_at']
    list_filter = ['lesson__lesson_pack', 'is_completed']
    search_fields = ['student__username', 'student__email', 'lesson__title']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('student', 'lesson')
        }),
        ('Progress', {
            'fields': ('is_completed', 'completed_at')
        }),
    )


@admin.register(StudentPracticeExamAttempt)
class StudentPracticeExamAttemptAdmin(admin.ModelAdmin):
    list_display = ['student', 'practice_exam', 'attempt_number', 'score', 'passed', 'submitted_at', 'started_at']
    list_filter = ['practice_exam__lesson_pack', 'passed', 'submitted_at']
    search_fields = ['student__username', 'student__email', 'practice_exam__title']
    ordering = ['-started_at']
    readonly_fields = ['started_at', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('student', 'practice_exam', 'attempt_number')
        }),
        ('Answers', {
            'fields': ('answers',)
        }),
        ('Results', {
            'fields': ('score', 'passed', 'time_taken')
        }),
        ('Timestamps', {
            'fields': ('started_at', 'submitted_at', 'created_at', 'updated_at')
        }),
    )