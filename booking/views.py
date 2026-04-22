from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated, AllowAny

from .models import Teacher
from .serializers import (
    TeacherListSerializer,
    TeacherDetailSerializer,
    TeacherCreateUpdateSerializer,
  
)

import logging
logger = logging.getLogger(__name__)



# ============================================
# HELPER FUNCTIONS
# ============================================

def _send_subscription_emails(subscription):
    """
    helper function لإرسال الـ 3 إيميلات بعد الاشتراك
    """
    program = subscription.program
    teacher = program.teacher
    student = subscription.student

    schedules_text = "\n".join([
        f"  - {s.get_day_of_week_display()} الساعة {s.time.strftime('%I:%M %p')}"
        for s in program.schedules.all()
    ])

    # إيميل الطالب
    try:
        send_mail(
            subject=f"✅ تم تأكيد اشتراكك في برنامج {program.title}",
            message=f"""
مرحباً {student.full_name}،

تم تأكيد اشتراكك بنجاح!

━━━━━━━━━━━━━━━━━━━━━━━━━━
📚 تفاصيل البرنامج:
━━━━━━━━━━━━━━━━━━━━━━━━━━
البرنامج: {program.title}
المدرس: {teacher.name}
المدة: {program.duration}
النظام: {program.get_recurrence_display()}
المواعيد:
{schedules_text}

━━━━━━━━━━━━━━━━━━━━━━━━━━
💳 تفاصيل الدفع:
━━━━━━━━━━━━━━━━━━━━━━━━━━
المبلغ: {subscription.amount} جنيه
رقم العملية: {subscription.payment_id}
━━━━━━━━━━━━━━━━━━━━━━━━━━

سيتم التواصل معك قريباً لتحديد تفاصيل البداية.
            """,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[student.email],
            fail_silently=True,
        )
    except Exception as e:
        logger.error(f"Student subscription email failed: {e}")

    # إيميل المدرس
    try:
        send_mail(
            subject=f"🎓 طالب جديد اشترك في برنامج {program.title}",
            message=f"""
مرحباً {teacher.name}،

طالب جديد اشترك في برنامجك!

الاسم: {student.full_name}
البريد: {student.email}
البرنامج: {program.title}
المواعيد:
{schedules_text}
            """,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[teacher.email],
            fail_silently=True,
        )
    except Exception as e:
        logger.error(f"Teacher subscription email failed: {e}")

    # إيميل التطبيق
    try:
        send_mail(
            subject=f"💰 اشتراك جديد - {program.title}",
            message=f"""
اشتراك جديد في المنصة!


الطالب: {student.full_name} ({student.email})
البرنامج: {program.title}
المدرس: {teacher.name}
المبلغ: {subscription.amount} جنيه
payment_id: {subscription.payment_id}
            """,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.COMPANY_EMAIL],
            fail_silently=True,
        )
    except Exception as e:
        logger.error(f"Company subscription email failed: {e}")
