from django.urls import path
from . import views
from . import ai_views


app_name = 'ielts'

urlpatterns = [
    # SKILLS
    path('skills/', views.list_skills, name='list-skills'),
    path('skills/<int:skill_id>/', views.get_skill, name='get-skill'),
    path('skills/create/', views.create_skill, name='create-skill'),
    path('skills/<int:skill_id>/update/', views.update_skill, name='update-skill'),
    path('skills/<int:skill_id>/delete/', views.delete_skill, name='delete-skill'),

    # QUESTIONS CREATE
    path('vocabulary/create/', views.create_vocabulary_question, name='create-vocabulary-question'),
    path('grammar/create/', views.create_grammar_question, name='create-grammar-question'),
    path('reading/passages/create/', views.create_reading_passage, name='create-reading-passage'),
    path('reading/passages/<int:passage_id>/questions/create/', views.create_reading_question, name='create-reading-question'),
    path('listening/audio/create/', views.create_listening_audio, name='create-listening-audio'),
    path('listening/audio/<int:audio_id>/questions/create/', views.create_listening_question, name='create-listening-question'),
    path('writing/questions/create/', views.create_writing_question, name='create-writing-question'),

    # QUESTIONS DISPLAY
    path('skills/<int:skill_id>/questions/', views.get_skill_questions, name='get-skill-questions'),

    # ============================================
    # نظام المحاولات الجديد
    # ============================================
    # إرسال إجابة MCQ (Vocabulary, Grammar, Reading, Listening)
    path(
        'skills/<int:skill_id>/questions/<str:question_type>/<int:question_id>/submit/',
        views.submit_mcq_answer,
        name='submit-mcq-answer'
    ),
    # Show Answer
    path(
        'skills/<int:skill_id>/questions/<str:question_type>/<int:question_id>/show-answer/',
        views.use_show_answer,
        name='use-show-answer'
    ),
    # حالة المحاولات (للـ frontend)
    path(
        'skills/<int:skill_id>/questions/<str:question_type>/<int:question_id>/attempt-status/',
        views.get_question_attempt_status,
        name='question-attempt-status'
    ),

    # PROGRESS
    path('my-progress/', views.my_progress, name='my-progress'),
    path('skills/<int:skill_id>/my-progress/', views.skill_progress, name='skill-progress'),

    # UPDATE & DELETE
    path('vocabulary/<int:question_id>/update/', views.update_vocabulary_question, name='update-vocabulary-question'),
    path('vocabulary/<int:question_id>/delete/', views.delete_vocabulary_question, name='delete-vocabulary-question'),
    path('grammar/<int:question_id>/update/', views.update_grammar_question, name='update-grammar-question'),
    path('grammar/<int:question_id>/delete/', views.delete_grammar_question, name='delete-grammar-question'),
    path('reading/passages/<int:passage_id>/update/', views.update_reading_passage, name='update-reading-passage'),
    path('reading/passages/<int:passage_id>/delete/', views.delete_reading_passage, name='delete-reading-passage'),
    path('reading/questions/<int:question_id>/update/', views.update_reading_question, name='update-reading-question'),
    path('reading/questions/<int:question_id>/delete/', views.delete_reading_question, name='delete-reading-question'),
    path('listening/audio/<int:audio_id>/update/', views.update_listening_audio, name='update-listening-audio'),
    path('listening/audio/<int:audio_id>/delete/', views.delete_listening_audio, name='delete-listening-audio'),
    path('listening/questions/<int:question_id>/update/', views.update_listening_question, name='update-listening-question'),
    path('listening/questions/<int:question_id>/delete/', views.delete_listening_question, name='delete-listening-question'),
    path('writing/questions/<int:question_id>/update/', views.update_writing_question, name='update-writing-question'),
    path('writing/questions/<int:question_id>/delete/', views.delete_writing_question, name='delete-writing-question'),
    path('writing/questions/<int:question_id>/submit/', views.submit_writing_answer, name='ielts-submit-writing'),
    path('skills/<int:skill_id>/set-children/', views.set_child_skills, name='set-child-skills'),

    path('speaking/videos/create/', views.create_speaking_video, name='create-speaking-video'),
    path('speaking/videos/<int:video_id>/questions/create/', views.create_speaking_question, name='create-speaking-question'),
    path('speaking/videos/<int:video_id>/update/', views.update_speaking_video, name='update-speaking-video'),
    path('speaking/videos/<int:video_id>/delete/', views.delete_speaking_video, name='delete-speaking-video'),
    path('speaking/questions/<int:question_id>/update/', views.update_speaking_question, name='update-speaking-question'),
    path('speaking/questions/<int:question_id>/delete/', views.delete_speaking_question, name='delete-speaking-question'),
    # AI Generation
    path('ai/extract-book/', ai_views.list_extracted_books, name='list-extracted-books'),
    path('ai/extract-book/upload/', ai_views.extract_book, name='extract-book'),
    path('ai/extract-book/<int:book_id>/status/', ai_views.extract_book_status, name='extract-book-status'),
    path('ai/extract-media/', ai_views.list_extracted_media, name='list-extracted-media'),
    path('ai/extract-media/upload/', ai_views.extract_media, name='extract-media'),
    path('ai/extract-media/<int:media_id>/status/', ai_views.extract_media_status, name='extract-media-status'),
    path('ai/generate-skill/', ai_views.generate_skill, name='generate-skill'),
    path('ai/jobs/<int:job_id>/status/', ai_views.generation_job_status, name='generation-job-status'),
]