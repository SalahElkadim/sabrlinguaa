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
    skills = IELTSSkill.objects.filter(is_active=True).order_by('order')
    serializer = IELTSSkillListSerializer(skills, many=True)
    return Response({'total_skills': skills.count(), 'skills': serializer.data})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_skill(request, skill_id):
    skill = get_object_or_404(IELTSSkill, id=skill_id)
    return Response(IELTSSkillSerializer(skill).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_skill(request):
    serializer = IELTSSkillSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    skill = serializer.save()
    return Response({'message': 'تم إنشاء المهارة بنجاح', 'skill': IELTSSkillSerializer(skill).data}, status=status.HTTP_201_CREATED)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_skill(request, skill_id):
    skill = get_object_or_404(IELTSSkill, id=skill_id)
    serializer = IELTSSkillSerializer(skill, data=request.data, partial=request.method == 'PATCH')
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    skill = serializer.save()
    return Response({'message': 'تم تحديث المهارة بنجاح', 'skill': IELTSSkillSerializer(skill).data})


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_skill(request, skill_id):
    skill = get_object_or_404(IELTSSkill, id=skill_id)
    skill_type, title = skill.skill_type, skill.title
    skill.delete()
    return Response({'message': 'تم حذف المهارة بنجاح', 'skill_id': skill_id, 'skill_type': skill_type, 'title': title})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_skill_lesson_packs(request, skill_id):
    skill = get_object_or_404(IELTSSkill, id=skill_id)
    lesson_packs = skill.lesson_packs.filter(is_active=True).order_by('order')
    serializer = LessonPackListSerializer(lesson_packs, many=True)
    return Response({
        'skill': {'id': skill.id, 'skill_type': skill.skill_type, 'title': skill.title},
        'total_lesson_packs': lesson_packs.count(),
        'lesson_packs': serializer.data
    })


# ============================================
# 2. LESSON PACKS CRUD
# ============================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_lesson_packs(request):
    skill_id = request.query_params.get('skill_id')
    skill_type = request.query_params.get('skill_type')
    lesson_packs = LessonPack.objects.select_related('skill').filter(is_active=True)
    if skill_id:
        lesson_packs = lesson_packs.filter(skill_id=skill_id)
    if skill_type:
        lesson_packs = lesson_packs.filter(skill__skill_type=skill_type)
    lesson_packs = lesson_packs.order_by('skill__order', 'order')
    serializer = LessonPackListSerializer(lesson_packs, many=True)
    return Response({'total_lesson_packs': lesson_packs.count(), 'lesson_packs': serializer.data})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_lesson_pack(request, pack_id):
    lesson_pack = get_object_or_404(LessonPack.objects.select_related('skill'), id=pack_id)
    return Response(LessonPackDetailSerializer(lesson_pack).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_lesson_pack(request):
    serializer = LessonPackDetailSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    with transaction.atomic():
        lesson_pack = serializer.save()
        IELTSPracticeExam.objects.get_or_create(
            lesson_pack=lesson_pack,
            defaults={
                'title': f'{lesson_pack.title} - Practice Exam',
                'instructions': 'Complete all questions within the time limit.'
            }
        )
    return Response({'message': 'تم إنشاء Lesson Pack بنجاح', 'lesson_pack': LessonPackDetailSerializer(lesson_pack).data}, status=status.HTTP_201_CREATED)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_lesson_pack(request, pack_id):
    lesson_pack = get_object_or_404(LessonPack, id=pack_id)
    serializer = LessonPackDetailSerializer(lesson_pack, data=request.data, partial=request.method == 'PATCH')
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    lesson_pack = serializer.save()
    return Response({'message': 'تم تحديث Lesson Pack بنجاح', 'lesson_pack': LessonPackDetailSerializer(lesson_pack).data})


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_lesson_pack(request, pack_id):
    lesson_pack = get_object_or_404(LessonPack, id=pack_id)
    title = lesson_pack.title
    lesson_pack.delete()
    return Response({'message': 'تم حذف Lesson Pack بنجاح', 'pack_id': pack_id, 'title': title})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_lesson_pack_lessons(request, pack_id):
    lesson_pack = get_object_or_404(LessonPack, id=pack_id)
    lessons = lesson_pack.lessons.filter(is_active=True).order_by('order')
    serializer = IELTSLessonListSerializer(lessons, many=True)
    return Response({
        'lesson_pack': {'id': lesson_pack.id, 'title': lesson_pack.title},
        'total_lessons': lessons.count(),
        'lessons': serializer.data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_lesson_pack_practice_exam(request, pack_id):
    lesson_pack = get_object_or_404(LessonPack, id=pack_id)
    practice_exam = lesson_pack.get_practice_exam()
    if not practice_exam:
        return Response({'error': 'لا يوجد امتحان لهذا الـ Lesson Pack'}, status=status.HTTP_404_NOT_FOUND)
    return Response(IELTSPracticeExamSerializer(practice_exam).data)


# ============================================
# 3. LESSONS CRUD
# ============================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_lessons(request):
    lesson_pack_id = request.query_params.get('lesson_pack_id')
    skill_id = request.query_params.get('skill_id')
    lessons = IELTSLesson.objects.select_related('lesson_pack__skill').filter(is_active=True)
    if lesson_pack_id:
        lessons = lessons.filter(lesson_pack_id=lesson_pack_id)
    if skill_id:
        lessons = lessons.filter(lesson_pack__skill_id=skill_id)
    lessons = lessons.order_by('lesson_pack__order', 'order')
    return Response({'total_lessons': lessons.count(), 'lessons': IELTSLessonListSerializer(lessons, many=True).data})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_lesson(request, lesson_id):
    lesson = get_object_or_404(
        IELTSLesson.objects.select_related('lesson_pack__skill'),
        id=lesson_id
    )
    return Response(IELTSLessonDetailWithQuestionsSerializer(lesson).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_lesson(request):
    serializer = IELTSLessonDetailSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    lesson = serializer.save()
    return Response({
        'message': 'تم إنشاء الدرس بنجاح',
        'lesson': IELTSLessonDetailSerializer(lesson).data,
        'note': 'يجب إضافة المحتوى للدرس'
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_lesson_with_content_and_questions(request):
    """
    إنشاء درس + محتوى + أسئلة في request واحد
    POST /api/ielts/lessons/create-full/
    """
    lesson_pack_id = request.data.get('lesson_pack')
    title = request.data.get('title')
    description = request.data.get('description', '')
    order = request.data.get('order', 0)
    content_data = request.data.get('content', {})
    questions_data = request.data.get('questions', [])

    if not lesson_pack_id or not title:
        return Response({'error': 'يجب إرسال lesson_pack و title'}, status=status.HTTP_400_BAD_REQUEST)

    lesson_pack = get_object_or_404(LessonPack, id=lesson_pack_id)
    skill_type = lesson_pack.skill.skill_type

    try:
        with transaction.atomic():
            lesson = IELTSLesson.objects.create(
                lesson_pack=lesson_pack,
                title=title,
                description=description,
                order=order,
                is_active=request.data.get('is_active', True)
            )

            if skill_type == 'READING':
                from sabr_questions.models import ReadingPassage, ReadingQuestion
                content = ReadingLessonContent.objects.create(
                    lesson=lesson,
                    reading_text=content_data.get('reading_text', ''),
                    explanation=content_data.get('explanation', ''),
                    vocabulary_words=content_data.get('vocabulary_words', []),
                    examples=content_data.get('examples', []),
                    video_url=content_data.get('video_url'),
                    resources=content_data.get('resources', [])
                )
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
                from sabr_questions.models import ListeningAudio, ListeningQuestion
                audio_url = content_data.get('audio_file')
                if not audio_url:
                    raise ValueError('audio_file مطلوب لدرس الاستماع')
                audio = ListeningAudio.objects.create(
                    title=title,
                    audio_file=audio_url,
                    transcript=content_data.get('transcript', ''),
                    duration=content_data.get('duration', 0),
                    usage_type='IELTS_LESSON',
                    ielts_lesson_pack=lesson_pack,
                    ielts_lesson=lesson,
                )
                ListeningLessonContent.objects.create(
                    lesson=lesson,
                    audio_file=audio_url,
                    transcript=content_data.get('transcript', ''),
                    vocabulary_explanation=content_data.get('vocabulary_explanation', ''),
                    listening_exercises=content_data.get('listening_exercises', []),
                    tips=content_data.get('tips', [])
                )
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
                from sabr_questions.models import SpeakingVideo, SpeakingQuestion
                video_url = content_data.get('video_file')
                if not video_url:
                    raise ValueError('video_file مطلوب لدرس التحدث')
                video = SpeakingVideo.objects.create(
                    title=title,
                    video_file=video_url,
                    description=content_data.get('description', ''),
                    duration=content_data.get('duration', 0),
                    usage_type='IELTS_LESSON',
                    ielts_lesson_pack=lesson_pack,
                    ielts_lesson=lesson,
                )
                SpeakingLessonContent.objects.create(
                    lesson=lesson,
                    video_file=video_url,
                    dialogue_texts=content_data.get('dialogue_texts', []),
                    useful_phrases=content_data.get('useful_phrases', []),
                    audio_examples=content_data.get('audio_examples', []),
                    pronunciation_tips=content_data.get('pronunciation_tips', '')
                )
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
                WritingLessonContent.objects.create(
                    lesson=lesson,
                    sample_texts=content_data.get('sample_texts', []),
                    writing_instructions=content_data.get('writing_instructions', ''),
                    tips=content_data.get('tips', []),
                    examples=content_data.get('examples', []),
                    video_url=content_data.get('video_url')
                )

        result_serializer = IELTSLessonDetailWithQuestionsSerializer(lesson)
        return Response({
            'message': 'تم إنشاء الدرس والمحتوى والأسئلة بنجاح',
            'lesson': result_serializer.data,
            'questions_created': len(questions_data)
        }, status=status.HTTP_201_CREATED)

    except ValueError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error creating IELTS lesson with content: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({'error': f'حدث خطأ: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_lesson(request, lesson_id):
    lesson = get_object_or_404(IELTSLesson, id=lesson_id)
    serializer = IELTSLessonDetailSerializer(lesson, data=request.data, partial=request.method == 'PATCH')
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    lesson = serializer.save()
    return Response({'message': 'تم تحديث الدرس بنجاح', 'lesson': IELTSLessonDetailSerializer(lesson).data})


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_lesson(request, lesson_id):
    lesson = get_object_or_404(IELTSLesson, id=lesson_id)
    title = lesson.title
    lesson.delete()
    return Response({'message': 'تم حذف الدرس بنجاح', 'lesson_id': lesson_id, 'title': title})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_lesson_complete(request, lesson_id):
    lesson = get_object_or_404(IELTSLesson, id=lesson_id)
    progress, created = StudentLessonProgress.objects.get_or_create(student=request.user, lesson=lesson)
    if not progress.is_completed:
        progress.is_completed = True
        progress.completed_at = timezone.now()
        progress.save()
        return Response({'message': 'تم تحديد الدرس كمكتمل', 'completed_at': progress.completed_at})
    return Response({'message': 'الدرس مكتمل بالفعل', 'completed_at': progress.completed_at})


# ============================================
# 3b. LESSON CONTENT CREATION (Per Skill)
# ============================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_reading_lesson_content(request, lesson_id):
    """
    إنشاء محتوى درس قراءة + Passage + Questions
    POST /api/ielts/lessons/{lesson_id}/content/reading/create/
    
    Body:
    {
        "passage_title": "The History of Science",
        "passage_text": "Academic texts are...",
        "source": "Teacher Created",
        "explanation": "شرح الدرس",
        "vocabulary_words": [{"english_word": "formal", "translate": "رسمي"}],
        "video_url": "",
        "questions": [
            {
                "question_text": "What is...",
                "choice_a": "A",
                "choice_b": "B",
                "choice_c": "C",
                "choice_d": "D",
                "correct_answer": "B",
                "explanation": "...",
                "points": 1
            }
        ]
    }
    """
    lesson = get_object_or_404(
        IELTSLesson.objects.select_related('lesson_pack__skill'),
        id=lesson_id
    )

    if lesson.lesson_pack.skill.skill_type != 'READING':
        return Response({'error': 'هذا الدرس ليس درس قراءة'}, status=status.HTTP_400_BAD_REQUEST)

    passage_text = request.data.get('passage_text', '')
    if not passage_text.strip():
        return Response({'error': 'passage_text مطلوب'}, status=status.HTTP_400_BAD_REQUEST)

    questions_data = request.data.get('questions', [])
    vocabulary_words = request.data.get('vocabulary_words', [])

    try:
        with transaction.atomic():
            # حذف المحتوى القديم لو موجود
            ReadingLessonContent.objects.filter(lesson=lesson).delete()

            # إنشاء ReadingLessonContent
            content = ReadingLessonContent.objects.create(
                lesson=lesson,
                reading_text=passage_text,
                explanation=request.data.get('explanation', ''),
                vocabulary_words=vocabulary_words,
                examples=request.data.get('examples', []),
                video_url=request.data.get('video_url') or None,
                resources=request.data.get('resources', [])
            )

            # إنشاء ReadingPassage + Questions
            passage = None
            questions_created = 0

            if questions_data:
                from sabr_questions.models import ReadingPassage, ReadingQuestion

                # حذف الـ passage القديم لو موجود
                ReadingPassage.objects.filter(
                    ielts_lesson=lesson
                ).delete()

                passage = ReadingPassage.objects.create(
                    title=request.data.get('passage_title', lesson.title),
                    passage_text=passage_text,
                    source=request.data.get('source', 'Teacher Created'),
                    usage_type='IELTS_LESSON',
                    ielts_lesson_pack=lesson.lesson_pack,
                    ielts_lesson=lesson,
                    is_active=True,
                )

                for i, q in enumerate(questions_data):
                    ReadingQuestion.objects.create(
                        passage=passage,
                        question_text=q.get('question_text', ''),
                        choice_a=q.get('choice_a', ''),
                        choice_b=q.get('choice_b', ''),
                        choice_c=q.get('choice_c', ''),
                        choice_d=q.get('choice_d', ''),
                        correct_answer=q.get('correct_answer', 'A'),
                        explanation=q.get('explanation', ''),
                        points=q.get('points', 1),
                        order=i + 1,
                        is_active=True,
                    )
                    questions_created += 1

        # إرجاع الدرس كامل
        lesson.refresh_from_db()
        return Response({
            'message': 'تم إضافة محتوى القراءة بنجاح',
            'lesson': IELTSLessonDetailWithQuestionsSerializer(lesson).data,
            'questions_created': questions_created,
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f"Error creating reading lesson content: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_listening_lesson_content(request, lesson_id):
    """
    إنشاء محتوى درس استماع + ListeningAudio + Questions
    POST /api/ielts/lessons/{lesson_id}/content/listening/create/
    
    Body:
    {
        "title": "IELTS Listening - Part 1",
        "audio_file": "https://res.cloudinary.com/.../audio.mp3",
        "transcript": "...",
        "duration": "180",
        "vocabulary_explanation": "...",
        "questions": [ ... ]
    }
    """
    lesson = get_object_or_404(
        IELTSLesson.objects.select_related('lesson_pack__skill'),
        id=lesson_id
    )

    if lesson.lesson_pack.skill.skill_type != 'LISTENING':
        return Response({'error': 'هذا الدرس ليس درس استماع'}, status=status.HTTP_400_BAD_REQUEST)

    audio_url = request.data.get('audio_file', '').strip()
    if not audio_url:
        return Response({'error': 'audio_file مطلوب'}, status=status.HTTP_400_BAD_REQUEST)

    questions_data = request.data.get('questions', [])

    try:
        with transaction.atomic():
            from sabr_questions.models import ListeningAudio, ListeningQuestion

            # حذف المحتوى القديم
            ListeningLessonContent.objects.filter(lesson=lesson).delete()
            ListeningAudio.objects.filter(ielts_lesson=lesson).delete()

            # إنشاء ListeningAudio
            duration = request.data.get('duration')
            audio = ListeningAudio.objects.create(
                title=request.data.get('title', lesson.title),
                audio_file=audio_url,
                transcript=request.data.get('transcript', ''),
                duration=int(duration) if duration else 0,
                usage_type='IELTS_LESSON',
                ielts_lesson_pack=lesson.lesson_pack,
                ielts_lesson=lesson,
                is_active=True,
            )

            # إنشاء ListeningLessonContent
            ListeningLessonContent.objects.create(
                lesson=lesson,
                audio_file=audio_url,
                transcript=request.data.get('transcript', ''),
                vocabulary_explanation=request.data.get('vocabulary_explanation', ''),
                listening_exercises=request.data.get('listening_exercises', []),
                tips=request.data.get('tips', [])
            )

            # إنشاء الأسئلة
            questions_created = 0
            for i, q in enumerate(questions_data):
                ListeningQuestion.objects.create(
                    audio=audio,
                    question_text=q.get('question_text', ''),
                    choice_a=q.get('choice_a', ''),
                    choice_b=q.get('choice_b', ''),
                    choice_c=q.get('choice_c', ''),
                    choice_d=q.get('choice_d', ''),
                    correct_answer=q.get('correct_answer', 'A'),
                    explanation=q.get('explanation', ''),
                    points=q.get('points', 1),
                    order=i + 1,
                    is_active=True,
                )
                questions_created += 1

        lesson.refresh_from_db()
        return Response({
            'message': 'تم إضافة محتوى الاستماع بنجاح',
            'lesson': IELTSLessonDetailWithQuestionsSerializer(lesson).data,
            'questions_created': questions_created,
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f"Error creating listening lesson content: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_speaking_lesson_content(request, lesson_id):
    """
    إنشاء محتوى درس تحدث + SpeakingVideo + Questions
    POST /api/ielts/lessons/{lesson_id}/content/speaking/create/
    
    Body:
    {
        "title": "How to introduce yourself",
        "video_file": "https://res.cloudinary.com/.../video.mp4",
        "description": "...",
        "duration": "180",
        "thumbnail": "https://...",
        "pronunciation_tips": "...",
        "questions": [ ... ]
    }
    """
    lesson = get_object_or_404(
        IELTSLesson.objects.select_related('lesson_pack__skill'),
        id=lesson_id
    )

    if lesson.lesson_pack.skill.skill_type != 'SPEAKING':
        return Response({'error': 'هذا الدرس ليس درس تحدث'}, status=status.HTTP_400_BAD_REQUEST)

    video_url = request.data.get('video_file', '').strip()
    if not video_url:
        return Response({'error': 'video_file مطلوب'}, status=status.HTTP_400_BAD_REQUEST)

    questions_data = request.data.get('questions', [])

    try:
        with transaction.atomic():
            from sabr_questions.models import SpeakingVideo, SpeakingQuestion

            # حذف المحتوى القديم
            SpeakingLessonContent.objects.filter(lesson=lesson).delete()
            SpeakingVideo.objects.filter(ielts_lesson=lesson).delete()

            # إنشاء SpeakingVideo
            duration = request.data.get('duration')
            video = SpeakingVideo.objects.create(
                title=request.data.get('title', lesson.title),
                video_file=video_url,
                description=request.data.get('description', ''),
                thumbnail=request.data.get('thumbnail', ''),
                duration=int(duration) if duration else 0,
                usage_type='IELTS_LESSON',
                ielts_lesson_pack=lesson.lesson_pack,
                ielts_lesson=lesson,
                is_active=True,
            )

            # إنشاء SpeakingLessonContent
            SpeakingLessonContent.objects.create(
                lesson=lesson,
                video_file=video_url,
                dialogue_texts=request.data.get('dialogue_texts', []),
                useful_phrases=request.data.get('useful_phrases', []),
                audio_examples=request.data.get('audio_examples', []),
                pronunciation_tips=request.data.get('pronunciation_tips', '')
            )

            # إنشاء الأسئلة
            questions_created = 0
            for i, q in enumerate(questions_data):
                SpeakingQuestion.objects.create(
                    video=video,
                    question_text=q.get('question_text', ''),
                    choice_a=q.get('choice_a', ''),
                    choice_b=q.get('choice_b', ''),
                    choice_c=q.get('choice_c', ''),
                    choice_d=q.get('choice_d', ''),
                    correct_answer=q.get('correct_answer', 'A'),
                    explanation=q.get('explanation', ''),
                    points=q.get('points', 1),
                    order=i + 1,
                    is_active=True,
                )
                questions_created += 1

        lesson.refresh_from_db()
        return Response({
            'message': 'تم إضافة محتوى التحدث بنجاح',
            'lesson': IELTSLessonDetailWithQuestionsSerializer(lesson).data,
            'questions_created': questions_created,
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f"Error creating speaking lesson content: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_writing_lesson_content(request, lesson_id):
    """
    إنشاء محتوى درس كتابة + WritingQuestion
    POST /api/ielts/lessons/{lesson_id}/content/writing/create/
    
    Body:
    {
        "writing_instructions": "The graph below shows...",
        "title": "IELTS Writing Task 1",
        "question_text": "Describe the graph...",
        "min_words": 150,
        "max_words": 250,
        "sample_answer": "...",
        "rubric": "...",
        "points": 10,
        "pass_threshold": 7
    }
    """
    lesson = get_object_or_404(
        IELTSLesson.objects.select_related('lesson_pack__skill'),
        id=lesson_id
    )

    if lesson.lesson_pack.skill.skill_type != 'WRITING':
        return Response({'error': 'هذا الدرس ليس درس كتابة'}, status=status.HTTP_400_BAD_REQUEST)

    question_text = request.data.get('question_text', '').strip()
    sample_answer = request.data.get('sample_answer', '').strip()
    rubric = request.data.get('rubric', '').strip()

    if not question_text:
        return Response({'error': 'question_text مطلوب'}, status=status.HTTP_400_BAD_REQUEST)
    if not sample_answer:
        return Response({'error': 'sample_answer مطلوب'}, status=status.HTTP_400_BAD_REQUEST)
    if not rubric:
        return Response({'error': 'rubric مطلوب'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        with transaction.atomic():
            from sabr_questions.models import WritingQuestion

            # حذف المحتوى القديم
            WritingLessonContent.objects.filter(lesson=lesson).delete()
            WritingQuestion.objects.filter(ielts_lesson=lesson).delete()

            # إنشاء WritingLessonContent
            WritingLessonContent.objects.create(
                lesson=lesson,
                writing_instructions=request.data.get('writing_instructions', question_text),
                sample_texts=request.data.get('sample_texts', []),
                tips=request.data.get('tips', []),
                examples=request.data.get('examples', []),
                video_url=request.data.get('video_url') or None,
            )

            # إنشاء WritingQuestion مرتبط بالـ lesson
            min_words = int(request.data.get('min_words', 150))
            max_words = int(request.data.get('max_words', 250))

            if max_words <= min_words:
                raise ValueError('الحد الأقصى يجب أن يكون أكبر من الحد الأدنى')

            pass_threshold = request.data.get('pass_threshold')

            WritingQuestion.objects.create(
                title=request.data.get('title', lesson.title),
                question_text=question_text,
                min_words=min_words,
                max_words=max_words,
                sample_answer=sample_answer,
                rubric=rubric,
                points=int(request.data.get('points', 10)),
                pass_threshold=int(pass_threshold) if pass_threshold else None,
                usage_type='IELTS_LESSON',
                ielts_lesson_pack=lesson.lesson_pack,
                ielts_lesson=lesson,
                is_active=True,
            )

        lesson.refresh_from_db()
        return Response({
            'message': 'تم إضافة محتوى الكتابة بنجاح',
            'lesson': IELTSLessonDetailWithQuestionsSerializer(lesson).data,
        }, status=status.HTTP_201_CREATED)

    except ValueError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error creating writing lesson content: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================
# 4. STUDENT PROGRESS
# ============================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_progress(request):
    lesson_pack_progress = StudentLessonPackProgress.objects.filter(
        student=request.user
    ).select_related('lesson_pack__skill').order_by('-created_at')
    lesson_progress = StudentLessonProgress.objects.filter(
        student=request.user, is_completed=True
    ).select_related('lesson__lesson_pack').order_by('-completed_at')[:20]

    total_packs = lesson_pack_progress.count()
    completed_packs = lesson_pack_progress.filter(is_completed=True).count()
    total_lessons = StudentLessonProgress.objects.filter(student=request.user).count()
    completed_lessons = StudentLessonProgress.objects.filter(student=request.user, is_completed=True).count()

    return Response({
        'summary': {
            'lesson_packs': {'total': total_packs, 'completed': completed_packs, 'in_progress': total_packs - completed_packs},
            'lessons': {'total': total_lessons, 'completed': completed_lessons, 'in_progress': total_lessons - completed_lessons}
        },
        'lesson_pack_progress': StudentLessonPackProgressSerializer(lesson_pack_progress, many=True).data,
        'recent_lessons': StudentLessonProgressSerializer(lesson_progress, many=True).data
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_lesson_pack_complete(request, pack_id):
    lesson_pack = get_object_or_404(LessonPack, id=pack_id)
    progress, created = StudentLessonPackProgress.objects.get_or_create(student=request.user, lesson_pack=lesson_pack)
    progress.mark_completed()
    return Response({'message': 'تم تحديد Lesson Pack كمكتمل', 'progress': StudentLessonPackProgressSerializer(progress).data})


# ============================================
# 5. EXAM ATTEMPTS
# ============================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_practice_exam(request, pack_id):
    lesson_pack = get_object_or_404(LessonPack, id=pack_id)
    practice_exam = lesson_pack.get_practice_exam()

    if not practice_exam:
        return Response({'error': 'لا يوجد امتحان لهذا الـ Lesson Pack'}, status=status.HTTP_404_NOT_FOUND)

    last_attempt = StudentPracticeExamAttempt.objects.filter(
        student=request.user, practice_exam=practice_exam
    ).order_by('-attempt_number').first()

    attempt_number = (last_attempt.attempt_number + 1) if last_attempt else 1
    attempt = StudentPracticeExamAttempt.objects.create(
        student=request.user, practice_exam=practice_exam, attempt_number=attempt_number
    )

    from sabr_questions.models import (
        VocabularyQuestion, GrammarQuestion, ReadingPassage,
        ListeningAudio, SpeakingVideo, WritingQuestion
    )

    def serialize_cloudinary(value):
        if value is None:
            return None
        if hasattr(value, 'url'):
            return value.url
        return str(value) if value else None

    vocabulary_questions = [
        {'id': q.id, 'question_text': q.question_text, 'choice_a': q.choice_a,
         'choice_b': q.choice_b, 'choice_c': q.choice_c, 'choice_d': q.choice_d, 'points': q.points}
        for q in VocabularyQuestion.objects.filter(ielts_lesson_pack=lesson_pack, usage_type='IELTS', is_active=True)
    ]

    grammar_questions = [
        {'id': q.id, 'question_text': q.question_text, 'choice_a': q.choice_a,
         'choice_b': q.choice_b, 'choice_c': q.choice_c, 'choice_d': q.choice_d, 'points': q.points}
        for q in GrammarQuestion.objects.filter(ielts_lesson_pack=lesson_pack, usage_type='IELTS', is_active=True)
    ]

    reading_passages = []
    for passage in ReadingPassage.objects.filter(ielts_lesson_pack=lesson_pack, usage_type='IELTS', is_active=True).prefetch_related('questions'):
        reading_passages.append({
            'id': passage.id, 'title': passage.title, 'passage_text': passage.passage_text,
            'questions': [
                {'id': q.id, 'question_text': q.question_text, 'choice_a': q.choice_a,
                 'choice_b': q.choice_b, 'choice_c': q.choice_c, 'choice_d': q.choice_d, 'points': q.points}
                for q in passage.questions.filter(is_active=True)
            ]
        })

    listening_audios = []
    for audio in ListeningAudio.objects.filter(ielts_lesson_pack=lesson_pack, usage_type='IELTS', is_active=True).prefetch_related('questions'):
        listening_audios.append({
            'id': audio.id, 'title': audio.title, 'audio_file': serialize_cloudinary(audio.audio_file),
            'questions': [
                {'id': q.id, 'question_text': q.question_text, 'choice_a': q.choice_a,
                 'choice_b': q.choice_b, 'choice_c': q.choice_c, 'choice_d': q.choice_d, 'points': q.points}
                for q in audio.questions.filter(is_active=True)
            ]
        })

    speaking_videos = []
    for video in SpeakingVideo.objects.filter(ielts_lesson_pack=lesson_pack, usage_type='IELTS', is_active=True).prefetch_related('questions'):
        speaking_videos.append({
            'id': video.id, 'title': video.title,
            'video_file': serialize_cloudinary(video.video_file),
            'thumbnail': serialize_cloudinary(video.thumbnail),
            'questions': [
                {'id': q.id, 'question_text': q.question_text, 'choice_a': q.choice_a,
                 'choice_b': q.choice_b, 'choice_c': q.choice_c, 'choice_d': q.choice_d, 'points': q.points}
                for q in video.questions.filter(is_active=True)
            ]
        })

    writing_questions = [
        {'id': q.id, 'title': q.title, 'question_text': q.question_text,
         'question_image': serialize_cloudinary(q.question_image),
         'min_words': q.min_words, 'max_words': q.max_words, 'points': q.points}
        for q in WritingQuestion.objects.filter(ielts_lesson_pack=lesson_pack, usage_type='IELTS', is_active=True)
    ]

    return Response({
        'message': 'تم بدء الامتحان بنجاح',
        'attempt': StudentPracticeExamAttemptSerializer(attempt).data,
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
    attempt = get_object_or_404(StudentPracticeExamAttempt, id=attempt_id, student=request.user)

    if attempt.submitted_at:
        return Response({'error': 'تم تسليم الامتحان بالفعل'}, status=status.HTTP_400_BAD_REQUEST)

    from sabr_questions.models import (
        VocabularyQuestion, GrammarQuestion, ReadingQuestion,
        ListeningQuestion, SpeakingQuestion, WritingQuestion
    )
    from placement_test.services.ai_grading import ai_grading_service

    answers = request.data.get('answers', {})
    if not answers:
        return Response({'error': 'يجب إرسال الإجابات'}, status=status.HTTP_400_BAD_REQUEST)

    lesson_pack = attempt.practice_exam.lesson_pack
    total_points = 0
    earned_points = 0
    results = {}

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

    grade_mcq(VocabularyQuestion, answers.get('vocabulary', {}), 'vocabulary')
    grade_mcq(GrammarQuestion, answers.get('grammar', {}), 'grammar')
    grade_mcq(ReadingQuestion, answers.get('reading', {}), 'reading')
    grade_mcq(ListeningQuestion, answers.get('listening', {}), 'listening')
    grade_mcq(SpeakingQuestion, answers.get('speaking', {}), 'speaking')

    writing_results = []
    total_ai_cost = 0.0

    for q_id_str, student_text in answers.get('writing', {}).items():
        try:
            writing_question = WritingQuestion.objects.get(id=int(q_id_str))
            if not student_text or not student_text.strip():
                writing_results.append({
                    'question_id': int(q_id_str), 'student_answer': '', 'score': 0,
                    'raw_score': 0, 'percentage': 0, 'is_correct': False, 'word_count': 0,
                    'is_within_limit': False, 'feedback': 'لم يتم تقديم إجابة',
                    'strengths': [], 'improvements': ['يجب كتابة إجابة'],
                    'points_possible': writing_question.points,
                })
                total_points += writing_question.points
                continue

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
                earned_points += grading_result['score']
            total_ai_cost += grading_result.get('cost', 0.0)
            writing_results.append({
                'question_id': int(q_id_str), 'student_answer': student_text,
                'score': grading_result['score'], 'raw_score': grading_result.get('raw_score', 0),
                'percentage': grading_result.get('percentage', 0), 'is_correct': grading_result['is_correct'],
                'word_count': grading_result['word_count'], 'is_within_limit': grading_result['is_within_limit'],
                'feedback': grading_result['feedback'], 'strengths': grading_result['strengths'],
                'improvements': grading_result['improvements'], 'points_possible': writing_question.points,
                'pass_threshold': writing_question.pass_threshold,
            })
        except WritingQuestion.DoesNotExist:
            continue
        except Exception as e:
            logger.error(f"Error grading writing Q:{q_id_str} attempt:{attempt_id} - {str(e)}")
            writing_results.append({
                'question_id': int(q_id_str), 'student_answer': student_text,
                'score': 0, 'is_correct': False, 'feedback': 'حدث خطأ أثناء التصحيح', 'status': 'error',
            })

    results['writing'] = writing_results

    score_percentage = round((earned_points / total_points * 100), 2) if total_points > 0 else 0
    passing_score = lesson_pack.exam_passing_score or 70
    passed = score_percentage >= passing_score

    attempt.answers = answers
    attempt.score = score_percentage
    attempt.passed = passed
    attempt.mark_submitted()

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
            'points': {'earned': earned_points, 'total': total_points},
            'submitted_at': attempt.submitted_at,
            'ai_grading_cost': round(total_ai_cost, 6),
            'summary': {
                'vocabulary': count_stats(results.get('vocabulary', [])),
                'grammar': count_stats(results.get('grammar', [])),
                'reading': count_stats(results.get('reading', [])),
                'listening': count_stats(results.get('listening', [])),
                'speaking': count_stats(results.get('speaking', [])),
                'writing': count_stats(results.get('writing', [])),
            },
            'breakdown': results,
        }
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_exam_attempts(request):
    pack_id = request.query_params.get('lesson_pack_id')
    attempts = StudentPracticeExamAttempt.objects.filter(
        student=request.user
    ).select_related('practice_exam__lesson_pack').order_by('-started_at')
    if pack_id:
        attempts = attempts.filter(practice_exam__lesson_pack_id=pack_id)
    total_attempts = attempts.count()
    passed_attempts = attempts.filter(passed=True).count()
    return Response({
        'summary': {'total_attempts': total_attempts, 'passed': passed_attempts, 'failed': total_attempts - passed_attempts},
        'attempts': StudentPracticeExamAttemptSerializer(attempts, many=True).data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_practice_exam(request, exam_id):
    practice_exam = get_object_or_404(IELTSPracticeExam.objects.select_related('lesson_pack__skill'), id=exam_id)
    return Response(IELTSPracticeExamSerializer(practice_exam).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_vocabulary_question(request):
    from sabr_questions.models import VocabularyQuestion, VocabularyQuestionSet
    data = request.data.copy()
    required_fields = ['question_text', 'options', 'correct_answer', 'ielts_lesson_pack']
    for field in required_fields:
        if field not in data:
            return Response({field: f'{field} مطلوب'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        options = data.get('options', [])
        if len(options) < 2:
            return Response({'options': 'يجب إضافة خيارين على الأقل'}, status=status.HTTP_400_BAD_REQUEST)
        question_set, _ = VocabularyQuestionSet.objects.get_or_create(
            title='IELTS Vocabulary Questions', usage_type='IELTS',
            defaults={'description': 'Auto-generated set for IELTS'}
        )
        correct_answer = data.get('correct_answer')
        correct_letter = next((chr(65 + idx) for idx, opt in enumerate(options) if opt == correct_answer), None)
        if not correct_letter:
            return Response({'correct_answer': 'الإجابة الصحيحة غير موجودة في الخيارات'}, status=status.HTTP_400_BAD_REQUEST)
        question = VocabularyQuestion.objects.create(
            question_set=question_set, question_text=data.get('question_text'),
            choice_a=options[0] if len(options) > 0 else '', choice_b=options[1] if len(options) > 1 else '',
            choice_c=options[2] if len(options) > 2 else '', choice_d=options[3] if len(options) > 3 else '',
            correct_answer=correct_letter, explanation=data.get('explanation', ''),
            points=data.get('points', 1), usage_type=data.get('usage_type', 'IELTS'),
            ielts_lesson_pack_id=data.get('ielts_lesson_pack'), is_active=data.get('is_active', True), order=0,
        )
        return Response({'message': 'تم إنشاء السؤال بنجاح', 'question': {'id': question.id, 'question_text': question.question_text}}, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_grammar_question(request):
    from sabr_questions.models import GrammarQuestion, GrammarQuestionSet
    data = request.data.copy()
    required_fields = ['question_text', 'options', 'correct_answer', 'ielts_lesson_pack']
    for field in required_fields:
        if field not in data:
            return Response({field: f'{field} مطلوب'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        options = data.get('options', [])
        if len(options) < 2:
            return Response({'options': 'يجب إضافة خيارين على الأقل'}, status=status.HTTP_400_BAD_REQUEST)
        question_set, _ = GrammarQuestionSet.objects.get_or_create(
            title='IELTS Grammar Questions', usage_type='IELTS',
            defaults={'description': 'Auto-generated set for IELTS'}
        )
        correct_answer = data.get('correct_answer')
        correct_letter = next((chr(65 + idx) for idx, opt in enumerate(options) if opt == correct_answer), None)
        if not correct_letter:
            return Response({'correct_answer': 'الإجابة الصحيحة غير موجودة في الخيارات'}, status=status.HTTP_400_BAD_REQUEST)
        question = GrammarQuestion.objects.create(
            question_set=question_set, question_text=data.get('question_text'),
            choice_a=options[0] if len(options) > 0 else '', choice_b=options[1] if len(options) > 1 else '',
            choice_c=options[2] if len(options) > 2 else '', choice_d=options[3] if len(options) > 3 else '',
            correct_answer=correct_letter, explanation=data.get('explanation', ''),
            points=data.get('points', 1), usage_type=data.get('usage_type', 'IELTS'),
            ielts_lesson_pack_id=data.get('ielts_lesson_pack'), is_active=data.get('is_active', True), order=0,
        )
        return Response({'message': 'تم إنشاء السؤال بنجاح', 'question': {'id': question.id, 'question_text': question.question_text}}, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


# ============================================
# 6. READING PASSAGES & QUESTIONS
# ============================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_reading_passage(request):
    from sabr_questions.models import ReadingPassage
    data = request.data.copy()
    required_fields = ['title', 'passage_text', 'ielts_lesson_pack']
    for field in required_fields:
        if field not in data:
            return Response({field: f'{field} مطلوب'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        passage = ReadingPassage.objects.create(
            title=data.get('title'), passage_text=data.get('passage_text'),
            source=data.get('source', 'Teacher Created'),
            usage_type=data.get('usage_type', 'IELTS'),
            ielts_lesson_pack_id=data.get('ielts_lesson_pack'),
            is_active=data.get('is_active', True), order=0,
        )
        return Response({'message': 'تم إنشاء القطعة بنجاح', 'passage': {'id': passage.id, 'title': passage.title}}, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_reading_question(request, passage_id):
    from sabr_questions.models import ReadingPassage, ReadingQuestion
    try:
        passage = ReadingPassage.objects.get(id=passage_id)
    except ReadingPassage.DoesNotExist:
        return Response({'error': 'القطعة غير موجودة'}, status=status.HTTP_404_NOT_FOUND)
    data = request.data.copy()
    for field in ['question_text', 'options', 'correct_answer']:
        if field not in data:
            return Response({field: f'{field} مطلوب'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        options = data.get('options', [])
        if len(options) < 2:
            return Response({'options': 'يجب إضافة خيارين على الأقل'}, status=status.HTTP_400_BAD_REQUEST)
        correct_answer = data.get('correct_answer')
        correct_letter = next((chr(65 + idx) for idx, opt in enumerate(options) if opt == correct_answer), None)
        if not correct_letter:
            return Response({'correct_answer': 'الإجابة الصحيحة غير موجودة في الخيارات'}, status=status.HTTP_400_BAD_REQUEST)
        question = ReadingQuestion.objects.create(
            passage=passage, question_text=data.get('question_text'),
            choice_a=options[0] if len(options) > 0 else '', choice_b=options[1] if len(options) > 1 else '',
            choice_c=options[2] if len(options) > 2 else '', choice_d=options[3] if len(options) > 3 else '',
            correct_answer=correct_letter, explanation=data.get('explanation', ''),
            points=data.get('points', 1), is_active=data.get('is_active', True), order=0,
        )
        return Response({'message': 'تم إنشاء السؤال بنجاح', 'question': {'id': question.id, 'question_text': question.question_text}}, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_reading_passage(request, passage_id):
    from sabr_questions.models import ReadingPassage
    try:
        passage = ReadingPassage.objects.prefetch_related('questions').get(id=passage_id)
        questions_data = [
            {'id': q.id, 'question_text': q.question_text, 'choice_a': q.choice_a, 'choice_b': q.choice_b,
             'choice_c': q.choice_c, 'choice_d': q.choice_d, 'correct_answer': q.correct_answer,
             'explanation': q.explanation, 'points': q.points, 'order': q.order}
            for q in passage.questions.all()
        ]
        return Response({
            'id': passage.id, 'title': passage.title, 'passage_text': passage.passage_text,
            'source': passage.source, 'questions_count': passage.questions.count(),
            'questions': questions_data, 'created_at': passage.created_at,
        })
    except ReadingPassage.DoesNotExist:
        return Response({'error': 'القطعة غير موجودة'}, status=status.HTTP_404_NOT_FOUND)


# ============================================
# 7. LISTENING AUDIOS & QUESTIONS
# ============================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_listening_audio(request):
    from sabr_questions.models import ListeningAudio
    data = request.data.copy()
    for field in ['title', 'audio_file', 'ielts_lesson_pack']:
        if field not in data:
            return Response({field: f'{field} مطلوب'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        audio = ListeningAudio.objects.create(
            title=data.get('title'), audio_file=data.get('audio_file'),
            transcript=data.get('transcript', ''), duration=data.get('duration'),
            usage_type=data.get('usage_type', 'IELTS'),
            ielts_lesson_pack_id=data.get('ielts_lesson_pack'),
            is_active=data.get('is_active', True), order=0,
        )
        return Response({'message': 'تم إنشاء التسجيل بنجاح', 'audio': {'id': audio.id, 'title': audio.title}}, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_listening_question(request, audio_id):
    from sabr_questions.models import ListeningAudio, ListeningQuestion
    try:
        audio = ListeningAudio.objects.get(id=audio_id)
    except ListeningAudio.DoesNotExist:
        return Response({'error': 'التسجيل غير موجود'}, status=status.HTTP_404_NOT_FOUND)
    data = request.data.copy()
    for field in ['question_text', 'options', 'correct_answer']:
        if field not in data:
            return Response({field: f'{field} مطلوب'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        options = data.get('options', [])
        correct_letter = next((chr(65 + idx) for idx, opt in enumerate(options) if opt == data.get('correct_answer')), None)
        if not correct_letter:
            return Response({'correct_answer': 'الإجابة الصحيحة غير موجودة في الخيارات'}, status=status.HTTP_400_BAD_REQUEST)
        question = ListeningQuestion.objects.create(
            audio=audio, question_text=data.get('question_text'),
            choice_a=options[0] if len(options) > 0 else '', choice_b=options[1] if len(options) > 1 else '',
            choice_c=options[2] if len(options) > 2 else '', choice_d=options[3] if len(options) > 3 else '',
            correct_answer=correct_letter, explanation=data.get('explanation', ''),
            points=data.get('points', 1), is_active=data.get('is_active', True), order=0,
        )
        return Response({'message': 'تم إنشاء السؤال بنجاح', 'question': {'id': question.id}}, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_listening_audio(request, audio_id):
    from sabr_questions.models import ListeningAudio
    try:
        audio = ListeningAudio.objects.prefetch_related('questions').get(id=audio_id)
        return Response({
            'id': audio.id, 'title': audio.title, 'audio_file': str(audio.audio_file),
            'transcript': audio.transcript, 'duration': audio.duration,
            'questions_count': audio.questions.count(),
            'questions': [
                {'id': q.id, 'question_text': q.question_text, 'choice_a': q.choice_a,
                 'choice_b': q.choice_b, 'choice_c': q.choice_c, 'choice_d': q.choice_d,
                 'correct_answer': q.correct_answer, 'explanation': q.explanation, 'points': q.points}
                for q in audio.questions.all()
            ],
            'created_at': audio.created_at,
        })
    except ListeningAudio.DoesNotExist:
        return Response({'error': 'التسجيل غير موجود'}, status=status.HTTP_404_NOT_FOUND)


# ============================================
# 8. SPEAKING VIDEOS & QUESTIONS
# ============================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_speaking_video(request):
    from sabr_questions.models import SpeakingVideo
    data = request.data.copy()
    for field in ['title', 'video_file', 'ielts_lesson_pack']:
        if field not in data:
            return Response({field: f'{field} مطلوب'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        video = SpeakingVideo.objects.create(
            title=data.get('title'), video_file=data.get('video_file'),
            description=data.get('description', ''), duration=data.get('duration'),
            thumbnail=data.get('thumbnail', ''), usage_type=data.get('usage_type', 'IELTS'),
            ielts_lesson_pack_id=data.get('ielts_lesson_pack'),
            is_active=data.get('is_active', True), order=0,
        )
        return Response({'message': 'تم إنشاء الفيديو بنجاح', 'video': {'id': video.id, 'title': video.title}}, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_speaking_question(request, video_id):
    from sabr_questions.models import SpeakingVideo, SpeakingQuestion
    try:
        video = SpeakingVideo.objects.get(id=video_id)
    except SpeakingVideo.DoesNotExist:
        return Response({'error': 'الفيديو غير موجود'}, status=status.HTTP_404_NOT_FOUND)
    data = request.data.copy()
    for field in ['question_text', 'options', 'correct_answer']:
        if field not in data:
            return Response({field: f'{field} مطلوب'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        options = data.get('options', [])
        correct_letter = next((chr(65 + idx) for idx, opt in enumerate(options) if opt == data.get('correct_answer')), None)
        if not correct_letter:
            return Response({'correct_answer': 'الإجابة الصحيحة غير موجودة في الخيارات'}, status=status.HTTP_400_BAD_REQUEST)
        question = SpeakingQuestion.objects.create(
            video=video, question_text=data.get('question_text'),
            choice_a=options[0] if len(options) > 0 else '', choice_b=options[1] if len(options) > 1 else '',
            choice_c=options[2] if len(options) > 2 else '', choice_d=options[3] if len(options) > 3 else '',
            correct_answer=correct_letter, explanation=data.get('explanation', ''),
            points=data.get('points', 1), is_active=data.get('is_active', True), order=0,
        )
        return Response({'message': 'تم إنشاء السؤال بنجاح', 'question': {'id': question.id}}, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_speaking_video(request, video_id):
    from sabr_questions.models import SpeakingVideo
    try:
        video = SpeakingVideo.objects.prefetch_related('questions').get(id=video_id)
        return Response({
            'id': video.id, 'title': video.title, 'video_file': str(video.video_file),
            'description': video.description, 'duration': video.duration, 'thumbnail': str(video.thumbnail),
            'questions_count': video.questions.count(),
            'questions': [
                {'id': q.id, 'question_text': q.question_text, 'choice_a': q.choice_a,
                 'choice_b': q.choice_b, 'choice_c': q.choice_c, 'choice_d': q.choice_d,
                 'correct_answer': q.correct_answer, 'explanation': q.explanation, 'points': q.points}
                for q in video.questions.all()
            ],
            'created_at': video.created_at,
        })
    except SpeakingVideo.DoesNotExist:
        return Response({'error': 'الفيديو غير موجود'}, status=status.HTTP_404_NOT_FOUND)


# ============================================
# 9. WRITING QUESTIONS
# ============================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_writing_question(request):
    from sabr_questions.models import WritingQuestion
    data = request.data.copy()
    required_fields = ['title', 'question_text', 'min_words', 'max_words', 'sample_answer', 'rubric', 'ielts_lesson_pack']
    for field in required_fields:
        if field not in data:
            return Response({field: f'{field} مطلوب'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        min_words, max_words = int(data.get('min_words')), int(data.get('max_words'))
        if max_words <= min_words:
            return Response({'error': 'الحد الأقصى يجب أن يكون أكبر من الحد الأدنى'}, status=status.HTTP_400_BAD_REQUEST)
        question = WritingQuestion.objects.create(
            title=data.get('title'), question_text=data.get('question_text'),
            min_words=min_words, max_words=max_words,
            sample_answer=data.get('sample_answer'), rubric=data.get('rubric'),
            usage_type=data.get('usage_type', 'IELTS'),
            ielts_lesson_pack_id=data.get('ielts_lesson_pack'),
            points=data.get('points', 10), is_active=data.get('is_active', True), order=0,
            pass_threshold=data.get('pass_threshold'),
        )
        return Response({'message': 'تم إنشاء السؤال بنجاح', 'question': {'id': question.id, 'title': question.title}}, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_writing_question(request, question_id):
    from sabr_questions.models import WritingQuestion
    try:
        question = WritingQuestion.objects.get(id=question_id)
        return Response({
            'id': question.id, 'title': question.title, 'question_text': question.question_text,
            'question_image': question.question_image.url if question.question_image else None,
            'min_words': question.min_words, 'max_words': question.max_words,
            'sample_answer': question.sample_answer, 'rubric': question.rubric,
            'points': question.points, 'pass_threshold': question.pass_threshold, 'created_at': question.created_at,
        })
    except WritingQuestion.DoesNotExist:
        return Response({'error': 'السؤال غير موجود'}, status=status.HTTP_404_NOT_FOUND)