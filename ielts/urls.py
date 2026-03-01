from django.urls import path
from . import views

app_name = 'ielts'

urlpatterns = [
    # ============================================
    # 1. IELTS SKILLS
    # ============================================
    path('skills/', views.list_skills, name='list-skills'),
    path('skills/<int:skill_id>/', views.get_skill, name='get-skill'),
    path('skills/create/', views.create_skill, name='create-skill'),
    path('skills/<int:skill_id>/update/', views.update_skill, name='update-skill'),
    path('skills/<int:skill_id>/delete/', views.delete_skill, name='delete-skill'),
    path('skills/<int:skill_id>/lesson-packs/', views.get_skill_lesson_packs, name='get-skill-lesson-packs'),
    
    # ============================================
    # 2. LESSON PACKS
    # ============================================
    path('lesson-packs/', views.list_lesson_packs, name='list-lesson-packs'),
    path('lesson-packs/<int:pack_id>/', views.get_lesson_pack, name='get-lesson-pack'),
    path('lesson-packs/create/', views.create_lesson_pack, name='create-lesson-pack'),
    path('lesson-packs/<int:pack_id>/update/', views.update_lesson_pack, name='update-lesson-pack'),
    path('lesson-packs/<int:pack_id>/delete/', views.delete_lesson_pack, name='delete-lesson-pack'),
    path('lesson-packs/<int:pack_id>/lessons/', views.get_lesson_pack_lessons, name='get-lesson-pack-lessons'),
    path('lesson-packs/<int:pack_id>/practice-exam/', views.get_lesson_pack_practice_exam, name='get-lesson-pack-practice-exam'),
    
    # ============================================
    # 3. LESSONS
    # ============================================
    path('lessons/', views.list_lessons, name='list-lessons'),
    path('lessons/create-full/', views.create_lesson_with_content_and_questions, name='create-lesson-full'),
    path('lessons/<int:lesson_id>/', views.get_lesson, name='get-lesson'),
    path('lessons/create/', views.create_lesson, name='create-lesson'),
    path('lessons/<int:lesson_id>/update/', views.update_lesson, name='update-lesson'),
    path('lessons/<int:lesson_id>/delete/', views.delete_lesson, name='delete-lesson'),
    path('lessons/<int:lesson_id>/mark-complete/', views.mark_lesson_complete, name='mark-lesson-complete'),
    
    # ============================================
    # 4. STUDENT PROGRESS
    # ============================================
    path('student/my-progress/', views.my_progress, name='my-progress'),
    path('student/lesson-packs/<int:pack_id>/mark-complete/', views.mark_lesson_pack_complete, name='mark-lesson-pack-complete'),
    
    # ============================================
    # 5. PRACTICE EXAMS
    # ============================================
    path('student/practice-exams/start/<int:pack_id>/', views.start_practice_exam, name='start-practice-exam'),
    path('student/practice-exams/submit/<int:attempt_id>/', views.submit_practice_exam, name='submit-practice-exam'),
    path('student/my-exam-attempts/', views.my_exam_attempts, name='my-exam-attempts'),
    path('practice-exams/<int:exam_id>/', views.get_practice_exam, name='get-practice-exam'),
    path('practice/vocabulary/create/', views.create_vocabulary_question, name='create-vocabulary-question'),
    path('practice/grammar/create/', views.create_grammar_question, name='create-grammar-question'),


    # ============================================
    # 6. READING PASSAGES & QUESTIONS
    # ============================================
    path('reading/passages/create/', views.create_reading_passage, name='create-reading-passage'),
    path('reading/passages/<int:passage_id>/', views.get_reading_passage, name='get-reading-passage'),
    path('reading/passages/<int:passage_id>/questions/create/', views.create_reading_question, name='create-reading-question'),
# في نهاية urlpatterns اضف:

    # ============================================
    # 7. LISTENING AUDIOS & QUESTIONS
    # ============================================
    path('listening/audios/create/', views.create_listening_audio, name='create-listening-audio'),
    path('listening/audios/<int:audio_id>/', views.get_listening_audio, name='get-listening-audio'),
    path('listening/audios/<int:audio_id>/questions/create/', views.create_listening_question, name='create-listening-question'),
    
    # ============================================
    # 8. SPEAKING VIDEOS & QUESTIONS
    # ============================================
    path('speaking/videos/create/', views.create_speaking_video, name='create-speaking-video'),
    path('speaking/videos/<int:video_id>/', views.get_speaking_video, name='get-speaking-video'),
    path('speaking/videos/<int:video_id>/questions/create/', views.create_speaking_question, name='create-speaking-question'),

    # ============================================
    # 9. WRITING QUESTIONS
    # ============================================
    path('writing/questions/create/', views.create_writing_question, name='create-writing-question'),
    path('writing/questions/<int:question_id>/', views.get_writing_question, name='get-writing-question'),
]