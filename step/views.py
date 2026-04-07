from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.paginator import Paginator
from django.db.models import Case, When, IntegerField, Value
from .models import (
    STEPSkill,
    StudentSTEPProgress,
    StudentSTEPQuestionView,StudentSTEPQuestionAttempt
)
from sabr_questions.models import SpeakingVideo

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
        if skill.skill_type not in ['VOCABULARY', 'GENERAL_PATH']:
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
            difficulty=data.get('difficulty', 'MEDIUM'),
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
        if skill.skill_type not in ['GRAMMAR', 'GENERAL_PATH']:
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
            difficulty=data.get('difficulty', 'MEDIUM'),
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
        if skill.skill_type not in ['READING', 'GENERAL_PATH']:
            return Response({'error': 'هذه المهارة ليست من نوع Reading'}, status=status.HTTP_400_BAD_REQUEST)

        passage_data = {
            'title': data.get('title'),
            'passage_text': data.get('passage_text'),
            'usage_type': 'STEP',
            'step_skill': skill,
            'is_active': data.get('is_active', True),
            'order': 0,
            'difficulty': data.get('difficulty', 'MEDIUM'),
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
            difficulty=data.get('difficulty', 'MEDIUM'),
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
        if skill.skill_type not in ['LISTENING', 'GENERAL_PATH']:
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
            difficulty=data.get('difficulty', 'MEDIUM'),
        )

        return Response({
            'message': 'تم إنشاء التسجيل الصوتي بنجاح',
            'audio': {
                'id': audio.id,
                'title': audio.title,
                'audio_file': str(audio.audio_file) if audio.audio_file else None,
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
            'difficulty': data.get('difficulty', 'MEDIUM'),
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


# Helper لترتيب الصعوبة: EASY=1, MEDIUM=2, HARD=3
DIFFICULTY_ORDER = Case(
    When(difficulty='EASY', then=Value(1)),
    When(difficulty='MEDIUM', then=Value(2)),
    When(difficulty='HARD', then=Value(3)),
    default=Value(2),
    output_field=IntegerField()
)

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
    student = request.user
    questions_data = []

    # ============================================================
    # ✅ جيب كل محاولات الطالب في المهارة دي دفعة واحدة
    # بنعمل dict بالشكل ده: {('VOCABULARY', 95): attempt_obj, ...}
    # عشان نعمل lookup سريع لكل سؤال من غير ما نضرب DB لكل سؤال
    # ============================================================
    attempts_qs = StudentSTEPQuestionAttempt.objects.filter(
        student=student,
        skill=skill,
    )
    attempts_map = {
        (a.question_type, a.question_id): a
        for a in attempts_qs
    }

    # ============================================================
    # جيب التوتال سكور للطالب في المهارة دي
    # ============================================================
    try:
        progress = StudentSTEPProgress.objects.get(student=student, skill=skill)
        skill_total_score = progress.total_score
    except StudentSTEPProgress.DoesNotExist:
        skill_total_score = 0

    # Helper: يجيب بيانات المحاولة لسؤال معين
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

    if skill.skill_type == 'VOCABULARY':
        questions = VocabularyQuestion.objects.filter(
            step_skill=skill, usage_type='STEP', is_active=True
        ).order_by(DIFFICULTY_ORDER, 'order', 'id')
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
                **get_attempt_data('VOCABULARY', q.id),  # ✅
            })

    elif skill.skill_type == 'GRAMMAR':
        questions = GrammarQuestion.objects.filter(
            step_skill=skill, usage_type='STEP', is_active=True
        ).order_by(DIFFICULTY_ORDER, 'order', 'id')
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
                **get_attempt_data('GRAMMAR', q.id),  # ✅
            })

    elif skill.skill_type == 'READING':
        passages = ReadingPassage.objects.filter(
            step_skill=skill, usage_type='STEP', is_active=True
        ).prefetch_related('questions').order_by(DIFFICULTY_ORDER, 'order', 'id')
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
                    **get_attempt_data('READING', q.id),  # ✅
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
        audios = ListeningAudio.objects.filter(
            step_skill=skill, usage_type='STEP', is_active=True
        ).prefetch_related('questions').order_by(DIFFICULTY_ORDER, 'order', 'id')
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
                    **get_attempt_data('LISTENING', q.id),  # ✅
                })
            questions_data.append({
                'id': audio.id, 'type': 'LISTENING',
                'title': audio.title,
                'audio_file': str(audio.audio_file) if audio.audio_file else None,
                'transcript': audio.transcript,
                'duration': audio.duration,
                'questions': audio_questions,
                'difficulty': audio.difficulty,
            })
    elif skill.skill_type == 'SPEAKING':

        videos = SpeakingVideo.objects.filter(
            step_skill=skill, usage_type='STEP', is_active=True
        ).prefetch_related('questions').order_by(DIFFICULTY_ORDER, 'order', 'id')
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
                'video_file': str(video.video_file) if video.video_file else None,
                'thumbnail': str(video.thumbnail) if video.thumbnail else None,
                'description': video.description,
                'duration': video.duration,
                'questions': video_questions,
                'difficulty': video.difficulty,
            })

    elif skill.skill_type == 'WRITING':
        questions = WritingQuestion.objects.filter(
            step_skill=skill, usage_type='STEP', is_active=True
        ).order_by(DIFFICULTY_ORDER, 'order', 'id')
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
                'difficulty': q.difficulty,
                **get_attempt_data('WRITING', q.id),  # ✅
            })

    elif skill.skill_type == 'GENERAL_PATH':
        from sabr_questions.models import (
            VocabularyQuestion, GrammarQuestion,
            ReadingPassage, ListeningAudio,
        )

        # ✅ للـ GENERAL_PATH، الـ attempts_map ممكن يحتاج يجيب من child skills كمان
        # بنوسع الـ attempts_map عشان يشمل كل الـ child skills
        child_skills = skill.child_skills.filter(is_active=True)
        if child_skills.exists():
            extra_attempts = StudentSTEPQuestionAttempt.objects.filter(
                student=student,
                skill__in=child_skills,
            )
            for a in extra_attempts:
                attempts_map.setdefault((a.question_type, a.question_id), a)

        # Vocabulary
        vocab_qs = VocabularyQuestion.objects.filter(
            step_skill=skill, usage_type='STEP', is_active=True
        ).order_by(DIFFICULTY_ORDER, 'order', 'id')
        for q in vocab_qs:
            questions_data.append({
                'id': q.id, 'type': 'VOCABULARY',
                'question_text': q.question_text,
                'question_image': q.question_image.url if q.question_image else None,
                'choice_a': q.choice_a, 'choice_b': q.choice_b,
                'choice_c': q.choice_c, 'choice_d': q.choice_d,
                'correct_answer': q.correct_answer,
                'explanation': q.explanation, 'points': q.points,
                'difficulty': q.difficulty,
                **get_attempt_data('VOCABULARY', q.id),  # ✅
            })

        # Grammar
        grammar_qs = GrammarQuestion.objects.filter(
            step_skill=skill, usage_type='STEP', is_active=True
        ).order_by(DIFFICULTY_ORDER, 'order', 'id')
        for q in grammar_qs:
            questions_data.append({
                'id': q.id, 'type': 'GRAMMAR',
                'question_text': q.question_text,
                'question_image': q.question_image.url if q.question_image else None,
                'choice_a': q.choice_a, 'choice_b': q.choice_b,
                'choice_c': q.choice_c, 'choice_d': q.choice_d,
                'correct_answer': q.correct_answer,
                'explanation': q.explanation, 'points': q.points,
                'difficulty': q.difficulty,
                **get_attempt_data('GRAMMAR', q.id),  # ✅
            })

        # Reading
        passages = ReadingPassage.objects.filter(
            step_skill=skill, usage_type='STEP', is_active=True
        ).prefetch_related('questions').order_by(DIFFICULTY_ORDER, 'order', 'id')
        for passage in passages:
            passage_questions = []
            for q in passage.questions.filter(is_active=True).order_by('order', 'id'):
                passage_questions.append({
                    'id': q.id, 'question_text': q.question_text,
                    'choice_a': q.choice_a, 'choice_b': q.choice_b,
                    'choice_c': q.choice_c, 'choice_d': q.choice_d,
                    'correct_answer': q.correct_answer,
                    'explanation': q.explanation, 'points': q.points,
                    **get_attempt_data('READING', q.id),  # ✅
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
        # Speaking
        videos = SpeakingVideo.objects.filter(step_skill=skill, usage_type='STEP', is_active=True).prefetch_related('questions').order_by(DIFFICULTY_ORDER, 'order', 'id')
        for video in videos:
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
                'video_file': str(video.video_file) if video.video_file else None,
                'thumbnail': str(video.thumbnail) if video.thumbnail else None,
                'description': video.description,
                'duration': video.duration,
                'questions': video_questions,
                'difficulty': video.difficulty,
            })
        # Listening
        audios = ListeningAudio.objects.filter(
            step_skill=skill, usage_type='STEP', is_active=True
        ).prefetch_related('questions').order_by(DIFFICULTY_ORDER, 'order', 'id')
        for audio in audios:
            audio_questions = []
            for q in audio.questions.filter(is_active=True).order_by('order', 'id'):
                audio_questions.append({
                    'id': q.id, 'question_text': q.question_text,
                    'choice_a': q.choice_a, 'choice_b': q.choice_b,
                    'choice_c': q.choice_c, 'choice_d': q.choice_d,
                    'correct_answer': q.correct_answer,
                    'explanation': q.explanation, 'points': q.points,
                    **get_attempt_data('LISTENING', q.id),  # ✅
                })
            questions_data.append({
                'id': audio.id, 'type': 'LISTENING',
                'title': audio.title,
                'audio_file': str(audio.audio_file) if audio.audio_file else None,
                'transcript': audio.transcript,
                'duration': audio.duration,
                'questions': audio_questions,
                'difficulty': audio.difficulty,
            })

        paginator = Paginator(questions_data, page_size)
        page_obj = paginator.get_page(page)
        questions_data = list(page_obj)

        return Response({
            'skill': {
                'id': skill.id,
                'title': skill.title,
                'skill_type': skill.skill_type,
            },
            'skill_total_score': skill_total_score,  # ✅
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total_pages': paginator.num_pages,
                'total_items': paginator.count,
            },
            'questions': questions_data
        }, status=status.HTTP_200_OK)

    # ============================================================
    # Response للـ skill types العادية (غير GENERAL_PATH)
    # ============================================================
    paginator = Paginator(questions_data, page_size)

    return Response({
        'skill': {
            'id': skill.id,
            'title': skill.title,
            'skill_type': skill.skill_type,
        },
        'skill_total_score': skill_total_score,  # ✅
        'pagination': {
            'page': page,
            'page_size': page_size,
            'total_pages': paginator.num_pages,
            'total_items': paginator.count,
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

    valid_types = ['VOCABULARY', 'GRAMMAR', 'READING', 'LISTENING', 'WRITING','SPEAKING']  # ← أضفنا LISTENING
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
                progress.increment_score()  # هيبقى +10 تلقائياً
                return Response({
                    'message': 'تم اجتياز السؤال',
                    'points_earned': 10,  # ✅ غير من 1 لـ 10
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

    all_skills = STEPSkill.objects.filter(is_active=True).exclude(skill_type='GENERAL_PATH')
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
    if skill.skill_type == 'GENERAL_PATH':
        child_skills = skill.child_skills.filter(is_active=True)
        total_viewed = 0
        total_score = 0
        total_questions = 0

        for child in child_skills:
            total_questions += child.get_total_questions_count()
            try:
                progress = StudentSTEPProgress.objects.get(student=student, skill=child)
                total_viewed += progress.viewed_questions_count
                total_score += progress.total_score
            except StudentSTEPProgress.DoesNotExist:
                pass

        overall_percentage = 0
        if total_questions > 0:
            overall_percentage = round((total_viewed / total_questions) * 100, 2)

        return Response({
            'skill': {'id': skill.id, 'title': skill.title, 'skill_type': skill.skill_type},
            'viewed_questions_count': total_viewed,
            'total_questions': total_questions,
            'progress_percentage': overall_percentage,
            'total_score': total_score,
        }, status=status.HTTP_200_OK)
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

# ============================================
# 5. UPDATE & DELETE QUESTIONS
# ============================================

def _map_options_to_letters(options, correct_answer):
    """Helper: يحول الخيارات والإجابة الصحيحة لحروف A/B/C/D"""
    correct_letter = None
    for idx, option in enumerate(options):
        if option == correct_answer:
            correct_letter = chr(65 + idx)
            break
    return correct_letter


# --- Vocabulary ---

@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_vocabulary_question(request, question_id):
    """
    PUT/PATCH /api/step/vocabulary/<question_id>/update/
    """
    from sabr_questions.models import VocabularyQuestion

    question = get_object_or_404(VocabularyQuestion, id=question_id, usage_type='STEP')
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

        if 'question_text' in data:
            question.question_text = data['question_text']
        if 'explanation' in data:
            question.explanation = data['explanation']
        if 'points' in data:
            question.points = data['points']
        if 'is_active' in data:
            question.is_active = data['is_active']
        if 'difficulty' in data:
            question.difficulty = data['difficulty']

        question.save()
        return Response({
            'message': 'تم تحديث السؤال بنجاح',
            'question': {'id': question.id, 'question_text': question.question_text}
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error updating vocabulary question: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_vocabulary_question(request, question_id):
    """
    DELETE /api/step/vocabulary/<question_id>/delete/
    """
    from sabr_questions.models import VocabularyQuestion

    question = get_object_or_404(VocabularyQuestion, id=question_id, usage_type='STEP')
    question.delete()
    return Response({'message': 'تم حذف السؤال بنجاح', 'question_id': question_id}, status=status.HTTP_200_OK)


# --- Grammar ---

@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_grammar_question(request, question_id):
    """
    PUT/PATCH /api/step/grammar/<question_id>/update/
    """
    from sabr_questions.models import GrammarQuestion

    question = get_object_or_404(GrammarQuestion, id=question_id, usage_type='STEP')
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

        if 'question_text' in data:
            question.question_text = data['question_text']
        if 'explanation' in data:
            question.explanation = data['explanation']
        if 'points' in data:
            question.points = data['points']
        if 'is_active' in data:
            question.is_active = data['is_active']
        if 'difficulty' in data:
            question.difficulty = data['difficulty']
        question.save()
        return Response({
            'message': 'تم تحديث السؤال بنجاح',
            'question': {'id': question.id, 'question_text': question.question_text}
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error updating grammar question: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_grammar_question(request, question_id):
    """
    DELETE /api/step/grammar/<question_id>/delete/
    """
    from sabr_questions.models import GrammarQuestion

    question = get_object_or_404(GrammarQuestion, id=question_id, usage_type='STEP')
    question.delete()
    return Response({'message': 'تم حذف السؤال بنجاح', 'question_id': question_id}, status=status.HTTP_200_OK)


# --- Reading Passage ---

@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_reading_passage(request, passage_id):
    """
    PUT/PATCH /api/step/reading/passages/<passage_id>/update/
    """
    from sabr_questions.models import ReadingPassage

    passage = get_object_or_404(ReadingPassage, id=passage_id, usage_type='STEP')
    data = request.data.copy()

    try:
        if 'title' in data:
            passage.title = data['title']
        if 'passage_text' in data:
            passage.passage_text = data['passage_text']
        if 'source' in data:
            passage.source = data['source']
        if 'is_active' in data:
            passage.is_active = data['is_active']
        if 'difficulty' in data:
            passage.difficulty = data['difficulty']
        passage.save()
        return Response({
            'message': 'تم تحديث القطعة بنجاح',
            'passage': {'id': passage.id, 'title': passage.title}
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error updating reading passage: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_reading_passage(request, passage_id):
    """
    DELETE /api/step/reading/passages/<passage_id>/delete/
    """
    from sabr_questions.models import ReadingPassage

    passage = get_object_or_404(ReadingPassage, id=passage_id, usage_type='STEP')
    passage.delete()
    return Response({'message': 'تم حذف القطعة وأسئلتها بنجاح', 'passage_id': passage_id}, status=status.HTTP_200_OK)


# --- Reading Question ---

@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_reading_question(request, question_id):
    """
    PUT/PATCH /api/step/reading/questions/<question_id>/update/
    """
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

        if 'question_text' in data:
            question.question_text = data['question_text']
        if 'explanation' in data:
            question.explanation = data['explanation']
        if 'points' in data:
            question.points = data['points']
        if 'is_active' in data:
            question.is_active = data['is_active']

        question.save()
        return Response({
            'message': 'تم تحديث السؤال بنجاح',
            'question': {'id': question.id, 'question_text': question.question_text}
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error updating reading question: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_reading_question(request, question_id):
    """
    DELETE /api/step/reading/questions/<question_id>/delete/
    """
    from sabr_questions.models import ReadingQuestion

    question = get_object_or_404(ReadingQuestion, id=question_id)
    question.delete()
    return Response({'message': 'تم حذف السؤال بنجاح', 'question_id': question_id}, status=status.HTTP_200_OK)


# --- Listening Audio ---

@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_listening_audio(request, audio_id):
    """
    PUT/PATCH /api/step/listening/audio/<audio_id>/update/
    """
    from sabr_questions.models import ListeningAudio

    audio = get_object_or_404(ListeningAudio, id=audio_id, usage_type='STEP')
    data = request.data.copy()

    try:
        if 'title' in data:
            audio.title = data['title']
        if 'audio_file' in data:
            audio.audio_file = data['audio_file']
        if 'transcript' in data:
            audio.transcript = data['transcript']
        if 'duration' in data:
            audio.duration = int(data['duration'])
        if 'is_active' in data:
            audio.is_active = data['is_active']
        if 'difficulty' in data:
            audio .difficulty = data['difficulty']

        audio.save()
        return Response({
            'message': 'تم تحديث التسجيل الصوتي بنجاح',
            'audio': {'id': audio.id, 'title': audio.title}
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error updating listening audio: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_listening_audio(request, audio_id):
    """
    DELETE /api/step/listening/audio/<audio_id>/delete/
    """
    from sabr_questions.models import ListeningAudio

    audio = get_object_or_404(ListeningAudio, id=audio_id, usage_type='STEP')
    audio.delete()
    return Response({'message': 'تم حذف التسجيل الصوتي وأسئلته بنجاح', 'audio_id': audio_id}, status=status.HTTP_200_OK)


# --- Listening Question ---

@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_listening_question(request, question_id):
    """
    PUT/PATCH /api/step/listening/questions/<question_id>/update/
    """
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

        if 'question_text' in data:
            question.question_text = data['question_text']
        if 'explanation' in data:
            question.explanation = data['explanation']
        if 'points' in data:
            question.points = data['points']
        if 'is_active' in data:
            question.is_active = data['is_active']

        question.save()
        return Response({
            'message': 'تم تحديث السؤال بنجاح',
            'question': {'id': question.id, 'question_text': question.question_text}
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error updating listening question: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_listening_question(request, question_id):
    """
    DELETE /api/step/listening/questions/<question_id>/delete/
    """
    from sabr_questions.models import ListeningQuestion

    question = get_object_or_404(ListeningQuestion, id=question_id)
    question.delete()
    return Response({'message': 'تم حذف السؤال بنجاح', 'question_id': question_id}, status=status.HTTP_200_OK)


# --- Writing ---

@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_writing_question(request, question_id):
    """
    PUT/PATCH /api/step/writing/questions/<question_id>/update/
    """
    from sabr_questions.models import WritingQuestion

    question = get_object_or_404(WritingQuestion, id=question_id, usage_type='STEP')
    data = request.data.copy()

    try:
        if 'title' in data:
            question.title = data['title']
        if 'question_text' in data:
            question.question_text = data['question_text']
        if 'min_words' in data:
            question.min_words = int(data['min_words'])
        if 'max_words' in data:
            question.max_words = int(data['max_words'])
        if 'sample_answer' in data:
            question.sample_answer = data['sample_answer']
        if 'rubric' in data:
            question.rubric = data['rubric']
        if 'is_active' in data:
            question.is_active = data['is_active']
        if 'difficulty' in data:
            question.difficulty = data['difficulty']

        if question.max_words <= question.min_words:
            return Response({'error': 'الحد الأقصى للكلمات يجب أن يكون أكبر من الحد الأدنى'}, status=status.HTTP_400_BAD_REQUEST)

        question.save()
        return Response({
            'message': 'تم تحديث السؤال بنجاح',
            'question': {'id': question.id, 'title': question.title}
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error updating writing question: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_writing_question(request, question_id):
    """
    DELETE /api/step/writing/questions/<question_id>/delete/
    """
    from sabr_questions.models import WritingQuestion

    question = get_object_or_404(WritingQuestion, id=question_id, usage_type='STEP')
    question.delete()
    return Response({'message': 'تم حذف السؤال بنجاح', 'question_id': question_id}, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_writing_answer(request, question_id):
    """
    POST /api/step/writing/questions/{question_id}/submit/
    Body: { "student_answer": "..." }
    """
    from sabr_questions.models import WritingQuestion
    from placement_test.services.ai_grading import AIGradingService
    import json

    question = get_object_or_404(WritingQuestion, id=question_id, usage_type='STEP')
    student_answer = request.data.get('student_answer', '').strip()

    if not student_answer:
        return Response(
            {'error': 'الإجابة مطلوبة'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # التحقق من عدد الكلمات
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
        # ✅ نفس الـ AIGradingService الموجود بالظبط
        grading_service = AIGradingService()

        grading_result = grading_service.grade_writing_question(
            question_text=question.question_text,
            student_answer=student_answer,
            sample_answer=question.sample_answer or '',
            rubric=question.rubric or '',
            max_points=10,          # دايماً من 10 في الـ STEP
            min_words=question.min_words,
            max_words=question.max_words,
            pass_threshold=60       # مش بنستخدمه لكن مطلوب للـ service
        )

        return Response({
            # ✅ النتيجة من 10 (raw_score مش binary)
            'score': grading_result.get('raw_score', 0),
            'percentage': grading_result.get('percentage', 0),
            'feedback': grading_result.get('feedback', ''),
            'strengths': grading_result.get('strengths', []),
            'improvements': grading_result.get('improvements', []),
            'word_count': word_count,
            # ✅ إشارة للـ frontend إنه يظهر زرار "تم المراجعة"
            'can_mark_as_viewed': True,
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error getting AI feedback for STEP writing: {str(e)}")
        return Response(
            {'error': 'حدث خطأ أثناء تقييم الإجابة، حاول مرة أخرى'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# ============================================
# نظام المحاولات الجديد
# ============================================

# نقاط المحاولات
ATTEMPT_POINTS = {1: 20, 2: 15, 3: 10}
SHOW_ANSWER_POINTS = 5
MAX_ATTEMPTS_POINTS = 5  # محاولة 4 أو أكتر


def _get_correct_answer_text(question_type, question_id):
    """
    Helper: يجيب نص الإجابة الصحيحة من السؤال
    بيرجع dict فيه correct_answer و explanation
    """
    from sabr_questions.models import (
        VocabularyQuestion, GrammarQuestion,
        ReadingQuestion, ListeningQuestion, WritingQuestion,SpeakingQuestion
    )

    model_map = {
        'VOCABULARY': VocabularyQuestion,
        'GRAMMAR': GrammarQuestion,
        'READING': ReadingQuestion,
        'LISTENING': ListeningQuestion,
        'SPEAKING': SpeakingQuestion,
    }

    if question_type == 'WRITING':
        q = get_object_or_404(WritingQuestion, id=question_id, usage_type='STEP')
        return {
            'sample_answer': q.sample_answer,
            'rubric': q.rubric,
        }

    model = model_map.get(question_type)
    if not model:
        return {}

    q = get_object_or_404(model, id=question_id)

    # نحول الحرف (A/B/C/D) لنص الإجابة
    choice_map = {
        'A': q.choice_a, 'B': q.choice_b,
        'C': q.choice_c, 'D': q.choice_d,
    }
    correct_text = choice_map.get(q.correct_answer, '')

    return {
        'correct_answer_letter': q.correct_answer,
        'correct_answer_text': correct_text,
        'explanation': q.explanation,
    }


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_mcq_answer(request, skill_id, question_type, question_id):
    """
    POST /api/step/skills/{skill_id}/questions/{question_type}/{question_id}/submit/

    يستقبل إجابة الطالب على سؤال MCQ ويحسب النقاط حسب عدد المحاولات.

    Body: { "selected_answer": "A" }  ← حرف الإجابة (A/B/C/D)

    Response:
    {
        "is_correct": true/false,
        "attempts_count": 2,
        "points_earned": 0,        ← 0 لو غلط، النقاط لو صح
        "total_points_this_question": 15,  ← النقاط المكتسبة من السؤال ده
        "total_score": 150,
        "progress_percentage": 45.5,
        "correct_answer": "B",     ← بس لو خلص محاولاته (4 محاولات غلط)
        "message": "..."
    }
    """
    from sabr_questions.models import (
        VocabularyQuestion, GrammarQuestion,
        ReadingQuestion, ListeningQuestion,SpeakingQuestion
    )

    skill = get_object_or_404(STEPSkill, id=skill_id)
    student = request.user

    valid_types = ['VOCABULARY', 'GRAMMAR', 'READING', 'LISTENING', 'SPEAKING']
    if question_type not in valid_types:
        return Response(
            {'error': f'استخدم هذا الـ endpoint للأنواع: {", ".join(valid_types)} فقط'},
            status=status.HTTP_400_BAD_REQUEST
        )

    selected_answer = request.data.get('selected_answer', '').strip().upper()
    if not selected_answer:
        return Response(
            {'error': 'selected_answer مطلوب (A/B/C/D)'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # نجيب الإجابة الصحيحة من الـ model المناسب
    model_map = {
        'VOCABULARY': VocabularyQuestion,
        'GRAMMAR': GrammarQuestion,
        'READING': ReadingQuestion,
        'LISTENING': ListeningQuestion,
        'SPEAKING': SpeakingQuestion,
    }
    model = model_map[question_type]
    question = get_object_or_404(model, id=question_id)
    correct_answer = question.correct_answer  # حرف A/B/C/D

    try:
        with transaction.atomic():
            # نجيب أو ننشئ record للمحاولة
            attempt, created = StudentSTEPQuestionAttempt.objects.get_or_create(
                student=student,
                question_type=question_type,
                question_id=question_id,
                defaults={'skill': skill}
            )

            # لو السؤال اتحل قبل كده (صح أو show answer) → ارفض
            if attempt.is_solved:
                progress, _ = StudentSTEPProgress.objects.get_or_create(
                    student=student, skill=skill
                )
                return Response({
                    'message': 'هذا السؤال تم حله من قبل ولا يمكن كسب نقاط إضافية منه',
                    'is_correct': selected_answer == correct_answer,
                    'attempts_count': attempt.attempts_count,
                    'total_points_this_question': attempt.points_earned,
                    'total_score': progress.total_score,
                    'progress_percentage': progress.calculate_progress_percentage(),
                    'already_solved': True,
                }, status=status.HTTP_200_OK)

            # زود عداد المحاولات
            attempt.attempts_count += 1
            attempt.save()

            is_correct = (selected_answer == correct_answer)
            progress, _ = StudentSTEPProgress.objects.get_or_create(
                student=student, skill=skill
            )

            if is_correct:
                # احسب النقاط حسب عدد المحاولات
                points = ATTEMPT_POINTS.get(attempt.attempts_count, MAX_ATTEMPTS_POINTS)
                attempt.is_solved = True
                attempt.points_earned = points
                attempt.solved_at = timezone.now()
                attempt.save()

                # زود التقدم
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
                # إجابة غلط
                # لو وصل المحاولة الرابعة → انتهى، 0 نقاط، نكشف الإجابة
                if attempt.attempts_count >= 4:
                    attempt.is_solved = True
                    attempt.points_earned = 0
                    attempt.solved_at = timezone.now()
                    attempt.save()

                    # نزود viewed_questions_count بس مش نقاط
                    progress.viewed_questions_count += 1
                    progress.save()

                    # نجيب الإجابة الصحيحة نصاً
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
                        'correct_answer_text': choice_map.get(correct_answer, ''),
                        'explanation': question.explanation,
                        'max_attempts_reached': True,
                    }, status=status.HTTP_200_OK)

                # لسه في محاولات
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
        logger.error(f"Error in submit_mcq_answer: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def use_show_answer(request, skill_id, question_type, question_id):
    """
    POST /api/step/skills/{skill_id}/questions/{question_type}/{question_id}/show-answer/

    لما الطالب يضغط "Show Answer":
    - لو السؤال لم يُحل بعد → يكسب 5 نقاط ويتعلم الإجابة
    - لو السؤال اتحل قبل كده → يشوف الإجابة بس من غير نقاط

    Response:
    {
        "points_earned": 5,         ← أو 0 لو اتحل قبل
        "total_score": 155,
        "correct_answer_letter": "B",
        "correct_answer_text": "...",
        "explanation": "...",
        "message": "..."
    }
    """
    from sabr_questions.models import (
        VocabularyQuestion, GrammarQuestion,
        ReadingQuestion, ListeningQuestion, WritingQuestion,
    )

    skill = get_object_or_404(STEPSkill, id=skill_id)
    student = request.user

    valid_types = ['VOCABULARY', 'GRAMMAR', 'READING', 'LISTENING', 'WRITING', 'SPEAKING']
    if question_type not in valid_types:
        return Response(
            {'error': f'نوع السؤال غير صحيح'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        with transaction.atomic():
            attempt, created = StudentSTEPQuestionAttempt.objects.get_or_create(
                student=student,
                question_type=question_type,
                question_id=question_id,
                defaults={'skill': skill}
            )

            progress, _ = StudentSTEPProgress.objects.get_or_create(
                student=student, skill=skill
            )

            # نجيب الإجابة الصحيحة
            answer_data = _get_correct_answer_text(question_type, question_id)

            # لو السؤال اتحل قبل كده → بس نكشف الإجابة من غير نقاط
            if attempt.is_solved:
                return Response({
                    'message': 'تم حل هذا السؤال من قبل',
                    'points_earned': 0,
                    'already_solved': True,
                    'total_score': progress.total_score,
                    'progress_percentage': progress.calculate_progress_percentage(),
                    **answer_data,
                }, status=status.HTTP_200_OK)

            # أول مرة يضغط show answer → 5 نقاط
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
        logger.error(f"Error in use_show_answer: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_question_attempt_status(request, skill_id, question_type, question_id):
    """
    GET /api/step/skills/{skill_id}/questions/{question_type}/{question_id}/attempt-status/

    يجيب حالة محاولات الطالب على سؤال معين.
    مفيد للـ frontend عشان يعرف يعرض كام محاولة اتعملت.

    Response:
    {
        "has_attempted": true,
        "attempts_count": 2,
        "is_solved": false,
        "points_earned": 0,
        "used_show_answer": false,
        "remaining_attempts": 2,
        "next_attempt_points": 10
    }
    """
    skill = get_object_or_404(STEPSkill, id=skill_id)
    student = request.user

    try:
        attempt = StudentSTEPQuestionAttempt.objects.get(
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

    except StudentSTEPQuestionAttempt.DoesNotExist:
        return Response({
            'has_attempted': False,
            'attempts_count': 0,
            'is_solved': False,
            'points_earned': 0,
            'used_show_answer': False,
            'remaining_attempts': 4,
            'next_attempt_points': 20,  # أول محاولة = 20 نقطة
        }, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def set_child_skills(request, skill_id):
    """
    POST /api/step/skills/{skill_id}/set-children/
    Body: { "child_skill_ids": [1, 2, 3, 4] }
    """
    skill = get_object_or_404(STEPSkill, id=skill_id)
    
    if skill.skill_type != 'GENERAL_PATH':
        return Response(
            {'error': 'هذه المهارة ليست مساراً عاماً'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    child_ids = request.data.get('child_skill_ids', [])
    
    # تتأكد إن مفيش GENERAL_PATH يكون child لـ GENERAL_PATH تاني
    invalid = STEPSkill.objects.filter(
        id__in=child_ids, skill_type='GENERAL_PATH'
    )
    if invalid.exists():
        return Response(
            {'error': 'لا يمكن إضافة مسار عام كمهارة فرعية'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    children = STEPSkill.objects.filter(id__in=child_ids)
    skill.child_skills.set(children)
    
    return Response({
        'message': 'تم تحديث المهارات الفرعية بنجاح',
        'child_skills': [{'id': c.id, 'title': c.title, 'skill_type': c.skill_type} for c in children]
    }, status=status.HTTP_200_OK)

# ============================================
# SPEAKING VIEWS
# ============================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_speaking_video(request):
    """
    POST /api/step/speaking/videos/create/
    """
    from sabr_questions.models import SpeakingVideo

    data = request.data.copy()
    required_fields = ['title', 'video_file', 'step_skill']
    for field in required_fields:
        if field not in data:
            return Response({field: f'{field} مطلوب'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        skill = get_object_or_404(STEPSkill, id=data.get('step_skill'))
        if skill.skill_type not in ['SPEAKING', 'GENERAL_PATH']:
            return Response(
                {'error': 'هذه المهارة ليست من نوع Speaking'},
                status=status.HTTP_400_BAD_REQUEST
            )

        video = SpeakingVideo.objects.create(
            title=data.get('title'),
            video_file=data.get('video_file'),
            description=data.get('description', ''),
            duration=int(data.get('duration', 0)),
            usage_type='STEP',
            step_skill=skill,
            order=int(data.get('order', 0)),
            is_active=data.get('is_active', True),
            difficulty=data.get('difficulty', 'MEDIUM'),
        )

        return Response({
            'message': 'تم إنشاء الفيديو بنجاح',
            'video': {
                'id': video.id,
                'title': video.title,
                'video_file': str(video.video_file) if video.video_file else None,
                'description': video.description,
                'duration': video.duration,
                'created_at': video.created_at,
            }
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f"Error creating STEP speaking video: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_speaking_question(request, video_id):
    """
    POST /api/step/speaking/videos/{video_id}/questions/create/
    """
    from sabr_questions.models import SpeakingVideo, SpeakingQuestion

    try:
        video = SpeakingVideo.objects.get(id=video_id, usage_type='STEP')
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

        correct_answer = data.get('correct_answer')
        correct_letter = None
        for idx, option in enumerate(options):
            if option == correct_answer:
                correct_letter = chr(65 + idx)
                break

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
            'question': {
                'id': question.id,
                'question_text': question.question_text,
                'created_at': question.created_at,
            }
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f"Error creating STEP speaking question: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_speaking_video(request, video_id):
    """
    PUT/PATCH /api/step/speaking/videos/{video_id}/update/
    """
    from sabr_questions.models import SpeakingVideo

    video = get_object_or_404(SpeakingVideo, id=video_id, usage_type='STEP')
    data = request.data.copy()

    try:
        if 'title' in data:
            video.title = data['title']
        if 'video_file' in data:
            video.video_file = data['video_file']
        if 'description' in data:
            video.description = data['description']
        if 'duration' in data:
            video.duration = int(data['duration'])
        if 'is_active' in data:
            video.is_active = data['is_active']
        if 'difficulty' in data:
            video.difficulty = data['difficulty']

        video.save()
        return Response({
            'message': 'تم تحديث الفيديو بنجاح',
            'video': {'id': video.id, 'title': video.title}
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error updating speaking video: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_speaking_video(request, video_id):
    """
    DELETE /api/step/speaking/videos/{video_id}/delete/
    """
    from sabr_questions.models import SpeakingVideo

    video = get_object_or_404(SpeakingVideo, id=video_id, usage_type='STEP')
    video.delete()
    return Response({'message': 'تم حذف الفيديو وأسئلته بنجاح', 'video_id': video_id}, status=status.HTTP_200_OK)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_speaking_question(request, question_id):
    """
    PUT/PATCH /api/step/speaking/questions/{question_id}/update/
    """
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

        if 'question_text' in data:
            question.question_text = data['question_text']
        if 'explanation' in data:
            question.explanation = data['explanation']
        if 'points' in data:
            question.points = data['points']
        if 'is_active' in data:
            question.is_active = data['is_active']

        question.save()
        return Response({
            'message': 'تم تحديث السؤال بنجاح',
            'question': {'id': question.id, 'question_text': question.question_text}
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error updating speaking question: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_speaking_question(request, question_id):
    """
    DELETE /api/step/speaking/questions/{question_id}/delete/
    """
    from sabr_questions.models import SpeakingQuestion

    question = get_object_or_404(SpeakingQuestion, id=question_id)
    question.delete()
    return Response({'message': 'تم حذف السؤال بنجاح', 'question_id': question_id}, status=status.HTTP_200_OK)