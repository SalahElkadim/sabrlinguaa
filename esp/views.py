from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.paginator import Paginator
from django.db.models import Case, When, IntegerField, Value
import math
from .models import (
    EspCategory,
    EspSkill,
    StudentEspProgress,
    StudentEspQuestionAttempt,
)
from .serializers import (
    EspCategoryListSerializer,
    EspCategoryDetailSerializer,
    EspSkillListSerializer,
    EspSkillDetailSerializer,
    StudentEspProgressSerializer,
)

import logging
logger = logging.getLogger(__name__)


# ============================================
# نظام النقاط
# ============================================

ATTEMPT_POINTS = {1: 20, 2: 15, 3: 10}
SHOW_ANSWER_POINTS = 5
MAX_ATTEMPTS_POINTS = 5

def _get_ordered_questions(queryset, order_type):
    """
    ترتيب الأسئلة حسب النوع المختار في المهارة.
    """
    if order_type == 'RANDOM':
        return queryset.order_by('?')

    elif order_type == 'SEQUENTIAL':
        return queryset.annotate(
            diff_order=Case(
                When(difficulty='EASY', then=Value(1)),
                When(difficulty='MEDIUM', then=Value(2)),
                When(difficulty='HARD', then=Value(3)),
                default=Value(2),
                output_field=IntegerField()
            )
        ).order_by('diff_order', 'order', 'id')

    elif order_type == 'CYCLIC':
        # جيب الكل مرتبين حسب الصعوبة
        easy   = list(queryset.filter(difficulty='EASY').order_by('order', 'id'))
        medium = list(queryset.filter(difficulty='MEDIUM').order_by('order', 'id'))
        hard   = list(queryset.filter(difficulty='HARD').order_by('order', 'id'))
        
        result = []
        chunk = 3
        max_rounds = max(
            math.ceil(len(easy) / chunk),
            math.ceil(len(medium) / chunk),
            math.ceil(len(hard) / chunk),
        )
        for i in range(max_rounds):
            result += easy[i*chunk : (i+1)*chunk]
            result += medium[i*chunk : (i+1)*chunk]
            result += hard[i*chunk : (i+1)*chunk]
        
        # رجّع list مش queryset — الـ Paginator يقبل الاتنين
        return result

    return queryset.order_by('order', 'id')

import cloudinary.utils

def _get_cloudinary_url(field_value, resource_type='video'):
    if not field_value:
        return None
    return cloudinary.utils.cloudinary_url(str(field_value), resource_type=resource_type)[0]