# ============================================
# 1. TEACHER CRUD (Admin)
# ============================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_teachers(request):
    """
    عرض جميع المدرسين النشطين

    GET /booking/teachers/
    """
    teachers = Teacher.objects.filter(is_active=True)
    serializer = TeacherListSerializer(teachers, many=True)

    return Response({
        'total_teachers': teachers.count(),
        'teachers': serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_teacher(request, teacher_id):
    """
    عرض تفاصيل مدرس معين

    GET /booking/teachers/{teacher_id}/
    """
    teacher = get_object_or_404(Teacher, id=teacher_id)
    serializer = TeacherDetailSerializer(teacher)

    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_teacher(request):
    """
    إنشاء مدرس جديد

    POST /booking/teachers/create/

    Body (multipart/form-data):
    {
        "name": "أحمد محمد",
        "profile_picture": <file>,
        "subject": "English",
        "years_of_experience": 5,
        "session_price": 150.00,
        "bio": "نبذة عن المدرس...",
        "is_active": true
    }
    """
    serializer = TeacherCreateUpdateSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    teacher = serializer.save()

    return Response({
        'message': 'تم إنشاء المدرس بنجاح',
        'teacher': TeacherDetailSerializer(teacher).data
    }, status=status.HTTP_201_CREATED)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_teacher(request, teacher_id):
    """
    تعديل بيانات مدرس

    PUT/PATCH /booking/teachers/{teacher_id}/update/
    """
    teacher = get_object_or_404(Teacher, id=teacher_id)

    partial = request.method == 'PATCH'
    serializer = TeacherCreateUpdateSerializer(
        teacher,
        data=request.data,
        partial=partial
    )

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    teacher = serializer.save()

    return Response({
        'message': 'تم تحديث بيانات المدرس بنجاح',
        'teacher': TeacherDetailSerializer(teacher).data
    }, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_teacher(request, teacher_id):
    """
    حذف مدرس

    DELETE /booking/teachers/{teacher_id}/delete/
    """
    teacher = get_object_or_404(Teacher, id=teacher_id)

    name = teacher.name
    teacher.delete()

    return Response({
        'message': 'تم حذف المدرس بنجاح',
        'teacher_id': teacher_id,
        'name': name
    }, status=status.HTTP_200_OK)



from .models import Teacher, Review
from .serializers import ReviewSerializer, ReviewCreateSerializer

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_review(request):
    """
    إنشاء تقييم جديد للمدرس
    POST /booking/reviews/create/
    Body: { "teacher": 1, "rating": 5, "comment": "ممتاز" }
    """
    serializer = ReviewCreateSerializer(
        data=request.data,
        context={'request': request}
    )
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    review = serializer.save(student=request.user)
    return Response(
        ReviewSerializer(review).data,
        status=status.HTTP_201_CREATED
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_teacher_reviews(request, teacher_id):
    """
    عرض تقييمات مدرس معين
    GET /booking/teachers/{teacher_id}/reviews/
    """
    teacher = get_object_or_404(Teacher, id=teacher_id)
    reviews = teacher.reviews.select_related('student').all()
    return Response({
        'average_rating': teacher.average_rating,
        'reviews_count': teacher.reviews_count,
        'reviews': ReviewSerializer(reviews, many=True).data
    })


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_review(request, teacher_id):
    """
    حذف تقييم الطالب لمدرس معين
    DELETE /booking/teachers/{teacher_id}/reviews/delete/
    """
    review = get_object_or_404(
        Review,
        teacher_id=teacher_id,
        student=request.user
    )
    review.delete()
    return Response({'message': 'تم حذف التقييم بنجاح'})

import hmac
import hashlib
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from .models import Program, ProgramSchedule, Subscription, CustomProgram
from .serializers import (
    ProgramListSerializer, ProgramCreateUpdateSerializer,
    SubscriptionSerializer, SubscriptionCreateSerializer,
    CustomProgramCreateSerializer, CustomProgramDetailSerializer,
)
from .moyasar_service import get_payment, verify_webhook_signature


# ============================================
# PROGRAM VIEWS
# ============================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_programs(request):
    """
    عرض جميع البرامج النشطة
    GET /booking/programs/
    
    Query Parameters:
    - teacher_id: filter by teacher
    """
    teacher_id = request.query_params.get('teacher_id')
    programs = Program.objects.filter(is_active=True).select_related('teacher').prefetch_related('schedules')

    if teacher_id:
        programs = programs.filter(teacher_id=teacher_id)

    serializer = ProgramListSerializer(programs, many=True)
    return Response({
        'total_programs': programs.count(),
        'programs': serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_program(request, program_id):
    """
    عرض تفاصيل برنامج معين
    GET /booking/programs/{program_id}/
    """
    program = get_object_or_404(Program, id=program_id)
    serializer = ProgramListSerializer(program)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_program(request):
    """
    إنشاء برنامج تعليمي جديد (للأدمن)
    POST /booking/programs/create/

    Body:
    {
        "teacher": 1,
        "title": "برنامج تأسيس الإنجليزي",
        "description": "برنامج شامل...",
        "recurrence": "weekly",
        "duration": "3 أشهر",
        "price": 500.00,
        "is_active": true,
        "schedules": [
            {"day_of_week": 5, "time": "08:00:00"},
            {"day_of_week": 6, "time": "16:00:00"},
            {"day_of_week": 3, "time": "15:00:00"}
        ]
    }
    """
    serializer = ProgramCreateUpdateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    program = serializer.save()
    return Response({
        'message': 'تم إنشاء البرنامج بنجاح',
        'program': ProgramListSerializer(program).data
    }, status=status.HTTP_201_CREATED)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_program(request, program_id):
    """
    تعديل برنامج تعليمي (للأدمن)
    PUT/PATCH /booking/programs/{program_id}/update/
    """
    program = get_object_or_404(Program, id=program_id)
    partial = request.method == 'PATCH'
    serializer = ProgramCreateUpdateSerializer(program, data=request.data, partial=partial)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    program = serializer.save()
    return Response({
        'message': 'تم تحديث البرنامج بنجاح',
        'program': ProgramListSerializer(program).data
    }, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_program(request, program_id):
    """
    حذف برنامج تعليمي (للأدمن)
    DELETE /booking/programs/{program_id}/delete/
    """
    program = get_object_or_404(Program, id=program_id)
    title = program.title
    program.delete()
    return Response({
        'message': 'تم حذف البرنامج بنجاح',
        'program_id': program_id,
        'title': title
    }, status=status.HTTP_200_OK)


# ============================================
# SUBSCRIPTION VIEWS
# ============================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_subscriptions(request):
    """
    عرض اشتراكات الطالب الحالي
    GET /booking/subscriptions/my/
    """
    subscriptions = Subscription.objects.filter(
        student=request.user,
        payment_status='paid'
    ).select_related('program__teacher').prefetch_related('program__schedules')

    serializer = SubscriptionSerializer(subscriptions, many=True)
    return Response({
        'total_subscriptions': subscriptions.count(),
        'subscriptions': serializer.data
    }, status=status.HTTP_200_OK)


# ============================================
# WEBHOOK - Moyasar
# ============================================

@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])  
def moyasar_webhook(request):
    """
    Webhook من Moyasar لتحديث حالة الدفع تلقائياً
    POST /booking/webhooks/moyasar/

    ⚠️ مش محتاج IsAuthenticated لأن Moyasar هو اللي بيبعت
    """
    # التحقق من الـ signature
    signature = request.headers.get('X-Moyasar-Signature', '')
    if not verify_webhook_signature(request.body, signature):
        logger.warning("Moyasar webhook: invalid signature")
        return Response({'error': 'Invalid signature'}, status=status.HTTP_400_BAD_REQUEST)

    event = request.data
    event_type = event.get('type')
    payment = event.get('data', {})
    payment_id = payment.get('id')
    payment_status = payment.get('status')

    logger.info(f"Moyasar webhook received: type={event_type}, payment_id={payment_id}, status={payment_status}")

    if event_type == 'payment_paid':
        Subscription.objects.filter(payment_id=payment_id).update(payment_status='paid')

    elif event_type == 'payment_failed':
        Subscription.objects.filter(payment_id=payment_id).update(payment_status='failed')

    return Response({'message': 'ok'}, status=status.HTTP_200_OK)


# ============================================
# CUSTOM PROGRAM VIEWS
# ============================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_custom_program(request):
    """
    إرسال طلب تخصيص برنامج
    POST /booking/custom-programs/create/

    Body:
    {
        "teacher": 1,
        "whatsapp_number": "01012345678",
        "recurrence": "weekly",
        "duration": "شهرين",
        "curriculum": "أريد التركيز على المحادثة والنطق",
        "schedules": [
            {"day_of_week": 5, "time": "09:00:00"},
            {"day_of_week": 1, "time": "17:00:00"}
        ]
    }
    """
    serializer = CustomProgramCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    custom_program = serializer.save(student=request.user)

    # إيميل للدعم
    try:
        student = request.user
        teacher = custom_program.teacher
        schedules_text = "\n".join([
            f"  - {s.get_day_of_week_display()} الساعة {s.time.strftime('%I:%M %p')}"
            for s in custom_program.schedules.all()
        ])

        send_mail(
            subject=f"📋 طلب تخصيص برنامج جديد - {student.full_name}",
            message=f"""
طلب تخصيص برنامج جديد!

━━━━━━━━━━━━━━━━━━━━━━━━━━
👤 بيانات الطالب:
━━━━━━━━━━━━━━━━━━━━━━━━━━
الاسم: {student.full_name}
البريد: {student.email}
واتساب: {custom_program.whatsapp_number}

━━━━━━━━━━━━━━━━━━━━━━━━━━
👨‍🏫 المدرس المطلوب:
━━━━━━━━━━━━━━━━━━━━━━━━━━
{teacher.name} - {teacher.subject}

━━━━━━━━━━━━━━━━━━━━━━━━━━
📚 تفاصيل البرنامج المطلوب:
━━━━━━━━━━━━━━━━━━━━━━━━━━
المنهج: {custom_program.curriculum}
المدة: {custom_program.duration}
النظام: {custom_program.get_recurrence_display()}
المواعيد المفضلة:
{schedules_text}
━━━━━━━━━━━━━━━━━━━━━━━━━━
            """,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.COMPANY_EMAIL],
            fail_silently=True,
        )
    except Exception as e:
        logger.error(f"Custom program support email failed: {e}")

    return Response({
        'message': 'تم إرسال طلب التخصيص بنجاح، سنقوم بالتواصل معك في أقرب وقت'
    }, status=status.HTTP_201_CREATED)


from .moyasar_service import create_payment, get_payment, verify_webhook_signature

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def initiate_subscription_payment(request):
    """
    إنشاء طلب الدفع باستخدام token من Moyasar.js
    POST /booking/subscriptions/pay/

    Body:
    {
        "program_id": 1,
        "token": "tok_xxxxxxxxxxxxxxxx"   ← الـ token من Moyasar.js في الـ Frontend
    }

    Response:
    {
        "payment_id": "pay_xxx",
        "status": "initiated",
        "transaction_url": "https://..."  ← لو محتاج 3DS redirect
        "amount": 500.00
    }
    """
    program_id = request.data.get('program_id')
    token = request.data.get('token')

    # Validation
    if not program_id:
        return Response({'error': 'program_id مطلوب'}, status=status.HTTP_400_BAD_REQUEST)
    if not token:
        return Response({'error': 'token مطلوب'}, status=status.HTTP_400_BAD_REQUEST)

    program = get_object_or_404(Program, id=program_id, is_active=True)

    # التحقق إن الطالب مش مشترك أصلاً
    already_subscribed = Subscription.objects.filter(
        student=request.user,
        program=program,
        payment_status='paid'
    ).exists()

    if already_subscribed:
        return Response(
            {'error': 'أنت مشترك بالفعل في هذا البرنامج'},
            status=status.HTTP_400_BAD_REQUEST
        )

    amount_halalas = int(program.price * 100)
    callback_url = f"{settings.FRONTEND_URL}/payment/callback"

    try:
        payment_data = create_payment(
            amount_halalas=amount_halalas,
            description=f"اشتراك في برنامج: {program.title}",
            callback_url=callback_url,
            token=token,                          # ← بنبعت الـ token هنا
            metadata={
                "program_id": str(program.id),
                "student_id": str(request.user.id),
            }
        )
    except Exception as e:
        logger.error(f"Moyasar create payment failed: {e}")
        return Response(
            {'error': 'تعذر إنشاء طلب الدفع، حاول مرة أخرى'},
            status=status.HTTP_502_BAD_GATEWAY
        )

    payment_status_from_moyasar = payment_data.get('status')
    moyasar_id = payment_data.get('id')
    transaction_url = payment_data.get('source', {}).get('transaction_url')

    # لو الدفع اتأكد على طول (paid) — بدون 3DS
    if payment_status_from_moyasar == 'paid':
        Subscription.objects.create(
            student=request.user,
            program=program,
            payment_id=moyasar_id,
            payment_status='paid',
            amount=program.price,
        )

    return Response({
        'payment_id': moyasar_id,
        'status': payment_status_from_moyasar,
        'transaction_url': transaction_url,   # ← الـ Frontend يعمل redirect لو موجود
        'amount': program.price,
    }, status=status.HTTP_200_OK)

@csrf_exempt
@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def subscription_payment_callback(request):
    payment_id = (
        request.data.get('payment_id') or
        request.data.get('id') or
        request.query_params.get('id')
    )

    if not payment_id:
        return Response({'error': 'payment_id مطلوب'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        payment_data = get_payment(payment_id)
    except Exception as e:
        logger.error(f"Moyasar callback - payment fetch failed: {e}")
        return Response({'error': 'تعذر التحقق من الدفع'}, status=status.HTTP_502_BAD_GATEWAY)

    if not payment_data or not isinstance(payment_data, dict):
        return Response({'error': 'بيانات الدفع غير صالحة'}, status=status.HTTP_502_BAD_GATEWAY)

    payment_status = payment_data.get('status')
    metadata = payment_data.get('metadata') or {}

    program_id = metadata.get('program_id') or request.data.get('program_id')
    student_id = metadata.get('student_id')

    logger.info(f"Callback - payment_id: {payment_id}, status: {payment_status}, program_id: {program_id}")

    if not program_id:
        return Response({'error': 'program_id مطلوب'}, status=status.HTTP_400_BAD_REQUEST)

    program = get_object_or_404(Program, id=program_id)

    # لو الاشتراك موجود بالفعل
    existing = Subscription.objects.filter(payment_id=payment_id).first()
    if existing:
        return Response({
            'status': existing.payment_status,
            'subscription_id': existing.id,
        }, status=status.HTTP_200_OK)

    from django.contrib.auth import get_user_model
    User = get_user_model()

    # جيب الـ student
    if student_id:
        student = get_object_or_404(User, id=student_id)
    elif request.user.is_authenticated:
        student = request.user
    else:
        return Response({'error': 'تعذر تحديد الطالب'}, status=status.HTTP_400_BAD_REQUEST)

    amount = payment_data.get('amount', 0) / 100

    subscription = Subscription.objects.create(
        student=student,
        program=program,
        payment_id=payment_id,
        payment_status='paid' if payment_status == 'paid' else 'failed',
        amount=amount,
    )

    if payment_status == 'paid':
        _send_subscription_emails(subscription)

    return Response({
        'status': payment_status,
        'subscription_id': subscription.id,
    }, status=status.HTTP_200_OK)