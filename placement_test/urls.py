from django.urls import path
from . import views

"""
URLs لإدارة بنوك الأسئلة
"""

urlpatterns = [
    # ============================================
    # 1. Question Bank CRUD Operations
    # ============================================
    path(
        'question-banks/create/',
        views.create_question_bank,
        name='create-question-bank'
    ),
    path(
        'question-banks/',
        views.list_question_banks,
        name='list-question-banks'
    ),
    path(
        'question-banks/<int:bank_id>/',
        views.get_question_bank,
        name='get-question-bank'
    ),
    path(
        'question-banks/<int:bank_id>/update/',
        views.update_question_bank,
        name='update-question-bank'
    ),
    path(
        'question-banks/<int:bank_id>/delete/',
        views.delete_question_bank,
        name='delete-question-bank'
    ),
    path(
        'question-banks/<int:bank_id>/statistics/',
        views.question_bank_statistics,
        name='question-bank-statistics'
    ),
    
    # ============================================
    # 2. Add Questions to Bank
    # ============================================
    
    # 2.1 Vocabulary Questions
    path(
        'question-banks/<int:bank_id>/add-vocabulary-question/',
        views.add_vocabulary_question,
        name='add-vocabulary-question'
    ),
    
    # 2.2 Grammar Questions
    path(
        'question-banks/<int:bank_id>/add-grammar-question/',
        views.add_grammar_question,
        name='add-grammar-question'
    ),
    
    # 2.3 Reading Questions
    path(
        'question-banks/<int:bank_id>/create-reading-passage/',
        views.create_reading_passage,
        name='create-reading-passage'
    ),
    path(
        'question-banks/<int:bank_id>/reading-passages/<int:passage_id>/add-question/',
        views.add_reading_question,
        name='add-reading-question'
    ),
    
    # 2.4 Listening Questions
    path(
        'question-banks/<int:bank_id>/create-listening-audio/',
        views.create_listening_audio,
        name='create-listening-audio'
    ),
    path(
        'question-banks/<int:bank_id>/listening-audios/<int:audio_id>/add-question/',
        views.add_listening_question,
        name='add-listening-question'
    ),
    
    # 2.5 Speaking Questions
    path(
        'question-banks/<int:bank_id>/create-speaking-video/',
        views.create_speaking_video,
        name='create-speaking-video'
    ),
    path(
        'question-banks/<int:bank_id>/speaking-videos/<int:video_id>/add-question/',
        views.add_speaking_question,
        name='add-speaking-question'
    ),
    
    # 2.6 Writing Questions
    path(
        'question-banks/<int:bank_id>/add-writing-question/',
        views.add_writing_question,
        name='add-writing-question'
    ),
    
    # ============================================
    # 3. Get Questions from Bank
    # ============================================
    
    # 3.1 All Questions (with optional filter)
    path(
        'question-banks/<int:bank_id>/all-questions/',
        views.get_all_bank_questions,
        name='get-all-bank-questions'
    ),
    
    # 3.2 Questions by Type
    path(
        'question-banks/<int:bank_id>/vocabulary-questions/',
        views.list_vocabulary_questions,
        name='list-bank-vocabulary-questions'
    ),
    path(
        'question-banks/<int:bank_id>/grammar-questions/',
        views.list_grammar_questions,
        name='list-bank-grammar-questions'
    ),
    path(
        'question-banks/<int:bank_id>/reading-passages/',
        views.list_reading_passages,
        name='list-bank-reading-passages'
    ),
    path(
        'question-banks/<int:bank_id>/listening-audios/',
        views.list_listening_audios,
        name='list-bank-listening-audios'
    ),
    path(
        'question-banks/<int:bank_id>/speaking-videos/',
        views.list_speaking_videos,
        name='list-bank-speaking-videos'
    ),
    path(
        'question-banks/<int:bank_id>/writing-questions/',
        views.list_writing_questions,
        name='list-bank-writing-questions'
    ),
    
    # ============================================
    # 4. Student - Create Exam from Bank
    # ============================================
    path(
        'student/create-exam/',
        views.create_exam_from_bank,
        name='student-create-exam'
    ),
    # ============================================
    # 5. Student - Submit Exam & Results
    # ============================================
    path(
        'student/submit-exam/<int:attempt_id>/',
        views.submit_exam,
        name='student-submit-exam'
    ),
    path(
        'student/exam-result/<int:attempt_id>/',
        views.get_exam_result,
        name='student-exam-result'
    ),
    path(
        'student/my-attempts/',
        views.my_exam_attempts,
        name='student-my-attempts'
    ),
    path(
        'student/active-exam/',
        views.get_active_exam,
        name='student-active-exam'
    ),
]