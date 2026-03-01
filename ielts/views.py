from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from cloudinary.models import CloudinaryResource

from .models import (
    IELTSSkill,
    LessonPack,
    IELTSLesson,
    ReadingLessonContent,
    WritingLessonContent,
    SpeakingLessonContent,
    ListeningLessonContent,
    IELTSPracticeExam,
    SpeakingRecordingTask,
    StudentSpeakingRecording,
    StudentLessonPackProgress,
    StudentLessonProgress,
    StudentPracticeExamAttempt,
)

from .serializers import (
    IELTSSkillSerializer,
    IELTSSkillListSerializer,
    IELTSLessonDetailWithQuestionsSerializer,
    LessonPackListSerializer,
    LessonPackDetailSerializer,
    IELTSLessonListSerializer,
    IELTSLessonDetailSerializer,
    ReadingLessonContentSerializer,
    WritingLessonContentSerializer,
    SpeakingLessonContentSerializer,
    ListeningLessonContentSerializer,
    IELTSPracticeExamSerializer,
    SpeakingRecordingTaskSerializer,
    StudentSpeakingRecordingSerializer,
    StudentLessonPackProgressSerializer,
    StudentLessonProgressSerializer,
    StudentPracticeExamAttemptSerializer,
)

import logging
logger = logging.getLogger(__name__)


