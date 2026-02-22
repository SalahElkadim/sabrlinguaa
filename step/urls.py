from django.urls import path
from . import views

app_name = 'step'

urlpatterns = [
    # ============================================
    # 1. STEP SKILLS CRUD
    # ============================================
    path('skills/', views.list_skills, name='list-skills'),
    path('skills/<int:skill_id>/', views.get_skill, name='get-skill'),
    path('skills/create/', views.create_skill, name='create-skill'),
    path('skills/<int:skill_id>/update/', views.update_skill, name='update-skill'),
    path('skills/<int:skill_id>/delete/', views.delete_skill, name='delete-skill'),
    
    # ============================================
    # 2. QUESTIONS MANAGEMENT (CREATE)
    # ============================================
    path('vocabulary/create/', views.create_vocabulary_question, name='create-vocabulary-question'),
    path('grammar/create/', views.create_grammar_question, name='create-grammar-question'),
    path('reading/passages/create/', views.create_reading_passage, name='create-reading-passage'),
    path('reading/passages/<int:passage_id>/questions/create/', views.create_reading_question, name='create-reading-question'),
    path('writing/questions/create/', views.create_writing_question, name='create-writing-question'),
    
    # ============================================
    # 3. QUESTIONS DISPLAY (للطالب)
    # ============================================
    path('skills/<int:skill_id>/questions/', views.get_skill_questions, name='get-skill-questions'),
    path('skills/<int:skill_id>/questions/<str:question_type>/<int:question_id>/mark-viewed/', views.mark_question_viewed, name='mark-question-viewed'),
    
    # ============================================
    # 4. STUDENT PROGRESS
    # ============================================
    path('my-progress/', views.my_progress, name='my-progress'),
    path('skills/<int:skill_id>/my-progress/', views.skill_progress, name='skill-progress'),
]