from django.urls import path
from .views import (
    # Placement Test
    PlacementTestListCreateAPIView,
    PlacementTestDetailAPIView,
    
    # MCQ
    MCQQuestionSetListCreateAPIView,
    MCQQuestionSetDetailAPIView,
    MCQQuestionListCreateAPIView,
    MCQQuestionDetailAPIView,
    
    # Reading
    ReadingPassageListCreateAPIView,
    ReadingPassageDetailAPIView,
    ReadingQuestionListCreateAPIView,
    ReadingQuestionDetailAPIView,
    
    # Listening
    ListeningAudioListCreateAPIView,
    ListeningAudioDetailAPIView,
    ListeningQuestionListCreateAPIView,
    ListeningQuestionDetailAPIView,
    
    # Speaking
    SpeakingVideoListCreateAPIView,
    SpeakingVideoDetailAPIView,
    SpeakingQuestionListCreateAPIView,
    SpeakingQuestionDetailAPIView,
    
    # Writing
    WritingQuestionListCreateAPIView,
    WritingQuestionDetailAPIView,
)

urlpatterns = [
    # ============================================
    # Placement Test URLs
    # ============================================
    path('tests/', PlacementTestListCreateAPIView.as_view(), name='test-list-create'),
    path('tests/<int:pk>/', PlacementTestDetailAPIView.as_view(), name='test-detail'),
    
    # ============================================
    # MCQ Question Set URLs
    # ============================================
    path('mcq-sets/', MCQQuestionSetListCreateAPIView.as_view(), name='mcq-set-list-create'),
    path('mcq-sets/<int:pk>/', MCQQuestionSetDetailAPIView.as_view(), name='mcq-set-detail'),
    
    # MCQ Questions URLs
    path('mcq-questions/', MCQQuestionListCreateAPIView.as_view(), name='mcq-question-list-create'),
    path('mcq-questions/<int:pk>/', MCQQuestionDetailAPIView.as_view(), name='mcq-question-detail'),
    
    # ============================================
    # Reading URLs
    # ============================================
    path('reading-passages/', ReadingPassageListCreateAPIView.as_view(), name='reading-passage-list-create'),
    path('reading-passages/<int:pk>/', ReadingPassageDetailAPIView.as_view(), name='reading-passage-detail'),
    
    # Reading Questions URLs
    path('reading-questions/', ReadingQuestionListCreateAPIView.as_view(), name='reading-question-list-create'),
    path('reading-questions/<int:pk>/', ReadingQuestionDetailAPIView.as_view(), name='reading-question-detail'),
    
    # ============================================
    # Listening URLs
    # ============================================
    path('listening-audios/', ListeningAudioListCreateAPIView.as_view(), name='listening-audio-list-create'),
    path('listening-audios/<int:pk>/', ListeningAudioDetailAPIView.as_view(), name='listening-audio-detail'),
    
    # Listening Questions URLs
    path('listening-questions/', ListeningQuestionListCreateAPIView.as_view(), name='listening-question-list-create'),
    path('listening-questions/<int:pk>/', ListeningQuestionDetailAPIView.as_view(), name='listening-question-detail'),
    
    # ============================================
    # Speaking URLs
    # ============================================
    path('speaking-videos/', SpeakingVideoListCreateAPIView.as_view(), name='speaking-video-list-create'),
    path('speaking-videos/<int:pk>/', SpeakingVideoDetailAPIView.as_view(), name='speaking-video-detail'),
    
    # Speaking Questions URLs
    path('speaking-questions/', SpeakingQuestionListCreateAPIView.as_view(), name='speaking-question-list-create'),
    path('speaking-questions/<int:pk>/', SpeakingQuestionDetailAPIView.as_view(), name='speaking-question-detail'),
    
    # ============================================
    # Writing URLs
    # ============================================
    path('writing-questions/', WritingQuestionListCreateAPIView.as_view(), name='writing-question-list-create'),
    path('writing-questions/<int:pk>/', WritingQuestionDetailAPIView.as_view(), name='writing-question-detail'),
]