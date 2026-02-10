from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
import random

from placement_test.models import QuestionBank, StudentPlacementTestAttempt,PlacementTest,StudentPlacementTestAnswer
from sabr_questions.models import (
    VocabularyQuestionSet,
    VocabularyQuestion,
    GrammarQuestionSet,
    GrammarQuestion,
    ReadingPassage,
    ReadingQuestion,
    ListeningAudio,
    ListeningQuestion,
    SpeakingVideo,
    SpeakingQuestion,
    WritingQuestion
)
from .serializers import (
    # Question Bank Serializers
    QuestionBankSerializer,
    QuestionBankCreateSerializer,
    QuestionBankDetailSerializer,
    QuestionBankUpdateSerializer,
    # Vocabulary Serializers
    CreateVocabularyQuestionSerializer,
    VocabularyQuestionSerializer,
    # Grammar Serializers
    CreateGrammarQuestionSerializer,
    GrammarQuestionSerializer,
    # Reading Serializers
    ReadingPassageSerializer,
    CreateReadingQuestionSerializer,
    ReadingQuestionSerializer,
    # Listening Serializers
    ListeningAudioSerializer,
    CreateListeningQuestionSerializer,
    ListeningQuestionSerializer,
    # Speaking Serializers
    SpeakingVideoSerializer,
    CreateSpeakingQuestionSerializer,
    SpeakingQuestionSerializer,
    # Writing Serializers
    CreateWritingQuestionSerializer,
    WritingQuestionSerializer
)

from placement_test.services.exam_service import exam_service
from placement_test.serializers import (
    # ... الـ imports الموجودة
    SubmitExamSerializer,
    ExamResultSerializer,
    StudentAnswerDetailSerializer,
    StudentAttemptListSerializer,
)
import logging

