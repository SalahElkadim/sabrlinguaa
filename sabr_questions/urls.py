from django.urls import path
from .views import (
    # Placement Test
    PlacementTestListCreateView,
    PlacementTestDetailView,
    
    # MCQ Question Set
    MCQQuestionSetListCreateView,
    MCQQuestionSetDetailView,
    
    # MCQ Question
    MCQQuestionListCreateView,
    MCQQuestionDetailView,
    
    # Reading Passage
    ReadingPassageListCreateView,
    ReadingPassageDetailView,
    
    # Reading Question
    ReadingQuestionListCreateView,
    ReadingQuestionDetailView,
    
    # Listening Audio
    ListeningAudioListCreateView,
    ListeningAudioDetailView,
    
    # Listening Question
    ListeningQuestionListCreateView,
    ListeningQuestionDetailView,
    
    # Speaking Video
    SpeakingVideoListCreateView,
    SpeakingVideoDetailView,
    
    # Speaking Question
    SpeakingQuestionListCreateView,
    SpeakingQuestionDetailView,
    
    # Writing Question
    WritingQuestionListCreateView,
    WritingQuestionDetailView,
)


urlpatterns = [
    # ============================================
    # Placement Test URLs
    # ============================================
    path('tests/', PlacementTestListCreateView.as_view(), name='test-list-create'),
    path('tests/<int:pk>/', PlacementTestDetailView.as_view(), name='test-detail'),
    
    # ============================================
    # MCQ Question Set URLs
    # ============================================
    path('mcq-sets/', MCQQuestionSetListCreateView.as_view(), name='mcq-set-list-create'),
    path('mcq-sets/<int:pk>/', MCQQuestionSetDetailView.as_view(), name='mcq-set-detail'),
    
    # ============================================
    # MCQ Question URLs
    # ============================================
    path('mcq-questions/', MCQQuestionListCreateView.as_view(), name='mcq-question-list-create'),
    path('mcq-questions/<int:pk>/', MCQQuestionDetailView.as_view(), name='mcq-question-detail'),
    
    # ============================================
    # Reading Passage URLs
    # ============================================
    path('reading-passages/', ReadingPassageListCreateView.as_view(), name='reading-passage-list-create'),
    path('reading-passages/<int:pk>/', ReadingPassageDetailView.as_view(), name='reading-passage-detail'),
    
    # ============================================
    # Reading Question URLs
    # ============================================
    path('reading-questions/', ReadingQuestionListCreateView.as_view(), name='reading-question-list-create'),
    path('reading-questions/<int:pk>/', ReadingQuestionDetailView.as_view(), name='reading-question-detail'),
    
    # ============================================
    # Listening Audio URLs
    # ============================================
    path('listening-audios/', ListeningAudioListCreateView.as_view(), name='listening-audio-list-create'),
    path('listening-audios/<int:pk>/', ListeningAudioDetailView.as_view(), name='listening-audio-detail'),
    
    # ============================================
    # Listening Question URLs
    # ============================================
    path('listening-questions/', ListeningQuestionListCreateView.as_view(), name='listening-question-list-create'),
    path('listening-questions/<int:pk>/', ListeningQuestionDetailView.as_view(), name='listening-question-detail'),
    
    # ============================================
    # Speaking Video URLs
    # ============================================
    path('speaking-videos/', SpeakingVideoListCreateView.as_view(), name='speaking-video-list-create'),
    path('speaking-videos/<int:pk>/', SpeakingVideoDetailView.as_view(), name='speaking-video-detail'),
    
    # ============================================
    # Speaking Question URLs
    # ============================================
    path('speaking-questions/', SpeakingQuestionListCreateView.as_view(), name='speaking-question-list-create'),
    path('speaking-questions/<int:pk>/', SpeakingQuestionDetailView.as_view(), name='speaking-question-detail'),
    
    # ============================================
    # Writing Question URLs
    # ============================================
    path('writing-questions/', WritingQuestionListCreateView.as_view(), name='writing-question-list-create'),
    path('writing-questions/<int:pk>/', WritingQuestionDetailView.as_view(), name='writing-question-detail'),
]