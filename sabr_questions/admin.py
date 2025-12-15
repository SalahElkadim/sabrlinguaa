from django.contrib import admin
from django.utils.html import format_html
from .models import (
    MCQQuestionSet, MCQQuestion,
    ReadingPassage, ReadingQuestion,
    ListeningAudio, ListeningQuestion,
    SpeakingVideo, SpeakingQuestion,
    WritingQuestion
)


# ============================================
# Inline Classes (للأسئلة الفرعية)
# ============================================

class MCQQuestionInline(admin.TabularInline):
    model = MCQQuestion
    extra = 1
    fields = ['question_text', 'choice_a', 'choice_b', 'choice_c', 'choice_d', 
              'correct_answer', 'points', 'order']
    ordering = ['order']


class ReadingQuestionInline(admin.TabularInline):
    model = ReadingQuestion
    extra = 1
    fields = ['question_text', 'choice_a', 'choice_b', 'choice_c', 'choice_d',
              'correct_answer', 'points', 'order']
    ordering = ['order']


class ListeningQuestionInline(admin.TabularInline):
    model = ListeningQuestion
    extra = 1
    fields = ['question_text', 'choice_a', 'choice_b', 'choice_c', 'choice_d',
              'correct_answer', 'points', 'order']
    ordering = ['order']


class SpeakingQuestionInline(admin.TabularInline):
    model = SpeakingQuestion
    extra = 1
    fields = ['question_text', 'choice_a', 'choice_b', 'choice_c', 'choice_d',
              'correct_answer', 'points', 'order']
    ordering = ['order']


# ============================================
# MCQ Admin
# ============================================

@admin.register(MCQQuestionSet)
class MCQQuestionSetAdmin(admin.ModelAdmin):
    list_display = ['title', 'questions_count', 'is_active', 'order', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'description']
    list_editable = ['is_active', 'order']
    ordering = ['order', '-created_at']
    inlines = [MCQQuestionInline]
    
    fieldsets = (
        ('معلومات أساسية', {
            'fields': ('title', 'description', 'order', 'is_active')
        }),
    )
    
    def questions_count(self, obj):
        count = obj.questions.count()
        return format_html(
            '<span style="background-color: #4CAF50; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            count
        )
    questions_count.short_description = 'عدد الأسئلة'


@admin.register(MCQQuestion)
class MCQQuestionAdmin(admin.ModelAdmin):
    list_display = ['question_preview', 'question_set', 'correct_answer', 
                    'points', 'order', 'created_at']
    list_filter = ['question_set', 'correct_answer', 'created_at']
    search_fields = ['question_text', 'explanation']
    list_editable = ['points', 'order']
    ordering = ['question_set', 'order', '-created_at']
    
    fieldsets = (
        ('السؤال', {
            'fields': ('question_set', 'question_text', 'question_image', 'order')
        }),
        ('الاختيارات', {
            'fields': ('choice_a', 'choice_b', 'choice_c', 'choice_d')
        }),
        ('الإجابة والتقييم', {
            'fields': ('correct_answer', 'explanation', 'points')
        }),
    )
    
    def question_preview(self, obj):
        return obj.question_text[:50] + '...' if len(obj.question_text) > 50 else obj.question_text
    question_preview.short_description = 'نص السؤال'


# ============================================
# Reading Admin
# ============================================

@admin.register(ReadingPassage)
class ReadingPassageAdmin(admin.ModelAdmin):
    list_display = ['title', 'questions_count', 'difficulty_level', 
                    'is_active', 'order', 'created_at']
    list_filter = ['difficulty_level', 'is_active', 'created_at']
    search_fields = ['title', 'passage_text', 'source']
    list_editable = ['is_active', 'order']
    ordering = ['order', '-created_at']
    inlines = [ReadingQuestionInline]
    
    fieldsets = (
        ('معلومات أساسية', {
            'fields': ('title', 'difficulty_level', 'order', 'is_active')
        }),
        ('القطعة', {
            'fields': ('passage_text', 'passage_image', 'source')
        }),
    )
    
    def questions_count(self, obj):
        count = obj.questions.count()
        return format_html(
            '<span style="background-color: #2196F3; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            count
        )
    questions_count.short_description = 'عدد الأسئلة'


@admin.register(ReadingQuestion)
class ReadingQuestionAdmin(admin.ModelAdmin):
    list_display = ['question_preview', 'passage', 'correct_answer', 
                    'points', 'order', 'created_at']
    list_filter = ['passage', 'correct_answer', 'created_at']
    search_fields = ['question_text', 'explanation']
    list_editable = ['points', 'order']
    ordering = ['passage', 'order', '-created_at']
    
    fieldsets = (
        ('السؤال', {
            'fields': ('passage', 'question_text', 'question_image', 'order')
        }),
        ('الاختيارات', {
            'fields': ('choice_a', 'choice_b', 'choice_c', 'choice_d')
        }),
        ('الإجابة والتقييم', {
            'fields': ('correct_answer', 'explanation', 'points')
        }),
    )
    
    def question_preview(self, obj):
        return obj.question_text[:50] + '...' if len(obj.question_text) > 50 else obj.question_text
    question_preview.short_description = 'نص السؤال'


# ============================================
# Listening Admin
# ============================================