logger = logging.getLogger(__name__)
# ============================================
# 1. QUESTION BANK CRUD OPERATIONS
# ============================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_question_bank(request):
    """
    إنشاء بنك أسئلة جديد
    
    POST /api/question-banks/create/
    
    Body:
    {
        "title": "بنك 1",
        "description": "بنك أسئلة شامل"  // اختياري
    }
    """
    serializer = QuestionBankCreateSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    question_bank = serializer.save()
    result_serializer = QuestionBankDetailSerializer(question_bank)
    
    return Response({
        'message': 'تم إنشاء بنك الأسئلة بنجاح',
        'question_bank': result_serializer.data
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_question_banks(request):
    """
    عرض جميع بنوك الأسئلة
    
    GET /api/question-banks/
    """
    question_banks = QuestionBank.objects.all().order_by('-created_at')
    serializer = QuestionBankSerializer(question_banks, many=True)
    
    return Response({
        'total_banks': question_banks.count(),
        'question_banks': serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_question_bank(request, bank_id):
    """
    عرض تفاصيل بنك أسئلة معين
    
    GET /api/question-banks/{bank_id}/
    """
    question_bank = get_object_or_404(QuestionBank, id=bank_id)
    serializer = QuestionBankDetailSerializer(question_bank)
    
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_question_bank(request, bank_id):
    """
    تعديل بنك أسئلة
    
    PUT /api/question-banks/{bank_id}/update/
    PATCH /api/question-banks/{bank_id}/update/
    
    Body:
    {
        "title": "بنك 1 - محدث",
        "description": "وصف جديد"
    }
    """
    question_bank = get_object_or_404(QuestionBank, id=bank_id)
    
    partial = request.method == 'PATCH'
    serializer = QuestionBankUpdateSerializer(
        question_bank,
        data=request.data,
        partial=partial
    )
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    question_bank = serializer.save()
    result_serializer = QuestionBankDetailSerializer(question_bank)
    
    return Response({
        'message': 'تم تحديث بنك الأسئلة بنجاح',
        'question_bank': result_serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_question_bank(request, bank_id):
    """
    حذف بنك أسئلة
    
    DELETE /api/question-banks/{bank_id}/delete/
    
    ⚠️ حذف نهائي - سيتم حذف جميع الأسئلة المرتبطة بالبنك
    """
    question_bank = get_object_or_404(QuestionBank, id=bank_id)
    
    title = question_bank.title
    question_bank.delete()
    
    return Response({
        'message': 'تم حذف بنك الأسئلة بنجاح',
        'bank_id': bank_id,
        'title': title
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def question_bank_statistics(request, bank_id):
    """
    إحصائيات بنك الأسئلة
    
    GET /api/question-banks/{bank_id}/statistics/
    """
    question_bank = get_object_or_404(QuestionBank, id=bank_id)
    
    # عدد الأسئلة الحالية
    vocab_count = question_bank.get_vocabulary_count()
    grammar_count = question_bank.get_grammar_count()
    reading_count = question_bank.get_reading_count()
    listening_count = question_bank.get_listening_count()
    speaking_count = question_bank.get_speaking_count()
    writing_count = question_bank.get_writing_count()
    total_count = question_bank.get_total_questions()
    
    # المتطلبات
    required = {
        'vocabulary': 10,
        'grammar': 10,
        'reading': 6,
        'listening': 10,
        'speaking': 10,
        'writing': 4,
        'total': 50
    }
    
    return Response({
        'question_bank': {
            'id': question_bank.id,
            'title': question_bank.title,
            'description': question_bank.description
        },
        'questions': {
            'vocabulary': vocab_count,
            'grammar': grammar_count,
            'reading': reading_count,
            'listening': listening_count,
            'speaking': speaking_count,
            'writing': writing_count,
            'total': total_count
        },
        'required_for_exam': required,
        'ready_status': {
            'vocabulary': vocab_count >= required['vocabulary'],
            'grammar': grammar_count >= required['grammar'],
            'reading': reading_count >= required['reading'],
            'listening': listening_count >= required['listening'],
            'speaking': speaking_count >= required['speaking'],
            'writing': writing_count >= required['writing']
        },
        'is_ready_for_exam': question_bank.is_ready_for_exam(),
        'missing_questions': {
            'vocabulary': max(0, required['vocabulary'] - vocab_count),
            'grammar': max(0, required['grammar'] - grammar_count),
            'reading': max(0, required['reading'] - reading_count),
            'listening': max(0, required['listening'] - listening_count),
            'speaking': max(0, required['speaking'] - speaking_count),
            'writing': max(0, required['writing'] - writing_count)
        }
    }, status=status.HTTP_200_OK)


# ============================================
# 2. ADD QUESTIONS TO BANK
# ============================================

# ---------- 2.1 Vocabulary Questions ----------

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_vocabulary_question(request, bank_id):
    """
    إضافة سؤال مفردات للبنك
    
    POST /api/question-banks/{bank_id}/add-vocabulary-question/
    """
    question_bank = get_object_or_404(QuestionBank, id=bank_id)
    serializer = CreateVocabularyQuestionSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    with transaction.atomic():
        question_set_id = serializer.validated_data.pop('question_set_id', None)
        question_set_title = serializer.validated_data.pop('question_set_title', None)
        question_set_description = serializer.validated_data.pop('question_set_description', '')
        
        if question_set_id:
            question_set = get_object_or_404(VocabularyQuestionSet, id=question_set_id)
        elif question_set_title:
            question_set, created = VocabularyQuestionSet.objects.get_or_create(
                title=question_set_title,
                usage_type='QUESTION_BANK',
                defaults={'description': question_set_description}
            )
        else:
            return Response(
                {'error': 'يجب تحديد question_set_id أو question_set_title'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        vocabulary_question = VocabularyQuestion.objects.create(
            question_set=question_set,
            usage_type='QUESTION_BANK',
            question_bank=question_bank,
            **serializer.validated_data
        )
    
    result_serializer = VocabularyQuestionSerializer(vocabulary_question)
    
    return Response({
        'message': 'تم إضافة سؤال المفردات بنجاح',
        'question': result_serializer.data,
        'question_bank': {
            'id': question_bank.id,
            'title': question_bank.title,
            'total_vocabulary_questions': question_bank.get_vocabulary_count()
        }
    }, status=status.HTTP_201_CREATED)


# ---------- 2.2 Grammar Questions ----------

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_grammar_question(request, bank_id):
    """
    إضافة سؤال قواعد للبنك
    
    POST /api/question-banks/{bank_id}/add-grammar-question/
    """
    question_bank = get_object_or_404(QuestionBank, id=bank_id)
    serializer = CreateGrammarQuestionSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    with transaction.atomic():
        question_set_id = serializer.validated_data.pop('question_set_id', None)
        question_set_title = serializer.validated_data.pop('question_set_title', None)
        question_set_description = serializer.validated_data.pop('question_set_description', '')
        
        if question_set_id:
            question_set = get_object_or_404(GrammarQuestionSet, id=question_set_id)
        elif question_set_title:
            question_set, created = GrammarQuestionSet.objects.get_or_create(
                title=question_set_title,
                usage_type='QUESTION_BANK',
                defaults={'description': question_set_description}
            )
        else:
            return Response(
                {'error': 'يجب تحديد question_set_id أو question_set_title'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        grammar_question = GrammarQuestion.objects.create(
            question_set=question_set,
            usage_type='QUESTION_BANK',
            question_bank=question_bank,
            **serializer.validated_data
        )
    
    result_serializer = GrammarQuestionSerializer(grammar_question)
    
    return Response({
        'message': 'تم إضافة سؤال القواعد بنجاح',
        'question': result_serializer.data,
        'question_bank': {
            'id': question_bank.id,
            'title': question_bank.title,
            'total_grammar_questions': question_bank.get_grammar_count()
        }
    }, status=status.HTTP_201_CREATED)


# ---------- 2.3 Reading Questions ----------

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_reading_passage(request, bank_id):
    """
    إنشاء قطعة قراءة جديدة للبنك
    
    POST /api/question-banks/{bank_id}/create-reading-passage/
    """
    question_bank = get_object_or_404(QuestionBank, id=bank_id)
    serializer = ReadingPassageSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    reading_passage = ReadingPassage.objects.create(
        usage_type='QUESTION_BANK',
        question_bank=question_bank,
        **serializer.validated_data
    )
    
    result_serializer = ReadingPassageSerializer(reading_passage)
    
    return Response({
        'message': 'تم إنشاء قطعة القراءة بنجاح',
        'passage': result_serializer.data
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_reading_question(request, bank_id, passage_id):
    """
    إضافة سؤال قراءة لقطعة معينة
    
    POST /api/question-banks/{bank_id}/reading-passages/{passage_id}/add-question/
    """
    question_bank = get_object_or_404(QuestionBank, id=bank_id)
    reading_passage = get_object_or_404(
        ReadingPassage,
        id=passage_id,
        question_bank=question_bank
    )
    
    serializer = CreateReadingQuestionSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    reading_question = ReadingQuestion.objects.create(
        passage=reading_passage,
        **serializer.validated_data
    )
    
    result_serializer = ReadingQuestionSerializer(reading_question)
    
    return Response({
        'message': 'تم إضافة سؤال القراءة بنجاح',
        'question': result_serializer.data,
        'passage': {
            'id': reading_passage.id,
            'title': reading_passage.title,
            'total_questions': reading_passage.get_questions_count()
        }
    }, status=status.HTTP_201_CREATED)


# ---------- 2.4 Listening Questions ----------

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_listening_audio(request, bank_id):
    """
    إنشاء تسجيل صوتي جديد للبنك
    
    POST /api/question-banks/{bank_id}/create-listening-audio/
    """
    question_bank = get_object_or_404(QuestionBank, id=bank_id)
    serializer = ListeningAudioSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    listening_audio = ListeningAudio.objects.create(
        usage_type='QUESTION_BANK',
        question_bank=question_bank,
        **serializer.validated_data
    )
    
    result_serializer = ListeningAudioSerializer(listening_audio)
    
    return Response({
        'message': 'تم إنشاء التسجيل الصوتي بنجاح',
        'audio': result_serializer.data
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_listening_question(request, bank_id, audio_id):
    """
    إضافة سؤال استماع لتسجيل صوتي معين
    
    POST /api/question-banks/{bank_id}/listening-audios/{audio_id}/add-question/
    """
    question_bank = get_object_or_404(QuestionBank, id=bank_id)
    listening_audio = get_object_or_404(
        ListeningAudio,
        id=audio_id,
        question_bank=question_bank
    )
    
    serializer = CreateListeningQuestionSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    listening_question = ListeningQuestion.objects.create(
        audio=listening_audio,
        **serializer.validated_data
    )
    
    result_serializer = ListeningQuestionSerializer(listening_question)
    
    return Response({
        'message': 'تم إضافة سؤال الاستماع بنجاح',
        'question': result_serializer.data,
        'audio': {
            'id': listening_audio.id,
            'title': listening_audio.title,
            'total_questions': listening_audio.get_questions_count()
        }
    }, status=status.HTTP_201_CREATED)


# ---------- 2.5 Speaking Questions ----------

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_speaking_video(request, bank_id):
    """
    إنشاء فيديو تحدث جديد للبنك
    
    POST /api/question-banks/{bank_id}/create-speaking-video/
    """
    question_bank = get_object_or_404(QuestionBank, id=bank_id)
    serializer = SpeakingVideoSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    speaking_video = SpeakingVideo.objects.create(
        usage_type='QUESTION_BANK',
        question_bank=question_bank,
        **serializer.validated_data
    )
    
    result_serializer = SpeakingVideoSerializer(speaking_video)
    
    return Response({
        'message': 'تم إنشاء فيديو التحدث بنجاح',
        'video': result_serializer.data
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_speaking_question(request, bank_id, video_id):
    """
    إضافة سؤال تحدث لفيديو معين
    
    POST /api/question-banks/{bank_id}/speaking-videos/{video_id}/add-question/
    """
    question_bank = get_object_or_404(QuestionBank, id=bank_id)
    speaking_video = get_object_or_404(
        SpeakingVideo,
        id=video_id,
        question_bank=question_bank
    )
    
    serializer = CreateSpeakingQuestionSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    speaking_question = SpeakingQuestion.objects.create(
        video=speaking_video,
        **serializer.validated_data
    )
    
    result_serializer = SpeakingQuestionSerializer(speaking_question)
    
    return Response({
        'message': 'تم إضافة سؤال التحدث بنجاح',
        'question': result_serializer.data,
        'video': {
            'id': speaking_video.id,
            'title': speaking_video.title,
            'total_questions': speaking_video.get_questions_count()
        }
    }, status=status.HTTP_201_CREATED)


# ---------- 2.6 Writing Questions ----------

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_writing_question(request, bank_id):
    """
    إضافة سؤال كتابة للبنك
    
    POST /api/question-banks/{bank_id}/add-writing-question/
    """
    question_bank = get_object_or_404(QuestionBank, id=bank_id)
    serializer = CreateWritingQuestionSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    writing_question = WritingQuestion.objects.create(
        usage_type='QUESTION_BANK',
        question_bank=question_bank,
        **serializer.validated_data
    )
    
    result_serializer = WritingQuestionSerializer(writing_question)
    
    return Response({
        'message': 'تم إضافة سؤال الكتابة بنجاح',
        'question': result_serializer.data,
        'question_bank': {
            'id': question_bank.id,
            'title': question_bank.title,
            'total_writing_questions': question_bank.get_writing_count()
        }
    }, status=status.HTTP_201_CREATED)


# ============================================
# 3. LIST QUESTIONS FROM BANK
# ============================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_bank_questions(request, bank_id):
    """
    عرض جميع الأسئلة الموجودة في البنك
    
    GET /api/question-banks/{bank_id}/all-questions/
    
    Query Parameters (Optional):
    - question_type: filter by type (vocabulary, grammar, reading, listening, speaking, writing)
    
    Example: GET /api/question-banks/1/all-questions/?question_type=vocabulary
    """
    question_bank = get_object_or_404(QuestionBank, id=bank_id)
    question_type = request.query_params.get('question_type', None)
    
    response_data = {
        'question_bank': {
            'id': question_bank.id,
            'title': question_bank.title,
            'description': question_bank.description
        },
        'questions': {}
    }
    
    # Vocabulary Questions
    if not question_type or question_type == 'vocabulary':
        vocabulary_questions = VocabularyQuestion.objects.filter(
            question_bank=question_bank,
            is_active=True
        ).select_related('question_set').order_by('order', 'id')
        
        response_data['questions']['vocabulary'] = {
            'count': vocabulary_questions.count(),
            'questions': VocabularyQuestionSerializer(vocabulary_questions, many=True).data
        }
    
    # Grammar Questions
    if not question_type or question_type == 'grammar':
        grammar_questions = GrammarQuestion.objects.filter(
            question_bank=question_bank,
            is_active=True
        ).select_related('question_set').order_by('order', 'id')
        
        response_data['questions']['grammar'] = {
            'count': grammar_questions.count(),
            'questions': GrammarQuestionSerializer(grammar_questions, many=True).data
        }
    
    # Reading Passages & Questions
    if not question_type or question_type == 'reading':
        reading_passages = ReadingPassage.objects.filter(
            question_bank=question_bank,
            is_active=True
        ).prefetch_related('questions').order_by('order', 'id')
        
        passages_data = []
        total_reading_questions = 0
        
        for passage in reading_passages:
            passage_serializer = ReadingPassageSerializer(passage)
            questions = passage.questions.filter(is_active=True).order_by('order', 'id')
            questions_serializer = ReadingQuestionSerializer(questions, many=True)
            
            passages_data.append({
                'passage': passage_serializer.data,
                'questions': questions_serializer.data
            })
            total_reading_questions += questions.count()
        
        response_data['questions']['reading'] = {
            'count': total_reading_questions,
            'passages_count': reading_passages.count(),
            'passages': passages_data
        }
    
    # Listening Audios & Questions
    if not question_type or question_type == 'listening':
        listening_audios = ListeningAudio.objects.filter(
            question_bank=question_bank,
            is_active=True
        ).prefetch_related('questions').order_by('order', 'id')
        
        audios_data = []
        total_listening_questions = 0
        
        for audio in listening_audios:
            audio_serializer = ListeningAudioSerializer(audio)
            questions = audio.questions.filter(is_active=True).order_by('order', 'id')
            questions_serializer = ListeningQuestionSerializer(questions, many=True)
            
            audios_data.append({
                'audio': audio_serializer.data,
                'questions': questions_serializer.data
            })
            total_listening_questions += questions.count()
        
        response_data['questions']['listening'] = {
            'count': total_listening_questions,
            'audios_count': listening_audios.count(),
            'audios': audios_data
        }
    
    # Speaking Videos & Questions
    if not question_type or question_type == 'speaking':
        speaking_videos = SpeakingVideo.objects.filter(
            question_bank=question_bank,
            is_active=True
        ).prefetch_related('questions').order_by('order', 'id')
        
        videos_data = []
        total_speaking_questions = 0
        
        for video in speaking_videos:
            video_serializer = SpeakingVideoSerializer(video)
            questions = video.questions.filter(is_active=True).order_by('order', 'id')
            questions_serializer = SpeakingQuestionSerializer(questions, many=True)
            
            videos_data.append({
                'video': video_serializer.data,
                'questions': questions_serializer.data
            })
            total_speaking_questions += questions.count()
        
        response_data['questions']['speaking'] = {
            'count': total_speaking_questions,
            'videos_count': speaking_videos.count(),
            'videos': videos_data
        }
    
    # Writing Questions
    if not question_type or question_type == 'writing':
        writing_questions = WritingQuestion.objects.filter(
            question_bank=question_bank,
            is_active=True
        ).order_by('order', 'id')
        
        response_data['questions']['writing'] = {
            'count': writing_questions.count(),
            'questions': WritingQuestionSerializer(writing_questions, many=True).data
        }
    
    # Total count
    if not question_type:
        response_data['total_questions'] = question_bank.get_total_questions()
    
    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_vocabulary_questions(request, bank_id):
    """
    عرض جميع أسئلة المفردات في البنك
    
    GET /api/question-banks/{bank_id}/vocabulary-questions/
    """
    question_bank = get_object_or_404(QuestionBank, id=bank_id)
    
    questions = VocabularyQuestion.objects.filter(
        question_bank=question_bank,
        is_active=True
    ).select_related('question_set').order_by('order', 'id')
    
    serializer = VocabularyQuestionSerializer(questions, many=True)
    
    return Response({
        'question_bank': {
            'id': question_bank.id,
            'title': question_bank.title
        },
        'total_questions': questions.count(),
        'questions': serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_grammar_questions(request, bank_id):
    """
    عرض جميع أسئلة القواعد في البنك
    
    GET /api/question-banks/{bank_id}/grammar-questions/
    """
    question_bank = get_object_or_404(QuestionBank, id=bank_id)
    
    questions = GrammarQuestion.objects.filter(
        question_bank=question_bank,
        is_active=True
    ).select_related('question_set').order_by('order', 'id')
    
    serializer = GrammarQuestionSerializer(questions, many=True)
    
    return Response({
        'question_bank': {
            'id': question_bank.id,
            'title': question_bank.title
        },
        'total_questions': questions.count(),
        'questions': serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_reading_passages(request, bank_id):
    """
    عرض جميع قطع القراءة في البنك
    
    GET /api/question-banks/{bank_id}/reading-passages/
    """
    question_bank = get_object_or_404(QuestionBank, id=bank_id)
    
    passages = ReadingPassage.objects.filter(
        question_bank=question_bank,
        is_active=True
    ).prefetch_related('questions').order_by('order', 'id')
    
    serializer = ReadingPassageSerializer(passages, many=True)
    
    return Response({
        'question_bank': {
            'id': question_bank.id,
            'title': question_bank.title
        },
        'total_passages': passages.count(),
        'passages': serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_listening_audios(request, bank_id):
    """
    عرض جميع التسجيلات الصوتية في البنك
    
    GET /api/question-banks/{bank_id}/listening-audios/
    """
    question_bank = get_object_or_404(QuestionBank, id=bank_id)
    
    audios = ListeningAudio.objects.filter(
        question_bank=question_bank,
        is_active=True
    ).prefetch_related('questions').order_by('order', 'id')
    
    serializer = ListeningAudioSerializer(audios, many=True)
    
    return Response({
        'question_bank': {
            'id': question_bank.id,
            'title': question_bank.title
        },
        'total_audios': audios.count(),
        'audios': serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_speaking_videos(request, bank_id):
    """
    عرض جميع فيديوهات التحدث في البنك
    
    GET /api/question-banks/{bank_id}/speaking-videos/
    """
    question_bank = get_object_or_404(QuestionBank, id=bank_id)
    
    videos = SpeakingVideo.objects.filter(
        question_bank=question_bank,
        is_active=True
    ).prefetch_related('questions').order_by('order', 'id')
    
    serializer = SpeakingVideoSerializer(videos, many=True)
    
    return Response({
        'question_bank': {
            'id': question_bank.id,
            'title': question_bank.title
        },
        'total_videos': videos.count(),
        'videos': serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_writing_questions(request, bank_id):
    """
    عرض جميع أسئلة الكتابة في البنك
    
    GET /api/question-banks/{bank_id}/writing-questions/
    """
    question_bank = get_object_or_404(QuestionBank, id=bank_id)
    
    questions = WritingQuestion.objects.filter(
        question_bank=question_bank,
        is_active=True
    ).order_by('order', 'id')
    
    serializer = WritingQuestionSerializer(questions, many=True)
    
    return Response({
        'question_bank': {
            'id': question_bank.id,
            'title': question_bank.title
        },
        'total_questions': questions.count(),
        'questions': serializer.data
    }, status=status.HTTP_200_OK)


# ============================================
# 4. STUDENT EXAM CREATION
# ============================================
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_exam_from_bank(request):
    """
    إنشاء امتحان عشوائي من بنك الأسئلة
    
    ✅ التعديل الجديد:
    - لا يحتاج question_bank_id في الـ request
    - يبحث عن بنوك جاهزة تلقائيًا
    - يختار بنك عشوائي إذا كان هناك أكثر من واحد
    """
    
    # ✅ البحث عن جميع البنوك الجاهزة للامتحان
    ready_banks = []
    all_banks = QuestionBank.objects.all()
    
    for bank in all_banks:
        if bank.is_ready_for_exam():
            ready_banks.append(bank)
    
    # ✅ التحقق من وجود بنوك جاهزة
    if not ready_banks:
        return Response({
            'error': 'لا يوجد بنوك أسئلة جاهزة للامتحان',
            'message': 'يجب أن يحتوي البنك على الأقل على: 10 vocabulary, 10 grammar, 6 reading, 10 listening, 10 speaking, 4 writing',
            'available_banks': QuestionBank.objects.count(),
            'ready_banks': 0
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # ✅ اختيار بنك عشوائي من البنوك الجاهزة
    question_bank = random.choice(ready_banks)
    
    # ✅ Create or get default PlacementTest
    placement_test, created = PlacementTest.objects.get_or_create(
        title=f"Placement Test - {question_bank.title}",
        defaults={
            'description': f'Auto-generated for {question_bank.title}',
            'duration_minutes': 30,
            'total_questions': 50,
            'vocabulary_count': 10,
            'grammar_count': 10,
            'reading_count': 6,
            'listening_count': 10,
            'speaking_count': 10,
            'writing_count': 4,
        }
    )
    
    # ⚠️ TODO: REMOVE COMMENTS IN PRODUCTION ⚠️
    # ========================================
    # 🚧 الكود ده معطل مؤقتاً للتطوير فقط
    # ========================================
    
    # Check if student already has an active attempt
    # active_attempt = StudentPlacementTestAttempt.objects.filter(
    #     student=request.user,
    #     status='IN_PROGRESS'
    # ).first()
    
    # if active_attempt:
    #     return Response({
    #         'error': 'لديك امتحان قيد التنفيذ بالفعل',
    #         'attempt_id': active_attempt.id,
    #         'question_bank': {
    #             'id': active_attempt.question_bank.id,
    #             'title': active_attempt.question_bank.title
    #         },
    #         'started_at': active_attempt.started_at
    #     }, status=status.HTTP_400_BAD_REQUEST)
    
    # ========================================
    # ⚠️ END OF COMMENTED CODE ⚠️
    # ========================================

    # Start transaction
    with transaction.atomic():
        # Select random questions
        selected_questions = select_random_questions_from_bank(question_bank)
        
        # Create attempt
        attempt = StudentPlacementTestAttempt.objects.create(
            student=request.user,
            placement_test=placement_test,
            question_bank=question_bank,
            status='IN_PROGRESS',
            started_at=timezone.now()
        )
        
        # Save selected questions
        attempt.set_selected_questions(selected_questions)
        
        # Fetch actual question objects
        exam_questions = fetch_selected_questions(selected_questions)
    
    # Return response
    return Response({
        'message': 'تم إنشاء الامتحان بنجاح',
        'selected_bank_info': {
            'id': question_bank.id,
            'title': question_bank.title,
            'description': question_bank.description,
            'total_ready_banks': len(ready_banks),
            'was_randomly_selected': len(ready_banks) > 1
        },
        'attempt': {
            'id': attempt.id,
            'question_bank': {
                'id': question_bank.id,
                'title': question_bank.title
            },
            'duration_minutes': placement_test.duration_minutes,
            'total_questions': placement_test.total_questions,
            'started_at': attempt.started_at,
            'ends_at': attempt.started_at + timezone.timedelta(minutes=placement_test.duration_minutes)
        },
        'questions': exam_questions,
        'distribution': {
            'vocabulary': len(selected_questions['vocabulary']),
            'grammar': len(selected_questions['grammar']),
            'reading': len(selected_questions['reading']),
            'listening': len(selected_questions['listening']),
            'speaking': len(selected_questions['speaking']),
            'writing': len(selected_questions['writing'])
        }
    }, status=status.HTTP_201_CREATED)
# ============================================
# 5. HELPER FUNCTIONS
# ============================================

def select_random_questions_from_bank(question_bank):
    """
    اختيار أسئلة عشوائية من البنك
    
    Returns:
        dict: {
            'vocabulary': [list of question IDs],
            'grammar': [list of question IDs],
            'reading': [list of question IDs],
            'listening': [list of question IDs],
            'speaking': [list of question IDs],
            'writing': [list of question IDs]
        }
    """
    selected_questions = {
        'vocabulary': [],
        'grammar': [],
        'reading': [],
        'listening': [],
        'speaking': [],
        'writing': []
    }
    
    # Vocabulary (10 questions)
    vocabulary_ids = list(
        VocabularyQuestion.objects.filter(
            question_bank=question_bank,
            is_active=True
        ).values_list('id', flat=True)
    )
    selected_questions['vocabulary'] = random.sample(vocabulary_ids, min(10, len(vocabulary_ids)))
    
    # Grammar (10 questions)
    grammar_ids = list(
        GrammarQuestion.objects.filter(
            question_bank=question_bank,
            is_active=True
        ).values_list('id', flat=True)
    )
    selected_questions['grammar'] = random.sample(grammar_ids, min(10, len(grammar_ids)))
    
    # Reading (6 questions)
    reading_ids = list(
        ReadingQuestion.objects.filter(
            passage__question_bank=question_bank,
            passage__is_active=True,
            is_active=True
        ).values_list('id', flat=True)
    )
    selected_questions['reading'] = random.sample(reading_ids, min(6, len(reading_ids)))
    
    # Listening (10 questions)
    listening_ids = list(
        ListeningQuestion.objects.filter(
            audio__question_bank=question_bank,
            audio__is_active=True,
            is_active=True
        ).values_list('id', flat=True)
    )
    selected_questions['listening'] = random.sample(listening_ids, min(10, len(listening_ids)))
    
    # Speaking (10 questions)
    speaking_ids = list(
        SpeakingQuestion.objects.filter(
            video__question_bank=question_bank,
            video__is_active=True,
            is_active=True
        ).values_list('id', flat=True)
    )
    selected_questions['speaking'] = random.sample(speaking_ids, min(10, len(speaking_ids)))
    
    # Writing (4 questions)
    writing_ids = list(
        WritingQuestion.objects.filter(
            question_bank=question_bank,
            is_active=True
        ).values_list('id', flat=True)
    )
    selected_questions['writing'] = random.sample(writing_ids, min(4, len(writing_ids)))
    
    return selected_questions


def fetch_selected_questions(selected_questions):
    """
    جلب الأسئلة الفعلية من الـ IDs
    
    Returns:
        dict: الأسئلة مع جميع التفاصيل
    """
    exam_questions = {}
    
    # Vocabulary
    vocab_questions = VocabularyQuestion.objects.filter(
        id__in=selected_questions['vocabulary']
    ).select_related('question_set')
    exam_questions['vocabulary'] = VocabularyQuestionSerializer(vocab_questions, many=True).data
    
    # Grammar
    grammar_questions = GrammarQuestion.objects.filter(
        id__in=selected_questions['grammar']
    ).select_related('question_set')
    exam_questions['grammar'] = GrammarQuestionSerializer(grammar_questions, many=True).data
    
    # Reading
    reading_questions = ReadingQuestion.objects.filter(
        id__in=selected_questions['reading']
    ).select_related('passage')
    exam_questions['reading'] = ReadingQuestionSerializer(reading_questions, many=True).data
    
    # Listening
    listening_questions = ListeningQuestion.objects.filter(
        id__in=selected_questions['listening']
    ).select_related('audio')
    exam_questions['listening'] = ListeningQuestionSerializer(listening_questions, many=True).data
    
    # Speaking
    speaking_questions = SpeakingQuestion.objects.filter(
        id__in=selected_questions['speaking']
    ).select_related('video')
    exam_questions['speaking'] = SpeakingQuestionSerializer(speaking_questions, many=True).data
    
    # Writing
    writing_questions = WritingQuestion.objects.filter(
        id__in=selected_questions['writing']
    )
    exam_questions['writing'] = WritingQuestionSerializer(writing_questions, many=True).data
    
    return exam_questions


# ============================================
# 5. STUDENT EXAM SUBMISSION & RESULTS
# ============================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_exam(request, attempt_id):
    """
    تقديم إجابات الامتحان
    
    POST /api/place/student/submit-exam/{attempt_id}/
    
    Body:
    {
        "answers": {
            "vocabulary": [
                {"question_id": 1, "selected_choice": "A"},
                {"question_id": 5, "selected_choice": "B"}
            ],
            "grammar": [
                {"question_id": 2, "selected_choice": "C"}
            ],
            "reading": [
                {"question_id": 3, "selected_choice": "D"}
            ],
            "listening": [
                {"question_id": 4, "selected_choice": "A"}
            ],
            "speaking": [
                {"question_id": 6, "selected_choice": "B"}
            ],
            "writing": [
                {
                    "question_id": 7,
                    "text_answer": "This is my answer to the writing question..."
                }
            ]
        }
    }
    """
    
    # التحقق من المحاولة
    try:
        attempt = StudentPlacementTestAttempt.objects.get(
            id=attempt_id,
            student=request.user,
            status='IN_PROGRESS'
        )
    except StudentPlacementTestAttempt.DoesNotExist:
        return Response({
            'error': 'الامتحان غير موجود أو تم إنهاؤه بالفعل'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # التحقق من انتهاء الوقت
    if attempt.is_time_up():
        attempt.status = 'ABANDONED'
        attempt.save()
        return Response({
            'error': 'انتهى وقت الامتحان',
            'started_at': attempt.started_at,
            'time_limit_minutes': attempt.placement_test.duration_minutes
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # التحقق من صحة البيانات
    serializer = SubmitExamSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({
            'error': 'بيانات غير صحيحة',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # تقديم الإجابات والحصول على النتيجة
    try:
        result = exam_service.submit_exam_answers(
            attempt_id=attempt_id,
            answers_data=serializer.validated_data['answers']
        )
        
        return Response({
            'message': 'تم تقديم الامتحان بنجاح',
            'result': result
        }, status=status.HTTP_200_OK)
        
    except ValueError as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        logger.error(f"Error submitting exam {attempt_id}: {str(e)}")
        return Response({
            'error': 'حدث خطأ أثناء تقديم الامتحان',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_exam_result(request, attempt_id):
    """
    عرض نتيجة امتحان معين
    
    GET /api/place/student/exam-result/{attempt_id}/
    """
    try:
        attempt = StudentPlacementTestAttempt.objects.get(
            id=attempt_id,
            student=request.user
        )
    except StudentPlacementTestAttempt.DoesNotExist:
        return Response({
            'error': 'الامتحان غير موجود'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # يجب أن يكون الامتحان مكتمل
    if attempt.status != 'COMPLETED':
        return Response({
            'error': 'الامتحان لم يكتمل بعد',
            'status': attempt.status
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # تفاصيل النتيجة
    result_serializer = ExamResultSerializer(attempt)
    
    # تفاصيل الإجابات
    answers = StudentPlacementTestAnswer.objects.filter(
        attempt=attempt
    ).order_by('answered_at')
    
    answers_by_type = {
        'vocabulary': [],
        'grammar': [],
        'reading': [],
        'listening': [],
        'speaking': [],
        'writing': []
    }
    
    for answer in answers:
        q_type = answer.get_question_type_display()
        type_mapping = {
            'مفردات': 'vocabulary',
            'قواعد': 'grammar',
            'قراءة': 'reading',
            'استماع': 'listening',
            'تحدث': 'speaking',
            'كتابة': 'writing'
        }
        
        key = type_mapping.get(q_type)
        if key:
            answers_by_type[key].append(
                StudentAnswerDetailSerializer(answer).data
            )
    
    # إحصائيات تفصيلية
    total_mcq = sum([
        len(answers_by_type['vocabulary']),
        len(answers_by_type['grammar']),
        len(answers_by_type['reading']),
        len(answers_by_type['listening']),
        len(answers_by_type['speaking'])
    ])
    
    correct_mcq = sum([
        sum(1 for a in answers_by_type['vocabulary'] if a['is_correct']),
        sum(1 for a in answers_by_type['grammar'] if a['is_correct']),
        sum(1 for a in answers_by_type['reading'] if a['is_correct']),
        sum(1 for a in answers_by_type['listening'] if a['is_correct']),
        sum(1 for a in answers_by_type['speaking'] if a['is_correct'])
    ])
    
    writing_scores = [a['points_earned'] for a in answers_by_type['writing']]
    total_writing_score = sum(writing_scores)
    max_writing_score = len(writing_scores) * 10  # assuming 10 points per writing question
    
    return Response({
        'exam_info': result_serializer.data,
        'statistics': {
            'mcq': {
                'total': total_mcq,
                'correct': correct_mcq,
                'wrong': total_mcq - correct_mcq,
                'accuracy': round((correct_mcq / total_mcq * 100), 2) if total_mcq > 0 else 0
            },
            'writing': {
                'total_questions': len(writing_scores),
                'total_score': total_writing_score,
                'max_score': max_writing_score,
                'average_score': round(sum(writing_scores) / len(writing_scores), 2) if writing_scores else 0
            }
        },
        'answers_details': answers_by_type
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_exam_attempts(request):
    """
    عرض جميع محاولات الطالب
    
    GET /api/place/student/my-attempts/
    
    Query Parameters:
    - status: IN_PROGRESS | COMPLETED | ABANDONED
    - limit: عدد النتائج (default: 10)
    """
    status_filter = request.query_params.get('status', None)
    limit = int(request.query_params.get('limit', 10))
    
    attempts = StudentPlacementTestAttempt.objects.filter(
        student=request.user
    ).select_related(
        'placement_test',
        'question_bank'
    ).order_by('-started_at')
    
    if status_filter:
        attempts = attempts.filter(status=status_filter)
    
    # Pagination
    attempts = attempts[:limit]
    
    serializer = StudentAttemptListSerializer(attempts, many=True)
    
    # إحصائيات عامة
    total_attempts = StudentPlacementTestAttempt.objects.filter(
        student=request.user
    ).count()
    
    completed_attempts = StudentPlacementTestAttempt.objects.filter(
        student=request.user,
        status='COMPLETED'
    ).count()
    
    in_progress = StudentPlacementTestAttempt.objects.filter(
        student=request.user,
        status='IN_PROGRESS'
    ).count()
    
    # أعلى درجة
    best_attempt = StudentPlacementTestAttempt.objects.filter(
        student=request.user,
        status='COMPLETED'
    ).order_by('-score').first()
    
    return Response({
        'summary': {
            'total_attempts': total_attempts,
            'completed': completed_attempts,
            'in_progress': in_progress,
            'best_score': best_attempt.score if best_attempt else 0,
            'best_level': best_attempt.level_achieved if best_attempt else None
        },
        'attempts': serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_active_exam(request):
    """
    الحصول على الامتحان النشط (إذا وُجد)
    
    GET /api/place/student/active-exam/
    """
    active_attempt = StudentPlacementTestAttempt.objects.filter(
        student=request.user,
        status='IN_PROGRESS'
    ).select_related('placement_test', 'question_bank').first()
    
    if not active_attempt:
        return Response({
            'message': 'لا يوجد امتحان نشط',
            'has_active_exam': False
        }, status=status.HTTP_200_OK)
    
    # التحقق من انتهاء الوقت
    if active_attempt.is_time_up():
        active_attempt.status = 'ABANDONED'
        active_attempt.save()
        return Response({
            'message': 'انتهى وقت الامتحان النشط',
            'has_active_exam': False
        }, status=status.HTTP_200_OK)
    
    # حساب الوقت المتبقي
    from django.utils import timezone
    import datetime
    
    elapsed = timezone.now() - active_attempt.started_at
    elapsed_minutes = elapsed.total_seconds() / 60
    remaining_minutes = active_attempt.placement_test.duration_minutes - elapsed_minutes
    
    return Response({
        'has_active_exam': True,
        'attempt': {
            'id': active_attempt.id,
            'question_bank_title': active_attempt.question_bank.title,
            'started_at': active_attempt.started_at,
            'duration_minutes': active_attempt.placement_test.duration_minutes,
            'elapsed_minutes': round(elapsed_minutes, 2),
            'remaining_minutes': round(max(0, remaining_minutes), 2),
            'total_questions': active_attempt.placement_test.total_questions
        }
    }, status=status.HTTP_200_OK)