# ============================================
# 1. CATEGORY CRUD
# ============================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_categories(request):
    """
    GET /api/esp/categories/
    """
    categories = EspCategory.objects.filter().order_by('order')
    serializer = EspCategoryListSerializer(categories, many=True)
    return Response({
        'total_categories': categories.count(),
        'categories': serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_category(request, category_id):
    """
    GET /api/esp/categories/{category_id}/
    """
    category = get_object_or_404(EspCategory, id=category_id)
    serializer = EspCategoryDetailSerializer(category)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_category(request):
    """
    POST /api/esp/categories/create/
    Body: { "name": "...", "description": "...", "order": 0 }
    """
    serializer = EspCategoryDetailSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    category = serializer.save()
    return Response({
        'message': 'تم إنشاء الكاتيجوري بنجاح',
        'category': EspCategoryDetailSerializer(category).data
    }, status=status.HTTP_201_CREATED)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_category(request, category_id):
    """
    PUT/PATCH /api/esp/categories/{category_id}/update/
    """
    category = get_object_or_404(EspCategory, id=category_id)
    partial = request.method == 'PATCH'
    serializer = EspCategoryDetailSerializer(category, data=request.data, partial=partial)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    category = serializer.save()
    return Response({
        'message': 'تم تحديث الكاتيجوري بنجاح',
        'category': EspCategoryDetailSerializer(category).data
    }, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_category(request, category_id):
    """
    DELETE /api/esp/categories/{category_id}/delete/
    """
    category = get_object_or_404(EspCategory, id=category_id)
    name = category.name
    category.delete()
    return Response({
        'message': 'تم حذف الكاتيجوري بنجاح',
        'category_id': category_id,
        'name': name
    }, status=status.HTTP_200_OK)


# ============================================
# 2. SKILL CRUD
# ============================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_skills(request, category_id):
    """
    GET /api/esp/categories/{category_id}/skills/
    """
    category = get_object_or_404(EspCategory, id=category_id)
    skills = EspSkill.objects.filter(category=category).order_by('order')
    serializer = EspSkillListSerializer(skills, many=True)
    return Response({
        'category': {'id': category.id, 'name': category.name},
        'total_skills': skills.count(),
        'skills': serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_skill(request, skill_id):
    """
    GET /api/esp/skills/{skill_id}/
    """
    skill = get_object_or_404(EspSkill, id=skill_id)
    serializer = EspSkillDetailSerializer(skill)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_skill(request, category_id):
    """
    POST /api/esp/categories/{category_id}/skills/create/
    Body: { "skill_type": "VOCABULARY", "title": "...", "description": "...", "order": 0 }
    """
    category = get_object_or_404(EspCategory, id=category_id)
    data = request.data.copy()
    data['category'] = category.id

    serializer = EspSkillDetailSerializer(data=data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    skill = serializer.save()
    return Response({
        'message': 'تم إنشاء المهارة بنجاح',
        'skill': EspSkillDetailSerializer(skill).data
    }, status=status.HTTP_201_CREATED)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_skill(request, skill_id):
    """
    PUT/PATCH /api/esp/skills/{skill_id}/update/
    """
    skill = get_object_or_404(EspSkill, id=skill_id)
    partial = request.method == 'PATCH'
    serializer = EspSkillDetailSerializer(skill, data=request.data, partial=partial)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    skill = serializer.save()
    return Response({
        'message': 'تم تحديث المهارة بنجاح',
        'skill': EspSkillDetailSerializer(skill).data
    }, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_skill(request, skill_id):
    """
    DELETE /api/esp/skills/{skill_id}/delete/
    """
    skill = get_object_or_404(EspSkill, id=skill_id)
    skill.delete()
    return Response({
        'message': 'تم حذف المهارة بنجاح',
        'skill_id': skill_id,
    }, status=status.HTTP_200_OK)


# ============================================
# 3. QUESTIONS MANAGEMENT (CREATE)
# ============================================

def _map_options_to_letters(options, correct_answer):
    for idx, option in enumerate(options):
        if option == correct_answer:
            return chr(65 + idx)
    return None


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_vocabulary_question(request):
    """
    POST /api/esp/vocabulary/create/
    Body: { "question_text": "...", "options": [...], "correct_answer": "...", "esp_skill": 1 }
    """
    from sabr_questions.models import VocabularyQuestion, VocabularyQuestionSet

    data = request.data.copy()
    required_fields = ['question_text', 'options', 'correct_answer', 'esp_skill']
    for field in required_fields:
        if field not in data:
            return Response({field: f'{field} مطلوب'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        skill = get_object_or_404(EspSkill, id=data.get('esp_skill'))
        if skill.skill_type != 'VOCABULARY':
            return Response({'error': 'هذه المهارة ليست من نوع Vocabulary'}, status=status.HTTP_400_BAD_REQUEST)

        options = data.get('options', [])
        if len(options) < 2:
            return Response({'options': 'يجب إضافة خيارين على الأقل'}, status=status.HTTP_400_BAD_REQUEST)

        correct_letter = _map_options_to_letters(options, data.get('correct_answer'))
        if not correct_letter:
            return Response({'correct_answer': 'الإجابة الصحيحة غير موجودة في الخيارات'}, status=status.HTTP_400_BAD_REQUEST)

        question_set, _ = VocabularyQuestionSet.objects.get_or_create(
            title='Esp Vocabulary Questions',
            usage_type='ESP',
            defaults={'description': 'Auto-generated set for Esp'}
        )

        question = VocabularyQuestion.objects.create(
            question_set=question_set,
            question_text=data.get('question_text'),
            choice_a=options[0] if len(options) > 0 else '',
            choice_b=options[1] if len(options) > 1 else '',
            choice_c=options[2] if len(options) > 2 else '',
            choice_d=options[3] if len(options) > 3 else '',
            correct_answer=correct_letter,
            explanation=data.get('explanation', ''),
            points=data.get('points', 1),
            usage_type='ESP',
            esp_skill=skill,
            is_active=data.get('is_active', True),
            order=0,
            difficulty=data.get('difficulty', 'MEDIUM'),
        )

        return Response({
            'message': 'تم إنشاء السؤال بنجاح',
            'question': {'id': question.id, 'question_text': question.question_text, 'created_at': question.created_at}
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f"Error creating esp vocabulary question: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_grammar_question(request):
    """
    POST /api/esp/grammar/create/
    """
    from sabr_questions.models import GrammarQuestion, GrammarQuestionSet

    data = request.data.copy()
    required_fields = ['question_text', 'options', 'correct_answer', 'esp_skill']
    for field in required_fields:
        if field not in data:
            return Response({field: f'{field} مطلوب'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        skill = get_object_or_404(EspSkill, id=data.get('esp_skill'))
        if skill.skill_type != 'GRAMMAR':
            return Response({'error': 'هذه المهارة ليست من نوع Grammar'}, status=status.HTTP_400_BAD_REQUEST)

        options = data.get('options', [])
        if len(options) < 2:
            return Response({'options': 'يجب إضافة خيارين على الأقل'}, status=status.HTTP_400_BAD_REQUEST)

        correct_letter = _map_options_to_letters(options, data.get('correct_answer'))
        if not correct_letter:
            return Response({'correct_answer': 'الإجابة الصحيحة غير موجودة في الخيارات'}, status=status.HTTP_400_BAD_REQUEST)

        question_set, _ = GrammarQuestionSet.objects.get_or_create(
            title='Esp Grammar Questions',
            usage_type='ESP',
            defaults={'description': 'Auto-generated set for Esp'}
        )

        question = GrammarQuestion.objects.create(
            question_set=question_set,
            question_text=data.get('question_text'),
            choice_a=options[0] if len(options) > 0 else '',
            choice_b=options[1] if len(options) > 1 else '',
            choice_c=options[2] if len(options) > 2 else '',
            choice_d=options[3] if len(options) > 3 else '',
            correct_answer=correct_letter,
            explanation=data.get('explanation', ''),
            points=data.get('points', 1),
            usage_type='ESP',
            esp_skill=skill,
            is_active=data.get('is_active', True),
            order=0,
            difficulty=data.get('difficulty', 'MEDIUM'),
        )

        return Response({
            'message': 'تم إنشاء السؤال بنجاح',
            'question': {'id': question.id, 'question_text': question.question_text, 'created_at': question.created_at}
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f"Error creating esp grammar question: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_reading_passage(request):
    """
    POST /api/esp/reading/passages/create/
    """
    from sabr_questions.models import ReadingPassage

    data = request.data.copy()
    required_fields = ['title', 'passage_text', 'esp_skill']
    for field in required_fields:
        if field not in data:
            return Response({field: f'{field} مطلوب'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        skill = get_object_or_404(EspSkill, id=data.get('esp_skill'))
        if skill.skill_type != 'READING':
            return Response({'error': 'هذه المهارة ليست من نوع Reading'}, status=status.HTTP_400_BAD_REQUEST)

        passage = ReadingPassage.objects.create(
            title=data.get('title'),
            passage_text=data.get('passage_text'),
            source=data.get('source', ''),
            usage_type='ESP',
            esp_skill=skill,
            is_active=data.get('is_active', True),
            order=0,
            difficulty=data.get('difficulty', 'MEDIUM'),
        )

        return Response({
            'message': 'تم إنشاء القطعة بنجاح',
            'passage': {'id': passage.id, 'title': passage.title, 'created_at': passage.created_at}
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f"Error creating esp reading passage: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_reading_question(request, passage_id):
    """
    POST /api/esp/reading/passages/{passage_id}/questions/create/
    """
    from sabr_questions.models import ReadingPassage, ReadingQuestion

    try:
        passage = ReadingPassage.objects.get(id=passage_id, usage_type='ESP')
    except ReadingPassage.DoesNotExist:
        return Response({'error': 'القطعة غير موجودة'}, status=status.HTTP_404_NOT_FOUND)

    data = request.data.copy()
    required_fields = ['question_text', 'options', 'correct_answer']
    for field in required_fields:
        if field not in data:
            return Response({field: f'{field} مطلوب'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        options = data.get('options', [])
        if len(options) < 2:
            return Response({'options': 'يجب إضافة خيارين على الأقل'}, status=status.HTTP_400_BAD_REQUEST)

        correct_letter = _map_options_to_letters(options, data.get('correct_answer'))
        if not correct_letter:
            return Response({'correct_answer': 'الإجابة الصحيحة غير موجودة في الخيارات'}, status=status.HTTP_400_BAD_REQUEST)

        question = ReadingQuestion.objects.create(
            passage=passage,
            question_text=data.get('question_text'),
            choice_a=options[0] if len(options) > 0 else '',
            choice_b=options[1] if len(options) > 1 else '',
            choice_c=options[2] if len(options) > 2 else '',
            choice_d=options[3] if len(options) > 3 else '',
            correct_answer=correct_letter,
            explanation=data.get('explanation', ''),
            points=data.get('points', 1),
            is_active=data.get('is_active', True),
            order=0,
            difficulty=data.get('difficulty', 'MEDIUM'),
        )

        return Response({
            'message': 'تم إنشاء السؤال بنجاح',
            'question': {'id': question.id, 'question_text': question.question_text, 'created_at': question.created_at}
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f"Error creating esp reading question: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_listening_audio(request):
    """
    POST /api/esp/listening/audio/create/
    """
    from sabr_questions.models import ListeningAudio

    data = request.data.copy()
    required_fields = ['title', 'audio_file', 'esp_skill']
    for field in required_fields:
        if field not in data:
            return Response({field: f'{field} مطلوب'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        skill = get_object_or_404(EspSkill, id=data.get('esp_skill'))
        if skill.skill_type != 'LISTENING':
            return Response({'error': 'هذه المهارة ليست من نوع Listening'}, status=status.HTTP_400_BAD_REQUEST)

        audio = ListeningAudio.objects.create(
            title=data.get('title'),
            audio_file=data.get('audio_file'),
            transcript=data.get('transcript', ''),
            duration=int(data.get('duration', 0)),
            usage_type='ESP',
            esp_skill=skill,
            order=int(data.get('order', 0)),
            is_active=data.get('is_active', True),
            difficulty=data.get('difficulty', 'MEDIUM'),
        )

        return Response({
            'message': 'تم إنشاء التسجيل الصوتي بنجاح',
            'audio': {'id': audio.id, 'title': audio.title, 'created_at': audio.created_at}
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f"Error creating esp listening audio: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_listening_question(request, audio_id):
    """
    POST /api/esp/listening/audio/{audio_id}/questions/create/
    """
    from sabr_questions.models import ListeningAudio, ListeningQuestion

    try:
        audio = ListeningAudio.objects.get(id=audio_id, usage_type='ESP')
    except ListeningAudio.DoesNotExist:
        return Response({'error': 'التسجيل الصوتي غير موجود'}, status=status.HTTP_404_NOT_FOUND)

    data = request.data.copy()
    required_fields = ['question_text', 'options', 'correct_answer']
    for field in required_fields:
        if field not in data:
            return Response({field: f'{field} مطلوب'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        options = data.get('options', [])
        if len(options) < 2:
            return Response({'options': 'يجب إضافة خيارين على الأقل'}, status=status.HTTP_400_BAD_REQUEST)

        correct_letter = _map_options_to_letters(options, data.get('correct_answer'))
        if not correct_letter:
            return Response({'correct_answer': 'الإجابة الصحيحة غير موجودة في الخيارات'}, status=status.HTTP_400_BAD_REQUEST)

        question = ListeningQuestion.objects.create(
            audio=audio,
            question_text=data.get('question_text'),
            choice_a=options[0] if len(options) > 0 else '',
            choice_b=options[1] if len(options) > 1 else '',
            choice_c=options[2] if len(options) > 2 else '',
            choice_d=options[3] if len(options) > 3 else '',
            correct_answer=correct_letter,
            explanation=data.get('explanation', ''),
            points=data.get('points', 1),
            order=int(data.get('order', 0)),
            is_active=data.get('is_active', True),
        )

        return Response({
            'message': 'تم إنشاء السؤال بنجاح',
            'question': {'id': question.id, 'question_text': question.question_text, 'created_at': question.created_at}
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f"Error creating esp listening question: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_speaking_video(request):
    """
    POST /api/esp/speaking/videos/create/
    """
    from sabr_questions.models import SpeakingVideo

    data = request.data.copy()
    required_fields = ['title', 'video_file', 'esp_skill']
    for field in required_fields:
        if field not in data:
            return Response({field: f'{field} مطلوب'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        skill = get_object_or_404(EspSkill, id=data.get('esp_skill'))
        if skill.skill_type != 'SPEAKING':
            return Response({'error': 'هذه المهارة ليست من نوع Speaking'}, status=status.HTTP_400_BAD_REQUEST)

        video = SpeakingVideo.objects.create(
            title=data.get('title'),
            video_file=data.get('video_file'),
            description=data.get('description', ''),
            duration=int(data.get('duration', 0)),
            usage_type='ESP',
            esp_skill=skill,
            order=int(data.get('order', 0)),
            is_active=data.get('is_active', True),
            difficulty=data.get('difficulty', 'MEDIUM'),
        )

        return Response({
            'message': 'تم إنشاء الفيديو بنجاح',
            'video': {'id': video.id, 'title': video.title, 'created_at': video.created_at}
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f"Error creating esp speaking video: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_speaking_question(request, video_id):
    """
    POST /api/esp/speaking/videos/{video_id}/questions/create/
    """
    from sabr_questions.models import SpeakingVideo, SpeakingQuestion

    try:
        video = SpeakingVideo.objects.get(id=video_id, usage_type='ESP')
    except SpeakingVideo.DoesNotExist:
        return Response({'error': 'الفيديو غير موجود'}, status=status.HTTP_404_NOT_FOUND)

    data = request.data.copy()
    required_fields = ['question_text', 'options', 'correct_answer']
    for field in required_fields:
        if field not in data:
            return Response({field: f'{field} مطلوب'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        options = data.get('options', [])
        if len(options) < 2:
            return Response({'options': 'يجب إضافة خيارين على الأقل'}, status=status.HTTP_400_BAD_REQUEST)

        correct_letter = _map_options_to_letters(options, data.get('correct_answer'))
        if not correct_letter:
            return Response({'correct_answer': 'الإجابة الصحيحة غير موجودة في الخيارات'}, status=status.HTTP_400_BAD_REQUEST)

        question = SpeakingQuestion.objects.create(
            video=video,
            question_text=data.get('question_text'),
            choice_a=options[0] if len(options) > 0 else '',
            choice_b=options[1] if len(options) > 1 else '',
            choice_c=options[2] if len(options) > 2 else '',
            choice_d=options[3] if len(options) > 3 else '',
            correct_answer=correct_letter,
            explanation=data.get('explanation', ''),
            points=data.get('points', 1),
            order=int(data.get('order', 0)),
            is_active=data.get('is_active', True),
        )

        return Response({
            'message': 'تم إنشاء السؤال بنجاح',
            'question': {'id': question.id, 'question_text': question.question_text, 'created_at': question.created_at}
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f"Error creating esp speaking question: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_writing_question(request):
    """
    POST /api/esp/writing/questions/create/
    """
    from sabr_questions.models import WritingQuestion

    data = request.data.copy()
    required_fields = ['title', 'question_text', 'min_words', 'max_words', 'esp_skill']
    for field in required_fields:
        if field not in data:
            return Response({field: f'{field} مطلوب'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        skill = get_object_or_404(EspSkill, id=data.get('esp_skill'))
        if skill.skill_type != 'WRITING':
            return Response({'error': 'هذه المهارة ليست من نوع Writing'}, status=status.HTTP_400_BAD_REQUEST)

        min_words = int(data.get('min_words'))
        max_words = int(data.get('max_words'))
        if max_words <= min_words:
            return Response({'error': 'الحد الأقصى للكلمات يجب أن يكون أكبر من الحد الأدنى'}, status=status.HTTP_400_BAD_REQUEST)

        question = WritingQuestion.objects.create(
            title=data.get('title'),
            question_text=data.get('question_text'),
            min_words=min_words,
            max_words=max_words,
            sample_answer=data.get('sample_answer', ''),
            rubric=data.get('rubric', ''),
            usage_type='ESP',
            esp_skill=skill,
            points=data.get('points', 10),
            is_active=data.get('is_active', True),
            order=0,
            difficulty=data.get('difficulty', 'MEDIUM'),
        )

        return Response({
            'message': 'تم إنشاء السؤال بنجاح',
            'question': {'id': question.id, 'title': question.title, 'created_at': question.created_at}
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f"Error creating esp writing question: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


# ============================================
# 4. QUESTIONS DISPLAY (للطالب)
# ============================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_skill_questions(request, skill_id):
    """
    GET /api/esp/skills/{skill_id}/questions/?page=1&page_size=20
    """
    from sabr_questions.models import (
        VocabularyQuestion, GrammarQuestion,
        ReadingPassage, ListeningAudio, WritingQuestion,
    )
    from sabr_questions.models import SpeakingVideo

    skill = get_object_or_404(EspSkill, id=skill_id)
    page = int(request.query_params.get('page', 1))
    page_size = int(request.query_params.get('page_size', 20))
    student = request.user

    # جيب كل محاولات الطالب دفعة واحدة
    attempts_qs = StudentEspQuestionAttempt.objects.filter(student=student, skill=skill)
    attempts_map = {(a.question_type, a.question_id): a for a in attempts_qs}

    # جيب التوتال سكور
    try:
        progress = StudentEspProgress.objects.get(student=student, skill=skill)
        skill_total_score = progress.total_score
    except StudentEspProgress.DoesNotExist:
        skill_total_score = 0

    def get_attempt_data(q_type, q_id):
        attempt = attempts_map.get((q_type, q_id))
        if attempt:
            return {
                'is_solved': attempt.is_solved,
                'points_earned': attempt.points_earned,
                'attempts_count': attempt.attempts_count,
                'used_show_answer': attempt.used_show_answer,
            }
        return {
            'is_solved': False,
            'points_earned': 0,
            'attempts_count': 0,
            'used_show_answer': False,
        }

    questions_data = []

    if skill.skill_type == 'VOCABULARY':
        qs = VocabularyQuestion.objects.filter(esp_skill=skill, usage_type='ESP', is_active=True)
        questions = _get_ordered_questions(qs, skill.question_order_type)
        paginator = Paginator(questions, page_size)
        page_obj = paginator.get_page(page)
        for q in page_obj:
            questions_data.append({
                'id': q.id, 'type': 'VOCABULARY',
                'question_text': q.question_text,
                'question_image': q.question_image.url if q.question_image else None,
                'choice_a': q.choice_a, 'choice_b': q.choice_b,
                'choice_c': q.choice_c, 'choice_d': q.choice_d,
                'correct_answer': q.correct_answer,
                'explanation': q.explanation, 'points': q.points,
                'difficulty': q.difficulty,
                **get_attempt_data('VOCABULARY', q.id),
            })

    elif skill.skill_type == 'GRAMMAR':
        qs = GrammarQuestion.objects.filter(esp_skill=skill, usage_type='ESP', is_active=True)
        questions = _get_ordered_questions(qs, skill.question_order_type)
        paginator = Paginator(questions, page_size)
        page_obj = paginator.get_page(page)
        for q in page_obj:
            questions_data.append({
                'id': q.id, 'type': 'GRAMMAR',
                'question_text': q.question_text,
                'question_image': q.question_image.url if q.question_image else None,
                'choice_a': q.choice_a, 'choice_b': q.choice_b,
                'choice_c': q.choice_c, 'choice_d': q.choice_d,
                'correct_answer': q.correct_answer,
                'explanation': q.explanation, 'points': q.points,
                'difficulty': q.difficulty,
                **get_attempt_data('GRAMMAR', q.id),
            })

    elif skill.skill_type == 'READING':
        qs = ReadingPassage.objects.filter(esp_skill=skill, usage_type='ESP', is_active=True)
        passages = _get_ordered_questions(qs, skill.question_order_type)
        paginator = Paginator(passages, page_size)
        page_obj = paginator.get_page(page)
        for passage in page_obj:
            passage_questions = []
            for q in passage.questions.filter(is_active=True).order_by('order', 'id'):
                passage_questions.append({
                    'id': q.id, 'question_text': q.question_text,
                    'choice_a': q.choice_a, 'choice_b': q.choice_b,
                    'choice_c': q.choice_c, 'choice_d': q.choice_d,
                    'correct_answer': q.correct_answer,
                    'explanation': q.explanation, 'points': q.points,
                    **get_attempt_data('READING', q.id),
                })
            questions_data.append({
                'id': passage.id, 'type': 'READING',
                'title': passage.title,
                'passage_text': passage.passage_text,
                'passage_image': passage.passage_image.url if passage.passage_image else None,
                'source': passage.source,
                'questions': passage_questions,
                'difficulty': passage.difficulty,
            })

    elif skill.skill_type == 'LISTENING':
        qs = ListeningAudio.objects.filter(esp_skill=skill, usage_type='ESP', is_active=True)
        audios = _get_ordered_questions(qs, skill.question_order_type)
        paginator = Paginator(audios, page_size)
        page_obj = paginator.get_page(page)
        for audio in page_obj:
            audio_questions = []
            for q in audio.questions.filter(is_active=True).order_by('order', 'id'):
                audio_questions.append({
                    'id': q.id, 'question_text': q.question_text,
                    'choice_a': q.choice_a, 'choice_b': q.choice_b,
                    'choice_c': q.choice_c, 'choice_d': q.choice_d,
                    'correct_answer': q.correct_answer,
                    'explanation': q.explanation, 'points': q.points,
                    **get_attempt_data('LISTENING', q.id),
                })
            questions_data.append({
                'id': audio.id, 'type': 'LISTENING',
                'title': audio.title,
                'audio_file': _get_cloudinary_url(audio.audio_file, resource_type='video'),
                'transcript': audio.transcript,
                'duration': audio.duration,
                'questions': audio_questions,
                'difficulty': audio.difficulty,
            })

    elif skill.skill_type == 'SPEAKING':
        qs = SpeakingVideo.objects.filter(esp_skill=skill, usage_type='ESP', is_active=True)
        videos = _get_ordered_questions(qs, skill.question_order_type)
        paginator = Paginator(videos, page_size)
        page_obj = paginator.get_page(page)
        for video in page_obj:
            video_questions = []
            for q in video.questions.filter(is_active=True).order_by('order', 'id'):
                video_questions.append({
                    'id': q.id, 'question_text': q.question_text,
                    'choice_a': q.choice_a, 'choice_b': q.choice_b,
                    'choice_c': q.choice_c, 'choice_d': q.choice_d,
                    'correct_answer': q.correct_answer,
                    'explanation': q.explanation, 'points': q.points,
                    **get_attempt_data('SPEAKING', q.id),
                })
            questions_data.append({
                'id': video.id, 'type': 'SPEAKING',
                'title': video.title,
                'video_file': _get_cloudinary_url(video.video_file, resource_type='video'),
                'thumbnail': _get_cloudinary_url(video.thumbnail, resource_type='image'),
                'description': video.description,
                'duration': video.duration,
                'questions': video_questions,
                'difficulty': video.difficulty,
            })

    elif skill.skill_type == 'WRITING':
        qs = WritingQuestion.objects.filter(esp_skill=skill, usage_type='ESP', is_active=True)
        questions = _get_ordered_questions(qs, skill.question_order_type)
        paginator = Paginator(questions, page_size)
        page_obj = paginator.get_page(page)
        for q in page_obj:
            questions_data.append({
                'id': q.id, 'type': 'WRITING',
                'title': q.title, 'question_text': q.question_text,
                'question_image': q.question_image.url if q.question_image else None,
                'min_words': q.min_words, 'max_words': q.max_words,
                'sample_answer': q.sample_answer, 'rubric': q.rubric,
                'points': q.points, 'difficulty': q.difficulty,
                **get_attempt_data('WRITING', q.id),
            })

    paginator = Paginator(questions_data, page_size)

    return Response({
        'skill': {
            'id': skill.id,
            'title': skill.title,
            'skill_type': skill.skill_type,
            'category': {'id': skill.category.id, 'name': skill.category.name},
        },
        'skill_total_score': skill_total_score,
        'pagination': {
            'page': page,
            'page_size': page_size,
            'total_pages': paginator.num_pages,
            'total_items': paginator.count,
        },
        'questions': questions_data
    }, status=status.HTTP_200_OK)


# ============================================
# 5. نظام المحاولات
# ============================================

def _get_correct_answer_data(question_type, question_id):
    from sabr_questions.models import (
        VocabularyQuestion, GrammarQuestion,
        ReadingQuestion, ListeningQuestion, WritingQuestion, SpeakingQuestion
    )

    if question_type == 'WRITING':
        q = get_object_or_404(WritingQuestion, id=question_id, usage_type='ESP')
        return {'sample_answer': q.sample_answer, 'rubric': q.rubric}

    model_map = {
        'VOCABULARY': VocabularyQuestion,
        'GRAMMAR': GrammarQuestion,
        'READING': ReadingQuestion,
        'LISTENING': ListeningQuestion,
        'SPEAKING': SpeakingQuestion,
    }
    model = model_map.get(question_type)
    if not model:
        return {}

    q = get_object_or_404(model, id=question_id)
    choice_map = {'A': q.choice_a, 'B': q.choice_b, 'C': q.choice_c, 'D': q.choice_d}
    return {
        'correct_answer_letter': q.correct_answer,
        'correct_answer_text': choice_map.get(q.correct_answer, ''),
        'explanation': q.explanation,
    }


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_mcq_answer(request, skill_id, question_type, question_id):
    """
    POST /api/esp/skills/{skill_id}/questions/{question_type}/{question_id}/submit/
    Body: { "selected_answer": "A" }
    """
    from sabr_questions.models import (
        VocabularyQuestion, GrammarQuestion,
        ReadingQuestion, ListeningQuestion, SpeakingQuestion
    )

    skill = get_object_or_404(EspSkill, id=skill_id)
    student = request.user

    valid_types = ['VOCABULARY', 'GRAMMAR', 'READING', 'LISTENING', 'SPEAKING']
    if question_type not in valid_types:
        return Response(
            {'error': f'استخدم هذا الـ endpoint للأنواع: {", ".join(valid_types)} فقط'},
            status=status.HTTP_400_BAD_REQUEST
        )

    selected_answer = request.data.get('selected_answer', '').strip().upper()
    if not selected_answer:
        return Response({'error': 'selected_answer مطلوب (A/B/C/D)'}, status=status.HTTP_400_BAD_REQUEST)

    model_map = {
        'VOCABULARY': VocabularyQuestion,
        'GRAMMAR': GrammarQuestion,
        'READING': ReadingQuestion,
        'LISTENING': ListeningQuestion,
        'SPEAKING': SpeakingQuestion,
    }
    question = get_object_or_404(model_map[question_type], id=question_id)
    correct_answer = question.correct_answer

    try:
        with transaction.atomic():
            attempt, created = StudentEspQuestionAttempt.objects.get_or_create(
                student=student,
                question_type=question_type,
                question_id=question_id,
                defaults={'skill': skill}
            )

            if attempt.is_solved:
                progress, _ = StudentEspProgress.objects.get_or_create(student=student, skill=skill)
                return Response({
                    'message': 'هذا السؤال تم حله من قبل',
                    'is_correct': selected_answer == correct_answer,
                    'attempts_count': attempt.attempts_count,
                    'total_points_this_question': attempt.points_earned,
                    'total_score': progress.total_score,
                    'progress_percentage': progress.calculate_progress_percentage(),
                    'already_solved': True,
                }, status=status.HTTP_200_OK)

            attempt.attempts_count += 1
            attempt.save()

            is_correct = (selected_answer == correct_answer)
            progress, _ = StudentEspProgress.objects.get_or_create(student=student, skill=skill)

            if is_correct:
                points = ATTEMPT_POINTS.get(attempt.attempts_count, MAX_ATTEMPTS_POINTS)
                attempt.is_solved = True
                attempt.points_earned = points
                attempt.solved_at = timezone.now()
                attempt.save()
                progress.add_score(points)

                return Response({
                    'is_correct': True,
                    'attempts_count': attempt.attempts_count,
                    'points_earned': points,
                    'total_points_this_question': points,
                    'total_score': progress.total_score,
                    'progress_percentage': progress.calculate_progress_percentage(),
                    'message': f'إجابة صحيحة! حصلت على {points} نقطة',
                }, status=status.HTTP_200_OK)

            else:
                if attempt.attempts_count >= 4:
                    attempt.is_solved = True
                    attempt.points_earned = 0
                    attempt.solved_at = timezone.now()
                    attempt.save()
                    progress.viewed_questions_count += 1
                    progress.save()

                    choice_map = {
                        'A': question.choice_a, 'B': question.choice_b,
                        'C': question.choice_c, 'D': question.choice_d,
                    }
                    return Response({
                        'is_correct': False,
                        'attempts_count': attempt.attempts_count,
                        'points_earned': 0,
                        'total_points_this_question': 0,
                        'total_score': progress.total_score,
                        'progress_percentage': progress.calculate_progress_percentage(),
                        'message': 'انتهت محاولاتك. الإجابة الصحيحة هي:',
                        'correct_answer_letter': correct_answer,
                        'correct_answer_text': {'A': question.choice_a, 'B': question.choice_b, 'C': question.choice_c, 'D': question.choice_d}.get(correct_answer, ''),
                        'explanation': question.explanation,
                        'max_attempts_reached': True,
                    }, status=status.HTTP_200_OK)

                remaining = 4 - attempt.attempts_count
                return Response({
                    'is_correct': False,
                    'attempts_count': attempt.attempts_count,
                    'points_earned': 0,
                    'total_points_this_question': 0,
                    'total_score': progress.total_score,
                    'progress_percentage': progress.calculate_progress_percentage(),
                    'message': f'إجابة خاطئة. لديك {remaining} محاولة متبقية',
                    'remaining_attempts': remaining,
                    'next_attempt_points': ATTEMPT_POINTS.get(attempt.attempts_count + 1, MAX_ATTEMPTS_POINTS),
                }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error in esp submit_mcq_answer: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def use_show_answer(request, skill_id, question_type, question_id):
    """
    POST /api/esp/skills/{skill_id}/questions/{question_type}/{question_id}/show-answer/
    """
    skill = get_object_or_404(EspSkill, id=skill_id)
    student = request.user

    valid_types = ['VOCABULARY', 'GRAMMAR', 'READING', 'LISTENING', 'WRITING', 'SPEAKING']
    if question_type not in valid_types:
        return Response({'error': 'نوع السؤال غير صحيح'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        with transaction.atomic():
            attempt, created = StudentEspQuestionAttempt.objects.get_or_create(
                student=student,
                question_type=question_type,
                question_id=question_id,
                defaults={'skill': skill}
            )
            progress, _ = StudentEspProgress.objects.get_or_create(student=student, skill=skill)
            answer_data = _get_correct_answer_data(question_type, question_id)

            if attempt.is_solved:
                return Response({
                    'message': 'تم حل هذا السؤال من قبل',
                    'points_earned': 0,
                    'already_solved': True,
                    'total_score': progress.total_score,
                    'progress_percentage': progress.calculate_progress_percentage(),
                    **answer_data,
                }, status=status.HTTP_200_OK)

            attempt.is_solved = True
            attempt.used_show_answer = True
            attempt.points_earned = SHOW_ANSWER_POINTS
            attempt.solved_at = timezone.now()
            attempt.save()
            progress.add_score(SHOW_ANSWER_POINTS)

            return Response({
                'message': f'حصلت على {SHOW_ANSWER_POINTS} نقاط',
                'points_earned': SHOW_ANSWER_POINTS,
                'already_solved': False,
                'total_score': progress.total_score,
                'progress_percentage': progress.calculate_progress_percentage(),
                **answer_data,
            }, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f"Error in esp use_show_answer: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_question_attempt_status(request, skill_id, question_type, question_id):
    """
    GET /api/esp/skills/{skill_id}/questions/{question_type}/{question_id}/attempt-status/
    """
    get_object_or_404(EspSkill, id=skill_id)
    student = request.user

    try:
        attempt = StudentEspQuestionAttempt.objects.get(
            student=student,
            question_type=question_type,
            question_id=question_id,
        )
        remaining = max(0, 4 - attempt.attempts_count) if not attempt.is_solved else 0
        next_points = ATTEMPT_POINTS.get(attempt.attempts_count + 1, MAX_ATTEMPTS_POINTS) if not attempt.is_solved else 0

        return Response({
            'has_attempted': True,
            'attempts_count': attempt.attempts_count,
            'is_solved': attempt.is_solved,
            'points_earned': attempt.points_earned,
            'used_show_answer': attempt.used_show_answer,
            'remaining_attempts': remaining,
            'next_attempt_points': next_points,
        }, status=status.HTTP_200_OK)

    except StudentEspQuestionAttempt.DoesNotExist:
        return Response({
            'has_attempted': False,
            'attempts_count': 0,
            'is_solved': False,
            'points_earned': 0,
            'used_show_answer': False,
            'remaining_attempts': 4,
            'next_attempt_points': 20,
        }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_writing_answer(request, question_id):
    """
    POST /api/esp/writing/questions/{question_id}/submit/
    Body: { "student_answer": "..." }
    """
    from sabr_questions.models import WritingQuestion
    from placement_test.services.ai_grading import AIGradingService

    question = get_object_or_404(WritingQuestion, id=question_id, usage_type='ESP')
    student_answer = request.data.get('student_answer', '').strip()

    if not student_answer:
        return Response({'error': 'الإجابة مطلوبة'}, status=status.HTTP_400_BAD_REQUEST)

    word_count = len(student_answer.split())
    if word_count < question.min_words:
        return Response({
            'error': f'الإجابة قصيرة جداً، الحد الأدنى {question.min_words} كلمة',
            'word_count': word_count,
        }, status=status.HTTP_400_BAD_REQUEST)
    if word_count > question.max_words:
        return Response({
            'error': f'الإجابة طويلة جداً، الحد الأقصى {question.max_words} كلمة',
            'word_count': word_count,
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        grading_service = AIGradingService()
        grading_result = grading_service.grade_writing_question(
            question_text=question.question_text,
            student_answer=student_answer,
            sample_answer=question.sample_answer or '',
            rubric=question.rubric or '',
            max_points=10,
            min_words=question.min_words,
            max_words=question.max_words,
            pass_threshold=60
        )

        return Response({
            'score': grading_result.get('raw_score', 0),
            'percentage': grading_result.get('percentage', 0),
            'feedback': grading_result.get('feedback', ''),
            'strengths': grading_result.get('strengths', []),
            'improvements': grading_result.get('improvements', []),
            'word_count': word_count,
            'can_mark_as_viewed': True,
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error getting AI feedback for Esp writing: {str(e)}")
        return Response(
            {'error': 'حدث خطأ أثناء تقييم الإجابة، حاول مرة أخرى'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ============================================
# 6. STUDENT PROGRESS
# ============================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_progress(request):
    """
    GET /api/esp/my-progress/
    """
    student = request.user
    progress_records = StudentEspProgress.objects.filter(
        student=student
    ).select_related('skill', 'skill__category').order_by('skill__category__order', 'skill__order')

    total_score = sum(p.total_score for p in progress_records)
    total_viewed = sum(p.viewed_questions_count for p in progress_records)

    all_skills = EspSkill.objects.filter()
    total_available = sum(skill.get_total_questions_count() for skill in all_skills)

    overall_percentage = 0
    if total_available > 0:
        overall_percentage = round((total_viewed / total_available) * 100, 2)

    serializer = StudentEspProgressSerializer(progress_records, many=True)

    return Response({
        'summary': {
            'total_score': total_score,
            'total_viewed_questions': total_viewed,
            'total_available_questions': total_available,
            'overall_progress_percentage': overall_percentage,
        },
        'skills_progress': serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_progress_by_category(request, category_id):
    """
    GET /api/esp/categories/{category_id}/my-progress/
    """
    category = get_object_or_404(EspCategory, id=category_id)
    student = request.user

    skills = EspSkill.objects.filter(category=category)
    total_viewed = 0
    total_score = 0
    total_questions = 0
    skills_progress = []

    for skill in skills:
        total_questions += skill.get_total_questions_count()
        try:
            progress = StudentEspProgress.objects.get(student=student, skill=skill)
            total_viewed += progress.viewed_questions_count
            total_score += progress.total_score
            skills_progress.append(StudentEspProgressSerializer(progress).data)
        except StudentEspProgress.DoesNotExist:
            skills_progress.append({
                'skill': skill.id,
                'skill_title': skill.title,
                'skill_type': skill.skill_type,
                'viewed_questions_count': 0,
                'total_questions': skill.get_total_questions_count(),
                'progress_percentage': 0,
                'total_score': 0,
            })

    overall_percentage = 0
    if total_questions > 0:
        overall_percentage = round((total_viewed / total_questions) * 100, 2)

    return Response({
        'category': {'id': category.id, 'name': category.name},
        'summary': {
            'total_score': total_score,
            'total_viewed_questions': total_viewed,
            'total_questions': total_questions,
            'overall_progress_percentage': overall_percentage,
        },
        'skills_progress': skills_progress,
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def skill_progress(request, skill_id):
    """
    GET /api/esp/skills/{skill_id}/my-progress/
    """
    skill = get_object_or_404(EspSkill, id=skill_id)
    student = request.user

    try:
        progress = StudentEspProgress.objects.get(student=student, skill=skill)
        serializer = StudentEspProgressSerializer(progress)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except StudentEspProgress.DoesNotExist:
        return Response({
            'skill': {'id': skill.id, 'title': skill.title, 'skill_type': skill.skill_type},
            'viewed_questions_count': 0,
            'total_questions': skill.get_total_questions_count(),
            'progress_percentage': 0,
            'total_score': 0,
        }, status=status.HTTP_200_OK)


# ============================================
# 7. UPDATE & DELETE QUESTIONS
# ============================================

@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_vocabulary_question(request, question_id):
    from sabr_questions.models import VocabularyQuestion
    question = get_object_or_404(VocabularyQuestion, id=question_id, usage_type='ESP')
    data = request.data.copy()
    try:
        if 'options' in data and 'correct_answer' in data:
            options = data.get('options', [])
            correct_letter = _map_options_to_letters(options, data.get('correct_answer'))
            if not correct_letter:
                return Response({'correct_answer': 'الإجابة الصحيحة غير موجودة في الخيارات'}, status=status.HTTP_400_BAD_REQUEST)
            question.choice_a = options[0] if len(options) > 0 else question.choice_a
            question.choice_b = options[1] if len(options) > 1 else question.choice_b
            question.choice_c = options[2] if len(options) > 2 else question.choice_c
            question.choice_d = options[3] if len(options) > 3 else question.choice_d
            question.correct_answer = correct_letter
        if 'question_text' in data: question.question_text = data['question_text']
        if 'explanation' in data: question.explanation = data['explanation']
        if 'points' in data: question.points = data['points']
        if 'is_active' in data: question.is_active = data['is_active']
        if 'difficulty' in data: question.difficulty = data['difficulty']
        question.save()
        return Response({'message': 'تم تحديث السؤال بنجاح', 'question': {'id': question.id}}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_vocabulary_question(request, question_id):
    from sabr_questions.models import VocabularyQuestion
    question = get_object_or_404(VocabularyQuestion, id=question_id, usage_type='ESP')
    question.delete()
    return Response({'message': 'تم حذف السؤال بنجاح'}, status=status.HTTP_200_OK)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_grammar_question(request, question_id):
    from sabr_questions.models import GrammarQuestion
    question = get_object_or_404(GrammarQuestion, id=question_id, usage_type='ESP')
    data = request.data.copy()
    try:
        if 'options' in data and 'correct_answer' in data:
            options = data.get('options', [])
            correct_letter = _map_options_to_letters(options, data.get('correct_answer'))
            if not correct_letter:
                return Response({'correct_answer': 'الإجابة الصحيحة غير موجودة في الخيارات'}, status=status.HTTP_400_BAD_REQUEST)
            question.choice_a = options[0] if len(options) > 0 else question.choice_a
            question.choice_b = options[1] if len(options) > 1 else question.choice_b
            question.choice_c = options[2] if len(options) > 2 else question.choice_c
            question.choice_d = options[3] if len(options) > 3 else question.choice_d
            question.correct_answer = correct_letter
        if 'question_text' in data: question.question_text = data['question_text']
        if 'explanation' in data: question.explanation = data['explanation']
        if 'points' in data: question.points = data['points']
        if 'is_active' in data: question.is_active = data['is_active']
        if 'difficulty' in data: question.difficulty = data['difficulty']
        question.save()
        return Response({'message': 'تم تحديث السؤال بنجاح', 'question': {'id': question.id}}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_grammar_question(request, question_id):
    from sabr_questions.models import GrammarQuestion
    question = get_object_or_404(GrammarQuestion, id=question_id, usage_type='ESP')
    question.delete()
    return Response({'message': 'تم حذف السؤال بنجاح'}, status=status.HTTP_200_OK)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_reading_passage(request, passage_id):
    from sabr_questions.models import ReadingPassage
    passage = get_object_or_404(ReadingPassage, id=passage_id, usage_type='ESP')
    data = request.data.copy()
    try:
        if 'title' in data: passage.title = data['title']
        if 'passage_text' in data: passage.passage_text = data['passage_text']
        if 'source' in data: passage.source = data['source']
        if 'is_active' in data: passage.is_active = data['is_active']
        if 'difficulty' in data: passage.difficulty = data['difficulty']
        passage.save()
        return Response({'message': 'تم تحديث القطعة بنجاح', 'passage': {'id': passage.id}}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_reading_passage(request, passage_id):
    from sabr_questions.models import ReadingPassage
    passage = get_object_or_404(ReadingPassage, id=passage_id, usage_type='ESP')
    passage.delete()
    return Response({'message': 'تم حذف القطعة وأسئلتها بنجاح'}, status=status.HTTP_200_OK)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_reading_question(request, question_id):
    from sabr_questions.models import ReadingQuestion
    question = get_object_or_404(ReadingQuestion, id=question_id)
    data = request.data.copy()
    try:
        if 'options' in data and 'correct_answer' in data:
            options = data.get('options', [])
            correct_letter = _map_options_to_letters(options, data.get('correct_answer'))
            if not correct_letter:
                return Response({'correct_answer': 'الإجابة الصحيحة غير موجودة في الخيارات'}, status=status.HTTP_400_BAD_REQUEST)
            question.choice_a = options[0] if len(options) > 0 else question.choice_a
            question.choice_b = options[1] if len(options) > 1 else question.choice_b
            question.choice_c = options[2] if len(options) > 2 else question.choice_c
            question.choice_d = options[3] if len(options) > 3 else question.choice_d
            question.correct_answer = correct_letter
        if 'question_text' in data: question.question_text = data['question_text']
        if 'explanation' in data: question.explanation = data['explanation']
        if 'points' in data: question.points = data['points']
        if 'is_active' in data: question.is_active = data['is_active']
        question.save()
        return Response({'message': 'تم تحديث السؤال بنجاح'}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_reading_question(request, question_id):
    from sabr_questions.models import ReadingQuestion
    question = get_object_or_404(ReadingQuestion, id=question_id)
    question.delete()
    return Response({'message': 'تم حذف السؤال بنجاح'}, status=status.HTTP_200_OK)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_listening_audio(request, audio_id):
    from sabr_questions.models import ListeningAudio
    audio = get_object_or_404(ListeningAudio, id=audio_id, usage_type='ESP')
    data = request.data.copy()
    try:
        if 'title' in data: audio.title = data['title']
        if 'audio_file' in data: audio.audio_file = data['audio_file']
        if 'transcript' in data: audio.transcript = data['transcript']
        if 'duration' in data: audio.duration = int(data['duration'])
        if 'is_active' in data: audio.is_active = data['is_active']
        if 'difficulty' in data: audio.difficulty = data['difficulty']
        audio.save()
        return Response({'message': 'تم تحديث التسجيل الصوتي بنجاح'}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_listening_audio(request, audio_id):
    from sabr_questions.models import ListeningAudio
    audio = get_object_or_404(ListeningAudio, id=audio_id, usage_type='ESP')
    audio.delete()
    return Response({'message': 'تم حذف التسجيل الصوتي وأسئلته بنجاح'}, status=status.HTTP_200_OK)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_listening_question(request, question_id):
    from sabr_questions.models import ListeningQuestion
    question = get_object_or_404(ListeningQuestion, id=question_id)
    data = request.data.copy()
    try:
        if 'options' in data and 'correct_answer' in data:
            options = data.get('options', [])
            correct_letter = _map_options_to_letters(options, data.get('correct_answer'))
            if not correct_letter:
                return Response({'correct_answer': 'الإجابة الصحيحة غير موجودة في الخيارات'}, status=status.HTTP_400_BAD_REQUEST)
            question.choice_a = options[0] if len(options) > 0 else question.choice_a
            question.choice_b = options[1] if len(options) > 1 else question.choice_b
            question.choice_c = options[2] if len(options) > 2 else question.choice_c
            question.choice_d = options[3] if len(options) > 3 else question.choice_d
            question.correct_answer = correct_letter
        if 'question_text' in data: question.question_text = data['question_text']
        if 'explanation' in data: question.explanation = data['explanation']
        if 'points' in data: question.points = data['points']
        if 'is_active' in data: question.is_active = data['is_active']
        question.save()
        return Response({'message': 'تم تحديث السؤال بنجاح'}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_listening_question(request, question_id):
    from sabr_questions.models import ListeningQuestion
    question = get_object_or_404(ListeningQuestion, id=question_id)
    question.delete()
    return Response({'message': 'تم حذف السؤال بنجاح'}, status=status.HTTP_200_OK)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_speaking_video(request, video_id):
    from sabr_questions.models import SpeakingVideo
    video = get_object_or_404(SpeakingVideo, id=video_id, usage_type='ESP')
    data = request.data.copy()
    try:
        if 'title' in data: video.title = data['title']
        if 'video_file' in data: video.video_file = data['video_file']
        if 'description' in data: video.description = data['description']
        if 'duration' in data: video.duration = int(data['duration'])
        if 'is_active' in data: video.is_active = data['is_active']
        if 'difficulty' in data: video.difficulty = data['difficulty']
        video.save()
        return Response({'message': 'تم تحديث الفيديو بنجاح'}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_speaking_video(request, video_id):
    from sabr_questions.models import SpeakingVideo
    video = get_object_or_404(SpeakingVideo, id=video_id, usage_type='ESP')
    video.delete()
    return Response({'message': 'تم حذف الفيديو وأسئلته بنجاح'}, status=status.HTTP_200_OK)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_speaking_question(request, question_id):
    from sabr_questions.models import SpeakingQuestion
    question = get_object_or_404(SpeakingQuestion, id=question_id)
    data = request.data.copy()
    try:
        if 'options' in data and 'correct_answer' in data:
            options = data.get('options', [])
            correct_letter = _map_options_to_letters(options, data.get('correct_answer'))
            if not correct_letter:
                return Response({'correct_answer': 'الإجابة الصحيحة غير موجودة في الخيارات'}, status=status.HTTP_400_BAD_REQUEST)
            question.choice_a = options[0] if len(options) > 0 else question.choice_a
            question.choice_b = options[1] if len(options) > 1 else question.choice_b
            question.choice_c = options[2] if len(options) > 2 else question.choice_c
            question.choice_d = options[3] if len(options) > 3 else question.choice_d
            question.correct_answer = correct_letter
        if 'question_text' in data: question.question_text = data['question_text']
        if 'explanation' in data: question.explanation = data['explanation']
        if 'points' in data: question.points = data['points']
        if 'is_active' in data: question.is_active = data['is_active']
        question.save()
        return Response({'message': 'تم تحديث السؤال بنجاح'}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_speaking_question(request, question_id):
    from sabr_questions.models import SpeakingQuestion
    question = get_object_or_404(SpeakingQuestion, id=question_id)
    question.delete()
    return Response({'message': 'تم حذف السؤال بنجاح'}, status=status.HTTP_200_OK)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_writing_question(request, question_id):
    from sabr_questions.models import WritingQuestion
    question = get_object_or_404(WritingQuestion, id=question_id, usage_type='ESP')
    data = request.data.copy()
    try:
        if 'title' in data: question.title = data['title']
        if 'question_text' in data: question.question_text = data['question_text']
        if 'min_words' in data: question.min_words = int(data['min_words'])
        if 'max_words' in data: question.max_words = int(data['max_words'])
        if 'sample_answer' in data: question.sample_answer = data['sample_answer']
        if 'rubric' in data: question.rubric = data['rubric']
        if 'is_active' in data: question.is_active = data['is_active']
        if 'difficulty' in data: question.difficulty = data['difficulty']
        if question.max_words <= question.min_words:
            return Response({'error': 'الحد الأقصى للكلمات يجب أن يكون أكبر من الحد الأدنى'}, status=status.HTTP_400_BAD_REQUEST)
        question.save()
        return Response({'message': 'تم تحديث السؤال بنجاح'}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_writing_question(request, question_id):
    from sabr_questions.models import WritingQuestion
    question = get_object_or_404(WritingQuestion, id=question_id, usage_type='ESP')
    question.delete()
    return Response({'message': 'تم حذف السؤال بنجاح'}, status=status.HTTP_200_OK)