@admin.register(ListeningAudio)
class ListeningAudioAdmin(admin.ModelAdmin):
    list_display = ['title', 'questions_count', 'difficulty_level', 
                    'duration_display', 'is_active', 'order', 'created_at']
    list_filter = ['difficulty_level', 'is_active', 'created_at']
    search_fields = ['title', 'transcript']
    list_editable = ['is_active', 'order']
    ordering = ['order', '-created_at']
    inlines = [ListeningQuestionInline]
    
    fieldsets = (
        ('معلومات أساسية', {
            'fields': ('title', 'difficulty_level', 'order', 'is_active')
        }),
        ('التسجيل الصوتي', {
            'fields': ('audio_file', 'duration', 'transcript')
        }),
    )
    
    def questions_count(self, obj):
        count = obj.questions.count()
        return format_html(
            '<span style="background-color: #FF9800; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            count
        )
    questions_count.short_description = 'عدد الأسئلة'
    
    def duration_display(self, obj):
        if obj.duration:
            minutes = obj.duration // 60
            seconds = obj.duration % 60
            return f"{minutes}:{seconds:02d}"
        return "-"
    duration_display.short_description = 'المدة'


@admin.register(ListeningQuestion)
class ListeningQuestionAdmin(admin.ModelAdmin):
    list_display = ['question_preview', 'audio', 'correct_answer', 
                    'points', 'order', 'created_at']
    list_filter = ['audio', 'correct_answer', 'created_at']
    search_fields = ['question_text', 'explanation']
    list_editable = ['points', 'order']
    ordering = ['audio', 'order', '-created_at']
    
    fieldsets = (
        ('السؤال', {
            'fields': ('audio', 'question_text', 'question_image', 'order')
        }),
        ('الاختيارات', {
            'fields': ('choice_a', 'choice_b', 'choice_c', 'choice_d')
        }),
        ('الإجابة والتقييم', {
            'fields': ('correct_answer', 'explanation', 'points')
        }),
    )
    
    def question_preview(self, obj):
        return obj.question_text[:50] + '...' if len(obj.question_text) > 50 else obj.question_text
    question_preview.short_description = 'نص السؤال'


# ============================================
# Speaking Admin
# ============================================

@admin.register(SpeakingVideo)
class SpeakingVideoAdmin(admin.ModelAdmin):
    list_display = ['title', 'questions_count', 'duration_display', 
                    'is_active', 'order', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'description']
    list_editable = ['is_active', 'order']
    ordering = ['order', '-created_at']
    inlines = [SpeakingQuestionInline]
    
    fieldsets = (
        ('معلومات أساسية', {
            'fields': ('title', 'description', 'order', 'is_active')
        }),
        ('الفيديو', {
            'fields': ('video_file', 'thumbnail', 'duration')
        }),
    )
    
    def questions_count(self, obj):
        count = obj.questions.count()
        return format_html(
            '<span style="background-color: #9C27B0; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            count
        )
    questions_count.short_description = 'عدد الأسئلة'
    
    def duration_display(self, obj):
        if obj.duration:
            minutes = obj.duration // 60
            seconds = obj.duration % 60
            return f"{minutes}:{seconds:02d}"
        return "-"
    duration_display.short_description = 'المدة'


@admin.register(SpeakingQuestion)
class SpeakingQuestionAdmin(admin.ModelAdmin):
    list_display = ['question_preview', 'video', 'correct_answer', 
                    'points', 'order', 'created_at']
    list_filter = ['video', 'correct_answer', 'created_at']
    search_fields = ['question_text', 'explanation']
    list_editable = ['points', 'order']
    ordering = ['video', 'order', '-created_at']
    
    fieldsets = (
        ('السؤال', {
            'fields': ('video', 'question_text', 'question_image', 'order')
        }),
        ('الاختيارات', {
            'fields': ('choice_a', 'choice_b', 'choice_c', 'choice_d')
        }),
        ('الإجابة والتقييم', {
            'fields': ('correct_answer', 'explanation', 'points')
        }),
    )
    
    def question_preview(self, obj):
        return obj.question_text[:50] + '...' if len(obj.question_text) > 50 else obj.question_text
    question_preview.short_description = 'نص السؤال'


# ============================================
# Writing Admin
# ============================================

@admin.register(WritingQuestion)
class WritingQuestionAdmin(admin.ModelAdmin):
    list_display = ['title', 'difficulty_level', 'points', 'word_range', 
                    'is_active', 'order', 'created_at']
    list_filter = ['difficulty_level', 'is_active', 'created_at']
    search_fields = ['title', 'question_text', 'sample_answer']
    list_editable = ['is_active', 'order']
    ordering = ['order', '-created_at']
    
    fieldsets = (
        ('معلومات أساسية', {
            'fields': ('title', 'difficulty_level', 'order', 'is_active')
        }),
        ('السؤال', {
            'fields': ('question_text', 'question_image')
        }),
        ('متطلبات الإجابة', {
            'fields': ('min_words', 'max_words', 'points')
        }),
        ('نموذج الإجابة والتقييم', {
            'fields': ('sample_answer', 'rubric'),
            'classes': ('collapse',)  # قابل للطي
        }),
    )
    
    def word_range(self, obj):
        return format_html(
            '<span style="color: #607D8B;">{} - {} كلمة</span>',
            obj.min_words, obj.max_words
        )
    word_range.short_description = 'نطاق الكلمات'


# ============================================
# تخصيص Admin Site
# ============================================

admin.site.site_header = "إدارة منصة سبر لينجوا التعليمية"
admin.site.site_title = "سبر لينجوا"
admin.site.index_title = "لوحة التحكم - إدارة الأسئلة"