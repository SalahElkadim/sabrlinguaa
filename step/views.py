from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.paginator import Paginator

from .models import (
    STEPSkill,
    StudentSTEPProgress,
    StudentSTEPQuestionView,
)

from .serializers import (
    STEPSkillListSerializer,
    STEPSkillDetailSerializer,
    StudentSTEPProgressSerializer,
    StudentSTEPQuestionViewSerializer,
    VocabularyQuestionSTEPSerializer,
    GrammarQuestionSTEPSerializer,
    ReadingPassageSTEPSerializer,
    ListeningAudioSTEPSerializer,
    WritingQuestionSTEPSerializer,
)

import logging
logger = logging.getLogger(__name__)


# ============================================
# 1. STEP SKILLS CRUD
# ============================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_skills(request):
    """
    GET /api/step/skills/
    """
    skills = STEPSkill.objects.filter(is_active=True).order_by('order')
    serializer = STEPSkillListSerializer(skills, many=True)
    return Response({
        'total_skills': skills.count(),
        'skills': serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_skill(request, skill_id):
    """
    GET /api/step/skills/{skill_id}/
    """
    skill = get_object_or_404(STEPSkill, id=skill_id)
    serializer = STEPSkillDetailSerializer(skill)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_skill(request):
    """
    POST /api/step/skills/create/
    """
    serializer = STEPSkillDetailSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    skill = serializer.save()
    return Response({
        'message': 'تم إنشاء المهارة بنجاح',
        'skill': STEPSkillDetailSerializer(skill).data
    }, status=status.HTTP_201_CREATED)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_skill(request, skill_id):
    """
    PUT/PATCH /api/step/skills/{skill_id}/update/
    """
    skill = get_object_or_404(STEPSkill, id=skill_id)
    partial = request.method == 'PATCH'
    serializer = STEPSkillDetailSerializer(skill, data=request.data, partial=partial)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    skill = serializer.save()
    return Response({
        'message': 'تم تحديث المهارة بنجاح',
        'skill': STEPSkillDetailSerializer(skill).data
    }, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_skill(request, skill_id):
    """
    DELETE /api/step/skills/{skill_id}/delete/
    """
    skill = get_object_or_404(STEPSkill, id=skill_id)
    skill_type = skill.skill_type
    title = skill.title
    skill.delete()
    return Response({
        'message': 'تم حذف المهارة بنجاح',
        'skill_id': skill_id,
        'skill_type': skill_type,
        'title': title
    }, status=status.HTTP_200_OK)


# ============================================
# 2. QUESTIONS MANAGEMENT (CREATE)
# ============================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_vocabulary_question(request):
    """
    POST /api/step/vocabulary/create/
    """
    from sabr_questions.models import VocabularyQuestion, VocabularyQuestionSet

    data = request.data.copy()
    required_fields = ['question_text', 'options', 'correct_answer', 'step_skill']
    for field in required_fields:
        if field not in data:
            return Response({field: f'{field} مطلوب'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        skill = get_object_or_404(STEPSkill, id=data.get('step_skill'))
        if skill.skill_type != 'VOCABULARY':
            return Response({'error': 'هذه المهارة ليست من نوع Vocabulary'}, status=status.HTTP_400_BAD_REQUEST)

        options = data.get('options', [])
        if len(options) < 2:
            return Response({'options': 'يجب إضافة خيارين على الأقل'}, status=status.HTTP_400_BAD_REQUEST)

        question_set, _ = VocabularyQuestionSet.objects.get_or_create(
            title='STEP Vocabulary Questions',
            usage_type='STEP',
            defaults={'description': 'Auto-generated set for STEP'}
        )

        correct_answer = data.get('correct_answer')
        correct_letter = None
        for idx, option in enumerate(options):
            if option == correct_answer:
                correct_letter = chr(65 + idx)
                break

        if not correct_letter:
            return Response({'correct_answer': 'الإجابة الصحيحة غير موجودة في الخيارات'}, status=status.HTTP_400_BAD_REQUEST)

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
            usage_type='STEP',
            step_skill=skill,
            is_active=data.get('is_active', True),
            order=0,
        )

        return Response({
            'message': 'تم إنشاء السؤال بنجاح',
            'question': {'id': question.id, 'question_text': question.question_text, 'created_at': question.created_at}
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f"Error creating vocabulary question: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_grammar_question(request):
    """
    POST /api/step/grammar/create/
    """
    from sabr_questions.models import GrammarQuestion, GrammarQuestionSet

    data = request.data.copy()
    required_fields = ['question_text', 'options', 'correct_answer', 'step_skill']
    for field in required_fields:
        if field not in data:
            return Response({field: f'{field} مطلوب'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        skill = get_object_or_404(STEPSkill, id=data.get('step_skill'))
        if skill.skill_type != 'GRAMMAR':
            return Response({'error': 'هذه المهارة ليست من نوع Grammar'}, status=status.HTTP_400_BAD_REQUEST)

        options = data.get('options', [])
        if len(options) < 2:
            return Response({'options': 'يجب إضافة خيارين على الأقل'}, status=status.HTTP_400_BAD_REQUEST)

        question_set, _ = GrammarQuestionSet.objects.get_or_create(
            title='STEP Grammar Questions',
            usage_type='STEP',
            defaults={'description': 'Auto-generated set for STEP'}
        )

        correct_answer = data.get('correct_answer')
        correct_letter = None
        for idx, option in enumerate(options):
            if option == correct_answer:
                correct_letter = chr(65 + idx)
                break

        if not correct_letter:
            return Response({'correct_answer': 'الإجابة الصحيحة غير موجودة في الخيارات'}, status=status.HTTP_400_BAD_REQUEST)

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
            usage_type='STEP',
            step_skill=skill,
            is_active=data.get('is_active', True),
            order=0,
        )

        return Response({
            'message': 'تم إنشاء السؤال بنجاح',
            'question': {'id': question.id, 'question_text': question.question_text, 'created_at': question.created_at}
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f"Error creating grammar question: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_reading_passage(request):
    """
    POST /api/step/reading/passages/create/
    """
    from sabr_questions.models import ReadingPassage

    data = request.data.copy()
    required_fields = ['title', 'passage_text', 'step_skill']
    for field in required_fields:
        if field not in data:
            return Response({field: f'{field} مطلوب'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        skill = get_object_or_404(STEPSkill, id=data.get('step_skill'))
        if skill.skill_type != 'READING':
            return Response({'error': 'هذه المهارة ليست من نوع Reading'}, status=status.HTTP_400_BAD_REQUEST)

        passage_data = {
            'title': data.get('title'),
            'passage_text': data.get('passage_text'),
            'usage_type': 'STEP',
            'step_skill': skill,
            'is_active': data.get('is_active', True),
            'order': 0,
        }
        if 'source' in data:
            passage_data['source'] = data.get('source')
        if 'passage_image' in data and data.get('passage_image'):
            passage_data['passage_image'] = data.get('passage_image')

        passage = ReadingPassage.objects.create(**passage_data)

        return Response({
            'message': 'تم إنشاء القطعة بنجاح',
            'passage': {'id': passage.id, 'title': passage.title, 'created_at': passage.created_at}
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f"Error creating reading passage: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_reading_question(request, passage_id):
    """
    POST /api/step/reading/passages/{passage_id}/questions/create/
    """
    from sabr_questions.models import ReadingPassage, ReadingQuestion

    try:
        passage = ReadingPassage.objects.get(id=passage_id, usage_type='STEP')
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

        correct_answer = data.get('correct_answer')
        correct_letter = None
        for idx, option in enumerate(options):
            if option == correct_answer:
                correct_letter = chr(65 + idx)
                break

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
        )

        return Response({
            'message': 'تم إنشاء السؤال بنجاح',
            'question': {'id': question.id, 'question_text': question.question_text, 'created_at': question.created_at}
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f"Error creating reading question: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


# ============================================
# LISTENING VIEWS ← جديد
# ============================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_listening_audio(request):
    """
    إنشاء تسجيل صوتي جديد لمهارة STEP Listening

    POST /api/step/listening/audio/create/

    Body:
    {
        "title": "Conversation at the airport",
        "audio_file": "https://res.cloudinary.com/.../audio.mp3",
        "transcript": "نص التسجيل الصوتي...",
        "duration": 120,
        "step_skill": 1,
        "order": 1
    }
    """
    from sabr_questions.models import ListeningAudio

    data = request.data.copy()
    required_fields = ['title', 'audio_file', 'step_skill']
    for field in required_fields:
        if field not in data:
            return Response({field: f'{field} مطلوب'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        skill = get_object_or_404(STEPSkill, id=data.get('step_skill'))
        if skill.skill_type != 'LISTENING':
            return Response(
                {'error': 'هذه المهارة ليست من نوع Listening'},
                status=status.HTTP_400_BAD_REQUEST
            )

        audio = ListeningAudio.objects.create(
            title=data.get('title'),
            audio_file=data.get('audio_file'),
            transcript=data.get('transcript', ''),
            duration=int(data.get('duration', 0)),
            usage_type='STEP',
            step_skill=skill,
            order=int(data.get('order', 0)),
            is_active=data.get('is_active', True),
        )

        return Response({
            'message': 'تم إنشاء التسجيل الصوتي بنجاح',
            'audio': {
                'id': audio.id,
                'title': audio.title,
                'audio_file': audio.audio_file.url if audio.audio_file else None,
                'transcript': audio.transcript,
                'duration': audio.duration,
                'created_at': audio.created_at,
            }
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f"Error creating STEP listening audio: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_listening_question(request, audio_id):
    """
    إنشاء سؤال لتسجيل صوتي معين

    POST /api/step/listening/audio/{audio_id}/questions/create/

    Body:
    {
        "question_text": "What did the man order?",
        "options": ["Coffee", "Tea", "Water", "Juice"],
        "correct_answer": "Coffee",
        "explanation": "The man clearly ordered coffee",
        "points": 1
    }
    """
    from sabr_questions.models import ListeningAudio, ListeningQuestion

    try:
        audio = ListeningAudio.objects.get(id=audio_id, usage_type='STEP')
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

        correct_answer = data.get('correct_answer')
        correct_letter = None
        for idx, option in enumerate(options):
            if option == correct_answer:
                correct_letter = chr(65 + idx)
                break

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
            'question': {
                'id': question.id,
                'question_text': question.question_text,
                'created_at': question.created_at,
            }
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f"Error creating STEP listening question: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_writing_question(request):
    """
    POST /api/step/writing/questions/create/
    """
    from sabr_questions.models import WritingQuestion

    data = request.data.copy()
    required_fields = ['title', 'question_text', 'min_words', 'max_words', 'sample_answer', 'rubric', 'step_skill']
    for field in required_fields:
        if field not in data:
            return Response({field: f'{field} مطلوب'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        skill = get_object_or_404(STEPSkill, id=data.get('step_skill'))
        if skill.skill_type != 'WRITING':
            return Response({'error': 'هذه المهارة ليست من نوع Writing'}, status=status.HTTP_400_BAD_REQUEST)

        min_words = int(data.get('min_words'))
        max_words = int(data.get('max_words'))
        if max_words <= min_words:
            return Response({'error': 'الحد الأقصى للكلمات يجب أن يكون أكبر من الحد الأدنى'}, status=status.HTTP_400_BAD_REQUEST)

        question_data = {
            'title': data.get('title'),
            'question_text': data.get('question_text'),
            'min_words': min_words,
            'max_words': max_words,
            'sample_answer': data.get('sample_answer'),
            'rubric': data.get('rubric'),
            'usage_type': 'STEP',
            'step_skill': skill,
            'points': data.get('points', 10),
            'is_active': data.get('is_active', True),
            'order': 0,
        }
        if 'question_image' in data and data.get('question_image'):
            question_data['question_image'] = data.get('question_image')
        if 'pass_threshold' in data:
            question_data['pass_threshold'] = data.get('pass_threshold')

        question = WritingQuestion.objects.create(**question_data)

        return Response({
            'message': 'تم إنشاء السؤال بنجاح',
            'question': {'id': question.id, 'title': question.title, 'created_at': question.created_at}
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f"Error creating writing question: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


# ============================================
# 3. QUESTIONS DISPLAY (للطالب)
# ============================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_skill_questions(request, skill_id):
    """
    GET /api/step/skills/{skill_id}/questions/?page=1&page_size=20
    """
    from sabr_questions.models import (
        VocabularyQuestion,
        GrammarQuestion,
        ReadingPassage,
        ListeningAudio,
        WritingQuestion,
    )

    skill = get_object_or_404(STEPSkill, id=skill_id)
    page = int(request.query_params.get('page', 1))
    page_size = int(request.query_params.get('page_size', 20))
    questions_data = []

    if skill.skill_type == 'VOCABULARY':
        questions = VocabularyQuestion.objects.filter(
            step_skill=skill, usage_type='STEP', is_active=True
        ).order_by('order', 'id')
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
            })

    elif skill.skill_type == 'GRAMMAR':
        questions = GrammarQuestion.objects.filter(
            step_skill=skill, usage_type='STEP', is_active=True
        ).order_by('order', 'id')
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
            })

    elif skill.skill_type == 'READING':
        passages = ReadingPassage.objects.filter(
            step_skill=skill, usage_type='STEP', is_active=True
        ).prefetch_related('questions').order_by('order', 'id')
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
                })
            questions_data.append({
                'id': passage.id, 'type': 'READING',
                'title': passage.title,
                'passage_text': passage.passage_text,
                'passage_image': passage.passage_image.url if passage.passage_image else None,
                'source': passage.source,
                'questions': passage_questions,
            })

    elif skill.skill_type == 'LISTENING':  # ← جديد
        audios = ListeningAudio.objects.filter(
            step_skill=skill, usage_type='STEP', is_active=True
        ).prefetch_related('questions').order_by('order', 'id')
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
                })
            questions_data.append({
                'id': audio.id, 'type': 'LISTENING',
                'title': audio.title,
                'audio_file': audio.audio_file.url if audio.audio_file else None,
                'transcript': audio.transcript,
                'duration': audio.duration,
                'questions': audio_questions,
            })

    elif skill.skill_type == 'WRITING':
        questions = WritingQuestion.objects.filter(
            step_skill=skill, usage_type='STEP', is_active=True
        ).order_by('order', 'id')
        paginator = Paginator(questions, page_size)
        page_obj = paginator.get_page(page)
        for q in page_obj:
            questions_data.append({
                'id': q.id, 'type': 'WRITING',
                'title': q.title, 'question_text': q.question_text,
                'question_image': q.question_image.url if q.question_image else None,
                'min_words': q.min_words, 'max_words': q.max_words,
                'sample_answer': q.sample_answer, 'rubric': q.rubric,
                'points': q.points,
            })

    return Response({
        'skill': {
            'id': skill.id,
            'title': skill.title,
            'skill_type': skill.skill_type,
        },
        'pagination': {
            'page': page,
            'page_size': page_size,
            'total_pages': paginator.num_pages if 'paginator' in locals() else 1,
            'total_items': paginator.count if 'paginator' in locals() else len(questions_data),
        },
        'questions': questions_data
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_question_viewed(request, skill_id, question_type, question_id):
    """
    POST /api/step/skills/{skill_id}/questions/{question_type}/{question_id}/mark-viewed/
    question_type: VOCABULARY, GRAMMAR, READING, LISTENING, WRITING
    """
    skill = get_object_or_404(STEPSkill, id=skill_id)
    student = request.user

    valid_types = ['VOCABULARY', 'GRAMMAR', 'READING', 'LISTENING', 'WRITING']  # ← أضفنا LISTENING
    if question_type not in valid_types:
        return Response(
            {'error': f'نوع السؤال غير صحيح. يجب أن يكون أحد: {", ".join(valid_types)}'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        with transaction.atomic():
            view_record, created = StudentSTEPQuestionView.objects.get_or_create(
                student=student,
                skill=skill,
                question_type=question_type,
                question_id=question_id
            )

            if created:
                progress, _ = StudentSTEPProgress.objects.get_or_create(
                    student=student, skill=skill
                )
                progress.increment_score()
                return Response({
                    'message': 'تم تسجيل فتح السؤال وإضافة نقطة',
                    'points_earned': 1,
                    'total_score': progress.total_score,
                    'progress_percentage': progress.calculate_progress_percentage()
                }, status=status.HTTP_201_CREATED)
            else:
                progress = StudentSTEPProgress.objects.get(student=student, skill=skill)
                return Response({
                    'message': 'السؤال تم فتحه من قبل',
                    'points_earned': 0,
                    'total_score': progress.total_score,
                    'progress_percentage': progress.calculate_progress_percentage()
                }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error marking question viewed: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


# ============================================
# 4. STUDENT PROGRESS
# ============================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_progress(request):
    """
    GET /api/step/my-progress/
    """
    student = request.user
    progress_records = StudentSTEPProgress.objects.filter(
        student=student
    ).select_related('skill').order_by('skill__order')

    progress_serializer = StudentSTEPProgressSerializer(progress_records, many=True)

    total_score = sum(p.total_score for p in progress_records)
    total_viewed = sum(p.viewed_questions_count for p in progress_records)

    all_skills = STEPSkill.objects.filter(is_active=True)
    total_available = sum(skill.get_total_questions_count() for skill in all_skills)

    overall_percentage = 0
    if total_available > 0:
        overall_percentage = round((total_viewed / total_available) * 100, 2)

    return Response({
        'summary': {
            'total_score': total_score,
            'total_viewed_questions': total_viewed,
            'total_available_questions': total_available,
            'overall_progress_percentage': overall_percentage
        },
        'skills_progress': progress_serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def skill_progress(request, skill_id):
    """
    GET /api/step/skills/{skill_id}/my-progress/
    """
    skill = get_object_or_404(STEPSkill, id=skill_id)
    student = request.user

    try:
        progress = StudentSTEPProgress.objects.get(student=student, skill=skill)
        serializer = StudentSTEPProgressSerializer(progress)
        return Response(serializer.data, status=status.HTTP_200_OK)

    except StudentSTEPProgress.DoesNotExist:
        return Response({
            'skill': {'id': skill.id, 'title': skill.title, 'skill_type': skill.skill_type},
            'viewed_questions_count': 0,
            'total_questions': skill.get_total_questions_count(),
            'progress_percentage': 0,
            'total_score': 0,
        }, status=status.HTTP_200_OK)