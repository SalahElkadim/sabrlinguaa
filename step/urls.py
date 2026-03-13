from django.urls import path
from . import views

app_name = 'step'  # ← ضيف السطر ده

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
    
    # ← جديد Listening
    path('listening/audio/create/', views.create_listening_audio, name='create-listening-audio'),
    path('listening/audio/<int:audio_id>/questions/create/', views.create_listening_question, name='create-listening-question'),
    
    path('writing/questions/create/', views.create_writing_question, name='create-writing-question'),

    # QUESTIONS DISPLAY
    path('skills/<int:skill_id>/questions/', views.get_skill_questions, name='get-skill-questions'),
    path('skills/<int:skill_id>/questions/<str:question_type>/<int:question_id>/mark-viewed/', views.mark_question_viewed, name='mark-question-viewed'),

    # PROGRESS
    path('my-progress/', views.my_progress, name='my-progress'),
    path('skills/<int:skill_id>/my-progress/', views.skill_progress, name='skill-progress'),
]