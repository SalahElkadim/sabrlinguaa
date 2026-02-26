from django.urls import path
from levels import views

app_name = 'levels'

urlpatterns = [
    # ============================================
    # 1. LEVEL URLS
    # ============================================
    path('levels/create/', views.create_level, name='create_level'),
    path('levels/', views.list_levels, name='list_levels'),
    path('levels/<int:level_id>/', views.get_level, name='get_level'),
    path('levels/<int:level_id>/update/', views.update_level, name='update_level'),
    path('levels/<int:level_id>/delete/', views.delete_level, name='delete_level'),
    
    # ============================================
    # 2. UNIT URLS
    # ============================================
    path('units/create/', views.create_unit, name='create_unit'),
    path('units/', views.list_units, name='list_units'),
    path('units/<int:unit_id>/', views.get_unit, name='get_unit'),
    path('units/<int:unit_id>/update/', views.update_unit, name='update_unit'),
    path('units/<int:unit_id>/delete/', views.delete_unit, name='delete_unit'),
    
    # ============================================
    # 3. LESSON URLS
    # ============================================
    path('lessons/create/', views.create_lesson, name='create_lesson'),
    path('lessons/', views.list_lessons, name='list_lessons'),
    path('lessons/<int:lesson_id>/', views.get_lesson, name='get_lesson'),
    path('lessons/<int:lesson_id>/update/', views.update_lesson, name='update_lesson'),
    path('lessons/<int:lesson_id>/delete/', views.delete_lesson, name='delete_lesson'),
    
    # ============================================
    # 4. LESSON CONTENT URLS
    # ============================================
    
    # Reading with Passage
    path('lesson-content/reading/create-with-passage/', views.create_reading_lesson_content_with_passage, name='create_reading_lesson_content_with_passage'),
    path('lesson-content/reading/<int:lesson_id>/with-passage/', views.get_reading_lesson_content_with_passage, name='get_reading_lesson_content_with_passage'),
    path('lesson-content/reading/<int:lesson_id>/update-with-passage/', views.update_reading_lesson_content_with_passage, name='update_reading_lesson_content_with_passage'),
    path('lesson-content/reading/<int:lesson_id>/delete-with-passage/', views.delete_reading_lesson_content_with_passage, name='delete_reading_lesson_content_with_passage'),
    
    # Listening with Audio
    path('lesson-content/listening/create-with-audio/', views.create_listening_lesson_content_with_audio, name='create_listening_lesson_content_with_audio'),
    path('lesson-content/listening/<int:lesson_id>/with-audio/', views.get_listening_lesson_content_with_audio, name='get_listening_lesson_content_with_audio'),
    path('lesson-content/listening/<int:lesson_id>/update-with-audio/', views.update_listening_lesson_content_with_audio, name='update_listening_lesson_content_with_audio'),
    path('lesson-content/listening/<int:lesson_id>/delete-with-audio/', views.delete_listening_lesson_content_with_audio, name='delete_listening_lesson_content_with_audio'),
    
    # Speaking with Video
    path('lesson-content/speaking/create-with-video/', views.create_speaking_lesson_content_with_video, name='create_speaking_lesson_content_with_video'),
    path('lesson-content/speaking/<int:lesson_id>/with-video/', views.get_speaking_lesson_content_with_video, name='get_speaking_lesson_content_with_video'),
    path('lesson-content/speaking/<int:lesson_id>/update-with-video/', views.update_speaking_lesson_content_with_video, name='update_speaking_lesson_content_with_video'),
    path('lesson-content/speaking/<int:lesson_id>/delete-with-video/', views.delete_speaking_lesson_content_with_video, name='delete_speaking_lesson_content_with_video'),
    
    # ============================================
    # Writing Lesson Content
    path('lesson-content/writing/create/', views.create_writing_lesson_content, name='create_writing_lesson_content'),
    path('lesson-content/writing/<int:lesson_id>/', views.get_writing_lesson_content, name='get_writing_lesson_content'),
    path('lesson-content/writing/<int:lesson_id>/update/', views.update_writing_lesson_content, name='update_writing_lesson_content'),
    path('lesson-content/writing/<int:lesson_id>/delete/', views.delete_writing_lesson_content, name='delete_writing_lesson_content'),
    
    # ============================================
    # 5. EXAM URLS
    # ============================================
    
    # ============================================
# أضف الـ URLs دي في urls.py بتاع levels
# في نهاية الـ urlpatterns
# ============================================

# Combined Lesson Detail (Lesson + Content + Questions)
    path('lesson-detail/reading/<int:lesson_id>/',  views.get_reading_lesson_full,  name='get_reading_lesson_full'),
    path('lesson-detail/listening/<int:lesson_id>/', views.get_listening_lesson_full, name='get_listening_lesson_full'),
    path('lesson-detail/speaking/<int:lesson_id>/',  views.get_speaking_lesson_full,  name='get_speaking_lesson_full'),
    path('lesson-detail/writing/<int:lesson_id>/',   views.get_writing_lesson_full,   name='get_writing_lesson_full'),
    # ============================================
    # 6. QUESTION BANK URLS
    # ============================================
    path('question-banks/', views.list_question_banks, name='list_question_banks'),
    path('question-banks/<int:bank_id>/', views.get_question_bank, name='get_question_bank'),
    path('question-banks/<int:bank_id>/statistics/', views.question_bank_statistics, name='question_bank_statistics'),
    
    # ============================================
    # 7. ADD QUESTIONS TO BANK URLS
    # ============================================
    
    # Vocabulary
    path('question-banks/<int:bank_id>/add-vocabulary/', views.add_vocabulary_question_to_bank, name='add_vocabulary_question_to_bank'),
    
    # Grammar
    path('question-banks/<int:bank_id>/add-grammar/', views.add_grammar_question_to_bank, name='add_grammar_question_to_bank'),
    
    # Reading
    path('question-banks/<int:bank_id>/create-reading-passage/', views.create_reading_passage_in_bank, name='create_reading_passage_in_bank'),
    path('question-banks/<int:bank_id>/reading-passages/<int:passage_id>/add-question/', views.add_reading_question_to_passage, name='add_reading_question_to_passage'),
    
    # Listening
    path('question-banks/<int:bank_id>/create-listening-audio/', views.create_listening_audio_in_bank, name='create_listening_audio_in_bank'),
    path('question-banks/<int:bank_id>/listening-audios/<int:audio_id>/add-question/', views.add_listening_question_to_audio, name='add_listening_question_to_audio'),
    
    # Speaking
    path('question-banks/<int:bank_id>/create-speaking-video/', views.create_speaking_video_in_bank, name='create_speaking_video_in_bank'),
    path('question-banks/<int:bank_id>/speaking-videos/<int:video_id>/add-question/', views.add_speaking_question_to_video, name='add_speaking_question_to_video'),
    
    # Writing
    path('question-banks/<int:bank_id>/add-writing/', views.add_writing_question_to_bank, name='add_writing_question_to_bank'),
    
    # ============================================
    # 8. STUDENT PROGRESS URLS
    # ============================================
    path('student/start-level/<int:level_id>/', views.start_level, name='start_level'),
    path('student/start-unit/<int:unit_id>/', views.start_unit, name='start_unit'),
    path('student/complete-lesson/<int:lesson_id>/', views.complete_lesson, name='complete_lesson'),
    path('student/my-progress/', views.my_progress, name='my_progress'),
    path('student/my-current-level/', views.my_current_level, name='my_current_level'),
    
    # ============================================
    # 9. EXAM TAKING URLS
    # ============================================
    
    # Unit Exam
    path('student/exams/unit/start/<int:unit_id>/', views.start_unit_exam, name='start_unit_exam'),
    path('student/exams/unit/submit/<int:attempt_id>/', views.submit_unit_exam, name='submit_unit_exam'),
    path('student/exams/unit/my-attempts/', views.my_unit_exam_attempts, name='my_unit_exam_attempts'),
    
    # Level Exam
    path('student/exams/level/start/<int:level_id>/', views.start_level_exam, name='start_level_exam'),
    path('student/exams/level/submit/<int:attempt_id>/', views.submit_level_exam, name='submit_level_exam'),
    path('student/exams/level/my-attempts/', views.my_level_exam_attempts, name='my_level_exam_attempts'),
]