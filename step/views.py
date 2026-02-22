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
    عرض جميع المهارات
    
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
    عرض تفاصيل مهارة
    
    GET /api/step/skills/{skill_id}/
    """
    skill = get_object_or_404(STEPSkill, id=skill_id)
    serializer = STEPSkillDetailSerializer(skill)
    
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_skill(request):
    """
    إنشاء مهارة جديدة
    
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
    تعديل مهارة
    
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
    حذف مهارة
    
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
    إنشاء سؤال Vocabulary جديد
    
    POST /api/step/vocabulary/create/
    """
    from sabr_questions.models import VocabularyQuestion, VocabularyQuestionSet
    
    data = request.data.copy()
    
    # التحقق من البيانات المطلوبة
    required_fields = ['question_text', 'options', 'correct_answer', 'step_skill']
    for field in required_fields:
        if field not in data:
            return Response(
                {field: f'{field} مطلوب'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    try:
        # التحقق من وجود المهارة
        skill = get_object_or_404(STEPSkill, id=data.get('step_skill'))
        if skill.skill_type != 'VOCABULARY':
            return Response(
                {'error': 'هذه المهارة ليست من نوع Vocabulary'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # تحويل options إلى choice_a, choice_b, choice_c, choice_d
        options = data.get('options', [])
        if len(options) < 2:
            return Response(
                {'options': 'يجب إضافة خيارين على الأقل'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create or get default question set for STEP
        question_set, _ = VocabularyQuestionSet.objects.get_or_create(
            title='STEP Vocabulary Questions',
            usage_type='STEP',
            defaults={'description': 'Auto-generated set for STEP'}
        )
        
        # معرفة الحرف الصحيح من الإجابة
        correct_answer = data.get('correct_answer')
        correct_letter = None
        for idx, option in enumerate(options):
            if option == correct_answer:
                correct_letter = chr(65 + idx)  # A, B, C, D
                break
        
        if not correct_letter:
            return Response(
                {'correct_answer': 'الإجابة الصحيحة غير موجودة في الخيارات'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # تحضير البيانات للـ model
        question_data = {
            'question_set': question_set,
            'question_text': data.get('question_text'),
            'choice_a': options[0] if len(options) > 0 else '',
            'choice_b': options[1] if len(options) > 1 else '',
            'choice_c': options[2] if len(options) > 2 else '',
            'choice_d': options[3] if len(options) > 3 else '',
            'correct_answer': correct_letter,
            'explanation': data.get('explanation', ''),
            'points': data.get('points', 1),
            'usage_type': 'STEP',
            'step_skill': skill,
            'is_active': data.get('is_active', True),
            'order': 0,
        }
        
        # إنشاء السؤال
        question = VocabularyQuestion.objects.create(**question_data)
        
        return Response({
            'message': 'تم إنشاء السؤال بنجاح',
            'question': {
                'id': question.id,
                'question_text': question.question_text,
                'created_at': question.created_at
            }
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error creating vocabulary question: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_grammar_question(request):
    """
    إنشاء سؤال Grammar جديد
    
    POST /api/step/grammar/create/
    """
    from sabr_questions.models import GrammarQuestion, GrammarQuestionSet
    
    data = request.data.copy()
    
    # التحقق من البيانات المطلوبة
    required_fields = ['question_text', 'options', 'correct_answer', 'step_skill']
    for field in required_fields:
        if field not in data:
            return Response(
                {field: f'{field} مطلوب'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    try:
        # التحقق من وجود المهارة
        skill = get_object_or_404(STEPSkill, id=data.get('step_skill'))
        if skill.skill_type != 'GRAMMAR':
            return Response(
                {'error': 'هذه المهارة ليست من نوع Grammar'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # تحويل options إلى choice_a, choice_b, choice_c, choice_d
        options = data.get('options', [])
        if len(options) < 2:
            return Response(
                {'options': 'يجب إضافة خيارين على الأقل'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create or get default question set for STEP
        question_set, _ = GrammarQuestionSet.objects.get_or_create(
            title='STEP Grammar Questions',
            usage_type='STEP',
            defaults={'description': 'Auto-generated set for STEP'}
        )
        
        # معرفة الحرف الصحيح من الإجابة
        correct_answer = data.get('correct_answer')
        correct_letter = None
        for idx, option in enumerate(options):
            if option == correct_answer:
                correct_letter = chr(65 + idx)  # A, B, C, D
                break
        
        if not correct_letter:
            return Response(
                {'correct_answer': 'الإجابة الصحيحة غير موجودة في الخيارات'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # تحضير البيانات للـ model
        question_data = {
            'question_set': question_set,
            'question_text': data.get('question_text'),
            'choice_a': options[0] if len(options) > 0 else '',
            'choice_b': options[1] if len(options) > 1 else '',
            'choice_c': options[2] if len(options) > 2 else '',
            'choice_d': options[3] if len(options) > 3 else '',
            'correct_answer': correct_letter,
            'explanation': data.get('explanation', ''),
            'points': data.get('points', 1),
            'usage_type': 'STEP',
            'step_skill': skill,
            'is_active': data.get('is_active', True),
            'order': 0,
        }
        
        # إنشاء السؤال
        question = GrammarQuestion.objects.create(**question_data)
        
        return Response({
            'message': 'تم إنشاء السؤال بنجاح',
            'question': {
                'id': question.id,
                'question_text': question.question_text,
                'created_at': question.created_at
            }
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error creating grammar question: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_reading_passage(request):
    """
    إنشاء قطعة قراءة جديدة
    
    POST /api/step/reading/passages/create/
    """
    from sabr_questions.models import ReadingPassage
    
    data = request.data.copy()
    
    # التحقق من البيانات المطلوبة
    required_fields = ['title', 'passage_text', 'step_skill']
    for field in required_fields:
        if field not in data:
            return Response(
                {field: f'{field} مطلوب'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    try:
        # التحقق من وجود المهارة
        skill = get_object_or_404(STEPSkill, id=data.get('step_skill'))
        if skill.skill_type != 'READING':
            return Response(
                {'error': 'هذه المهارة ليست من نوع Reading'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # تحضير البيانات للـ model
        passage_data = {
            'title': data.get('title'),
            'passage_text': data.get('passage_text'),
            'usage_type': 'STEP',
            'step_skill': skill,
            'is_active': data.get('is_active', True),
            'order': 0,
        }
        
        # إضافة الحقول الاختيارية
        if 'source' in data:
            passage_data['source'] = data.get('source')
        
        if 'passage_image' in data and data.get('passage_image'):
            passage_data['passage_image'] = data.get('passage_image')
        
        # إنشاء القطعة
        passage = ReadingPassage.objects.create(**passage_data)
        
        return Response({
            'message': 'تم إنشاء القطعة بنجاح',
            'passage': {
                'id': passage.id,
                'title': passage.title,
                'created_at': passage.created_at
            }
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error creating reading passage: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_reading_question(request, passage_id):
    """
    إنشاء سؤال قراءة جديد لقطعة معينة
    
    POST /api/step/reading/passages/{passage_id}/questions/create/
    """
    from sabr_questions.models import ReadingPassage, ReadingQuestion
    
    # التحقق من وجود القطعة
    try:
        passage = ReadingPassage.objects.get(id=passage_id, usage_type='STEP')
    except ReadingPassage.DoesNotExist:
        return Response(
            {'error': 'القطعة غير موجودة'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    data = request.data.copy()
    
    # التحقق من البيانات المطلوبة
    required_fields = ['question_text', 'options', 'correct_answer']
    for field in required_fields:
        if field not in data:
            return Response(
                {field: f'{field} مطلوب'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    try:
        # تحويل options إلى choice_a, choice_b, choice_c, choice_d
        options = data.get('options', [])
        if len(options) < 2:
            return Response(
                {'options': 'يجب إضافة خيارين على الأقل'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # معرفة الحرف الصحيح من الإجابة
        correct_answer = data.get('correct_answer')
        correct_letter = None
        for idx, option in enumerate(options):
            if option == correct_answer:
                correct_letter = chr(65 + idx)  # A, B, C, D
                break
        
        if not correct_letter:
            return Response(
                {'correct_answer': 'الإجابة الصحيحة غير موجودة في الخيارات'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # تحضير البيانات للـ model
        question_data = {
            'passage': passage,
            'question_text': data.get('question_text'),
            'choice_a': options[0] if len(options) > 0 else '',
            'choice_b': options[1] if len(options) > 1 else '',
            'choice_c': options[2] if len(options) > 2 else '',
            'choice_d': options[3] if len(options) > 3 else '',
            'correct_answer': correct_letter,
            'explanation': data.get('explanation', ''),
            'points': data.get('points', 1),
            'is_active': data.get('is_active', True),
            'order': 0,
        }
        
        # إنشاء السؤال
        question = ReadingQuestion.objects.create(**question_data)
        
        return Response({
            'message': 'تم إنشاء السؤال بنجاح',
            'question': {
                'id': question.id,
                'question_text': question.question_text,
                'created_at': question.created_at
            }
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error creating reading question: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_writing_question(request):
    """
    إنشاء سؤال كتابة جديد
    
    POST /api/step/writing/questions/create/
    """
    from sabr_questions.models import WritingQuestion
    
    data = request.data.copy()
    
    # التحقق من البيانات المطلوبة
    required_fields = ['title', 'question_text', 'min_words', 'max_words', 'sample_answer', 'rubric', 'step_skill']
    for field in required_fields:
        if field not in data:
            return Response(
                {field: f'{field} مطلوب'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    try:
        # التحقق من وجود المهارة
        skill = get_object_or_404(STEPSkill, id=data.get('step_skill'))
        if skill.skill_type != 'WRITING':
            return Response(
                {'error': 'هذه المهارة ليست من نوع Writing'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # التحقق من أن max_words أكبر من min_words
        min_words = int(data.get('min_words'))
        max_words = int(data.get('max_words'))
        
        if max_words <= min_words:
            return Response(
                {'error': 'الحد الأقصى للكلمات يجب أن يكون أكبر من الحد الأدنى'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # تحضير البيانات للـ model
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
        
        # إضافة الحقول الاختيارية
        if 'question_image' in data and data.get('question_image'):
            question_data['question_image'] = data.get('question_image')
        
        if 'pass_threshold' in data:
            question_data['pass_threshold'] = data.get('pass_threshold')
        
        # إنشاء السؤال
        question = WritingQuestion.objects.create(**question_data)
        
        return Response({
            'message': 'تم إنشاء السؤال بنجاح',
            'question': {
                'id': question.id,
                'title': question.title,
                'created_at': question.created_at
            }
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error creating writing question: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


# ============================================
# 3. QUESTIONS DISPLAY (للطالب)
# ============================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_skill_questions(request, skill_id):
    """
    عرض أسئلة المهارة (مع الحلول)
    
    GET /api/step/skills/{skill_id}/questions/?page=1&page_size=20
    """
    from sabr_questions.models import (
        VocabularyQuestion,
        GrammarQuestion,
        ReadingPassage,
        WritingQuestion
    )
    
    skill = get_object_or_404(STEPSkill, id=skill_id)
    
    page = int(request.query_params.get('page', 1))
    page_size = int(request.query_params.get('page_size', 20))
    
    questions_data = []
    
    # حسب نوع المهارة
    if skill.skill_type == 'VOCABULARY':
        questions = VocabularyQuestion.objects.filter(
            step_skill=skill,
            usage_type='STEP',
            is_active=True
        ).order_by('order', 'id')
        
        paginator = Paginator(questions, page_size)
        page_obj = paginator.get_page(page)
        
        for q in page_obj:
            questions_data.append({
                'id': q.id,
                'type': 'VOCABULARY',
                'question_text': q.question_text,
                'question_image': q.question_image.url if q.question_image else None,
                'choice_a': q.choice_a,
                'choice_b': q.choice_b,
                'choice_c': q.choice_c,
                'choice_d': q.choice_d,
                'correct_answer': q.correct_answer,
                'explanation': q.explanation,
                'points': q.points,
            })
    
    elif skill.skill_type == 'GRAMMAR':
        questions = GrammarQuestion.objects.filter(
            step_skill=skill,
            usage_type='STEP',
            is_active=True
        ).order_by('order', 'id')
        
        paginator = Paginator(questions, page_size)
        page_obj = paginator.get_page(page)
        
        for q in page_obj:
            questions_data.append({
                'id': q.id,
                'type': 'GRAMMAR',
                'question_text': q.question_text,
                'question_image': q.question_image.url if q.question_image else None,
                'choice_a': q.choice_a,
                'choice_b': q.choice_b,
                'choice_c': q.choice_c,
                'choice_d': q.choice_d,
                'correct_answer': q.correct_answer,
                'explanation': q.explanation,
                'points': q.points,
            })
    
    elif skill.skill_type == 'READING':
        passages = ReadingPassage.objects.filter(
            step_skill=skill,
            usage_type='STEP',
            is_active=True
        ).prefetch_related('questions').order_by('order', 'id')
        
        paginator = Paginator(passages, page_size)
        page_obj = paginator.get_page(page)
        
        for passage in page_obj:
            passage_questions = []
            for q in passage.questions.all():
                passage_questions.append({
                    'id': q.id,
                    'question_text': q.question_text,
                    'choice_a': q.choice_a,
                    'choice_b': q.choice_b,
                    'choice_c': q.choice_c,
                    'choice_d': q.choice_d,
                    'correct_answer': q.correct_answer,
                    'explanation': q.explanation,
                    'points': q.points,
                })
            
            questions_data.append({
                'id': passage.id,
                'type': 'READING',
                'title': passage.title,
                'passage_text': passage.passage_text,
                'passage_image': passage.passage_image.url if passage.passage_image else None,
                'source': passage.source,
                'questions': passage_questions,
            })
    
    elif skill.skill_type == 'WRITING':
        questions = WritingQuestion.objects.filter(
            step_skill=skill,
            usage_type='STEP',
            is_active=True
        ).order_by('order', 'id')
        
        paginator = Paginator(questions, page_size)
        page_obj = paginator.get_page(page)
        
        for q in page_obj:
            questions_data.append({
                'id': q.id,
                'type': 'WRITING',
                'title': q.title,
                'question_text': q.question_text,
                'question_image': q.question_image.url if q.question_image else None,
                'min_words': q.min_words,
                'max_words': q.max_words,
                'sample_answer': q.sample_answer,
                'rubric': q.rubric,
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
    تسجيل فتح السؤال وإضافة نقطة
    
    POST /api/step/skills/{skill_id}/questions/{question_type}/{question_id}/mark-viewed/
    
    question_type: VOCABULARY, GRAMMAR, READING, WRITING
    """
    skill = get_object_or_404(STEPSkill, id=skill_id)
    student = request.user
    
    # التحقق من question_type
    valid_types = ['VOCABULARY', 'GRAMMAR', 'READING', 'WRITING']
    if question_type not in valid_types:
        return Response(
            {'error': f'نوع السؤال غير صحيح. يجب أن يكون أحد: {", ".join(valid_types)}'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        with transaction.atomic():
            # محاولة إنشاء السجل (لو موجود هيرجع created=False)
            view_record, created = StudentSTEPQuestionView.objects.get_or_create(
                student=student,
                skill=skill,
                question_type=question_type,
                question_id=question_id
            )
            
            if created:
                # السؤال اتفتح لأول مرة - نضيف نقطة
                progress, _ = StudentSTEPProgress.objects.get_or_create(
                    student=student,
                    skill=skill
                )
                progress.increment_score()
                
                return Response({
                    'message': 'تم تسجيل فتح السؤال وإضافة نقطة',
                    'points_earned': 1,
                    'total_score': progress.total_score,
                    'progress_percentage': progress.calculate_progress_percentage()
                }, status=status.HTTP_201_CREATED)
            else:
                # السؤال اتفتح قبل كده
                progress = StudentSTEPProgress.objects.get(
                    student=student,
                    skill=skill
                )
                
                return Response({
                    'message': 'السؤال تم فتحه من قبل',
                    'points_earned': 0,
                    'total_score': progress.total_score,
                    'progress_percentage': progress.calculate_progress_percentage()
                }, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Error marking question viewed: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


# ============================================
# 4. STUDENT PROGRESS
# ============================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_progress(request):
    """
    عرض تقدم الطالب في جميع المهارات
    
    GET /api/step/my-progress/
    """
    student = request.user
    
    # الحصول على تقدم الطالب في كل المهارات
    progress_records = StudentSTEPProgress.objects.filter(
        student=student
    ).select_related('skill').order_by('skill__order')
    
    progress_serializer = StudentSTEPProgressSerializer(progress_records, many=True)
    
    # إحصائيات عامة
    total_score = sum(p.total_score for p in progress_records)
    total_viewed = sum(p.viewed_questions_count for p in progress_records)
    
    # حساب إجمالي الأسئلة المتاحة
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
    عرض تقدم الطالب في مهارة معينة
    
    GET /api/step/skills/{skill_id}/my-progress/
    """
    skill = get_object_or_404(STEPSkill, id=skill_id)
    student = request.user
    
    try:
        progress = StudentSTEPProgress.objects.get(
            student=student,
            skill=skill
        )
        serializer = StudentSTEPProgressSerializer(progress)
        
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    except StudentSTEPProgress.DoesNotExist:
        # لو الطالب لسه مفتحش أي سؤال في المهارة دي
        return Response({
            'skill': {
                'id': skill.id,
                'title': skill.title,
                'skill_type': skill.skill_type,
            },
            'viewed_questions_count': 0,
            'total_questions': skill.get_total_questions_count(),
            'progress_percentage': 0,
            'total_score': 0,
        }, status=status.HTTP_200_OK)