import logging
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

logger = logging.getLogger(__name__)

VALID_SKILL_TYPES = ['VOCABULARY', 'GRAMMAR', 'READING', 'LISTENING', 'SPEAKING', 'WRITING']


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def extract_book(request):
    """
    POST /api/step/ai/extract-book/
    Body (multipart): { name, pdf_file }
    """
    from .ai_models import ExtractedBook
    from .tasks import extract_book_task

    name = request.data.get('name', '').strip()
    pdf_file = request.FILES.get('pdf_file')

    if not name:
        return Response({'error': 'اسم الكتاب مطلوب'}, status=status.HTTP_400_BAD_REQUEST)
    if not pdf_file:
        return Response({'error': 'ملف PDF مطلوب'}, status=status.HTTP_400_BAD_REQUEST)
    if not pdf_file.name.lower().endswith('.pdf'):
        return Response({'error': 'الملف يجب أن يكون بصيغة PDF'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        import cloudinary.uploader
        upload_result = cloudinary.uploader.upload(
            pdf_file,
            resource_type='raw',
            folder='step/ai/books',
            access_mode='public',
        )
        book = ExtractedBook.objects.create(
            name=name,
            pdf_file=upload_result['public_id'],
            status='PENDING',
            uploaded_by=request.user,
        )

        extract_book_task.delay(book.id)

        return Response({
            'message': 'جاري استخراج النص من الكتاب',
            'book_id': book.id,
            'status': book.status,
        }, status=status.HTTP_202_ACCEPTED)

    except Exception as e:
        logger.error(f"[extract_book] Error: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def extract_book_status(request, book_id):
    """
    GET /api/step/ai/extract-book/{book_id}/status/
    """
    from .ai_models import ExtractedBook

    book = get_object_or_404(ExtractedBook, id=book_id)
    return Response({
        'book_id': book.id,
        'name': book.name,
        'status': book.status,
        'page_count': book.page_count,
        'error_message': book.error_message,
        'has_text': bool(book.extracted_text),
        'created_at': book.created_at,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_extracted_books(request):
    """
    GET /api/step/ai/extract-book/
    """
    from .ai_models import ExtractedBook

    books = ExtractedBook.objects.filter(status='DONE').order_by('-created_at')
    return Response({
        'books': [
            {
                'id': b.id,
                'name': b.name,
                'page_count': b.page_count,
                'created_at': b.created_at,
                'status': b.status,
            }
            for b in books
        ]
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def extract_media(request):
    """
    POST /api/step/ai/extract-media/
    Body (multipart): { name, media_file }
    """
    from .ai_models import ExtractedMedia
    from .tasks import extract_media_task

    name = request.data.get('name', '').strip()
    media_file = request.FILES.get('media_file')

    if not name:
        return Response({'error': 'اسم الميديا مطلوب'}, status=status.HTTP_400_BAD_REQUEST)
    if not media_file:
        return Response({'error': 'ملف الميديا مطلوب'}, status=status.HTTP_400_BAD_REQUEST)

    filename = media_file.name.lower()
    video_exts = ('.mp4', '.mov', '.avi', '.mkv', '.webm')
    audio_exts = ('.mp3', '.wav', '.m4a', '.ogg', '.flac')

    if filename.endswith(video_exts):
        media_type = 'VIDEO'
    elif filename.endswith(audio_exts):
        media_type = 'AUDIO'
    else:
        return Response(
            {'error': 'صيغة الملف غير مدعومة. استخدم mp4/mov/avi للفيديو أو mp3/wav/m4a للصوت'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        import cloudinary.uploader
        upload_result = cloudinary.uploader.upload(
            media_file,
            resource_type='raw',
            folder='step/ai/media',
        )
        media = ExtractedMedia.objects.create(
            name=name,
            media_file=upload_result['public_id'],
            media_type=media_type,
            status='PENDING',
            uploaded_by=request.user,
        )

        extract_media_task.delay(media.id)

        return Response({
            'message': 'جاري استخراج الترانسكريبت',
            'media_id': media.id,
            'media_type': media_type,
            'status': media.status,
        }, status=status.HTTP_202_ACCEPTED)

    except Exception as e:
        logger.error(f"[extract_media] Error: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def extract_media_status(request, media_id):
    """
    GET /api/step/ai/extract-media/{media_id}/status/
    """
    from .ai_models import ExtractedMedia

    media = get_object_or_404(ExtractedMedia, id=media_id)
    return Response({
        'media_id': media.id,
        'name': media.name,
        'media_type': media.media_type,
        'status': media.status,
        'duration_seconds': media.duration_seconds,
        'error_message': media.error_message,
        'has_transcript': bool(media.transcript),
        'created_at': media.created_at,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_extracted_media(request):
    """
    GET /api/step/ai/extract-media/
    """
    from .ai_models import ExtractedMedia

    media_qs = ExtractedMedia.objects.filter(status='DONE').order_by('-created_at')
    return Response({
        'media': [
            {
                'id': m.id,
                'name': m.name,
                'media_type': m.media_type,
                'duration_seconds': m.duration_seconds,
                'created_at': m.created_at,
            }
            for m in media_qs
        ]
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_skill(request):
    """
    POST /api/step/ai/generate-skill/
    Body:
    {
        "skill_type": "VOCABULARY",
        "skill_title": "Advanced Vocabulary",
        "skill_description": "...",
        "book_ids": [1, 2],
        "media_ids": [3],
        "no_easy": 5,
        "no_medium": 5,
        "no_hard": 5,
        "additional_notes": "..."
    }
    """
    from .ai_models import AIGenerationJob, ExtractedBook, ExtractedMedia
    from .tasks import generate_skill_task

    data = request.data

    # Validation
    skill_type = data.get('skill_type', '').upper()
    if skill_type not in VALID_SKILL_TYPES:
        return Response(
            {'error': f'skill_type غير صحيح. يجب أن يكون أحد: {", ".join(VALID_SKILL_TYPES)}'},
            status=status.HTTP_400_BAD_REQUEST
        )

    skill_title = data.get('skill_title', '').strip()
    if not skill_title:
        return Response({'error': 'skill_title مطلوب'}, status=status.HTTP_400_BAD_REQUEST)

    no_easy = int(data.get('no_easy', 0))
    no_medium = int(data.get('no_medium', 0))
    no_hard = int(data.get('no_hard', 0))

    if no_easy + no_medium + no_hard == 0:
        return Response({'error': 'يجب تحديد عدد الأسئلة (سهل أو متوسط أو صعب)'}, status=status.HTTP_400_BAD_REQUEST)

    book_ids = data.get('book_ids', [])
    media_ids = data.get('media_ids', [])

    if not book_ids and not media_ids:
        return Response({'error': 'يجب تحديد كتاب واحد على الأقل أو ميديا واحدة على الأقل'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # تأكد إن الـ content موجود وجاهز
        books = ExtractedBook.objects.filter(id__in=book_ids, status='DONE')
        media_qs = ExtractedMedia.objects.filter(id__in=media_ids, status='DONE')

        not_ready_books = set(book_ids) - set(books.values_list('id', flat=True))
        not_ready_media = set(int(x) for x in media_ids) - set(media_qs.values_list('id', flat=True))

        if not_ready_books:
            return Response(
                {'error': f'الكتب التالية غير جاهزة أو غير موجودة: {list(not_ready_books)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if not_ready_media:
            return Response(
                {'error': f'الميديا التالية غير جاهزة أو غير موجودة: {list(not_ready_media)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # إنشاء الـ job
        job = AIGenerationJob.objects.create(
            skill_type=skill_type,
            skill_title=skill_title,
            skill_description=data.get('skill_description', ''),
            no_easy=no_easy,
            no_medium=no_medium,
            no_hard=no_hard,
            additional_notes=data.get('additional_notes', ''),
            status='PENDING',
            created_by=request.user,
        )
        job.books.set(books)
        job.media.set(media_qs)
        job.save()

        generate_skill_task.delay(job.id)

        return Response({
            'message': 'بدأ توليد المهارة والأسئلة',
            'job_id': job.id,
            'status': job.status,
            'total_questions_requested': job.total_questions_requested,
        }, status=status.HTTP_202_ACCEPTED)

    except Exception as e:
        logger.error(f"[generate_skill] Error: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def generation_job_status(request, job_id):
    """
    GET /api/step/ai/jobs/{job_id}/status/
    """
    from .ai_models import AIGenerationJob

    job = get_object_or_404(AIGenerationJob, id=job_id)
    response_data = {
        'job_id': job.id,
        'status': job.status,
        'skill_type': job.skill_type,
        'skill_title': job.skill_title,
        'total_questions_requested': job.total_questions_requested,
        'questions_created': job.questions_created,
        'error_message': job.error_message,
        'created_at': job.created_at,
        'updated_at': job.updated_at,
    }
    if job.skill:
        response_data['skill_id'] = job.skill.id
        response_data['skill_title'] = job.skill.title

    return Response(response_data)