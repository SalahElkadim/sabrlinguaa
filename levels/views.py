from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
import random
import json
from cloudinary.models import CloudinaryResource
from placement_test.services.exam_service import exam_service
from placement_test.services.ai_grading import ai_grading_service
from levels.models import (
    Level, Unit, Lesson,
    ReadingLessonContent, ListeningLessonContent,
    SpeakingLessonContent, WritingLessonContent,
    UnitExam, LevelExam,
    StudentLevel, StudentUnit, StudentLesson,
    StudentUnitExamAttempt, StudentLevelExamAttempt,
    LevelsUnitsQuestionBank
)

from levels.serializers import (
    # Level Serializers
    LevelListSerializer, LevelDetailSerializer, LevelCreateUpdateSerializer,
    # Unit Serializers
    UnitDetailSerializer, UnitCreateUpdateSerializer,
    # Lesson Serializers
    LessonDetailSerializer, LessonCreateUpdateSerializer,
    # Lesson Content Serializers
    ReadingLessonContentSerializer, ReadingLessonContentCreateUpdateSerializer,
    ListeningLessonContentSerializer, ListeningLessonContentCreateUpdateSerializer,
    SpeakingLessonContentSerializer, SpeakingLessonContentCreateUpdateSerializer,
    WritingLessonContentSerializer, WritingLessonContentCreateUpdateSerializer,
    # Exam Serializers
    UnitExamSerializer, UnitExamCreateUpdateSerializer,
    LevelExamSerializer, LevelExamCreateUpdateSerializer,
    # Progress Serializers
    StudentLevelSerializer, StudentUnitSerializer, StudentLessonSerializer,
    # Question Bank Serializers
    LevelsUnitsQuestionBankListSerializer, LevelsUnitsQuestionBankDetailSerializer, LevelsUnitsQuestionBankCreateUpdateSerializer,
    # Exam Attempt Serializers
    StudentUnitExamAttemptSerializer, StudentLevelExamAttemptSerializer
)

from sabr_questions.models import (
    VocabularyQuestion, VocabularyQuestionSet,
    GrammarQuestion, GrammarQuestionSet,
    ReadingPassage, ReadingQuestion,
    ListeningAudio, ListeningQuestion,
    SpeakingVideo, SpeakingQuestion,
    WritingQuestion
)

import logging
logger = logging.getLogger(__name__)