# ============================================
# 1. IELTS SKILLS CRUD
# ============================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_skills(request):
    """
    عرض جميع المهارات
    
    GET /api/ielts/skills/
    """
    skills = IELTSSkill.objects.filter(is_active=True).order_by('order')
    serializer = IELTSSkillListSerializer(skills, many=True)
    
    return Response({
        'total_skills': skills.count(),
        'skills': serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_skill(request, skill_id):
    """
    عرض تفاصيل مهارة
    
    GET /api/ielts/skills/{skill_id}/
    """
    skill = get_object_or_404(IELTSSkill, id=skill_id)
    serializer = IELTSSkillSerializer(skill)
    
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_skill(request):
    """
    إنشاء مهارة جديدة
    
    POST /api/ielts/skills/create/
    """
    serializer = IELTSSkillSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    skill = serializer.save()
    
    return Response({
        'message': 'تم إنشاء المهارة بنجاح',
        'skill': IELTSSkillSerializer(skill).data
    }, status=status.HTTP_201_CREATED)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_skill(request, skill_id):
    """
    تعديل مهارة
    
    PUT/PATCH /api/ielts/skills/{skill_id}/update/
    """
    skill = get_object_or_404(IELTSSkill, id=skill_id)
    
    partial = request.method == 'PATCH'
    serializer = IELTSSkillSerializer(skill, data=request.data, partial=partial)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    skill = serializer.save()
    
    return Response({
        'message': 'تم تحديث المهارة بنجاح',
        'skill': IELTSSkillSerializer(skill).data
    }, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_skill(request, skill_id):
    """
    حذف مهارة
    
    DELETE /api/ielts/skills/{skill_id}/delete/
    """
    skill = get_object_or_404(IELTSSkill, id=skill_id)
    
    skill_type = skill.skill_type
    title = skill.title
    skill.delete()
    
    return Response({
        'message': 'تم حذف المهارة بنجاح',
        'skill_id': skill_id,
        'skill_type': skill_type,
        'title': title
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_skill_lesson_packs(request, skill_id):
    """
    الحصول على جميع Lesson Packs تحت مهارة معينة
    
    GET /api/ielts/skills/{skill_id}/lesson-packs/
    """
    skill = get_object_or_404(IELTSSkill, id=skill_id)
    lesson_packs = skill.lesson_packs.filter(is_active=True).order_by('order')
    serializer = LessonPackListSerializer(lesson_packs, many=True)
    
    return Response({
        'skill': {
            'id': skill.id,
            'skill_type': skill.skill_type,
            'title': skill.title
        },
        'total_lesson_packs': lesson_packs.count(),
        'lesson_packs': serializer.data
    }, status=status.HTTP_200_OK)


# ============================================
# 2. LESSON PACKS CRUD
# ============================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_lesson_packs(request):
    """
    عرض جميع Lesson Packs
    
    GET /api/ielts/lesson-packs/
    """
    skill_id = request.query_params.get('skill_id')
    skill_type = request.query_params.get('skill_type')
    
    lesson_packs = LessonPack.objects.select_related('skill').filter(is_active=True)
    
    if skill_id:
        lesson_packs = lesson_packs.filter(skill_id=skill_id)
    
    if skill_type:
        lesson_packs = lesson_packs.filter(skill__skill_type=skill_type)
    
    lesson_packs = lesson_packs.order_by('skill__order', 'order')
    
    serializer = LessonPackListSerializer(lesson_packs, many=True)
    
    return Response({
        'total_lesson_packs': lesson_packs.count(),
        'lesson_packs': serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_lesson_pack(request, pack_id):
    """
    عرض تفاصيل Lesson Pack
    
    GET /api/ielts/lesson-packs/{pack_id}/
    """
    lesson_pack = get_object_or_404(
        LessonPack.objects.select_related('skill'),
        id=pack_id
    )
    serializer = LessonPackDetailSerializer(lesson_pack)
    
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_lesson_pack(request):
    """
    إنشاء Lesson Pack جديد
    
    POST /api/ielts/lesson-packs/create/
    """
    serializer = LessonPackDetailSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    with transaction.atomic():
        lesson_pack = serializer.save()
        
        # إنشاء Practice Exam تلقائياً
        IELTSPracticeExam.objects.get_or_create(
            lesson_pack=lesson_pack,
            defaults={
                'title': f'{lesson_pack.title} - Practice Exam',
                'instructions': 'Complete all questions within the time limit.'
            }
        )
    
    result_serializer = LessonPackDetailSerializer(lesson_pack)
    
    return Response({
        'message': 'تم إنشاء Lesson Pack بنجاح',
        'lesson_pack': result_serializer.data
    }, status=status.HTTP_201_CREATED)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_lesson_pack(request, pack_id):
    """
    تعديل Lesson Pack
    
    PUT/PATCH /api/ielts/lesson-packs/{pack_id}/update/
    """
    lesson_pack = get_object_or_404(LessonPack, id=pack_id)
    
    partial = request.method == 'PATCH'
    serializer = LessonPackDetailSerializer(lesson_pack, data=request.data, partial=partial)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    lesson_pack = serializer.save()
    
    return Response({
        'message': 'تم تحديث Lesson Pack بنجاح',
        'lesson_pack': LessonPackDetailSerializer(lesson_pack).data
    }, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_lesson_pack(request, pack_id):
    """
    حذف Lesson Pack
    
    DELETE /api/ielts/lesson-packs/{pack_id}/delete/
    """
    lesson_pack = get_object_or_404(LessonPack, id=pack_id)
    
    title = lesson_pack.title
    lesson_pack.delete()
    
    return Response({
        'message': 'تم حذف Lesson Pack بنجاح',
        'pack_id': pack_id,
        'title': title
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_lesson_pack_lessons(request, pack_id):
    """
    الحصول على جميع الدروس في Lesson Pack
    
    GET /api/ielts/lesson-packs/{pack_id}/lessons/
    """
    lesson_pack = get_object_or_404(LessonPack, id=pack_id)
    lessons = lesson_pack.lessons.filter(is_active=True).order_by('order')
    serializer = IELTSLessonListSerializer(lessons, many=True)
    
    return Response({
        'lesson_pack': {
            'id': lesson_pack.id,
            'title': lesson_pack.title
        },
        'total_lessons': lessons.count(),
        'lessons': serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_lesson_pack_practice_exam(request, pack_id):
    """
    الحصول على Practice Exam للـ Lesson Pack
    
    GET /api/ielts/lesson-packs/{pack_id}/practice-exam/
    """
    lesson_pack = get_object_or_404(LessonPack, id=pack_id)
    practice_exam = lesson_pack.get_practice_exam()
    
    if not practice_exam:
        return Response(
            {'error': 'لا يوجد امتحان لهذا الـ Lesson Pack'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    serializer = IELTSPracticeExamSerializer(practice_exam)
    
    return Response(serializer.data, status=status.HTTP_200_OK)


# ============================================
# 3. LESSONS CRUD
# ============================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_lessons(request):
    """
    عرض جميع الدروس
    
    GET /api/ielts/lessons/
    """
    lesson_pack_id = request.query_params.get('lesson_pack_id')
    skill_id = request.query_params.get('skill_id')
    
    lessons = IELTSLesson.objects.select_related('lesson_pack__skill').filter(is_active=True)
    
    if lesson_pack_id:
        lessons = lessons.filter(lesson_pack_id=lesson_pack_id)
    
    if skill_id:
        lessons = lessons.filter(lesson_pack__skill_id=skill_id)
    
    lessons = lessons.order_by('lesson_pack__order', 'order')
    
    serializer = IELTSLessonListSerializer(lessons, many=True)
    
    return Response({
        'total_lessons': lessons.count(),
        'lessons': serializer.data
    }, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_lesson(request, lesson_id):
    """
    عرض تفاصيل درس مع المحتوى والأسئلة
    
    GET /api/ielts/lessons/{lesson_id}/
    """
    lesson = get_object_or_404(
        IELTSLesson.objects.select_related('lesson_pack__skill'),
        id=lesson_id
    )
    serializer = IELTSLessonDetailWithQuestionsSerializer(lesson)

    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_lesson_with_content_and_questions(request):
    """
    إنشاء درس + محتوى + أسئلة في request واحد
    
    POST /api/ielts/lessons/create-full/
    
    Body for READING:
    {
        "lesson_pack": 1,
        "title": "Reading Academic Texts",
        "description": "...",
        "order": 1,
        "content": {
            "reading_text": "Academic texts are formal writings...",
            "explanation": "شرح الدرس",
            "vocabulary_words": ["formal", "academic"],
            "examples": [],
            "video_url": null
        },
        "questions": [
            {
                "question_text": "What is the main topic?",
                "choice_a": "Sports",
                "choice_b": "Academic writing",
                "choice_c": "History",
                "choice_d": "Science",
                "correct_answer": "B",
                "explanation": "The text is about academic writing",
                "points": 1,
                "order": 1
            }
        ]
    }
    
    Body for LISTENING:
    {
        "lesson_pack": 2,
        "title": "Listening to a Lecture",
        "description": "...",
        "order": 1,
        "content": {
            "audio_file": "https://res.cloudinary.com/.../audio.mp3",
            "transcript": "...",
            "vocabulary_explanation": "...",
            "tips": []
        },
        "questions": [ ... ]
    }
    """
    lesson_pack_id = request.data.get('lesson_pack')
    title = request.data.get('title')
    description = request.data.get('description', '')
    order = request.data.get('order', 0)
    content_data = request.data.get('content', {})
    questions_data = request.data.get('questions', [])

    if not lesson_pack_id or not title:
        return Response({
            'error': 'يجب إرسال lesson_pack و title'
        }, status=status.HTTP_400_BAD_REQUEST)

    lesson_pack = get_object_or_404(LessonPack, id=lesson_pack_id)
    skill_type = lesson_pack.skill.skill_type

    try:
        with transaction.atomic():
            # 1. إنشاء الدرس
            lesson = IELTSLesson.objects.create(
                lesson_pack=lesson_pack,
                title=title,
                description=description,
                order=order,
                is_active=request.data.get('is_active', True)
            )

            # 2. إنشاء المحتوى حسب الـ skill_type
            if skill_type == 'READING':
                from .models import ReadingLessonContent
                from sabr_questions.models import ReadingPassage, ReadingQuestion

                # إنشاء المحتوى
                content = ReadingLessonContent.objects.create(
                    lesson=lesson,
                    reading_text=content_data.get('reading_text', ''),
                    explanation=content_data.get('explanation', ''),
                    vocabulary_words=content_data.get('vocabulary_words', []),
                    examples=content_data.get('examples', []),
                    video_url=content_data.get('video_url'),
                    resources=content_data.get('resources', [])
                )

                # إنشاء Passage للأسئلة
                if questions_data:
                    passage = ReadingPassage.objects.create(
                        title=title,
                        passage_text=content_data.get('reading_text', ''),
                        usage_type='IELTS_LESSON',
                        ielts_lesson_pack=lesson_pack,
                        ielts_lesson=lesson,
                    )

                    for q in questions_data:
                        ReadingQuestion.objects.create(
                            passage=passage,
                            question_text=q.get('question_text'),
                            choice_a=q.get('choice_a'),
                            choice_b=q.get('choice_b'),
                            choice_c=q.get('choice_c'),
                            choice_d=q.get('choice_d'),
                            correct_answer=q.get('correct_answer'),
                            explanation=q.get('explanation', ''),
                            points=q.get('points', 1),
                            order=q.get('order', 0),
                        )

            elif skill_type == 'LISTENING':
                from .models import ListeningLessonContent
                from sabr_questions.models import ListeningAudio, ListeningQuestion

                audio_url = content_data.get('audio_file')
                if not audio_url:
                    raise ValueError('audio_file مطلوب لدرس الاستماع')

                # إنشاء ListeningAudio
                audio = ListeningAudio(
                    title=title,
                    transcript=content_data.get('transcript', ''),
                    duration=content_data.get('duration', 0),
                    usage_type='IELTS_LESSON',
                    ielts_lesson_pack=lesson_pack,
                    ielts_lesson=lesson,
                )

                # تعيين audio_file من Cloudinary URL
                if 'cloudinary.com' in audio_url:
                    from cloudinary.models import CloudinaryResource
                    parts = audio_url.split('/upload/')
                    public_id = '/'.join(parts[1].split('/')[1:]).rsplit('.', 1)[0] if len(parts) > 1 else 'default'
                    audio.audio_file = CloudinaryResource(
                        public_id=public_id,
                        format='mp3',
                        resource_type='video'
                    )
                audio.save()

                # إنشاء المحتوى
                content = ListeningLessonContent.objects.create(
                    lesson=lesson,
                    audio_file=audio_url,
                    transcript=content_data.get('transcript', ''),
                    vocabulary_explanation=content_data.get('vocabulary_explanation', ''),
                    listening_exercises=content_data.get('listening_exercises', []),
                    tips=content_data.get('tips', [])
                )

                # إنشاء الأسئلة
                for q in questions_data:
                    ListeningQuestion.objects.create(
                        audio=audio,
                        question_text=q.get('question_text'),
                        choice_a=q.get('choice_a'),
                        choice_b=q.get('choice_b'),
                        choice_c=q.get('choice_c'),
                        choice_d=q.get('choice_d'),
                        correct_answer=q.get('correct_answer'),
                        explanation=q.get('explanation', ''),
                        points=q.get('points', 1),
                        order=q.get('order', 0),
                    )

            elif skill_type == 'SPEAKING':
                from .models import SpeakingLessonContent
                from sabr_questions.models import SpeakingVideo, SpeakingQuestion

                video_url = content_data.get('video_file')
                if not video_url:
                    raise ValueError('video_file مطلوب لدرس التحدث')

                # إنشاء SpeakingVideo
                video = SpeakingVideo(
                    title=title,
                    description=content_data.get('description', ''),
                    duration=content_data.get('duration', 0),
                    usage_type='IELTS_LESSON',
                    ielts_lesson_pack=lesson_pack,
                    ielts_lesson=lesson,
                )

                if 'cloudinary.com' in video_url:
                    from cloudinary.models import CloudinaryResource
                    parts = video_url.split('/upload/')
                    public_id = '/'.join(parts[1].split('/')[1:]).rsplit('.', 1)[0] if len(parts) > 1 else 'default'
                    video.video_file = CloudinaryResource(
                        public_id=public_id,
                        format='mp4',
                        resource_type='video'
                    )
                video.save()

                # إنشاء المحتوى
                content = SpeakingLessonContent.objects.create(
                    lesson=lesson,
                    video_file=video_url,
                    dialogue_texts=content_data.get('dialogue_texts', []),
                    useful_phrases=content_data.get('useful_phrases', []),
                    audio_examples=content_data.get('audio_examples', []),
                    pronunciation_tips=content_data.get('pronunciation_tips', '')
                )

                # إنشاء الأسئلة
                for q in questions_data:
                    SpeakingQuestion.objects.create(
                        video=video,
                        question_text=q.get('question_text'),
                        choice_a=q.get('choice_a'),
                        choice_b=q.get('choice_b'),
                        choice_c=q.get('choice_c'),
                        choice_d=q.get('choice_d'),
                        correct_answer=q.get('correct_answer'),
                        explanation=q.get('explanation', ''),
                        points=q.get('points', 1),
                        order=q.get('order', 0),
                    )

            elif skill_type == 'WRITING':
                from .models import WritingLessonContent

                content = WritingLessonContent.objects.create(
                    lesson=lesson,
                    sample_texts=content_data.get('sample_texts', []),
                    writing_instructions=content_data.get('writing_instructions', ''),
                    tips=content_data.get('tips', []),
                    examples=content_data.get('examples', []),
                    video_url=content_data.get('video_url')
                )
                # Writing مفيهاش MCQ

        result_serializer = IELTSLessonDetailWithQuestionsSerializer(lesson)

        return Response({
            'message': 'تم إنشاء الدرس والمحتوى والأسئلة بنجاح',
            'lesson': result_serializer.data,
            'questions_created': len(questions_data)
        }, status=status.HTTP_201_CREATED)

    except ValueError as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        logger.error(f"Error creating IELTS lesson with content: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            'error': f'حدث خطأ: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_lesson(request):
    """
    إنشاء درس جديد
    
    POST /api/ielts/lessons/create/
    """
    serializer = IELTSLessonDetailSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    lesson = serializer.save()
    
    return Response({
        'message': 'تم إنشاء الدرس بنجاح',
        'lesson': IELTSLessonDetailSerializer(lesson).data,
        'note': 'يجب إضافة المحتوى للدرس'
    }, status=status.HTTP_201_CREATED)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_lesson(request, lesson_id):
    """
    تعديل درس
    
    PUT/PATCH /api/ielts/lessons/{lesson_id}/update/
    """
    lesson = get_object_or_404(IELTSLesson, id=lesson_id)
    
    partial = request.method == 'PATCH'
    serializer = IELTSLessonDetailSerializer(lesson, data=request.data, partial=partial)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    lesson = serializer.save()
    
    return Response({
        'message': 'تم تحديث الدرس بنجاح',
        'lesson': IELTSLessonDetailSerializer(lesson).data
    }, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_lesson(request, lesson_id):
    """
    حذف درس
    
    DELETE /api/ielts/lessons/{lesson_id}/delete/
    """
    lesson = get_object_or_404(IELTSLesson, id=lesson_id)
    
    title = lesson.title
    lesson.delete()
    
    return Response({
        'message': 'تم حذف الدرس بنجاح',
        'lesson_id': lesson_id,
        'title': title
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_lesson_complete(request, lesson_id):
    """
    تحديد الدرس كمكتمل للطالب الحالي
    
    POST /api/ielts/lessons/{lesson_id}/mark-complete/
    """
    lesson = get_object_or_404(IELTSLesson, id=lesson_id)
    student = request.user
    
    progress, created = StudentLessonProgress.objects.get_or_create(
        student=student,
        lesson=lesson
    )
    
    if not progress.is_completed:
        progress.is_completed = True
        progress.completed_at = timezone.now()
        progress.save()
        
        return Response({
            'message': 'تم تحديد الدرس كمكتمل',
            'completed_at': progress.completed_at
        }, status=status.HTTP_200_OK)
    
    return Response({
        'message': 'الدرس مكتمل بالفعل',
        'completed_at': progress.completed_at
    }, status=status.HTTP_200_OK)


# ============================================
# 4. STUDENT PROGRESS
# ============================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_progress(request):
    """
    عرض تقدم الطالب
    
    GET /api/ielts/student/my-progress/
    """
    # Lesson Pack Progress
    lesson_pack_progress = StudentLessonPackProgress.objects.filter(
        student=request.user
    ).select_related('lesson_pack__skill').order_by('-created_at')
    
    pack_serializer = StudentLessonPackProgressSerializer(lesson_pack_progress, many=True)
    
    # Lesson Progress
    lesson_progress = StudentLessonProgress.objects.filter(
        student=request.user,
        is_completed=True
    ).select_related('lesson__lesson_pack').order_by('-completed_at')[:20]
    
    lesson_serializer = StudentLessonProgressSerializer(lesson_progress, many=True)
    
    # إحصائيات
    total_packs = lesson_pack_progress.count()
    completed_packs = lesson_pack_progress.filter(is_completed=True).count()
    
    total_lessons = StudentLessonProgress.objects.filter(student=request.user).count()
    completed_lessons = StudentLessonProgress.objects.filter(
        student=request.user,
        is_completed=True
    ).count()
    
    return Response({
        'summary': {
            'lesson_packs': {
                'total': total_packs,
                'completed': completed_packs,
                'in_progress': total_packs - completed_packs
            },
            'lessons': {
                'total': total_lessons,
                'completed': completed_lessons,
                'in_progress': total_lessons - completed_lessons
            }
        },
        'lesson_pack_progress': pack_serializer.data,
        'recent_lessons': lesson_serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_lesson_pack_complete(request, pack_id):
    """
    تحديد Lesson Pack كمكتمل
    
    POST /api/ielts/student/lesson-packs/{pack_id}/mark-complete/
    """
    lesson_pack = get_object_or_404(LessonPack, id=pack_id)
    
    progress, created = StudentLessonPackProgress.objects.get_or_create(
        student=request.user,
        lesson_pack=lesson_pack
    )
    
    progress.mark_completed()
    
    serializer = StudentLessonPackProgressSerializer(progress)
    
    return Response({
        'message': 'تم تحديد Lesson Pack كمكتمل',
        'progress': serializer.data
    }, status=status.HTTP_200_OK)


# ============================================
# 5. EXAM ATTEMPTS
# ============================================
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_practice_exam(request, pack_id):
    lesson_pack = get_object_or_404(LessonPack, id=pack_id)
    practice_exam = lesson_pack.get_practice_exam()
    
    if not practice_exam:
        return Response(
            {'error': 'لا يوجد امتحان لهذا الـ Lesson Pack'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    last_attempt = StudentPracticeExamAttempt.objects.filter(
        student=request.user,
        practice_exam=practice_exam
    ).order_by('-attempt_number').first()
    
    attempt_number = (last_attempt.attempt_number + 1) if last_attempt else 1
    
    attempt = StudentPracticeExamAttempt.objects.create(
        student=request.user,
        practice_exam=practice_exam,
        attempt_number=attempt_number
    )
    
    from sabr_questions.models import (
        VocabularyQuestion, GrammarQuestion,
        ReadingPassage, ListeningAudio,
        SpeakingVideo, WritingQuestion
    )
    
    # ============================================
    # Helper لتحويل CloudinaryResource
    # ============================================
    def serialize_cloudinary(value):
        if value is None:
            return None
        if hasattr(value, 'url'):
            return value.url
        return str(value) if value else None
    
    # Vocabulary Questions
    vocabulary_questions = []
    for q in VocabularyQuestion.objects.filter(
        ielts_lesson_pack=lesson_pack,
        usage_type='IELTS',
        is_active=True
    ):
        vocabulary_questions.append({
            'id': q.id,
            'question_text': q.question_text,
            'choice_a': q.choice_a,
            'choice_b': q.choice_b,
            'choice_c': q.choice_c,
            'choice_d': q.choice_d,
            'points': q.points,
        })
    
    # Grammar Questions
    grammar_questions = []
    for q in GrammarQuestion.objects.filter(
        ielts_lesson_pack=lesson_pack,
        usage_type='IELTS',
        is_active=True
    ):
        grammar_questions.append({
            'id': q.id,
            'question_text': q.question_text,
            'choice_a': q.choice_a,
            'choice_b': q.choice_b,
            'choice_c': q.choice_c,
            'choice_d': q.choice_d,
            'points': q.points,
        })
    
    # Reading Passages + Questions
    reading_passages = []
    for passage in ReadingPassage.objects.filter(
        ielts_lesson_pack=lesson_pack,
        usage_type='IELTS',
        is_active=True
    ).prefetch_related('questions'):
        questions = []
        for q in passage.questions.filter(is_active=True):
            questions.append({
                'id': q.id,
                'question_text': q.question_text,
                'choice_a': q.choice_a,
                'choice_b': q.choice_b,
                'choice_c': q.choice_c,
                'choice_d': q.choice_d,
                'points': q.points,
            })
        reading_passages.append({
            'id': passage.id,
            'title': passage.title,
            'passage_text': passage.passage_text,
            'questions': questions,
        })
    
    # Listening Audios + Questions
    listening_audios = []
    for audio in ListeningAudio.objects.filter(
        ielts_lesson_pack=lesson_pack,
        usage_type='IELTS',
        is_active=True
    ).prefetch_related('questions'):
        questions = []
        for q in audio.questions.filter(is_active=True):
            questions.append({
                'id': q.id,
                'question_text': q.question_text,
                'choice_a': q.choice_a,
                'choice_b': q.choice_b,
                'choice_c': q.choice_c,
                'choice_d': q.choice_d,
                'points': q.points,
            })
        listening_audios.append({
            'id': audio.id,
            'title': audio.title,
            'audio_file': serialize_cloudinary(audio.audio_file),  # ✅ هنا الحل
            'questions': questions,
        })
    
    # Speaking Videos + Questions
    speaking_videos = []
    for video in SpeakingVideo.objects.filter(
        ielts_lesson_pack=lesson_pack,
        usage_type='IELTS',
        is_active=True
    ).prefetch_related('questions'):
        questions = []
        for q in video.questions.filter(is_active=True):
            questions.append({
                'id': q.id,
                'question_text': q.question_text,
                'choice_a': q.choice_a,
                'choice_b': q.choice_b,
                'choice_c': q.choice_c,
                'choice_d': q.choice_d,
                'points': q.points,
            })
        speaking_videos.append({
            'id': video.id,
            'title': video.title,
            'video_file': serialize_cloudinary(video.video_file),      # ✅ هنا الحل
            'thumbnail': serialize_cloudinary(video.thumbnail),        # ✅ هنا الحل
            'questions': questions,
        })
    
    # Writing Questions
    writing_questions = []
    for q in WritingQuestion.objects.filter(
        ielts_lesson_pack=lesson_pack,
        usage_type='IELTS',
        is_active=True
    ):
        writing_questions.append({
            'id': q.id,
            'title': q.title,
            'question_text': q.question_text,
            'question_image': serialize_cloudinary(q.question_image),  # ✅ هنا الحل
            'min_words': q.min_words,
            'max_words': q.max_words,
            'points': q.points,
        })
    
    serializer = StudentPracticeExamAttemptSerializer(attempt)
    
    return Response({
        'message': 'تم بدء الامتحان بنجاح',
        'attempt': serializer.data,
        'exam_info': {
            'time_limit': lesson_pack.exam_time_limit,
            'passing_score': lesson_pack.exam_passing_score,
            'total_questions': practice_exam.get_questions_count()
        },
        'questions': {
            'vocabulary': vocabulary_questions,
            'grammar': grammar_questions,
            'reading': reading_passages,
            'listening': listening_audios,
            'speaking': speaking_videos,
            'writing': writing_questions,
        }
    }, status=status.HTTP_201_CREATED)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_practice_exam(request, attempt_id):
    """
    تسليم Practice Exam
    
    POST /api/ielts/student/practice-exams/submit/{attempt_id}/
    
    Body:
    {
        "answers": {
            "vocabulary": {"63": "A", "64": "B"},
            "grammar":    {"61": "A", "62": "C"},
            "reading":    {"86": "A", "89": "B"},   ← question IDs مباشرة
            "listening":  {"49": "A"},               ← question IDs مباشرة
            "speaking":   {},
            "writing":    {"26": "My essay text..."}
        }
    }
    """
    attempt = get_object_or_404(
        StudentPracticeExamAttempt,
        id=attempt_id,
        student=request.user
    )
    
    if attempt.submitted_at:
        return Response(
            {'error': 'تم تسليم الامتحان بالفعل'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    from sabr_questions.models import (
        VocabularyQuestion, GrammarQuestion,
        ReadingQuestion, ListeningQuestion,
        SpeakingQuestion, WritingQuestion
    )
    from placement_test.services.ai_grading import ai_grading_service
    
    answers = request.data.get('answers', {})
    
    # التحقق من وجود answers
    if not answers:
        return Response(
            {'error': 'يجب إرسال الإجابات'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    lesson_pack = attempt.practice_exam.lesson_pack
    total_points = 0
    earned_points = 0
    results = {}
    
    # ============================================
    # Helper لتصحيح MCQ
    # ============================================
    def grade_mcq(model, answer_dict, result_key):
        nonlocal total_points, earned_points
        
        question_results = []
        
        for q_id_str, student_answer in answer_dict.items():
            try:
                question = model.objects.get(id=int(q_id_str))
                is_correct = question.correct_answer == student_answer.upper()
                
                total_points += question.points
                if is_correct:
                    earned_points += question.points
                
                question_results.append({
                    'question_id': question.id,
                    'student_answer': student_answer.upper(),
                    'correct_answer': question.correct_answer,
                    'is_correct': is_correct,
                    'points_earned': question.points if is_correct else 0,
                    'points_possible': question.points,
                })
            except (model.DoesNotExist, ValueError):
                continue
        
        results[result_key] = question_results
    
    # ============================================
    # تصحيح MCQ
    # ============================================
    grade_mcq(VocabularyQuestion, answers.get('vocabulary', {}), 'vocabulary')
    grade_mcq(GrammarQuestion,    answers.get('grammar', {}),    'grammar')
    grade_mcq(ReadingQuestion,    answers.get('reading', {}),    'reading')
    grade_mcq(ListeningQuestion,  answers.get('listening', {}),  'listening')
    grade_mcq(SpeakingQuestion,   answers.get('speaking', {}),   'speaking')
    
    # ============================================
    # تصحيح Writing بالـ AI
    # ============================================
    writing_results = []
    total_ai_cost = 0.0
    
    for q_id_str, student_text in answers.get('writing', {}).items():
        try:
            writing_question = WritingQuestion.objects.get(id=int(q_id_str))
            
            # التحقق من أن الإجابة مش فاضية
            if not student_text or not student_text.strip():
                writing_results.append({
                    'question_id': int(q_id_str),
                    'student_answer': '',
                    'score': 0,
                    'raw_score': 0,
                    'percentage': 0,
                    'is_correct': False,
                    'word_count': 0,
                    'is_within_limit': False,
                    'feedback': 'لم يتم تقديم إجابة',
                    'strengths': [],
                    'improvements': ['يجب كتابة إجابة'],
                    'points_possible': writing_question.points,
                })
                total_points += writing_question.points
                continue
            
            logger.info(f"AI grading writing Q:{q_id_str} for IELTS attempt:{attempt_id}")
            
            grading_result = ai_grading_service.grade_writing_question(
                question_text=writing_question.question_text,
                student_answer=student_text,
                sample_answer=writing_question.sample_answer or '',
                rubric=writing_question.rubric or '',
                max_points=writing_question.points,
                min_words=writing_question.min_words,
                max_words=writing_question.max_words,
                pass_threshold=writing_question.pass_threshold
            )
            
            total_points += writing_question.points
            if grading_result['is_correct']:
                earned_points += grading_result['score']  # 0 or 1
            
            total_ai_cost += grading_result.get('cost', 0.0)
            
            writing_results.append({
                'question_id': int(q_id_str),
                'student_answer': student_text,
                'score': grading_result['score'],             # 0 or 1
                'raw_score': grading_result.get('raw_score', 0),
                'percentage': grading_result.get('percentage', 0),
                'is_correct': grading_result['is_correct'],
                'word_count': grading_result['word_count'],
                'is_within_limit': grading_result['is_within_limit'],
                'feedback': grading_result['feedback'],
                'strengths': grading_result['strengths'],
                'improvements': grading_result['improvements'],
                'points_possible': writing_question.points,
                'pass_threshold': writing_question.pass_threshold,
            })
            
        except WritingQuestion.DoesNotExist:
            continue
        except Exception as e:
            logger.error(f"Error grading writing Q:{q_id_str} attempt:{attempt_id} - {str(e)}")
            writing_results.append({
                'question_id': int(q_id_str),
                'student_answer': student_text,
                'score': 0,
                'is_correct': False,
                'feedback': 'حدث خطأ أثناء التصحيح، سيتم المراجعة يدوياً',
                'status': 'error',
            })
    
    results['writing'] = writing_results
    
    # ============================================
    # حساب النتيجة النهائية
    # ============================================
    score_percentage = round(
        (earned_points / total_points * 100), 2
    ) if total_points > 0 else 0
    
    passing_score = lesson_pack.exam_passing_score or 70
    passed = score_percentage >= passing_score
    
    # حفظ النتيجة
    attempt.answers = answers
    attempt.score = score_percentage
    attempt.passed = passed
    attempt.mark_submitted()
    
    # ============================================
    # إحصائيات سريعة
    # ============================================
    def count_stats(result_list):
        correct = sum(1 for r in result_list if r.get('is_correct'))
        return {'correct': correct, 'total': len(result_list)}
    
    return Response({
        'message': 'تم تسليم الامتحان بنجاح',
        'result': {
            'attempt_id': attempt.id,
            'attempt_number': attempt.attempt_number,
            'score': score_percentage,
            'passed': passed,
            'passing_score': passing_score,
            'points': {
                'earned': earned_points,
                'total': total_points,
            },
            'submitted_at': attempt.submitted_at,
            'ai_grading_cost': round(total_ai_cost, 6),
            # إحصائيات سريعة لكل section
            'summary': {
                'vocabulary': count_stats(results.get('vocabulary', [])),
                'grammar':    count_stats(results.get('grammar', [])),
                'reading':    count_stats(results.get('reading', [])),
                'listening':  count_stats(results.get('listening', [])),
                'speaking':   count_stats(results.get('speaking', [])),
                'writing':    count_stats(results.get('writing', [])),
            },
            # تفصيل كل سؤال
            'breakdown': results,
        }
    }, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_exam_attempts(request):
    """
    عرض محاولات الامتحانات
    
    GET /api/ielts/student/my-exam-attempts/
    """
    pack_id = request.query_params.get('lesson_pack_id')
    
    attempts = StudentPracticeExamAttempt.objects.filter(
        student=request.user
    ).select_related('practice_exam__lesson_pack').order_by('-started_at')
    
    if pack_id:
        attempts = attempts.filter(practice_exam__lesson_pack_id=pack_id)
    
    serializer = StudentPracticeExamAttemptSerializer(attempts, many=True)
    
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
def get_practice_exam(request, exam_id):
    """
    عرض تفاصيل Practice Exam
    
    GET /api/ielts/practice-exams/{exam_id}/
    """
    practice_exam = get_object_or_404(
        IELTSPracticeExam.objects.select_related('lesson_pack__skill'),
        id=exam_id
    )
    
    serializer = IELTSPracticeExamSerializer(practice_exam)
    
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_vocabulary_question(request):
    """
    إنشاء سؤال Vocabulary جديد
    
    POST /api/ielts/vocabulary/create/
    """
    from sabr_questions.models import VocabularyQuestion, VocabularyQuestionSet
    
    data = request.data.copy()
    
    # التحقق من البيانات المطلوبة
    required_fields = ['question_text', 'options', 'correct_answer', 'ielts_lesson_pack']
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
        
        # Create or get default question set for IELTS
        question_set, _ = VocabularyQuestionSet.objects.get_or_create(
            title='IELTS Vocabulary Questions',
            usage_type='IELTS',
            defaults={'description': 'Auto-generated set for IELTS'}
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
            'usage_type': data.get('usage_type', 'IELTS'),
            'ielts_lesson_pack_id': data.get('ielts_lesson_pack'),
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
    
    POST /ielts/Grammar/create/
    """
    from sabr_questions.models import GrammarQuestion, GrammarQuestionSet
    
    data = request.data.copy()
    
    # التحقق من البيانات المطلوبة
    required_fields = ['question_text', 'options', 'correct_answer', 'ielts_lesson_pack']
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
        
        # Create or get default question set for IELTS
        question_set, _ = GrammarQuestionSet.objects.get_or_create(
            title='IELTS Grammar Questions',
            usage_type='IELTS',
            defaults={'description': 'Auto-generated set for IELTS'}
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
            'usage_type': data.get('usage_type', 'IELTS'),
            'ielts_lesson_pack_id': data.get('ielts_lesson_pack'),
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
        logger.error(f"Error creating Grammar question: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )

# في نهاية ملف views.py اضف الكود ده:

# ============================================
# 6. READING PASSAGES & QUESTIONS
# ============================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_reading_passage(request):
    """
    إنشاء قطعة قراءة جديدة
    
    POST /api/ielts/reading/passages/create/
    """
    from sabr_questions.models import ReadingPassage
    
    data = request.data.copy()
    
    # التحقق من البيانات المطلوبة
    required_fields = ['title', 'passage_text', 'ielts_lesson_pack']
    for field in required_fields:
        if field not in data:
            return Response(
                {field: f'{field} مطلوب'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    try:
        # تحضير البيانات للـ model
        passage_data = {
            'title': data.get('title'),
            'passage_text': data.get('passage_text'),
            'usage_type': data.get('usage_type', 'IELTS'),
            'ielts_lesson_pack_id': data.get('ielts_lesson_pack'),
            'is_active': data.get('is_active', True),
            'order': 0,
        }
        
        # إضافة الحقول الاختيارية
        if 'difficulty' in data:
            passage_data['difficulty'] = data.get('difficulty')
        
        if 'reading_time' in data:
            passage_data['reading_time'] = data.get('reading_time')
        
        if 'source' in data:
            passage_data['source'] = data.get('source')
        
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
    
    POST /api/ielts/reading/passages/{passage_id}/questions/create/
    """
    from sabr_questions.models import ReadingPassage, ReadingQuestion
    
    # التحقق من وجود القطعة
    try:
        passage = ReadingPassage.objects.get(id=passage_id)
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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_reading_passage(request, passage_id):
    """
    الحصول على تفاصيل قطعة قراءة مع أسئلتها
    
    GET /api/ielts/reading/passages/{passage_id}/
    """
    from sabr_questions.models import ReadingPassage
    
    try:
        passage = ReadingPassage.objects.prefetch_related('questions').get(id=passage_id)
        
        questions_data = []
        for q in passage.questions.all():
            questions_data.append({
                'id': q.id,
                'question_text': q.question_text,
                'choice_a': q.choice_a,
                'choice_b': q.choice_b,
                'choice_c': q.choice_c,
                'choice_d': q.choice_d,
                'correct_answer': q.correct_answer,
                'explanation': q.explanation,
                'points': q.points,
                'order': q.order,
            })
        
        return Response({
            'id': passage.id,
            'title': passage.title,
            'passage_text': passage.passage_text,
            'difficulty': passage.difficulty if hasattr(passage, 'difficulty') else None,
            'reading_time': passage.reading_time if hasattr(passage, 'reading_time') else None,
            'source': passage.source,
            'questions_count': passage.questions.count(),
            'questions': questions_data,
            'created_at': passage.created_at,
        }, status=status.HTTP_200_OK)
        
    except ReadingPassage.DoesNotExist:
        return Response(
            {'error': 'القطعة غير موجودة'},
            status=status.HTTP_404_NOT_FOUND
        )

# في نهاية ملف views.py اضف الكود ده:

# ============================================
# 7. LISTENING AUDIOS & QUESTIONS
# ============================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_listening_audio(request):
    """
    إنشاء تسجيل صوتي جديد
    
    POST /api/ielts/listening/audios/create/
    """
    from sabr_questions.models import ListeningAudio
    
    data = request.data.copy()
    
    # التحقق من البيانات المطلوبة
    required_fields = ['title', 'audio_file', 'ielts_lesson_pack']
    for field in required_fields:
        if field not in data:
            return Response(
                {field: f'{field} مطلوب'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    try:
        # تحضير البيانات للـ model
        audio_data = {
            'title': data.get('title'),
            'audio_file': data.get('audio_file'),
            'usage_type': data.get('usage_type', 'IELTS'),
            'ielts_lesson_pack_id': data.get('ielts_lesson_pack'),
            'is_active': data.get('is_active', True),
            'order': 0,
        }
        
        # إضافة الحقول الاختيارية
        if 'transcript' in data:
            audio_data['transcript'] = data.get('transcript')
        
        if 'duration' in data:
            audio_data['duration'] = data.get('duration')
        
        # إنشاء التسجيل
        audio = ListeningAudio.objects.create(**audio_data)
        
        return Response({
            'message': 'تم إنشاء التسجيل بنجاح',
            'audio': {
                'id': audio.id,
                'title': audio.title,
                'created_at': audio.created_at
            }
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error creating listening audio: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_listening_question(request, audio_id):
    """
    إنشاء سؤال استماع جديد لتسجيل معين
    
    POST /api/ielts/listening/audios/{audio_id}/questions/create/
    """
    from sabr_questions.models import ListeningAudio, ListeningQuestion
    
    # التحقق من وجود التسجيل
    try:
        audio = ListeningAudio.objects.get(id=audio_id)
    except ListeningAudio.DoesNotExist:
        return Response(
            {'error': 'التسجيل غير موجود'},
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
            'audio': audio,
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
        question = ListeningQuestion.objects.create(**question_data)
        
        return Response({
            'message': 'تم إنشاء السؤال بنجاح',
            'question': {
                'id': question.id,
                'question_text': question.question_text,
                'created_at': question.created_at
            }
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error creating listening question: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_listening_audio(request, audio_id):
    """
    الحصول على تفاصيل تسجيل صوتي مع أسئلته
    
    GET /api/ielts/listening/audios/{audio_id}/
    """
    from sabr_questions.models import ListeningAudio
    
    try:
        audio = ListeningAudio.objects.prefetch_related('questions').get(id=audio_id)
        
        questions_data = []
        for q in audio.questions.all():
            questions_data.append({
                'id': q.id,
                'question_text': q.question_text,
                'choice_a': q.choice_a,
                'choice_b': q.choice_b,
                'choice_c': q.choice_c,
                'choice_d': q.choice_d,
                'correct_answer': q.correct_answer,
                'explanation': q.explanation,
                'points': q.points,
                'order': q.order,
            })
        
        return Response({
            'id': audio.id,
            'title': audio.title,
            'audio_file': audio.audio_file,
            'transcript': audio.transcript,
            'duration': audio.duration,
            'questions_count': audio.questions.count(),
            'questions': questions_data,
            'created_at': audio.created_at,
        }, status=status.HTTP_200_OK)
        
    except ListeningAudio.DoesNotExist:
        return Response(
            {'error': 'التسجيل غير موجود'},
            status=status.HTTP_404_NOT_FOUND
        )


# ============================================
# 8. SPEAKING VIDEOS & QUESTIONS
# ============================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_speaking_video(request):
    """
    إنشاء فيديو تحدث جديد
    
    POST /api/ielts/speaking/videos/create/
    """
    from sabr_questions.models import SpeakingVideo
    
    data = request.data.copy()
    
    # التحقق من البيانات المطلوبة
    required_fields = ['title', 'video_file', 'ielts_lesson_pack']
    for field in required_fields:
        if field not in data:
            return Response(
                {field: f'{field} مطلوب'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    try:
        # تحضير البيانات للـ model
        video_data = {
            'title': data.get('title'),
            'video_file': data.get('video_file'),
            'usage_type': data.get('usage_type', 'IELTS'),
            'ielts_lesson_pack_id': data.get('ielts_lesson_pack'),
            'is_active': data.get('is_active', True),
            'order': 0,
        }
        
        # إضافة الحقول الاختيارية
        if 'description' in data:
            video_data['description'] = data.get('description')
        
        if 'duration' in data:
            video_data['duration'] = data.get('duration')
        
        if 'thumbnail' in data:
            video_data['thumbnail'] = data.get('thumbnail')
        
        # إنشاء الفيديو
        video = SpeakingVideo.objects.create(**video_data)
        
        return Response({
            'message': 'تم إنشاء الفيديو بنجاح',
            'video': {
                'id': video.id,
                'title': video.title,
                'created_at': video.created_at
            }
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error creating speaking video: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_speaking_question(request, video_id):
    """
    إنشاء سؤال تحدث جديد لفيديو معين
    
    POST /api/ielts/speaking/videos/{video_id}/questions/create/
    """
    from sabr_questions.models import SpeakingVideo, SpeakingQuestion
    
    # التحقق من وجود الفيديو
    try:
        video = SpeakingVideo.objects.get(id=video_id)
    except SpeakingVideo.DoesNotExist:
        return Response(
            {'error': 'الفيديو غير موجود'},
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
            'video': video,
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
        question = SpeakingQuestion.objects.create(**question_data)
        
        return Response({
            'message': 'تم إنشاء السؤال بنجاح',
            'question': {
                'id': question.id,
                'question_text': question.question_text,
                'created_at': question.created_at
            }
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error creating speaking question: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_speaking_video(request, video_id):
    """
    الحصول على تفاصيل فيديو مع أسئلته
    
    GET /api/ielts/speaking/videos/{video_id}/
    """
    from sabr_questions.models import SpeakingVideo
    
    try:
        video = SpeakingVideo.objects.prefetch_related('questions').get(id=video_id)
        
        questions_data = []
        for q in video.questions.all():
            questions_data.append({
                'id': q.id,
                'question_text': q.question_text,
                'choice_a': q.choice_a,
                'choice_b': q.choice_b,
                'choice_c': q.choice_c,
                'choice_d': q.choice_d,
                'correct_answer': q.correct_answer,
                'explanation': q.explanation,
                'points': q.points,
                'order': q.order,
            })
        
        return Response({
            'id': video.id,
            'title': video.title,
            'video_file': video.video_file,
            'description': video.description,
            'duration': video.duration,
            'thumbnail': video.thumbnail,
            'questions_count': video.questions.count(),
            'questions': questions_data,
            'created_at': video.created_at,
        }, status=status.HTTP_200_OK)
        
    except SpeakingVideo.DoesNotExist:
        return Response(
            {'error': 'الفيديو غير موجود'},
            status=status.HTTP_404_NOT_FOUND
        )
# في نهاية ملف views.py اضف:

# ============================================
# 9. WRITING QUESTIONS
# ============================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_writing_question(request):
    """
    إنشاء سؤال كتابة جديد
    
    POST /api/ielts/writing/questions/create/
    """
    from sabr_questions.models import WritingQuestion
    
    data = request.data.copy()
    
    # التحقق من البيانات المطلوبة
    required_fields = ['title', 'question_text', 'min_words', 'max_words', 'sample_answer', 'rubric', 'ielts_lesson_pack']
    for field in required_fields:
        if field not in data:
            return Response(
                {field: f'{field} مطلوب'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    try:
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
            'usage_type': data.get('usage_type', 'IELTS'),
            'ielts_lesson_pack_id': data.get('ielts_lesson_pack'),
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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_writing_question(request, question_id):
    """
    الحصول على تفاصيل سؤال كتابة
    
    GET /api/ielts/writing/questions/{question_id}/
    """
    from sabr_questions.models import WritingQuestion
    
    try:
        question = WritingQuestion.objects.get(id=question_id)
        
        return Response({
            'id': question.id,
            'title': question.title,
            'question_text': question.question_text,
            'question_image': question.question_image.url if question.question_image else None,
            'min_words': question.min_words,
            'max_words': question.max_words,
            'sample_answer': question.sample_answer,
            'rubric': question.rubric,
            'points': question.points,
            'pass_threshold': question.pass_threshold,
            'created_at': question.created_at,
        }, status=status.HTTP_200_OK)
        
    except WritingQuestion.DoesNotExist:
        return Response(
            {'error': 'السؤال غير موجود'},
            status=status.HTTP_404_NOT_FOUND
        )