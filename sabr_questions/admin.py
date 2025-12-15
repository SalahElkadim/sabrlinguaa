from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    PlacementTest,
    MCQQuestionSet, MCQQuestion,
    ReadingPassage, ReadingQuestion,
    ListeningAudio, ListeningQuestion,
    SpeakingVideo, SpeakingQuestion,
    WritingQuestion
)


# ============================================
# Placement Test Admin
# ============================================

@admin.register(PlacementTest)
class PlacementTestAdmin(admin.ModelAdmin):
    list_display = ['title', 'duration_display', 'total_questions', 'total_points_display', 
                    'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'description']
    list_editable = ['is_active']
    
    fieldsets = (
        ('معلومات أساسية', {
            'fields': ('title', 'description', 'duration_minutes', 'is_active')
        }),
        ('درجات المستويات', {
            'fields': ('a1_min_score', 'a2_min_score', 'b1_min_score', 'b2_min_score'),
            'description': 'حدد الحد الأدنى من الدرجات لكل مستوى'
        }),
    )
    
    def duration_display(self, obj):
        return format_html(
            '<span style="color: #FF5722; font-weight: bold;">⏱️ {} دقيقة</span>',
            obj.duration_minutes
        )
    duration_display.short_description = 'المدة'
    
    def total_questions(self, obj):
        count = obj.get_questions_count()
        return format_html(
            '<span style="background-color: #2196F3; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">📝 {}</span>',
            count
        )
    total_questions.short_description = 'عدد الأسئلة'
    
    def total_points_display(self, obj):
        points = obj.get_total_points()
        return format_html(
            '<span style="background-color: #4CAF50; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">⭐ {}</span>',
            points
        )
    total_points_display.short_description = 'مجموع النقاط'
    
    def get_readonly_fields(self, request, obj=None):
        # عرض ملخص الامتحان عند التعديل فقط
        if obj:
            return self.readonly_fields + ('exam_summary',)
        return self.readonly_fields
    
    def exam_summary(self, obj):
        """عرض ملخص تفصيلي للامتحان"""
        html = '<div style="background: #f5f5f5; padding: 15px; border-radius: 5px; margin: 10px 0;">'
        html += '<h3 style="margin-top: 0;">📊 ملخص الامتحان</h3>'
        
        # MCQ
        mcq_count = sum(s.questions.count() for s in obj.mcq_sets.all())
        if mcq_count > 0:
            html += f'<p>✅ أسئلة MCQ: <strong>{mcq_count}</strong> سؤال</p>'
        
        # Reading
        reading_count = sum(p.questions.count() for p in obj.reading_passages.all())
        if reading_count > 0:
            html += f'<p>📖 أسئلة القراءة: <strong>{reading_count}</strong> سؤال</p>'
        
        # Listening
        listening_count = sum(a.questions.count() for a in obj.listening_audios.all())
        if listening_count > 0:
            html += f'<p>🎧 أسئلة الاستماع: <strong>{listening_count}</strong> سؤال</p>'
        
        # Speaking
        speaking_count = sum(v.questions.count() for v in obj.speaking_videos.all())
        if speaking_count > 0:
            html += f'<p>🎤 أسئلة التحدث: <strong>{speaking_count}</strong> سؤال</p>'
        
        # Writing
        writing_count = obj.writing_questions.count()
        if writing_count > 0:
            html += f'<p>✍️ أسئلة الكتابة: <strong>{writing_count}</strong> سؤال</p>'
        
        html += f'<hr><p style="font-size: 16px;"><strong>المجموع الكلي: {obj.get_questions_count()} سؤال | {obj.get_total_points()} نقطة</strong></p>'
        html += '</div>'
        
        return mark_safe(html)
    exam_summary.short_description = 'ملخص الامتحان'


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
    list_display = ['title', 'placement_test', 'questions_count', 'is_active', 'order', 'created_at']
    list_filter = ['placement_test', 'is_active', 'created_at']
    search_fields = ['title', 'description']
    list_editable = ['is_active', 'order']
    ordering = ['placement_test', 'order', '-created_at']
    inlines = [MCQQuestionInline]
    
    fieldsets = (
        ('معلومات أساسية', {
            'fields': ('placement_test', 'title', 'description', 'order', 'is_active')
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
    list_filter = ['question_set__placement_test', 'question_set', 'correct_answer', 'created_at']
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
    list_display = ['title', 'placement_test', 'questions_count', 'is_active', 'order', 'created_at']
    list_filter = ['placement_test', 'is_active', 'created_at']
    search_fields = ['title', 'passage_text', 'source']
    list_editable = ['is_active', 'order']
    ordering = ['placement_test', 'order', '-created_at']
    inlines = [ReadingQuestionInline]
    
    fieldsets = (
        ('معلومات أساسية', {
            'fields': ('placement_test', 'title', 'order', 'is_active')
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
    list_filter = ['passage__placement_test', 'passage', 'correct_answer', 'created_at']
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
    list_display = ['title', 'placement_test', 'questions_count', 'duration_display', 
                    'is_active', 'order', 'created_at']
    list_filter = ['placement_test', 'is_active', 'created_at']
    search_fields = ['title', 'transcript']
    list_editable = ['is_active', 'order']
    ordering = ['placement_test', 'order', '-created_at']
    inlines = [ListeningQuestionInline]
    
    fieldsets = (
        ('معلومات أساسية', {
            'fields': ('placement_test', 'title', 'order', 'is_active')
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
    list_filter = ['audio__placement_test', 'audio', 'correct_answer', 'created_at']
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
    list_display = ['title', 'placement_test', 'questions_count', 'duration_display', 
                    'is_active', 'order', 'created_at']
    list_filter = ['placement_test', 'is_active', 'created_at']
    search_fields = ['title', 'description']
    list_editable = ['is_active', 'order']
    ordering = ['placement_test', 'order', '-created_at']
    inlines = [SpeakingQuestionInline]
    
    fieldsets = (
        ('معلومات أساسية', {
            'fields': ('placement_test', 'title', 'description', 'order', 'is_active')
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
    list_filter = ['video__placement_test', 'video', 'correct_answer', 'created_at']
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
    list_display = ['title', 'placement_test', 'points', 'word_range', 
                    'is_active', 'order', 'created_at']
    list_filter = ['placement_test', 'is_active', 'created_at']
    search_fields = ['title', 'question_text', 'sample_answer']
    list_editable = ['is_active', 'order']
    ordering = ['placement_test', 'order', '-created_at']
    
    fieldsets = (
        ('معلومات أساسية', {
            'fields': ('placement_test', 'title', 'order', 'is_active')
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