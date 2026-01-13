from django.urls import path
from .views import (
    # Level URLs
    LevelListCreateAPIView,
    LevelDetailAPIView,
    
    # Unit URLs
    UnitListCreateAPIView,
    UnitDetailAPIView,
    
    # Section URLs
    SectionListCreateAPIView,
    SectionDetailAPIView,
    
    # Lesson URLs
    LessonListCreateAPIView,
    LessonDetailAPIView,
    
    # Exercise URLs
    ExerciseListCreateAPIView,
    ExerciseDetailAPIView,
    
    # MCQ Question URLs
    ExerciseMCQQuestionListCreateAPIView,
    ExerciseMCQQuestionDetailAPIView,
    
    # Reading Passage URLs
    ExerciseReadingPassageListCreateAPIView,
    ExerciseReadingPassageDetailAPIView,
    
    # Reading Question URLs
    ExerciseReadingQuestionListCreateAPIView,
    ExerciseReadingQuestionDetailAPIView,
    
    # Listening Audio URLs
    ExerciseListeningAudioListCreateAPIView,
    ExerciseListeningAudioDetailAPIView,
    
    # Listening Question URLs
    ExerciseListeningQuestionListCreateAPIView,
    ExerciseListeningQuestionDetailAPIView,
    
    # Speaking Video URLs
    ExerciseSpeakingVideoListCreateAPIView,
    ExerciseSpeakingVideoDetailAPIView,
    
    # Speaking Question URLs
    ExerciseSpeakingQuestionListCreateAPIView,
    ExerciseSpeakingQuestionDetailAPIView,
    
    # Writing Question URLs
    ExerciseWritingQuestionListCreateAPIView,
    ExerciseWritingQuestionDetailAPIView,
)

app_name = 'courses'

urlpatterns = [
    # ============================================
    # Level URLs
    # ============================================
    path('levels/', LevelListCreateAPIView.as_view(), name='level-list-create'),
    path('levels/<int:pk>/', LevelDetailAPIView.as_view(), name='level-detail'),
    
    # ============================================
    # Unit URLs
    # ============================================
    path('units/', UnitListCreateAPIView.as_view(), name='unit-list-create'),
    path('units/<int:pk>/', UnitDetailAPIView.as_view(), name='unit-detail'),
    
    # ============================================
    # Section URLs
    # ============================================
    path('sections/', SectionListCreateAPIView.as_view(), name='section-list-create'),
    path('sections/<int:pk>/', SectionDetailAPIView.as_view(), name='section-detail'),
    
    # ============================================
    # Lesson URLs
    # ============================================
    path('lessons/', LessonListCreateAPIView.as_view(), name='lesson-list-create'),
    path('lessons/<int:pk>/', LessonDetailAPIView.as_view(), name='lesson-detail'),
    
    # ============================================
    # Exercise URLs
    # ============================================
    path('exercises/', ExerciseListCreateAPIView.as_view(), name='exercise-list-create'),
    path('exercises/<int:pk>/', ExerciseDetailAPIView.as_view(), name='exercise-detail'),
    
    # ============================================
    # MCQ Question URLs
    # ============================================
    path('mcq-questions/', ExerciseMCQQuestionListCreateAPIView.as_view(), 
         name='mcq-question-list-create'),
    path('mcq-questions/<int:pk>/', ExerciseMCQQuestionDetailAPIView.as_view(), 
         name='mcq-question-detail'),
    
    # ============================================
    # Reading Passage URLs
    # ============================================
    path('reading-passages/', ExerciseReadingPassageListCreateAPIView.as_view(), 
         name='reading-passage-list-create'),
    path('reading-passages/<int:pk>/', ExerciseReadingPassageDetailAPIView.as_view(), 
         name='reading-passage-detail'),
    
    # ============================================
    # Reading Question URLs
    # ============================================
    path('reading-questions/', ExerciseReadingQuestionListCreateAPIView.as_view(), 
         name='reading-question-list-create'),
    path('reading-questions/<int:pk>/', ExerciseReadingQuestionDetailAPIView.as_view(), 
         name='reading-question-detail'),
    
    # ============================================
    # Listening Audio URLs
    # ============================================
    path('listening-audios/', ExerciseListeningAudioListCreateAPIView.as_view(), 
         name='listening-audio-list-create'),
    path('listening-audios/<int:pk>/', ExerciseListeningAudioDetailAPIView.as_view(), 
         name='listening-audio-detail'),
    
    # ============================================
    # Listening Question URLs
    # ============================================
    path('listening-questions/', ExerciseListeningQuestionListCreateAPIView.as_view(), 
         name='listening-question-list-create'),
    path('listening-questions/<int:pk>/', ExerciseListeningQuestionDetailAPIView.as_view(), 
         name='listening-question-detail'),
    
    # ============================================
    # Speaking Video URLs
    # ============================================
    path('speaking-videos/', ExerciseSpeakingVideoListCreateAPIView.as_view(), 
         name='speaking-video-list-create'),
    path('speaking-videos/<int:pk>/', ExerciseSpeakingVideoDetailAPIView.as_view(), 
         name='speaking-video-detail'),
    
    # ============================================
    # Speaking Question URLs
    # ============================================
    path('speaking-questions/', ExerciseSpeakingQuestionListCreateAPIView.as_view(), 
         name='speaking-question-list-create'),
    path('speaking-questions/<int:pk>/', ExerciseSpeakingQuestionDetailAPIView.as_view(), 
         name='speaking-question-detail'),
    
    # ============================================
    # Writing Question URLs
    # ============================================
    path('writing-questions/', ExerciseWritingQuestionListCreateAPIView.as_view(), 
         name='writing-question-list-create'),
    path('writing-questions/<int:pk>/', ExerciseWritingQuestionDetailAPIView.as_view(), 
         name='writing-question-detail'),
]