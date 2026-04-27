import logging
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

logger = logging.getLogger(__name__)

VALID_SKILL_TYPES = ['VOCABULARY', 'GRAMMAR', 'READING', 'LISTENING', 'SPEAKING', 'WRITING', 'GENERAL_PATH']


# ============================================================
# BOOK EXTRACTION
# ============================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def extract_book(request):
    """
    POST /api/esp/ai/extract-book/
    Body (multipart): { name, pdf_file }
    """
    from .ai_models import EspExtractedBook
    from .tasks import esp_extract_book_task

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
            folder='esp/ai/books',
            access_mode='public',
        )
        book = EspExtractedBook.objects.create(
            name=name,
            pdf_file=upload_result['public_id'],
            status='PENDING',
            uploaded_by=request.user,
        )

        esp_extract_book_task.delay(book.id)

        return Response({
            'message': 'جاري استخراج النص من الكتاب',
            'book_id': book.id,
            'status': book.status,
        }, status=status.HTTP_202_ACCEPTED)

    except Exception as e:
        logger.error(f"[Esp extract_book] Error: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def extract_book_status(request, book_id):
    """
    GET /api/esp/ai/extract-book/{book_id}/status/
    """
    from .ai_models import EspExtractedBook

    book = get_object_or_404(EspExtractedBook, id=book_id)
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
    GET /api/esp/ai/extract-book/
    """
    from .ai_models import EspExtractedBook

    books = EspExtractedBook.objects.filter(status='DONE').order_by('-created_at')
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


# ============================================================
# MEDIA EXTRACTION
# ============================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def extract_media(request):
    """
    POST /api/esp/ai/extract-media/
    Body (multipart): { name, media_file }
    """
    from .ai_models import EspExtractedMedia
    from .tasks import esp_extract_media_task

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
            folder='esp/ai/media',
        )
        media = EspExtractedMedia.objects.create(
            name=name,
            media_file=upload_result['public_id'],
            media_type=media_type,
            status='PENDING',
            uploaded_by=request.user,
        )

        esp_extract_media_task.delay(media.id)

        return Response({
            'message': 'جاري استخراج الترانسكريبت',
            'media_id': media.id,
            'media_type': media_type,
            'status': media.status,
        }, status=status.HTTP_202_ACCEPTED)

    except Exception as e:
        logger.error(f"[Esp extract_media] Error: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def extract_media_status(request, media_id):
    """
    GET /api/esp/ai/extract-media/{media_id}/status/
    """
    from .ai_models import EspExtractedMedia

    media = get_object_or_404(EspExtractedMedia, id=media_id)
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
    GET /api/esp/ai/extract-media/
    """
    from .ai_models import EspExtractedMedia

    media_qs = EspExtractedMedia.objects.filter(status='DONE').order_by('-created_at')
    return Response({
        'media': [
            {
                'id': m.id,
                'name': m.name,
                'media_type': m.media_type,
                'duration_seconds': m.duration_seconds,
                'created_at': m.created_at,
                'status': m.status,
            }
            for m in media_qs
        ]
    })


# ============================================================
# AI SKILL GENERATION
# الفرق الجوهري: بنبعت category_id عشان الـ skill تتعمل جوّاها
# ============================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_skill(request):
    """
    POST /api/esp/ai/generate-skill/

    Body:
    {
        "category_id": 3,              ← مطلوب - الكاتيجوري اللي هيتضاف جوّاها الـ skill
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
    from .ai_models import EspAIGenerationJob, EspExtractedBook, EspExtractedMedia
    from .models import EspCategory
    from .tasks import esp_generate_skill_task

    data = request.data

    # Validation - category_id مطلوب (الفرق عن IELTS)
    category_id = data.get('category_id')
    if not category_id:
        return Response({'error': 'category_id مطلوب'}, status=status.HTTP_400_BAD_REQUEST)

    category = get_object_or_404(EspCategory, id=category_id, is_active=True)

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
        return Response(
            {'error': 'يجب تحديد عدد الأسئلة (سهل أو متوسط أو صعب)'},
            status=status.HTTP_400_BAD_REQUEST
        )

    book_ids = data.get('book_ids', [])
    media_ids = data.get('media_ids', [])

    if not book_ids and not media_ids:
        return Response(
            {'error': 'يجب تحديد كتاب واحد على الأقل أو ميديا واحدة على الأقل'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        books = EspExtractedBook.objects.filter(id__in=book_ids, status='DONE')
        media_qs = EspExtractedMedia.objects.filter(id__in=media_ids, status='DONE')

        not_ready_books = set(int(x) for x in book_ids) - set(books.values_list('id', flat=True))
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

        job = EspAIGenerationJob.objects.create(
            category=category,
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

        esp_generate_skill_task.delay(job.id)

        return Response({
            'message': 'بدأ توليد المهارة والأسئلة',
            'job_id': job.id,
            'category_id': category.id,
            'category_name': category.name,
            'skill_type': skill_type,
            'status': job.status,
            'total_questions_requested': job.total_questions_requested,
        }, status=status.HTTP_202_ACCEPTED)

    except Exception as e:
        logger.error(f"[Esp generate_skill] Error: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def generation_job_status(request, job_id):
    """
    GET /api/esp/ai/jobs/{job_id}/status/
    """
    from .ai_models import EspAIGenerationJob

    job = get_object_or_404(EspAIGenerationJob, id=job_id)

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

    if job.category:
        response_data['category_id'] = job.category.id
        response_data['category_name'] = job.category.name

    if job.skill:
        response_data['skill_id'] = job.skill.id
        response_data['skill_title_created'] = job.skill.title

    return Response(response_data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_generation_jobs(request):
    """
    GET /api/esp/ai/jobs/
    فلترة اختيارية بالكاتيجوري: ?category_id=3
    """
    from .ai_models import EspAIGenerationJob
    from sabr_questions.models import ListeningAudio, SpeakingVideo

    qs = EspAIGenerationJob.objects.select_related('category', 'skill').order_by('-created_at')

    category_id = request.query_params.get('category_id')
    if category_id:
        qs = qs.filter(category_id=category_id)

    def get_media_ids(j):
        if j.skill_type == 'LISTENING' and j.skill:
            audio = ListeningAudio.objects.filter(
                esp_skill=j.skill, usage_type='ESP'
            ).first()
            return {'audio_id': audio.id if audio else None, 'video_id': None}
        elif j.skill_type == 'SPEAKING' and j.skill:
            video = SpeakingVideo.objects.filter(
                esp_skill=j.skill, usage_type='ESP'
            ).first()
            return {'audio_id': None, 'video_id': video.id if video else None}
        return {'audio_id': None, 'video_id': None}

    return Response({
        'jobs': [
            {
                'job_id': j.id,
                'status': j.status,
                'category_id': j.category.id if j.category else None,
                'category_name': j.category.name if j.category else None,
                'skill_type': j.skill_type,
                'skill_title': j.skill_title,
                'skill_id': j.skill.id if j.skill else None,
                'total_questions_requested': j.total_questions_requested,
                'questions_created': j.questions_created,
                'error_message': j.error_message,
                'created_at': j.created_at,
                **get_media_ids(j),
            }
            for j in qs[:50]
        ]
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_questions_to_skill(request):
    """
    POST /api/esp/ai/add-questions/

    Body:
    {
        "skill_id": 5,
        "book_ids": [1, 2],
        "media_ids": [3],
        "no_easy": 5,
        "no_medium": 5,
        "no_hard": 5,
        "additional_notes": "..."
    }
    """
    from .ai_models import EspAIGenerationJob, EspExtractedBook, EspExtractedMedia
    from .models import EspSkill
    from .tasks import esp_add_questions_to_skill_task

    data = request.data

    skill_id = data.get('skill_id')
    if not skill_id:
        return Response({'error': 'skill_id مطلوب'}, status=status.HTTP_400_BAD_REQUEST)

    skill = get_object_or_404(EspSkill, id=skill_id)

    no_easy   = int(data.get('no_easy',   0))
    no_medium = int(data.get('no_medium', 0))
    no_hard   = int(data.get('no_hard',   0))

    if no_easy + no_medium + no_hard == 0:
        return Response(
            {'error': 'يجب تحديد عدد الأسئلة (سهل أو متوسط أو صعب)'},
            status=status.HTTP_400_BAD_REQUEST
        )

    book_ids  = data.get('book_ids',  [])
    media_ids = data.get('media_ids', [])

    if not book_ids and not media_ids:
        return Response(
            {'error': 'يجب تحديد كتاب واحد على الأقل أو ميديا واحدة على الأقل'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        books    = EspExtractedBook.objects.filter(id__in=book_ids,  status='DONE')
        media_qs = EspExtractedMedia.objects.filter(id__in=media_ids, status='DONE')

        not_ready_books = set(int(x) for x in book_ids)  - set(books.values_list('id', flat=True))
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

        job = EspAIGenerationJob.objects.create(
            category=skill.category,        # ← نربطه بنفس كاتيجوري الـ skill
            skill=skill,                    # ← الـ skill الموجودة مباشرةً
            skill_type=skill.skill_type,
            skill_title=skill.title,
            skill_description=skill.description or '',
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

        esp_add_questions_to_skill_task.delay(job.id)

        return Response({
            'message': 'بدأ توليد الأسئلة وإضافتها على المهارة',
            'job_id': job.id,
            'skill_id': skill.id,
            'skill_title': skill.title,
            'skill_type': skill.skill_type,
            'category_id': skill.category.id,
            'category_name': skill.category.name,
            'total_questions_requested': job.total_questions_requested,
            'status': job.status,
        }, status=status.HTTP_202_ACCEPTED)

    except Exception as e:
        logger.error(f"[Esp add_questions_to_skill] Error: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)