# ============================================
# 1. LEVEL CRUD OPERATIONS
# ============================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_level(request):
    """
    إنشاء مستوى جديد
    
    POST /api/levels/create/
    
    Body:
    {
        "code": "A1",
        "title": "Beginner Level",
        "description": "Starting level for English learners",
        "order": 1,
        "is_active": true
    }
    """
    serializer = LevelCreateUpdateSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    with transaction.atomic():
        level = serializer.save()
        
        # ✅ إنشاء LevelsUnitsQuestionBank تلقائياً للمستوى
        LevelsUnitsQuestionBank.objects.create(
            level=level,
            title=f"Question Bank - {level.code}",
            description=f"Automatically created for Level {level.code}"
        )
    
    result_serializer = LevelDetailSerializer(level)
    
    return Response({
        'message': 'تم إنشاء المستوى بنجاح',
        'level': result_serializer.data
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_levels(request):
    """
    عرض جميع المستويات
    
    GET /api/levels/
    """
    levels = Level.objects.filter(is_active=True).order_by('order', 'code')
    serializer = LevelListSerializer(levels, many=True)
    
    return Response({
        'total_levels': levels.count(),
        'levels': serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_level(request, level_id):
    """
    عرض تفاصيل مستوى معين
    
    GET /api/levels/{level_id}/
    """
    level = get_object_or_404(Level, id=level_id)
    serializer = LevelDetailSerializer(level)
    
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_level(request, level_id):
    """
    تعديل مستوى
    
    PUT /api/levels/{level_id}/update/
    PATCH /api/levels/{level_id}/update/
    """
    level = get_object_or_404(Level, id=level_id)
    
    partial = request.method == 'PATCH'
    serializer = LevelCreateUpdateSerializer(level, data=request.data, partial=partial)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    level = serializer.save()
    result_serializer = LevelDetailSerializer(level)
    
    return Response({
        'message': 'تم تحديث المستوى بنجاح',
        'level': result_serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_level(request, level_id):
    """
    حذف مستوى
    
    DELETE /api/levels/{level_id}/delete/
    """
    level = get_object_or_404(Level, id=level_id)
    
    code = level.code
    title = level.title
    level.delete()
    
    return Response({
        'message': 'تم حذف المستوى بنجاح',
        'level_id': level_id,
        'code': code,
        'title': title
    }, status=status.HTTP_200_OK)


# ============================================
# 2. UNIT CRUD OPERATIONS
# ============================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_unit(request):
    """
    إنشاء وحدة جديدة (مع إنشاء LevelsUnitsQuestionBank تلقائياً)
    
    POST /api/units/create/
    
    Body:
    {
        "level": 1,
        "title": "Introduction to English",
        "description": "First unit for beginners",
        "order": 1,
        "is_active": true
    }
    """
    serializer = UnitCreateUpdateSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # الـ create method في الـ Serializer بيعمل LevelsUnitsQuestionBank تلقائياً
    unit = serializer.save()
    result_serializer = UnitDetailSerializer(unit)
    
    return Response({
        'message': 'تم إنشاء الوحدة بنجاح (مع بنك الأسئلة)',
        'unit': result_serializer.data
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_units(request):
    """
    عرض جميع الوحدات
    
    GET /api/units/
    
    Query Parameters:
    - level_id: filter by level
    """
    level_id = request.query_params.get('level_id', None)
    
    units = Unit.objects.filter(is_active=True).select_related('level')
    
    if level_id:
        units = units.filter(level_id=level_id)
    
    units = units.order_by('level__order', 'order', 'id')
    
    serializer = UnitDetailSerializer(units, many=True)
    
    return Response({
        'total_units': units.count(),
        'units': serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_unit(request, unit_id):
    """
    عرض تفاصيل وحدة معينة
    
    GET /api/units/{unit_id}/
    """
    unit = get_object_or_404(Unit, id=unit_id)
    serializer = UnitDetailSerializer(unit)
    
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_unit(request, unit_id):
    """
    تعديل وحدة
    
    PUT /api/units/{unit_id}/update/
    PATCH /api/units/{unit_id}/update/
    """
    unit = get_object_or_404(Unit, id=unit_id)
    
    partial = request.method == 'PATCH'
    serializer = UnitCreateUpdateSerializer(unit, data=request.data, partial=partial)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    unit = serializer.save()
    result_serializer = UnitDetailSerializer(unit)
    
    return Response({
        'message': 'تم تحديث الوحدة بنجاح',
        'unit': result_serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_unit(request, unit_id):
    """
    حذف وحدة
    
    DELETE /api/units/{unit_id}/delete/
    """
    unit = get_object_or_404(Unit, id=unit_id)
    
    title = unit.title
    unit.delete()
    
    return Response({
        'message': 'تم حذف الوحدة بنجاح',
        'unit_id': unit_id,
        'title': title
    }, status=status.HTTP_200_OK)


# ============================================
# 3. LESSON CRUD OPERATIONS
# ============================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_lesson(request):
    """
    إنشاء درس جديد
    
    POST /api/lessons/create/
    
    Body:
    {
        "unit": 1,
        "lesson_type": "READING",
        "title": "Reading about animals",
        "order": 1,
        "is_active": true
    }
    """
    serializer = LessonCreateUpdateSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    lesson = serializer.save()
    result_serializer = LessonDetailSerializer(lesson)
    
    return Response({
        'message': 'تم إنشاء الدرس بنجاح',
        'lesson': result_serializer.data,
        'note': 'يجب إضافة المحتوى للدرس من endpoints المحتوى'
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_lessons(request):
    """
    عرض جميع الدروس
    
    GET /api/lessons/
    
    Query Parameters:
    - unit_id: filter by unit
    - lesson_type: filter by type (READING, LISTENING, SPEAKING, WRITING)
    """
    unit_id = request.query_params.get('unit_id', None)
    lesson_type = request.query_params.get('lesson_type', None)
    
    lessons = Lesson.objects.filter(is_active=True).select_related('unit', 'unit__level')
    
    if unit_id:
        lessons = lessons.filter(unit_id=unit_id)
    
    if lesson_type:
        lessons = lessons.filter(lesson_type=lesson_type)
    
    lessons = lessons.order_by('unit__level__order', 'unit__order', 'order', 'id')
    
    serializer = LessonDetailSerializer(lessons, many=True)
    
    return Response({
        'total_lessons': lessons.count(),
        'lessons': serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_lesson(request, lesson_id):
    """
    عرض تفاصيل درس معين
    
    GET /api/lessons/{lesson_id}/
    """
    lesson = get_object_or_404(Lesson, id=lesson_id)
    serializer = LessonDetailSerializer(lesson)
    
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_lesson(request, lesson_id):
    """
    تعديل درس
    
    PUT /api/lessons/{lesson_id}/update/
    PATCH /api/lessons/{lesson_id}/update/
    """
    lesson = get_object_or_404(Lesson, id=lesson_id)
    
    partial = request.method == 'PATCH'
    serializer = LessonCreateUpdateSerializer(lesson, data=request.data, partial=partial)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    lesson = serializer.save()
    result_serializer = LessonDetailSerializer(lesson)
    
    return Response({
        'message': 'تم تحديث الدرس بنجاح',
        'lesson': result_serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_lesson(request, lesson_id):
    """
    حذف درس
    
    DELETE /api/lessons/{lesson_id}/delete/
    """
    lesson = get_object_or_404(Lesson, id=lesson_id)
    
    title = lesson.title
    lesson.delete()
    
    return Response({
        'message': 'تم حذف الدرس بنجاح',
        'lesson_id': lesson_id,
        'title': title
    }, status=status.HTTP_200_OK)
# ============================================
# 4. LESSON CONTENT CRUD OPERATIONS
# ============================================
# ============================================
# LESSON CONTENT - DIRECT CREATION (بدون Question Bank)
# ============================================

from sabr_questions.serializers import (
    ReadingPassageSerializer,
    ListeningAudioSerializer,
    SpeakingVideoSerializer
)

# ============================================
# READING LESSON CONTENT (CRUD)
# ============================================
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_reading_lesson_content_with_passage(request):
    """
    إنشاء محتوى درس قراءة + إنشاء القطعة + الأسئلة المحلولة
    
    POST /api/lesson-content/reading/create-with-passage/
    
    Body:
    {
        "lesson": 1,
        "passage_data": {
            "title": "My Family",
            "passage_text": "I have a big family...",
            "passage_image": null,
            "source": "Teacher Created",
            "order": 1
        },
        "questions": [  // ← 🆕 الأسئلة المحلولة
            {
                "question_text": "How many people are in the family?",
                "question_image": null,
                "choice_a": "3",
                "choice_b": "5",
                "choice_c": "7",
                "choice_d": "10",
                "correct_answer": "B",
                "explanation": "The family has 5 members",
                "points": 1,
                "order": 1
            }
        ],
        "vocabulary_words": [
            {"english_word": "family", "translate": "عائلة"}
        ],
        "explanation": "شرح الدرس..."
    }
    """
    lesson_id = request.data.get('lesson')
    passage_data = request.data.get('passage_data')
    questions_data = request.data.get('questions', [])  # 🆕
    vocabulary_words = request.data.get('vocabulary_words', [])
    explanation = request.data.get('explanation', '')
    
    if not lesson_id or not passage_data:
        return Response({
            'error': 'يجب إرسال lesson و passage_data'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    lesson = get_object_or_404(Lesson, id=lesson_id)
    
    if lesson.lesson_type != 'READING':
        return Response({
            'error': 'الدرس يجب أن يكون من نوع READING'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # التحقق من عدم وجود محتوى مسبق
    if hasattr(lesson, 'reading_content'):
        return Response({
            'error': 'هذا الدرس يحتوي على محتوى بالفعل'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    with transaction.atomic():
        # 1. إنشاء ReadingPassage
        reading_passage = ReadingPassage.objects.create(
            usage_type='LESSON',
            lesson=lesson,
            levels_units_question_bank=None,
            **passage_data
        )
        
        # 🆕 2. إنشاء الأسئلة المحلولة
        created_questions = []
        for q_data in questions_data:
            question = ReadingQuestion.objects.create(
                passage=reading_passage,
                **q_data
            )
            created_questions.append(question)
        
        # 3. إنشاء ReadingLessonContent
        reading_content = ReadingLessonContent.objects.create(
            lesson=lesson,
            passage=reading_passage,
            vocabulary_words=vocabulary_words,
            explanation=explanation
        )
    
    result_serializer = ReadingLessonContentSerializer(reading_content)
    
    return Response({
        'message': 'تم إنشاء محتوى درس القراءة والقطعة والأسئلة بنجاح',
        'content': result_serializer.data,
        'questions_created': len(created_questions)  # 🆕
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_reading_lesson_content_with_passage(request, lesson_id):
    """
    عرض محتوى درس القراءة مع القطعة
    
    GET /api/lesson-content/reading/{lesson_id}/with-passage/
    """
    content = get_object_or_404(ReadingLessonContent, lesson_id=lesson_id)
    serializer = ReadingLessonContentSerializer(content)
    
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_reading_lesson_content_with_passage(request, lesson_id):
    """
    تعديل محتوى درس القراءة والقطعة والأسئلة
    
    PUT/PATCH /api/lesson-content/reading/{lesson_id}/update-with-passage/
    
    Body:
    {
        "passage_data": {
            "title": "My Family (Updated)",
            "passage_text": "Updated text...",
            "source": "Teacher Updated"
        },
        "questions": [  // ← 🆕 يمكن إضافة/تعديل/حذف
            {
                "id": 1,  // موجود = تعديل
                "question_text": "Updated question?",
                "choice_a": "A",
                "choice_b": "B",
                "choice_c": "C",
                "choice_d": "D",
                "correct_answer": "A"
            },
            {
                // بدون id = سؤال جديد
                "question_text": "New question?",
                "choice_a": "A",
                "choice_b": "B",
                "choice_c": "C",
                "choice_d": "D",
                "correct_answer": "B"
            }
        ],
        "vocabulary_words": [...],
        "explanation": "شرح محدث..."
    }
    """
    content = get_object_or_404(ReadingLessonContent, lesson_id=lesson_id)
    
    passage_data = request.data.get('passage_data')
    questions_data = request.data.get('questions')  # 🆕
    vocabulary_words = request.data.get('vocabulary_words')
    explanation = request.data.get('explanation')
    
    with transaction.atomic():
        # 1. تحديث القطعة
        if passage_data:
            for key, value in passage_data.items():
                setattr(content.passage, key, value)
            content.passage.save()
        
        # 🆕 2. تحديث الأسئلة
        if questions_data is not None:
            # جمع IDs الأسئلة الجديدة/المُحدثة
            updated_question_ids = []
            
            for q_data in questions_data:
                question_id = q_data.pop('id', None)
                
                if question_id:
                    # تحديث سؤال موجود
                    question = ReadingQuestion.objects.filter(
                        id=question_id,
                        passage=content.passage
                    ).first()
                    
                    if question:
                        for key, value in q_data.items():
                            setattr(question, key, value)
                        question.save()
                        updated_question_ids.append(question.id)
                else:
                    # إنشاء سؤال جديد
                    question = ReadingQuestion.objects.create(
                        passage=content.passage,
                        **q_data
                    )
                    updated_question_ids.append(question.id)
            
            # حذف الأسئلة اللي مش موجودة في الـ request
            ReadingQuestion.objects.filter(
                passage=content.passage
            ).exclude(id__in=updated_question_ids).delete()
        
        # 3. تحديث المحتوى
        if vocabulary_words is not None:
            content.vocabulary_words = vocabulary_words
        
        if explanation is not None:
            content.explanation = explanation
        
        content.save()
    
    result_serializer = ReadingLessonContentSerializer(content)
    
    return Response({
        'message': 'تم تحديث محتوى درس القراءة بنجاح',
        'content': result_serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_reading_lesson_content_with_passage(request, lesson_id):
    """
    حذف محتوى درس القراءة والقطعة
    
    DELETE /api/lesson-content/reading/{lesson_id}/delete-with-passage/
    """
    content = get_object_or_404(ReadingLessonContent, lesson_id=lesson_id)
    
    with transaction.atomic():
        # حذف القطعة أولاً
        passage_title = content.passage.title
        content.passage.delete()
        
        # حذف المحتوى
        content.delete()
    
    return Response({
        'message': 'تم حذف محتوى درس القراءة والقطعة بنجاح',
        'deleted_passage': passage_title
    }, status=status.HTTP_200_OK)


# ============================================
# LISTENING LESSON CONTENT (CRUD)
# ============================================
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_listening_lesson_content_with_audio(request):
    """
    إنشاء محتوى درس استماع + إنشاء التسجيل + الأسئلة المحلولة
    
    POST /api/lesson-content/listening/create-with-audio/
    
    Body (JSON):
    {
        "lesson": 2,
        "title": "Conversation at Restaurant",
        "audio_file": "https://res.cloudinary.com/dyxozpomy/video/upload/v123/audio.mp3",
        "transcript": "Waiter: Good morning...",
        "duration": "120",
        "order": "1",
        "questions": [  // ← 🆕 الأسئلة المحلولة
            {
                "question_text": "What did the customer order?",
                "choice_a": "Coffee",
                "choice_b": "Tea",
                "choice_c": "Water",
                "choice_d": "Juice",
                "correct_answer": "A",
                "explanation": "The customer ordered coffee",
                "points": 1,
                "order": 1
            }
        ],
        "explanation": "شرح الدرس..."
    }
    """
    lesson_id = request.data.get('lesson')
    explanation = request.data.get('explanation', '')
    questions_data = request.data.get('questions', [])  # 🆕
    
    # بيانات الصوت
    title = request.data.get('title')
    audio_url = request.data.get('audio_file')
    transcript = request.data.get('transcript', '')
    duration = request.data.get('duration', '0')
    order = request.data.get('order', '0')
    
    if not lesson_id or not title or not audio_url:
        return Response({
            'error': 'يجب إرسال lesson و title و audio_file'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    lesson = get_object_or_404(Lesson, id=lesson_id)
    
    if lesson.lesson_type != 'LISTENING':
        return Response({
            'error': 'الدرس يجب أن يكون من نوع LISTENING'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if hasattr(lesson, 'listening_content'):
        return Response({
            'error': 'هذا الدرس يحتوي على محتوى بالفعل'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        with transaction.atomic():
            # 1. إنشاء ListeningAudio
            listening_audio = ListeningAudio(
                usage_type='LESSON',
                lesson=lesson,
                levels_units_question_bank=None,
                title=title,
                transcript=transcript,
                duration=int(duration) if duration else 0,
                order=int(order) if order else 0
            )
            
            # تعيين الـ CloudinaryField يدوياً
            if 'cloudinary.com' in audio_url:
                parts = audio_url.split('/upload/')
                if len(parts) > 1:
                    public_id = parts[1].split('/')
                    public_id = '/'.join(public_id[1:])
                    public_id = public_id.rsplit('.', 1)[0]
                else:
                    public_id = 'listening/audio/default'
            else:
                public_id = 'listening/audio/default'
            
            listening_audio.audio_file = CloudinaryResource(
                public_id=public_id,
                format='mp3',
                resource_type='video'
            )
            
            listening_audio.save()
            
            # 🆕 2. إنشاء الأسئلة المحلولة
            created_questions = []
            for q_data in questions_data:
                question = ListeningQuestion.objects.create(
                    audio=listening_audio,
                    **q_data
                )
                created_questions.append(question)
            
            # 3. إنشاء ListeningLessonContent
            listening_content = ListeningLessonContent.objects.create(
                lesson=lesson,
                audio=listening_audio,
                explanation=explanation
            )
        
        result_serializer = ListeningLessonContentSerializer(listening_content)
        
        return Response({
            'message': 'تم إنشاء محتوى درس الاستماع والتسجيل والأسئلة بنجاح',
            'content': result_serializer.data,
            'questions_created': len(created_questions)  # 🆕
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({
            'error': f'حدث خطأ أثناء الحفظ: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_listening_lesson_content_with_audio(request, lesson_id):
    """
    عرض محتوى درس الاستماع مع التسجيل
    
    GET /api/lesson-content/listening/{lesson_id}/with-audio/
    """
    content = get_object_or_404(ListeningLessonContent, lesson_id=lesson_id)
    serializer = ListeningLessonContentSerializer(content)
    
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_listening_lesson_content_with_audio(request, lesson_id):
    """
    تعديل محتوى درس الاستماع والتسجيل والأسئلة
    
    PUT/PATCH /api/lesson-content/listening/{lesson_id}/update-with-audio/
    
    Body (JSON):
    {
        "title": "Updated Title",
        "audio_file": "https://res.cloudinary.com/...",  // اختياري
        "transcript": "Updated transcript...",
        "duration": "150",
        "questions": [  // ← 🆕
            {
                "id": 1,  // موجود = تعديل
                "question_text": "Updated question?"
            },
            {
                // بدون id = سؤال جديد
                "question_text": "New question?",
                "choice_a": "A",
                "choice_b": "B",
                "choice_c": "C",
                "choice_d": "D",
                "correct_answer": "A"
            }
        ],
        "explanation": "شرح محدث..."
    }
    """
    content = get_object_or_404(ListeningLessonContent, lesson_id=lesson_id)
    
    # بيانات الصوت
    title = request.data.get('title')
    audio_file = request.data.get('audio_file')
    transcript = request.data.get('transcript')
    duration = request.data.get('duration')
    questions_data = request.data.get('questions')  # 🆕
    explanation = request.data.get('explanation')
    
    try:
        with transaction.atomic():
            # 1. تحديث الصوت
            if title:
                content.audio.title = title
            if audio_file:
                content.audio.audio_file = audio_file
            if transcript is not None:
                content.audio.transcript = transcript
            if duration:
                content.audio.duration = int(duration)
            
            content.audio.save()
            
            # 🆕 2. تحديث الأسئلة
            if questions_data is not None:
                updated_question_ids = []
                
                for q_data in questions_data:
                    question_id = q_data.pop('id', None)
                    
                    if question_id:
                        # تحديث سؤال موجود
                        question = ListeningQuestion.objects.filter(
                            id=question_id,
                            audio=content.audio
                        ).first()
                        
                        if question:
                            for key, value in q_data.items():
                                setattr(question, key, value)
                            question.save()
                            updated_question_ids.append(question.id)
                    else:
                        # إنشاء سؤال جديد
                        question = ListeningQuestion.objects.create(
                            audio=content.audio,
                            **q_data
                        )
                        updated_question_ids.append(question.id)
                
                # حذف الأسئلة المحذوفة
                ListeningQuestion.objects.filter(
                    audio=content.audio
                ).exclude(id__in=updated_question_ids).delete()
            
            # 3. تحديث المحتوى
            if explanation is not None:
                content.explanation = explanation
            
            content.save()
        
        result_serializer = ListeningLessonContentSerializer(content)
        
        return Response({
            'message': 'تم تحديث محتوى درس الاستماع بنجاح',
            'content': result_serializer.data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': f'حدث خطأ أثناء التحديث: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_listening_lesson_content_with_audio(request, lesson_id):
    """
    حذف محتوى درس الاستماع والتسجيل
    
    DELETE /api/lesson-content/listening/{lesson_id}/delete-with-audio/
    """
    content = get_object_or_404(ListeningLessonContent, lesson_id=lesson_id)
    
    try:
        with transaction.atomic():
            audio_title = content.audio.title
            content.audio.delete()
            content.delete()
        
        return Response({
            'message': 'تم حذف محتوى درس الاستماع والتسجيل بنجاح',
            'deleted_audio': audio_title
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': f'حدث خطأ أثناء الحذف: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ============================================
# SPEAKING LESSON CONTENT (CRUD)
# ============================================
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_speaking_lesson_content_with_video(request):
    """
    إنشاء محتوى درس تحدث + إنشاء الفيديو + الأسئلة المحلولة
    
    POST /api/lesson-content/speaking/create-with-video/
    
    Body (JSON):
    {
        "lesson": 3,
        "title": "How to introduce yourself",
        "video_file": "https://res.cloudinary.com/dyxozpomy/video/upload/v123/video.mp4",
        "description": "Learn self introduction",
        "duration": "180",
        "thumbnail": "https://res.cloudinary.com/dyxozpomy/image/upload/v123/thumb.jpg",
        "order": "1",
        "questions": [  // ← 🆕 الأسئلة المحلولة
            {
                "question_text": "What should you say first?",
                "choice_a": "My name is...",
                "choice_b": "Goodbye",
                "choice_c": "Thank you",
                "choice_d": "Sorry",
                "correct_answer": "A",
                "points": 1,
                "order": 1
            }
        ],
        "explanation": "شرح الدرس..."
    }
    """
    lesson_id = request.data.get('lesson')
    explanation = request.data.get('explanation', '')
    questions_data = request.data.get('questions', [])  # 🆕
    
    # بيانات الفيديو
    title = request.data.get('title')
    video_url = request.data.get('video_file')
    description = request.data.get('description', '')
    duration = request.data.get('duration', '0')
    thumbnail_url = request.data.get('thumbnail')
    order = request.data.get('order', '0')
    
    if not lesson_id or not title or not video_url:
        return Response({
            'error': 'يجب إرسال lesson و title و video_file'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    lesson = get_object_or_404(Lesson, id=lesson_id)
    
    if lesson.lesson_type != 'SPEAKING':
        return Response({
            'error': 'الدرس يجب أن يكون من نوع SPEAKING'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if hasattr(lesson, 'speaking_content'):
        return Response({
            'error': 'هذا الدرس يحتوي على محتوى بالفعل'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        with transaction.atomic():
            # 1. إنشاء SpeakingVideo
            speaking_video = SpeakingVideo(
                usage_type='LESSON',
                lesson=lesson,
                levels_units_question_bank=None,
                title=title,
                description=description,
                duration=int(duration) if duration else 0,
                order=int(order) if order else 0
            )
            
            # تعيين الـ video_file من Cloudinary URL
            if 'cloudinary.com' in video_url:
                parts = video_url.split('/upload/')
                if len(parts) > 1:
                    public_id = parts[1].split('/')
                    public_id = '/'.join(public_id[1:])
                    public_id = public_id.rsplit('.', 1)[0]
                else:
                    public_id = 'speaking/videos/default'
            else:
                public_id = 'speaking/videos/default'
            
            from cloudinary.models import CloudinaryResource
            speaking_video.video_file = CloudinaryResource(
                public_id=public_id,
                format='mp4',
                resource_type='video'
            )
            
            # إضافة Thumbnail إذا كان موجود
            if thumbnail_url and 'cloudinary.com' in thumbnail_url:
                parts = thumbnail_url.split('/upload/')
                if len(parts) > 1:
                    thumb_public_id = parts[1].split('/')
                    thumb_public_id = '/'.join(thumb_public_id[1:])
                    thumb_public_id = thumb_public_id.rsplit('.', 1)[0]
                else:
                    thumb_public_id = 'speaking/thumbnails/default'
                
                speaking_video.thumbnail = CloudinaryResource(
                    public_id=thumb_public_id,
                    format='jpg',
                    resource_type='image'
                )
            
            speaking_video.save()
            
            # 🆕 2. إنشاء الأسئلة المحلولة
            created_questions = []
            for q_data in questions_data:
                question = SpeakingQuestion.objects.create(
                    video=speaking_video,
                    **q_data
                )
                created_questions.append(question)
            
            # 3. إنشاء SpeakingLessonContent
            speaking_content = SpeakingLessonContent.objects.create(
                lesson=lesson,
                video=speaking_video,
                explanation=explanation
            )
        
        result_serializer = SpeakingLessonContentSerializer(speaking_content)
        
        return Response({
            'message': 'تم إنشاء محتوى درس التحدث والفيديو والأسئلة بنجاح',
            'content': result_serializer.data,
            'questions_created': len(created_questions)  # 🆕
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({
            'error': f'حدث خطأ أثناء الحفظ: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_speaking_lesson_content_with_video(request, lesson_id):
    """
    تعديل محتوى درس التحدث والفيديو والأسئلة
    
    PUT/PATCH /api/lesson-content/speaking/{lesson_id}/update-with-video/
    
    Body (JSON):
    {
        "title": "Updated Title",
        "video_file": "https://res.cloudinary.com/...",  // اختياري
        "description": "Updated description...",
        "duration": "200",
        "thumbnail": "https://res.cloudinary.com/...",  // اختياري
        "questions": [  // ← 🆕
            {
                "id": 1,
                "question_text": "Updated question?"
            },
            {
                "question_text": "New question?",
                "choice_a": "A",
                "choice_b": "B",
                "choice_c": "C",
                "choice_d": "D",
                "correct_answer": "B"
            }
        ],
        "explanation": "شرح محدث..."
    }
    """
    content = get_object_or_404(SpeakingLessonContent, lesson_id=lesson_id)
    
    title = request.data.get('title')
    video_url = request.data.get('video_file')
    description = request.data.get('description')
    duration = request.data.get('duration')
    thumbnail_url = request.data.get('thumbnail')
    questions_data = request.data.get('questions')  # 🆕
    explanation = request.data.get('explanation')
    
    try:
        with transaction.atomic():
            # 1. تحديث الفيديو
            if title:
                content.video.title = title
            
            if video_url and 'cloudinary.com' in video_url:
                parts = video_url.split('/upload/')
                if len(parts) > 1:
                    public_id = parts[1].split('/')
                    public_id = '/'.join(public_id[1:])
                    public_id = public_id.rsplit('.', 1)[0]
                    
                    from cloudinary.models import CloudinaryResource
                    content.video.video_file = CloudinaryResource(
                        public_id=public_id,
                        format='mp4',
                        resource_type='video'
                    )
            
            if description is not None:
                content.video.description = description
            
            if duration:
                content.video.duration = int(duration)
            
            if thumbnail_url and 'cloudinary.com' in thumbnail_url:
                parts = thumbnail_url.split('/upload/')
                if len(parts) > 1:
                    thumb_public_id = parts[1].split('/')
                    thumb_public_id = '/'.join(thumb_public_id[1:])
                    thumb_public_id = thumb_public_id.rsplit('.', 1)[0]
                    
                    from cloudinary.models import CloudinaryResource
                    content.video.thumbnail = CloudinaryResource(
                        public_id=thumb_public_id,
                        format='jpg',
                        resource_type='image'
                    )
            
            content.video.save()
            
            # 🆕 2. تحديث الأسئلة
            if questions_data is not None:
                updated_question_ids = []
                
                for q_data in questions_data:
                    question_id = q_data.pop('id', None)
                    
                    if question_id:
                        # تحديث سؤال موجود
                        question = SpeakingQuestion.objects.filter(
                            id=question_id,
                            video=content.video
                        ).first()
                        
                        if question:
                            for key, value in q_data.items():
                                setattr(question, key, value)
                            question.save()
                            updated_question_ids.append(question.id)
                    else:
                        # إنشاء سؤال جديد
                        question = SpeakingQuestion.objects.create(
                            video=content.video,
                            **q_data
                        )
                        updated_question_ids.append(question.id)
                
                # حذف الأسئلة المحذوفة
                SpeakingQuestion.objects.filter(
                    video=content.video
                ).exclude(id__in=updated_question_ids).delete()
            
            # 3. تحديث المحتوى
            if explanation is not None:
                content.explanation = explanation
            
            content.save()
        
        result_serializer = SpeakingLessonContentSerializer(content)
        
        return Response({
            'message': 'تم تحديث محتوى درس التحدث بنجاح',
            'content': result_serializer.data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({
            'error': f'حدث خطأ أثناء التحديث: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_speaking_lesson_content_with_video(request, lesson_id):
    """
    عرض محتوى درس التحدث مع الفيديو
    
    GET /api/lesson-content/speaking/{lesson_id}/with-video/
    """
    content = get_object_or_404(SpeakingLessonContent, lesson_id=lesson_id)
    serializer = SpeakingLessonContentSerializer(content)
    
    return Response(serializer.data, status=status.HTTP_200_OK)



@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_speaking_lesson_content_with_video(request, lesson_id):
    """
    حذف محتوى درس التحدث والفيديو
    
    DELETE /api/lesson-content/speaking/{lesson_id}/delete-with-video/
    """
    content = get_object_or_404(SpeakingLessonContent, lesson_id=lesson_id)
    
    with transaction.atomic():
        video_title = content.video.title
        content.video.delete()
        content.delete()
    
    return Response({
        'message': 'تم حذف محتوى درس التحدث والفيديو بنجاح',
        'deleted_video': video_title
    }, status=status.HTTP_200_OK)

# ---------- 4.4 Writing Lesson Content ----------

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_writing_lesson_content(request):
    """
    إنشاء محتوى درس كتابة
    
    POST /api/lesson-content/writing/create/
    
    Body:
    {
        "lesson": 4,
        "title": "Writing about your family",
        "writing_passage": "Example passage...",
        "instructions": "Write about your family...",
        "sample_answer": "My family consists of..."
    }
    """
    serializer = WritingLessonContentCreateUpdateSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    content = serializer.save()
    result_serializer = WritingLessonContentSerializer(content)
    
    return Response({
        'message': 'تم إنشاء محتوى درس الكتابة بنجاح',
        'content': result_serializer.data
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_writing_lesson_content(request, lesson_id):
    """
    عرض محتوى درس الكتابة
    
    GET /api/lesson-content/writing/{lesson_id}/
    """
    content = get_object_or_404(WritingLessonContent, lesson_id=lesson_id)
    serializer = WritingLessonContentSerializer(content)
    
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_writing_lesson_content(request, lesson_id):
    """
    تعديل محتوى درس الكتابة
    
    PUT /api/lesson-content/writing/{lesson_id}/update/
    """
    content = get_object_or_404(WritingLessonContent, lesson_id=lesson_id)
    
    partial = request.method == 'PATCH'
    serializer = WritingLessonContentCreateUpdateSerializer(content, data=request.data, partial=partial)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    content = serializer.save()
    result_serializer = WritingLessonContentSerializer(content)
    
    return Response({
        'message': 'تم تحديث محتوى درس الكتابة بنجاح',
        'content': result_serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_writing_lesson_content(request, lesson_id):
    """
    حذف محتوى درس الكتابة
    
    DELETE /api/lesson-content/writing/{lesson_id}/delete/
    """
    content = get_object_or_404(WritingLessonContent, lesson_id=lesson_id)
    content.delete()
    
    return Response({
        'message': 'تم حذف محتوى درس الكتابة بنجاح'
    }, status=status.HTTP_200_OK)
# ============================================
# 5. EXAM CRUD OPERATIONS
# ============================================

# ---------- 5.1 Unit Exam ----------

# ---------- 5.2 Level Exam ----------

# ============================================
# 6. QUESTION BANK MANAGEMENT
# ============================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_question_banks(request):
    """
    عرض جميع بنوك الأسئلة
    
    GET /api/question-banks/
    
    Query Parameters:
    - unit_id: filter by unit
    - level_id: filter by level
    """
    unit_id = request.query_params.get('unit_id', None)
    level_id = request.query_params.get('level_id', None)
    
    banks = LevelsUnitsQuestionBank.objects.all().select_related('unit', 'level')
    
    if unit_id:
        banks = banks.filter(unit_id=unit_id)
    
    if level_id:
        banks = banks.filter(level_id=level_id)
    
    banks = banks.order_by('-created_at')
    
    serializer = LevelsUnitsQuestionBankListSerializer(banks, many=True)
    
    return Response({
        'total_banks': banks.count(),
        'banks': serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_question_bank(request, bank_id):
    """
    عرض تفاصيل بنك أسئلة
    
    GET /api/question-banks/{bank_id}/
    """
    bank = get_object_or_404(LevelsUnitsQuestionBank, id=bank_id)
    serializer = LevelsUnitsQuestionBankDetailSerializer(bank)
    
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def question_bank_statistics(request, bank_id):
    """
    إحصائيات بنك الأسئلة
    
    GET /api/question-banks/{bank_id}/statistics/
    """
    bank = get_object_or_404(LevelsUnitsQuestionBank, id=bank_id)
    
    # عدد الأسئلة الحالية
    stats = {
        'vocabulary': bank.get_vocabulary_count(),
        'grammar': bank.get_grammar_count(),
        'reading': bank.get_reading_count(),
        'listening': bank.get_listening_count(),
        'speaking': bank.get_speaking_count(),
        'writing': bank.get_writing_count(),
        'total': bank.get_total_questions()
    }
    
    # المتطلبات
    if bank.unit:
        required = {
            'vocabulary': 8,
            'grammar': 8,
            'reading': 10,
            'listening': 3,
            'speaking': 3,
            'writing': 3
        }
        is_ready = bank.is_ready_for_unit_exam()
        exam_type = 'Unit Exam'
    elif bank.level:
        required = {
            'vocabulary': 12,
            'grammar': 12,
            'reading': 20,
            'listening': 6,
            'speaking': 5,
            'writing': 5
        }
        is_ready = bank.is_ready_for_level_exam()
        exam_type = 'Level Exam'
    else:
        required = {}
        is_ready = False
        exam_type = 'Unknown'
    
    return Response({
        'question_bank': {
            'id': bank.id,
            'title': bank.title,
            'description': bank.description,
            'exam_type': exam_type
        },
        'questions': stats,
        'required_for_exam': required,
        'ready_status': {
            key: stats[key] >= required.get(key, 0)
            for key in stats.keys() if key != 'total'
        },
        'is_ready_for_exam': is_ready,
        'missing_questions': {
            key: max(0, required.get(key, 0) - stats[key])
            for key in stats.keys() if key != 'total'
        }
    }, status=status.HTTP_200_OK)


# هنا بعد كده نضيف الـ Functions الخاصة بإضافة الأسئلة للبنك
# (نفس الـ Logic من placement_test)
# سأضيفها في Part 4
# ============================================
# QUESTION MANAGEMENT - ADD TO views.py
# ============================================
# أضف هذا الكود في نهاية ملف views.py الموجود

from placement_test.serializers import (
    CreateVocabularyQuestionSerializer,
    VocabularyQuestionSerializer,
    CreateGrammarQuestionSerializer,
    GrammarQuestionSerializer,
    ReadingPassageSerializer,
    CreateReadingQuestionSerializer,
    ReadingQuestionSerializer,
    ListeningAudioSerializer,
    CreateListeningQuestionSerializer,
    ListeningQuestionSerializer,
    SpeakingVideoSerializer,
    CreateSpeakingQuestionSerializer,
    SpeakingQuestionSerializer,
    CreateWritingQuestionSerializer,
    WritingQuestionSerializer
)

# ============================================
# 7. ADD QUESTIONS TO QUESTION BANK
# ============================================

# ---------- 7.1 Vocabulary Questions ----------
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_vocabulary_question_to_bank(request, bank_id):
    question_bank = get_object_or_404(LevelsUnitsQuestionBank, id=bank_id)
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
            # ✅ تحديد usage_type بناءً على نوع البنك
            if question_bank.unit:
                usage_type = 'UNIT_EXAM'
            elif question_bank.level:
                usage_type = 'LEVEL_EXAM'
            else:
                usage_type = 'QUESTION_BANK'  # Placement Test
            
            question_set, created = VocabularyQuestionSet.objects.get_or_create(
                title=question_set_title,
                usage_type=usage_type,
                defaults={'description': question_set_description}
            )
        else:
            return Response(
                {'error': 'يجب تحديد question_set_id أو question_set_title'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # ✅ تحديد usage_type للسؤال
        if question_bank.unit:
            usage_type = 'UNIT_EXAM'
        elif question_bank.level:
            usage_type = 'LEVEL_EXAM'
        else:
            usage_type = 'QUESTION_BANK'  # Placement Test
        
        # ✅ إنشاء السؤال
        vocabulary_question = VocabularyQuestion.objects.create(
            question_set=question_set,
            usage_type=usage_type,
            levels_units_question_bank=question_bank,
            # ❌ لا unit_exam (ده instance من UnitExam model)
            # ❌ لا level_exam (ده instance من LevelExam model)
            # ❌ لا lesson
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
# ---------- 7.2 Grammar Questions ----------

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_grammar_question_to_bank(request, bank_id):
    """
    إضافة سؤال قواعد لبنك الأسئلة
    
    POST /api/levels/question-banks/{bank_id}/add-grammar/
    """
    question_bank = get_object_or_404(LevelsUnitsQuestionBank, id=bank_id)
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
            # ✅ تحديد usage_type بناءً على نوع البنك
            if question_bank.unit:
                usage_type = 'UNIT_EXAM'
            elif question_bank.level:
                usage_type = 'LEVEL_EXAM'
            else:
                usage_type = 'QUESTION_BANK'
            
            question_set, created = GrammarQuestionSet.objects.get_or_create(
                title=question_set_title,
                usage_type=usage_type,
                defaults={'description': question_set_description}
            )
        else:
            return Response(
                {'error': 'يجب تحديد question_set_id أو question_set_title'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # ✅ تحديد usage_type للسؤال فقط
        if question_bank.unit:
            usage_type = 'UNIT_EXAM'
        elif question_bank.level:
            usage_type = 'LEVEL_EXAM'
        else:
            usage_type = 'QUESTION_BANK'
        
        # ✅ إنشاء السؤال بدون unit_exam أو level_exam
        grammar_question = GrammarQuestion.objects.create(
            question_set=question_set,
            usage_type=usage_type,
            levels_units_question_bank=question_bank,
            # ❌ حذف unit_exam و level_exam
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

# ---------- 7.3 Reading Questions ----------

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_reading_passage_in_bank(request, bank_id):
    """
    إنشاء قطعة قراءة جديدة في البنك
    
    POST /api/levels/question-banks/{bank_id}/create-reading-passage/
    
    Body:
    {
        "title": "Animals in the Zoo",
        "passage_text": "The zoo has many animals...",
        "passage_image": null,
        "source": "English Book 1",
        "order": 1,
        "is_active": true
    }
    """
    question_bank = get_object_or_404(LevelsUnitsQuestionBank, id=bank_id)
    serializer = ReadingPassageSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    if question_bank.unit:
        usage_type = 'UNIT_EXAM'
    elif question_bank.level:
        usage_type = 'LEVEL_EXAM'
    else:
        usage_type = 'QUESTION_BANK'

    
    reading_passage = ReadingPassage.objects.create(
        usage_type=usage_type,
        levels_units_question_bank=question_bank,
        **serializer.validated_data
    )
    
    result_serializer = ReadingPassageSerializer(reading_passage)
    
    return Response({
        'message': 'تم إنشاء قطعة القراءة بنجاح',
        'passage': result_serializer.data
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_reading_question_to_passage(request, bank_id, passage_id):
    """
    إضافة سؤال قراءة لقطعة معينة
    
    POST /api/levels/question-banks/{bank_id}/reading-passages/{passage_id}/add-question/
    
    Body:
    {
        "question_text": "What animals are in the zoo?",
        "question_image": null,
        "choice_a": "Lions",
        "choice_b": "Tigers",
        "choice_c": "All animals",
        "choice_d": "None",
        "correct_answer": "C",
        "explanation": "...",
        "points": 1,
        "order": 1,
        "is_active": true
    }
    """
    question_bank = get_object_or_404(LevelsUnitsQuestionBank, id=bank_id)
    reading_passage = get_object_or_404(
        ReadingPassage,
        id=passage_id,
        levels_units_question_bank=question_bank
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


# ---------- 7.4 Listening Questions ----------

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_listening_audio_in_bank(request, bank_id):
    """
    إنشاء تسجيل صوتي جديد في البنك
    
    POST /api/levels/question-banks/{bank_id}/create-listening-audio/
    """
    question_bank = get_object_or_404(LevelsUnitsQuestionBank, id=bank_id)
    serializer = ListeningAudioSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    if question_bank.unit:
        usage_type = 'UNIT_EXAM'
        
    elif question_bank.level:
        usage_type = 'LEVEL_EXAM'
        
    else:
        usage_type = 'QUESTION_BANK'
        
    
    listening_audio = ListeningAudio.objects.create(
        usage_type=usage_type,
        levels_units_question_bank=question_bank,
        **serializer.validated_data
    )
    
    result_serializer = ListeningAudioSerializer(listening_audio)
    
    return Response({
        'message': 'تم إنشاء التسجيل الصوتي بنجاح',
        'audio': result_serializer.data
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_listening_question_to_audio(request, bank_id, audio_id):
    """
    إضافة سؤال استماع لتسجيل صوتي معين
    
    POST /api/levels/question-banks/{bank_id}/listening-audios/{audio_id}/add-question/
    """
    question_bank = get_object_or_404(LevelsUnitsQuestionBank, id=bank_id)
    listening_audio = get_object_or_404(
        ListeningAudio,
        id=audio_id,
        levels_units_question_bank=question_bank
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


# ---------- 7.5 Speaking Questions ----------

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_speaking_video_in_bank(request, bank_id):
    """
    إنشاء فيديو تحدث جديد في البنك
    
    POST /api/levels/question-banks/{bank_id}/create-speaking-video/
    """
    question_bank = get_object_or_404(LevelsUnitsQuestionBank, id=bank_id)
    serializer = SpeakingVideoSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    if question_bank.unit:
        usage_type = 'UNIT_EXAM'
        
    elif question_bank.level:
        usage_type = 'LEVEL_EXAM'
        
    else:
        usage_type = 'QUESTION_BANK'
        
    
    speaking_video = SpeakingVideo.objects.create(
        usage_type=usage_type,
        levels_units_question_bank=question_bank,
        **serializer.validated_data
    )
    
    result_serializer = SpeakingVideoSerializer(speaking_video)
    
    return Response({
        'message': 'تم إنشاء فيديو التحدث بنجاح',
        'video': result_serializer.data
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_speaking_question_to_video(request, bank_id, video_id):
    """
    إضافة سؤال تحدث لفيديو معين
    
    POST /api/levels/question-banks/{bank_id}/speaking-videos/{video_id}/add-question/
    """
    question_bank = get_object_or_404(LevelsUnitsQuestionBank, id=bank_id)
    speaking_video = get_object_or_404(
        SpeakingVideo,
        id=video_id,
        levels_units_question_bank=question_bank
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


# ---------- 7.6 Writing Questions ----------

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_writing_question_to_bank(request, bank_id):
    """
    إضافة سؤال كتابة للبنك
    
    POST /api/levels/question-banks/{bank_id}/add-writing/
    
    Body:
    {
        "title": "Write about your family",
        "question_text": "Write a short paragraph about your family...",
        "question_image": null,
        "min_words": 50,
        "max_words": 150,
        "sample_answer": "My family consists of...",
        "rubric": "Grading criteria...",
        "pass_threshold": 60,
        "order": 1,
        "is_active": true
    }
    """
    question_bank = get_object_or_404(LevelsUnitsQuestionBank, id=bank_id)
    serializer = CreateWritingQuestionSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    if question_bank.unit:
        usage_type = 'UNIT_EXAM'

    elif question_bank.level:
        usage_type = 'LEVEL_EXAM'

    else:
        usage_type = 'QUESTION_BANK'

    
    writing_question = WritingQuestion.objects.create(
        usage_type=usage_type,
        levels_units_question_bank=question_bank,
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
# STUDENT PROGRESS TRACKING - ADD TO views.py
# ============================================

# ============================================
# 8. STUDENT PROGRESS TRACKING
# ============================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_level(request, level_id):
    """
    بدء مستوى جديد للطالب
    
    POST /api/levels/student/start-level/{level_id}/
    
    ✅ Auto-creates:
    - StudentLevel (status='IN_PROGRESS')
    - Sets current_unit to first unit
    """
    level = get_object_or_404(Level, id=level_id, is_active=True)
    
    # التحقق من عدم وجود مستوى نشط بالفعل
    existing = StudentLevel.objects.filter(
        student=request.user,
        level=level
    ).first()
    
    if existing:
        if existing.status == 'IN_PROGRESS':
            return Response({
                'error': 'أنت بالفعل في هذا المستوى',
                'student_level': StudentLevelSerializer(existing).data
            }, status=status.HTTP_400_BAD_REQUEST)
        elif existing.status == 'COMPLETED':
            return Response({
                'error': 'لقد أكملت هذا المستوى بالفعل',
                'student_level': StudentLevelSerializer(existing).data
            }, status=status.HTTP_400_BAD_REQUEST)
    
    # الحصول على أول وحدة في المستوى
    first_unit = level.units.filter(is_active=True).order_by('order', 'id').first()
    
    if not first_unit:
        return Response({
            'error': 'هذا المستوى لا يحتوي على وحدات'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    with transaction.atomic():
        # إنشاء StudentLevel
        student_level = StudentLevel.objects.create(
            student=request.user,
            level=level,
            status='IN_PROGRESS',
            current_unit=first_unit,
            started_at=timezone.now()
        )
        
        # إنشاء StudentUnit للوحدة الأولى
        StudentUnit.objects.create(
            student=request.user,
            unit=first_unit,
            status='IN_PROGRESS',
            started_at=timezone.now()
        )
    
    serializer = StudentLevelSerializer(student_level)
    
    return Response({
        'message': 'تم بدء المستوى بنجاح',
        'student_level': serializer.data,
        'first_unit': {
            'id': first_unit.id,
            'title': first_unit.title
        }
    }, status=status.HTTP_201_CREATED)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_unit(request, unit_id):
    unit = get_object_or_404(Unit, id=unit_id, is_active=True)
    
    # التحقق من أن الطالب في المستوى الصحيح
    student_level = StudentLevel.objects.filter(
        student=request.user,
        level=unit.level,
        status='IN_PROGRESS'
    ).first()
    
    if not student_level:
        return Response({
            'error': 'يجب أن تبدأ المستوى أولاً'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # ✅ CHECK الجديد - التحقق من إكمال الوحدة السابقة
    if unit.order > 1:
        previous_unit = Unit.objects.filter(
            level=unit.level,
            order=unit.order - 1,
            is_active=True
        ).first()
        
        if previous_unit:
            previous_student_unit = StudentUnit.objects.filter(
                student=request.user,
                unit=previous_unit,
            ).first()
            
            if not previous_student_unit or previous_student_unit.status != 'COMPLETED':
                return Response({
                    'error': 'يجب إكمال الوحدة السابقة أولاً',
                    'previous_unit': {
                        'id': previous_unit.id,
                        'title': previous_unit.title,
                        'status': previous_student_unit.status if previous_student_unit else 'NOT_STARTED'
                    }
                }, status=status.HTTP_400_BAD_REQUEST)
    
    # التحقق من عدم وجود وحدة نشطة
    existing = StudentUnit.objects.filter(
        student=request.user,
        unit=unit
    ).first()
    
    if existing:
        if existing.status == 'IN_PROGRESS':
            return Response({
                'error': 'أنت بالفعل في هذه الوحدة',
                'student_unit': StudentUnitSerializer(existing).data
            }, status=status.HTTP_400_BAD_REQUEST)
        elif existing.status == 'COMPLETED':
            return Response({
                'error': 'لقد أكملت هذه الوحدة بالفعل',
                'student_unit': StudentUnitSerializer(existing).data
            }, status=status.HTTP_400_BAD_REQUEST)
    
    with transaction.atomic():
        student_unit = StudentUnit.objects.create(
            student=request.user,
            unit=unit,
            status='IN_PROGRESS',
            started_at=timezone.now()
        )
        
        student_level.current_unit = unit
        student_level.save()
    
    serializer = StudentUnitSerializer(student_unit)
    
    return Response({
        'message': 'تم بدء الوحدة بنجاح',
        'student_unit': serializer.data
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def complete_lesson(request, lesson_id):
    """
    إكمال درس
    
    POST /api/levels/student/complete-lesson/{lesson_id}/
    
    ✅ Updates/Creates StudentLesson (is_completed=True)
    ✅ Updates StudentUnit.lessons_completed
    ✅ Checks if unit is completed (all lessons done)
    """
    lesson = get_object_or_404(Lesson, id=lesson_id, is_active=True)
    
    # التحقق من أن الطالب في الوحدة الصحيحة
    student_unit = StudentUnit.objects.filter(
        student=request.user,
        unit=lesson.unit,
        status='IN_PROGRESS'
    ).first()
    
    if not student_unit:
        return Response({
            'error': 'يجب أن تبدأ الوحدة أولاً'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    with transaction.atomic():
        # إنشاء أو تحديث StudentLesson
        student_lesson, created = StudentLesson.objects.get_or_create(
            student=request.user,
            lesson=lesson,
            defaults={
                'is_completed': True,
                'completed_at': timezone.now()
            }
        )
        
        if not created and not student_lesson.is_completed:
            student_lesson.is_completed = True
            student_lesson.completed_at = timezone.now()
            student_lesson.save()
        
        # تحديث عدد الدروس المكتملة في الوحدة
        completed_lessons = StudentLesson.objects.filter(
            student=request.user,
            lesson__unit=lesson.unit,
            is_completed=True
        ).count()
        
        student_unit.lessons_completed = completed_lessons
        
        # التحقق من إكمال جميع دروس الوحدة
        total_lessons = lesson.unit.get_lessons_count()
        if completed_lessons >= total_lessons and not student_unit.exam_passed:
            # الوحدة مكتملة (الدروس فقط) - يحتاج لاجتياز الامتحان
            pass
        
        student_unit.save()
    
    serializer = StudentLessonSerializer(student_lesson)
    
    return Response({
        'message': 'تم إكمال الدرس بنجاح',
        'student_lesson': serializer.data,
        'unit_progress': {
            'lessons_completed': completed_lessons,
            'total_lessons': total_lessons,
            'percentage': round((completed_lessons / total_lessons * 100), 2) if total_lessons > 0 else 0
        }
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_progress(request):
    """
    عرض تقدم الطالب الكامل
    
    GET /api/levels/student/my-progress/
    
    Query Parameters:
    - level_id: filter by specific level
    """
    level_id = request.query_params.get('level_id', None)
    
    # المستويات
    student_levels = StudentLevel.objects.filter(
        student=request.user
    ).select_related('level', 'current_unit').order_by('level__order')
    
    if level_id:
        student_levels = student_levels.filter(level_id=level_id)
    
    levels_data = []
    for sl in student_levels:
        # الوحدات
        student_units = StudentUnit.objects.filter(
            student=request.user,
            unit__level=sl.level
        ).select_related('unit').order_by('unit__order')
        
        units_data = []
        for su in student_units:
            # الدروس
            completed_lessons = StudentLesson.objects.filter(
                student=request.user,
                lesson__unit=su.unit,
                is_completed=True
            ).count()
            
            total_lessons = su.unit.get_lessons_count()
            
            units_data.append({
                'id': su.id,
                'unit': {
                    'id': su.unit.id,
                    'title': su.unit.title
                },
                'status': su.status,
                'lessons_completed': completed_lessons,
                'total_lessons': total_lessons,
                'exam_passed': su.exam_passed,
                'started_at': su.started_at,
                'completed_at': su.completed_at
            })
        
        levels_data.append({
            'id': sl.id,
            'level': {
                'id': sl.level.id,
                'code': sl.level.code,
                'title': sl.level.title
            },
            'status': sl.status,
            'current_unit': {
                'id': sl.current_unit.id if sl.current_unit else None,
                'title': sl.current_unit.title if sl.current_unit else None
            } if sl.current_unit else None,
            'started_at': sl.started_at,
            'completed_at': sl.completed_at,
            'units': units_data
        })
    
    # إحصائيات عامة
    total_levels = StudentLevel.objects.filter(student=request.user).count()
    completed_levels = StudentLevel.objects.filter(
        student=request.user,
        status='COMPLETED'
    ).count()
    
    total_units = StudentUnit.objects.filter(student=request.user).count()
    completed_units = StudentUnit.objects.filter(
        student=request.user,
        status='COMPLETED'
    ).count()
    
    total_lessons = StudentLesson.objects.filter(student=request.user).count()
    completed_lessons = StudentLesson.objects.filter(
        student=request.user,
        is_completed=True
    ).count()
    
    return Response({
        'summary': {
            'levels': {
                'total': total_levels,
                'completed': completed_levels,
                'in_progress': total_levels - completed_levels
            },
            'units': {
                'total': total_units,
                'completed': completed_units,
                'in_progress': total_units - completed_units
            },
            'lessons': {
                'total': total_lessons,
                'completed': completed_lessons,
                'in_progress': total_lessons - completed_lessons
            }
        },
        'levels': levels_data
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_current_level(request):
    """
    عرض المستوى الحالي للطالب
    
    GET /api/levels/student/my-current-level/
    """
    current_level = StudentLevel.objects.filter(
        student=request.user,
        status='IN_PROGRESS'
    ).select_related('level', 'current_unit').first()
    
    if not current_level:
        return Response({
            'message': 'لا يوجد مستوى نشط حالياً',
            'has_current_level': False
        }, status=status.HTTP_200_OK)
    
    serializer = StudentLevelSerializer(current_level)
    
    # الوحدة الحالية
    current_unit = None
    if current_level.current_unit:
        student_unit = StudentUnit.objects.filter(
            student=request.user,
            unit=current_level.current_unit
        ).first()
        
        if student_unit:
            current_unit = StudentUnitSerializer(student_unit).data
    
    return Response({
        'has_current_level': True,
        'student_level': serializer.data,
        'current_unit': current_unit
    }, status=status.HTTP_200_OK)
# ============================================
# EXAM TAKING & GRADING - ADD TO views.py
# ============================================

# ============================================
# 9. HELPER FUNCTIONS FOR EXAM GENERATION
# ============================================

def select_random_questions_for_unit_exam(question_bank, unit_exam):
    """
    اختيار أسئلة عشوائية من البنك لامتحان الوحدة
    
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
    
    # Vocabulary
    vocab_ids = list(
        VocabularyQuestion.objects.filter(
            levels_units_question_bank=question_bank,
            is_active=True
        ).values_list('id', flat=True)
    )
    selected_questions['vocabulary'] = random.sample(
        vocab_ids,
        min(unit_exam.vocabulary_count, len(vocab_ids))
    )
    
    # Grammar
    grammar_ids = list(
        GrammarQuestion.objects.filter(
            levels_units_question_bank=question_bank,
            is_active=True
        ).values_list('id', flat=True)
    )
    selected_questions['grammar'] = random.sample(
        grammar_ids,
        min(unit_exam.grammar_count, len(grammar_ids))
    )
    
    # Reading - نختار questions عشوائية
    reading_ids = list(
        ReadingQuestion.objects.filter(
            passage__levels_units_question_bank=question_bank,
            passage__is_active=True,
            is_active=True
        ).values_list('id', flat=True)
    )
    selected_questions['reading'] = random.sample(
        reading_ids,
        min(unit_exam.reading_questions_count, len(reading_ids))
    )
    
    # Listening
    listening_ids = list(
        ListeningQuestion.objects.filter(
            audio__levels_units_question_bank=question_bank,
            audio__is_active=True,
            is_active=True
        ).values_list('id', flat=True)
    )
    selected_questions['listening'] = random.sample(
        listening_ids,
        min(unit_exam.listening_questions_count, len(listening_ids))
    )
    
    # Speaking
    speaking_ids = list(
        SpeakingQuestion.objects.filter(
            video__levels_units_question_bank=question_bank,
            video__is_active=True,
            is_active=True
        ).values_list('id', flat=True)
    )
    selected_questions['speaking'] = random.sample(
        speaking_ids,
        min(unit_exam.speaking_questions_count, len(speaking_ids))
    )
    
    # Writing
    writing_ids = list(
        WritingQuestion.objects.filter(
            levels_units_question_bank=question_bank,
            is_active=True
        ).values_list('id', flat=True)
    )
    selected_questions['writing'] = random.sample(
        writing_ids,
        min(unit_exam.writing_questions_count, len(writing_ids))
    )
    
    return selected_questions


def select_random_questions_for_level_exam(question_bank, level_exam):
    """
    اختيار أسئلة عشوائية من البنك لامتحان المستوى
    
    نفس المنطق لكن مع أعداد مختلفة
    """
    selected_questions = {
        'vocabulary': [],
        'grammar': [],
        'reading': [],
        'listening': [],
        'speaking': [],
        'writing': []
    }
    
    # Vocabulary
    vocab_ids = list(
        VocabularyQuestion.objects.filter(
            levels_units_question_bank=question_bank,
            is_active=True
        ).values_list('id', flat=True)
    )
    selected_questions['vocabulary'] = random.sample(
        vocab_ids,
        min(level_exam.vocabulary_count, len(vocab_ids))
    )
    
    # Grammar
    grammar_ids = list(
        GrammarQuestion.objects.filter(
            levels_units_question_bank=question_bank,
            is_active=True
        ).values_list('id', flat=True)
    )
    selected_questions['grammar'] = random.sample(
        grammar_ids,
        min(level_exam.grammar_count, len(grammar_ids))
    )
    
    # Reading
    reading_ids = list(
        ReadingQuestion.objects.filter(
            passage__levels_units_question_bank=question_bank,
            passage__is_active=True,
            is_active=True
        ).values_list('id', flat=True)
    )
    selected_questions['reading'] = random.sample(
        reading_ids,
        min(level_exam.reading_questions_count, len(reading_ids))
    )
    
    # Listening
    listening_ids = list(
        ListeningQuestion.objects.filter(
            audio__levels_units_question_bank=question_bank,
            audio__is_active=True,
            is_active=True
        ).values_list('id', flat=True)
    )
    selected_questions['listening'] = random.sample(
        listening_ids,
        min(level_exam.listening_questions_count, len(listening_ids))
    )
    
    # Speaking
    speaking_ids = list(
        SpeakingQuestion.objects.filter(
            video__levels_units_question_bank=question_bank,
            video__is_active=True,
            is_active=True
        ).values_list('id', flat=True)
    )
    selected_questions['speaking'] = random.sample(
        speaking_ids,
        min(level_exam.speaking_questions_count, len(speaking_ids))
    )
    
    # Writing
    writing_ids = list(
        WritingQuestion.objects.filter(
            levels_units_question_bank=question_bank,
            is_active=True
        ).values_list('id', flat=True)
    )
    selected_questions['writing'] = random.sample(
        writing_ids,
        min(level_exam.writing_questions_count, len(writing_ids))
    )
    
    return selected_questions


def fetch_selected_questions_data(selected_questions):
    """
    جلب بيانات الأسئلة المختارة
    """
    from placement_test.serializers import (
        VocabularyQuestionSerializer,
        GrammarQuestionSerializer,
        ReadingQuestionSerializer,
        ListeningQuestionSerializer,
        SpeakingQuestionSerializer,
        WritingQuestionSerializer
    )
    
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
# 10. UNIT EXAM - START & SUBMIT
# ============================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_unit_exam(request, unit_id):
    """
    بدء امتحان وحدة
    
    POST /api/levels/student/exams/unit/start/{unit_id}/ 
    """
    # ✅ جلب الـ Unit
    unit = get_object_or_404(Unit, id=unit_id, is_active=True)
    
    # ✅ جلب الامتحان التلقائي
    unit_exam = get_object_or_404(UnitExam, unit=unit)
    
    # التحقق من أن الطالب في الوحدة
    student_unit = StudentUnit.objects.filter(
        student=request.user,
        unit=unit,  # ← استخدم unit مباشرة
        status='IN_PROGRESS'
    ).first()
    
    if not student_unit:
        return Response({
            'error': 'يجب أن تبدأ الوحدة أولاً'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # التحقق من إكمال جميع الدروس
    total_lessons = unit_exam.unit.get_lessons_count()
    if student_unit.lessons_completed < total_lessons:
        return Response({
            'error': f'يجب إكمال جميع الدروس أولاً ({student_unit.lessons_completed}/{total_lessons})',
            'lessons_completed': student_unit.lessons_completed,
            'total_lessons': total_lessons
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # الحصول على LevelsUnitsQuestionBank
    question_bank = unit_exam.unit.question_banks.first()
    
    if not question_bank:
        return Response({
            'error': 'لا يوجد بنك أسئلة لهذه الوحدة'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # التحقق من جاهزية البنك
    if not question_bank.is_ready_for_unit_exam():
        stats = {
            'vocabulary': question_bank.get_vocabulary_count(),
            'grammar': question_bank.get_grammar_count(),
            'reading': question_bank.get_reading_count(),
            'listening': question_bank.get_listening_count(),
            'speaking': question_bank.get_speaking_count(),
            'writing': question_bank.get_writing_count()
        }
        
        return Response({
            'error': 'بنك الأسئلة غير جاهز للامتحان',
            'current_questions': stats,
            'required': {
                'vocabulary': 8,
                'grammar': 8,
                'reading': 10,
                'listening': 3,
                'speaking': 3,
                'writing': 3
            }
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # التحقق من عدم وجود محاولة نشطة
    active_attempt = StudentUnitExamAttempt.objects.filter(
        student=request.user,
        unit_exam=unit_exam,
        submitted_at__isnull=True
    ).first()
    
    if active_attempt:
        return Response({
            'error': 'لديك محاولة نشطة بالفعل',
            'attempt_id': active_attempt.id,
            'started_at': active_attempt.started_at
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # إنشاء المحاولة
    with transaction.atomic():
        # حساب رقم المحاولة
        last_attempt = StudentUnitExamAttempt.objects.filter(
            student=request.user,
            unit_exam=unit_exam
        ).order_by('-attempt_number').first()
        
        attempt_number = (last_attempt.attempt_number + 1) if last_attempt else 1
        
        # اختيار الأسئلة العشوائية
        selected_questions = select_random_questions_for_unit_exam(question_bank, unit_exam)
        
        # إنشاء المحاولة
        attempt = StudentUnitExamAttempt.objects.create(
            student=request.user,
            unit_exam=unit_exam,
            attempt_number=attempt_number,
            generated_questions=selected_questions,
            started_at=timezone.now()
        )
        
        # جلب بيانات الأسئلة
        exam_questions = fetch_selected_questions_data(selected_questions)
    
    return Response({
        'message': 'تم بدء الامتحان بنجاح',
        'attempt': {
            'id': attempt.id,
            'attempt_number': attempt.attempt_number,
            'started_at': attempt.started_at,
            'time_limit_minutes': unit_exam.time_limit,
            'ends_at': attempt.started_at + timezone.timedelta(minutes=unit_exam.time_limit)
        },
        'exam_info': {
            'id': unit_exam.id,
            'title': unit_exam.title,
            'instructions': unit_exam.instructions,
            'total_questions': unit_exam.get_total_questions(),
            'passing_score': unit_exam.passing_score
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

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_unit_exam(request, attempt_id):
    attempt = get_object_or_404(
        StudentUnitExamAttempt,
        id=attempt_id,
        student=request.user
    )
    
    if attempt.submitted_at:
        return Response({
            'error': 'تم تسليم هذا الامتحان بالفعل',
            'score': attempt.score,
            'passed': attempt.passed
        }, status=status.HTTP_400_BAD_REQUEST)
    
    answers = request.data.get('answers', {})
    
    if not answers:
        return Response({
            'error': 'يجب إرسال الإجابات'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    with transaction.atomic():
        attempt.answers = answers
        
        time_taken = (timezone.now() - attempt.started_at).total_seconds()
        attempt.time_taken = int(time_taken)
        
        total_score = 0
        max_score = 0
        
        generated_questions = attempt.generated_questions
        
        # ✅ تصحيح MCQ - النظام الجديد (arrays)
        mcq_config = {
            'vocabulary': VocabularyQuestion,
            'grammar': GrammarQuestion,
            'reading': ReadingQuestion,
            'listening': ListeningQuestion,
            'speaking': SpeakingQuestion,
        }
        
        for q_type, QuestionModel in mcq_config.items():
            question_ids = generated_questions.get(q_type, [])
            questions = QuestionModel.objects.filter(id__in=question_ids)
            
            # ✅ تحويل الـ array لـ dict للبحث السريع
            # answers[q_type] = [{"question_id": 1, "selected_choice": "A"}, ...]
            type_answers = {
                str(ans['question_id']): ans['selected_choice']
                for ans in answers.get(q_type, [])
                if 'question_id' in ans and 'selected_choice' in ans
            }
            
            for q in questions:
                max_score += q.points
                student_answer = type_answers.get(str(q.id))
                
                if student_answer == q.correct_answer:
                    total_score += q.points
        
        # ✅ تصحيح Writing - النظام الجديد
        writing_ids = generated_questions.get('writing', [])
        writing_questions = WritingQuestion.objects.filter(id__in=writing_ids)
        
        # answers['writing'] = [{"question_id": 7, "text_answer": "My answer..."}]
        writing_answers = {
            str(ans['question_id']): ans.get('text_answer', '')
            for ans in answers.get('writing', [])
            if 'question_id' in ans
        }
        
        for wq in writing_questions:
            max_score += wq.points
            student_answer = writing_answers.get(str(wq.id), '')
            
            if student_answer:
                try:
                    logger.info(f"Grading writing question {wq.id} for Unit Exam")
                    
                    ai_result = ai_grading_service.grade_writing_question(
                        question_text=wq.question_text,
                        student_answer=student_answer,
                        sample_answer=wq.sample_answer or '',
                        rubric=wq.rubric or '',
                        max_points=wq.points,
                        min_words=wq.min_words,
                        max_words=wq.max_words,
                        pass_threshold=wq.pass_threshold
                    )
                    
                    total_score += ai_result['score']
                    
                    logger.info(
                        f"Writing Q{wq.id}: Raw={ai_result['raw_score']}/{wq.points}, "
                        f"Percentage={ai_result['percentage']:.1f}%, "
                        f"Binary Score={ai_result['score']}/1, "
                        f"Cost=${ai_result['cost']:.6f}"
                    )
                    
                except Exception as e:
                    logger.error(f"AI Grading Error for Writing Q{wq.id}: {str(e)}")
                    word_count = len(student_answer.split())
                    if wq.min_words <= word_count <= wq.max_words:
                        total_score += 1
                        logger.warning(f"Used fallback grading for Q{wq.id}: word_count={word_count}, score=1")
                    else:
                        logger.warning(f"Used fallback grading for Q{wq.id}: word_count={word_count}, score=0")
        
        percentage = (total_score / max_score * 100) if max_score > 0 else 0
        passed = percentage >= attempt.unit_exam.passing_score
        
        attempt.score = int(percentage)
        attempt.passed = passed
        attempt.submitted_at = timezone.now()
        attempt.save()
        
        if passed:
            student_unit = StudentUnit.objects.get(
                student=request.user,
                unit=attempt.unit_exam.unit
            )
            student_unit.exam_passed = True
            student_unit.status = 'COMPLETED'
            student_unit.completed_at = timezone.now()
            student_unit.save()
            
            total_units = attempt.unit_exam.unit.level.get_units_count()
            completed_units = StudentUnit.objects.filter(
                student=request.user,
                unit__level=attempt.unit_exam.unit.level,
                status='COMPLETED'
            ).count()
    
    serializer = StudentUnitExamAttemptSerializer(attempt)
    
    return Response({
        'message': 'تم تسليم الامتحان بنجاح',
        'result': {
            'attempt': serializer.data,
            'score': attempt.score,
            'max_score': 100,
            'passed': attempt.passed,
            'passing_score': attempt.unit_exam.passing_score,
            'time_taken_seconds': attempt.time_taken,
            'time_taken_minutes': round(attempt.time_taken / 60, 2)
        },
        'unit_status': 'COMPLETED' if passed else 'FAILED'
    }, status=status.HTTP_200_OK)
# ============================================
# 11. LEVEL EXAM - START & SUBMIT
# ============================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_level_exam(request, level_id):
    """
    بدء امتحان مستوى
    
    POST /api/levels/student/exams/level/start/{level_id}/  ← تغيير
    """
    level = get_object_or_404(Level, id=level_id, is_active=True)
    
    # ✅ جلب الامتحان التلقائي
    level_exam = get_object_or_404(LevelExam, level=level)
    
    # التحقق من أن الطالب في المستوى
    student_level = StudentLevel.objects.filter(
        student=request.user,
        level=level,  # ← استخدم level مباشرة
        status='IN_PROGRESS'
    ).first()
    
    if not student_level:
        return Response({
            'error': 'يجب أن تبدأ المستوى أولاً'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # التحقق من إكمال جميع الوحدات
    total_units = level_exam.level.get_units_count()
    completed_units = StudentUnit.objects.filter(
        student=request.user,
        unit__level=level_exam.level,
        status='COMPLETED',
        exam_passed=True
    ).count()
    
    if completed_units < total_units:
        return Response({
            'error': f'يجب إكمال جميع الوحدات أولاً ({completed_units}/{total_units})',
            'completed_units': completed_units,
            'total_units': total_units
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # الحصول على LevelsUnitsQuestionBank
    question_bank = level_exam.level.question_banks.first()
    
    if not question_bank:
        return Response({
            'error': 'لا يوجد بنك أسئلة لهذا المستوى'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # التحقق من جاهزية البنك
    if not question_bank.is_ready_for_level_exam():
        stats = {
            'vocabulary': question_bank.get_vocabulary_count(),
            'grammar': question_bank.get_grammar_count(),
            'reading': question_bank.get_reading_count(),
            'listening': question_bank.get_listening_count(),
            'speaking': question_bank.get_speaking_count(),
            'writing': question_bank.get_writing_count()
        }
        
        return Response({
            'error': 'بنك الأسئلة غير جاهز للامتحان',
            'current_questions': stats,
            'required': {
                'vocabulary': 12,
                'grammar': 12,
                'reading': 20,
                'listening': 6,
                'speaking': 5,
                'writing': 5
            }
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # التحقق من عدم وجود محاولة نشطة
    active_attempt = StudentLevelExamAttempt.objects.filter(
        student=request.user,
        level_exam=level_exam,
        submitted_at__isnull=True
    ).first()
    
    if active_attempt:
        return Response({
            'error': 'لديك محاولة نشطة بالفعل',
            'attempt_id': active_attempt.id,
            'started_at': active_attempt.started_at
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # إنشاء المحاولة
    with transaction.atomic():
        # حساب رقم المحاولة
        last_attempt = StudentLevelExamAttempt.objects.filter(
            student=request.user,
            level_exam=level_exam
        ).order_by('-attempt_number').first()
        
        attempt_number = (last_attempt.attempt_number + 1) if last_attempt else 1
        
        # اختيار الأسئلة العشوائية
        selected_questions = select_random_questions_for_level_exam(question_bank, level_exam)
        
        # إنشاء المحاولة
        attempt = StudentLevelExamAttempt.objects.create(
            student=request.user,
            level_exam=level_exam,
            attempt_number=attempt_number,
            generated_questions=selected_questions,
            started_at=timezone.now()
        )
        
        # جلب بيانات الأسئلة
        exam_questions = fetch_selected_questions_data(selected_questions)
    
    return Response({
        'message': 'تم بدء امتحان المستوى بنجاح',
        'attempt': {
            'id': attempt.id,
            'attempt_number': attempt.attempt_number,
            'started_at': attempt.started_at,
            'time_limit_minutes': level_exam.time_limit,
            'ends_at': attempt.started_at + timezone.timedelta(minutes=level_exam.time_limit)
        },
        'exam_info': {
            'id': level_exam.id,
            'title': level_exam.title,
            'instructions': level_exam.instructions,
            'total_questions': level_exam.get_total_questions(),
            'passing_score': level_exam.passing_score
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

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_level_exam(request, attempt_id):
    attempt = get_object_or_404(
        StudentLevelExamAttempt,
        id=attempt_id,
        student=request.user
    )
    
    if attempt.submitted_at:
        return Response({
            'error': 'تم تسليم هذا الامتحان بالفعل',
            'score': attempt.score,
            'passed': attempt.passed
        }, status=status.HTTP_400_BAD_REQUEST)
    
    answers = request.data.get('answers', {})
    
    if not answers:
        return Response({
            'error': 'يجب إرسال الإجابات'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    with transaction.atomic():
        attempt.answers = answers
        
        time_taken = (timezone.now() - attempt.started_at).total_seconds()
        attempt.time_taken = int(time_taken)
        
        total_score = 0
        max_score = 0
        
        generated_questions = attempt.generated_questions
        
        # ✅ تصحيح MCQ - النظام الجديد (arrays)
        mcq_config = {
            'vocabulary': VocabularyQuestion,
            'grammar': GrammarQuestion,
            'reading': ReadingQuestion,
            'listening': ListeningQuestion,
            'speaking': SpeakingQuestion,
        }
        
        for q_type, QuestionModel in mcq_config.items():
            question_ids = generated_questions.get(q_type, [])
            questions = QuestionModel.objects.filter(id__in=question_ids)
            
            # ✅ تحويل الـ array لـ dict للبحث السريع
            type_answers = {
                str(ans['question_id']): ans['selected_choice']
                for ans in answers.get(q_type, [])
                if 'question_id' in ans and 'selected_choice' in ans
            }
            
            for q in questions:
                max_score += q.points
                student_answer = type_answers.get(str(q.id))
                
                if student_answer == q.correct_answer:
                    total_score += q.points
        
        # ✅ تصحيح Writing - النظام الجديد
        writing_ids = generated_questions.get('writing', [])
        writing_questions = WritingQuestion.objects.filter(id__in=writing_ids)
        
        writing_answers = {
            str(ans['question_id']): ans.get('text_answer', '')
            for ans in answers.get('writing', [])
            if 'question_id' in ans
        }
        
        for wq in writing_questions:
            max_score += wq.points
            student_answer = writing_answers.get(str(wq.id), '')
            
            if student_answer:
                try:
                    logger.info(f"Grading writing question {wq.id} for Level Exam")
                    
                    ai_result = ai_grading_service.grade_writing_question(
                        question_text=wq.question_text,
                        student_answer=student_answer,
                        sample_answer=wq.sample_answer or '',
                        rubric=wq.rubric or '',
                        max_points=wq.points,
                        min_words=wq.min_words,
                        max_words=wq.max_words,
                        pass_threshold=wq.pass_threshold
                    )
                    
                    total_score += ai_result['score']
                    
                    logger.info(
                        f"Writing Q{wq.id}: Raw={ai_result['raw_score']}/{wq.points}, "
                        f"Percentage={ai_result['percentage']:.1f}%, "
                        f"Binary Score={ai_result['score']}/1, "
                        f"Cost=${ai_result['cost']:.6f}"
                    )
                    
                except Exception as e:
                    logger.error(f"AI Grading Error for Writing Q{wq.id}: {str(e)}")
                    word_count = len(student_answer.split())
                    if wq.min_words <= word_count <= wq.max_words:
                        total_score += 1
                        logger.warning(f"Used fallback grading for Q{wq.id}: word_count={word_count}, score=1")
                    else:
                        logger.warning(f"Used fallback grading for Q{wq.id}: word_count={word_count}, score=0")
        
        percentage = (total_score / max_score * 100) if max_score > 0 else 0
        passed = percentage >= attempt.level_exam.passing_score
        
        attempt.score = int(percentage)
        attempt.passed = passed
        attempt.submitted_at = timezone.now()
        attempt.save()
        
        if passed:
            student_level = StudentLevel.objects.get(
                student=request.user,
                level=attempt.level_exam.level
            )
            student_level.status = 'COMPLETED'
            student_level.completed_at = timezone.now()
            student_level.save()
    
    serializer = StudentLevelExamAttemptSerializer(attempt)
    
    return Response({
        'message': 'تم تسليم امتحان المستوى بنجاح',
        'result': {
            'attempt': serializer.data,
            'score': attempt.score,
            'max_score': 100,
            'passed': attempt.passed,
            'passing_score': attempt.level_exam.passing_score,
            'time_taken_seconds': attempt.time_taken,
            'time_taken_minutes': round(attempt.time_taken / 60, 2)
        },
        'level_status': 'COMPLETED' if passed else 'FAILED',
        'congratulations': '🎉 تهانينا! لقد أكملت المستوى بنجاح!' if passed else None
    }, status=status.HTTP_200_OK)

# ============================================
# 12. EXAM RESULTS & HISTORY
# ============================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_unit_exam_attempts(request):
    """
    عرض جميع محاولات امتحانات الوحدات
    
    GET /api/levels/student/exams/unit/my-attempts/
    
    Query Parameters:
    - unit_id: filter by unit
    """
    unit_id = request.query_params.get('unit_id', None)
    
    attempts = StudentUnitExamAttempt.objects.filter(
        student=request.user
    ).select_related('unit_exam', 'unit_exam__unit').order_by('-started_at')
    
    if unit_id:
        attempts = attempts.filter(unit_exam__unit_id=unit_id)
    
    serializer = StudentUnitExamAttemptSerializer(attempts, many=True)
    
    # إحصائيات
    total_attempts = attempts.count()
    passed_attempts = attempts.filter(passed=True).count()
    
    return Response({
        'summary': {
            'total_attempts': total_attempts,
            'passed': passed_attempts,
            'failed': total_attempts - passed_attempts
        },
        'attempts': serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_level_exam_attempts(request):
    """
    عرض جميع محاولات امتحانات المستويات
    
    GET /api/levels/student/exams/level/my-attempts/
    """
    level_id = request.query_params.get('level_id', None)
    
    attempts = StudentLevelExamAttempt.objects.filter(
        student=request.user
    ).select_related('level_exam', 'level_exam__level').order_by('-started_at')
    
    if level_id:
        attempts = attempts.filter(level_exam__level_id=level_id)
    
    serializer = StudentLevelExamAttemptSerializer(attempts, many=True)
    
    # إحصائيات
    total_attempts = attempts.count()
    passed_attempts = attempts.filter(passed=True).count()
    
    return Response({
        'summary': {
            'total_attempts': total_attempts,
            'passed': passed_attempts,
            'failed': total_attempts - passed_attempts
        },
        'attempts': serializer.data
    }, status=status.HTTP_200_OK)