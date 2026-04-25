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
def _get_student_email_html(student, program, teacher, subscription, schedules_text):
    schedules_badges = "".join([
        f'<span style="background:#dcfce7;color:#15803d;padding:4px 12px;border-radius:20px;font-size:13px;font-weight:600;display:inline-block;margin:3px;">{s.get_day_of_week_display()} {s.time.strftime("%I:%M %p")}</span>'
        for s in program.schedules.all()
    ])
    return f"""
<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f4f4f4;font-family:Arial,sans-serif;direction:rtl;">
  <div style="max-width:560px;margin:24px auto;background:#fff;border-radius:12px;overflow:hidden;border:1px solid #e0e0e0;">
    
    <div style="background:#16a34a;padding:32px 28px;text-align:center;">
      <div style="font-size:36px;margin-bottom:8px;">🎓</div>
      <h1 style="color:#fff;margin:0;font-size:22px;font-weight:700;">تم تأكيد اشتراكك بنجاح!</h1>
      <p style="color:#bbf7d0;margin:8px 0 0;font-size:14px;">مرحباً بك في رحلتك التعليمية</p>
    </div>

    <div style="padding:28px;">
      <p style="color:#374151;font-size:15px;margin:0 0 20px;">مرحباً <strong>{student.full_name}</strong>،</p>

      <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:10px;padding:20px;margin-bottom:20px;">
        <div style="margin-bottom:14px;">
          <span style="font-size:18px;">📚</span>
          <span style="font-weight:700;color:#15803d;font-size:16px;margin-right:6px;">تفاصيل البرنامج</span>
        </div>
        <table style="width:100%;border-collapse:collapse;">
          <tr><td style="padding:6px 0;color:#6b7280;font-size:14px;width:40%;">البرنامج</td><td style="color:#111827;font-size:14px;font-weight:600;">{program.title}</td></tr>
          <tr><td style="padding:6px 0;color:#6b7280;font-size:14px;">المدرس</td><td style="color:#111827;font-size:14px;">{teacher.name}</td></tr>
          <tr><td style="padding:6px 0;color:#6b7280;font-size:14px;">المدة</td><td style="color:#111827;font-size:14px;">{program.duration}</td></tr>
          <tr><td style="padding:6px 0;color:#6b7280;font-size:14px;">النظام</td><td style="color:#111827;font-size:14px;">{program.get_recurrence_display()}</td></tr>
        </table>
        <div style="border-top:1px solid #bbf7d0;margin-top:12px;padding-top:12px;">
          <p style="color:#6b7280;font-size:13px;margin:0 0 8px;">المواعيد</p>
          {schedules_badges}
        </div>
      </div>

      <div style="background:#f9fafb;border:1px solid #e5e7eb;border-radius:10px;padding:20px;margin-bottom:20px;">
        <div style="margin-bottom:14px;">
          <span style="font-size:18px;">💳</span>
          <span style="font-weight:700;color:#374151;font-size:16px;margin-right:6px;">تفاصيل الدفع</span>
        </div>
        <div style="display:flex;justify-content:space-between;align-items:center;">
          <span style="color:#6b7280;font-size:14px;">المبلغ المدفوع</span>
          <span style="font-size:22px;font-weight:700;color:#16a34a;">{subscription.amount} ريال</span>
        </div>
        <div style="border-top:1px dashed #e5e7eb;margin-top:10px;padding-top:10px;">
          <span style="color:#9ca3af;font-size:12px;">رقم العملية: {subscription.payment_id}</span>
        </div>
        <tr>
        <td style="padding:6px 0;color:#6b7280;font-size:14px;">الرقم المرجعي</td>
        <td style="color:#16a34a;font-size:15px;font-weight:700;font-family:monospace;">
            {subscription.reference_number}
        </td>
        </tr>
      </div>

      <div style="background:#fffbeb;border:1px solid #fde68a;border-radius:10px;padding:16px;text-align:center;">
        <p style="color:#92400e;font-size:14px;margin:0;">⏳ سيتم التواصل معك قريباً لتحديد تفاصيل البداية</p>
      </div>
    </div>

    <div style="background:#f9fafb;border-top:1px solid #e5e7eb;padding:16px;text-align:center;">
      <p style="color:#9ca3af;font-size:12px;margin:0;">Sabrlinguaa · جميع الحقوق محفوظة</p>
    </div>
  </div>
</body>
</html>
"""


def _get_teacher_email_html(teacher, student, program, schedules_badges):
    return f"""
<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#f4f4f4;font-family:Arial,sans-serif;direction:rtl;">
  <div style="max-width:560px;margin:24px auto;background:#fff;border-radius:12px;overflow:hidden;border:1px solid #e0e0e0;">
    <div style="background:#1d4ed8;padding:28px;text-align:center;">
      <div style="font-size:32px;margin-bottom:8px;">🎓</div>
      <h1 style="color:#fff;margin:0;font-size:20px;font-weight:700;">طالب جديد اشترك في برنامجك!</h1>
    </div>
    <div style="padding:28px;">
      <p style="color:#374151;font-size:15px;margin:0 0 20px;">مرحباً <strong>{teacher.name}</strong>،</p>
      <div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:10px;padding:20px;">
        <table style="width:100%;border-collapse:collapse;">
          <tr><td style="padding:6px 0;color:#6b7280;font-size:14px;width:40%;">اسم الطالب</td><td style="color:#111827;font-size:14px;font-weight:600;">{student.full_name}</td></tr>
          <tr><td style="padding:6px 0;color:#6b7280;font-size:14px;">البريد</td><td style="color:#1d4ed8;font-size:14px;">{student.email}</td></tr>
          <tr><td style="padding:6px 0;color:#6b7280;font-size:14px;">البرنامج</td><td style="color:#111827;font-size:14px;">{program.title}</td></tr>
        </table>
        <div style="border-top:1px solid #bfdbfe;margin-top:12px;padding-top:12px;">
          <p style="color:#6b7280;font-size:13px;margin:0 0 8px;">المواعيد</p>
          {schedules_badges}
        </div>
      </div>
    </div>
    <div style="background:#f9fafb;border-top:1px solid #e5e7eb;padding:16px;text-align:center;">
      <p style="color:#9ca3af;font-size:12px;margin:0;">Sabrlinguaa · جميع الحقوق محفوظة</p>
    </div>
  </div>
</body>
</html>
"""


def _get_company_email_html(student, program, teacher, subscription):
    return f"""
<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#f4f4f4;font-family:Arial,sans-serif;direction:rtl;">
  <div style="max-width:560px;margin:24px auto;background:#fff;border-radius:12px;overflow:hidden;border:1px solid #e0e0e0;">
    <div style="background:#7c3aed;padding:28px;text-align:center;">
      <div style="font-size:32px;margin-bottom:8px;">💰</div>
      <h1 style="color:#fff;margin:0;font-size:20px;font-weight:700;">اشتراك جديد في المنصة!</h1>
    </div>
    <div style="padding:28px;">
      <div style="background:#faf5ff;border:1px solid #e9d5ff;border-radius:10px;padding:20px;">
        <table style="width:100%;border-collapse:collapse;">
          <tr><td style="padding:6px 0;color:#6b7280;font-size:14px;width:40%;">الطالب</td><td style="color:#111827;font-size:14px;font-weight:600;">{student.full_name}</td></tr>
          <tr><td style="padding:6px 0;color:#6b7280;font-size:14px;">البريد</td><td style="color:#111827;font-size:14px;">{student.email}</td></tr>
          <tr><td style="padding:6px 0;color:#6b7280;font-size:14px;">البرنامج</td><td style="color:#111827;font-size:14px;">{program.title}</td></tr>
          <tr><td style="padding:6px 0;color:#6b7280;font-size:14px;">المدرس</td><td style="color:#111827;font-size:14px;">{teacher.name}</td></tr>
          <tr><td style="padding:6px 0;color:#6b7280;font-size:14px;">المبلغ</td><td style="color:#16a34a;font-size:18px;font-weight:700;">{subscription.amount} ريال</td></tr>
          <tr><td style="padding:6px 0;color:#6b7280;font-size:14px;">payment_id</td><td style="color:#6b7280;font-size:12px;font-family:monospace;">{subscription.payment_id}</td></tr>
        </table>
      </div>
    </div>
    <div style="background:#f9fafb;border-top:1px solid #e5e7eb;padding:16px;text-align:center;">
      <p style="color:#9ca3af;font-size:12px;margin:0;">Sabrlinguaa Dashboard</p>
    </div>
  </div>
</body>
</html>
"""


def _send_subscription_emails(subscription):
    program = subscription.program
    teacher = program.teacher
    student = subscription.student

    schedules_badges = "".join([
        f'<span style="background:#dcfce7;color:#15803d;padding:4px 12px;border-radius:20px;font-size:13px;font-weight:600;display:inline-block;margin:3px;">{s.get_day_of_week_display()} {s.time.strftime("%I:%M %p")}</span>'
        for s in program.schedules.all()
    ])

    # إيميل الطالب
    try:
        from django.core.mail import EmailMultiAlternatives
        msg = EmailMultiAlternatives(
            subject=f"✅ تم تأكيد اشتراكك في برنامج {program.title}",
            body=f"تم تأكيد اشتراكك في برنامج {program.title}",  # plain text fallback
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[student.email],
        )
        msg.attach_alternative(
            _get_student_email_html(student, program, teacher, subscription, schedules_badges),
            "text/html"
        )
        msg.send(fail_silently=True)
    except Exception as e:
        logger.error(f"Student subscription email failed: {e}")

    # إيميل المدرس
    try:
        msg = EmailMultiAlternatives(
            subject=f"🎓 طالب جديد اشترك في برنامج {program.title}",
            body=f"طالب جديد: {student.full_name} اشترك في {program.title}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[teacher.email],
        )
        msg.attach_alternative(
            _get_teacher_email_html(teacher, student, program, schedules_badges),
            "text/html"
        )
        msg.send(fail_silently=True)
    except Exception as e:
        logger.error(f"Teacher subscription email failed: {e}")

    # إيميل الشركة
    try:
        msg = EmailMultiAlternatives(
            subject=f"💰 اشتراك جديد - {program.title}",
            body=f"اشتراك جديد: {student.full_name} - {program.title} - {subscription.amount} ريال",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[settings.COMPANY_EMAIL],
        )
        msg.attach_alternative(
            _get_company_email_html(student, program, teacher, subscription),
            "text/html"
        )
        msg.send(fail_silently=True)
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


# ─── أضف ده في views.py ───

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def all_subscriptions(request):
    """
    عرض كل اشتراكات الطلاب (للأدمن)
    GET /booking/subscriptions/all/
    
    ⚠️ ضيف permission_classes للتحقق إن المستخدم أدمن لو عندك نظام صلاحيات
    مثال: @permission_classes([IsAuthenticated, IsAdminUser])
    """
    subscriptions = Subscription.objects.select_related(
        'student', 'program__teacher'
    ).prefetch_related(
        'program__schedules'
    ).order_by('-created_at')

    serializer = SubscriptionSerializer(subscriptions, many=True)
    return Response({
        'total_subscriptions': subscriptions.count(),
        'subscriptions': serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_subscription(request, subscription_id):
    """
    حذف اشتراك (للأدمن)
    DELETE /booking/subscriptions/{subscription_id}/delete/
    """
    from django.shortcuts import get_object_or_404
    subscription = get_object_or_404(Subscription, id=subscription_id)
    subscription.delete()
    return Response({
        'message': 'تم حذف الاشتراك بنجاح',
        'subscription_id': subscription_id,
    }, status=status.HTTP_200_OK)


from django.contrib.auth import get_user_model
from django.db.models import Sum, Count, Q, Max
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

User = get_user_model()


def _build_student_report(user):
    """
    بيبني التقرير الكامل للطالب
    """
    from ielts.models import StudentIELTSProgress, StudentIELTSQuestionAttempt
    from step.models import StudentSTEPProgress, StudentSTEPQuestionAttempt
    from esp.models import StudentEspProgress, StudentEspQuestionAttempt
    from general.models import StudentGeneralProgress, StudentGeneralQuestionAttempt
    from .models import Subscription

    # ─── 1. معلومات الطالب الأساسية ───────────────────────────
    student_profile = getattr(user, 'student_profile', None)

    basic_info = {
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "user_type": user.user_type,
        "date_joined": user.date_joined,
        "is_email_verified": user.is_email_verified,
        "phone_number": student_profile.phone_number if student_profile else None,
    }

    # ─── Helper: بيحسب إحصائيات Section معين ──────────────────
    def _section_stats(progress_qs, attempts_qs):
        """
        progress_qs  → StudentXxxProgress queryset للطالب ده
        attempts_qs  → StudentXxxQuestionAttempt queryset للطالب ده
        """
        # النقاط والأسئلة من الـ Progress
        agg = progress_qs.aggregate(
            total_score=Sum('total_score'),
            total_solved=Sum('viewed_questions_count'),
        )
        total_score   = agg['total_score'] or 0
        total_solved  = agg['total_solved'] or 0

        # إحصائيات الـ Attempts
        attempts_agg = attempts_qs.aggregate(
            total_attempts=Count('id'),
            correct_first_try=Count('id', filter=Q(is_solved=True, attempts_count=1)),
            used_show_answer=Count('id', filter=Q(used_show_answer=True)),
            total_solved_attempts=Count('id', filter=Q(is_solved=True)),
        )
        total_attempts        = attempts_agg['total_attempts'] or 0
        correct_first_try     = attempts_agg['correct_first_try'] or 0
        used_show_answer      = attempts_agg['used_show_answer'] or 0
        total_solved_attempts = attempts_agg['total_solved_attempts'] or 0

        # نسبة الصح/الغلط
        correct_pct = round((total_solved_attempts / total_attempts * 100), 1) if total_attempts else 0
        wrong_pct   = round(100 - correct_pct, 1) if total_attempts else 0

        # نقاط per question_type
        by_type = (
            attempts_qs
            .values('question_type')
            .annotate(
                attempts=Count('id'),
                solved=Count('id', filter=Q(is_solved=True)),
                score=Sum('points_earned'),
            )
            .order_by('question_type')
        )

        # آخر نشاط في هذا الـ section
        last_activity = attempts_qs.aggregate(last=Max('created_at'))['last']

        return {
            "total_score": total_score,
            "total_questions_solved": total_solved,
            "total_attempts": total_attempts,
            "correct_answers": total_solved_attempts,
            "correct_percentage": correct_pct,
            "wrong_percentage": wrong_pct,
            "used_show_answer_count": used_show_answer,
            "correct_on_first_try": correct_first_try,
            "first_try_percentage": round((correct_first_try / total_attempts * 100), 1) if total_attempts else 0,
            "last_activity": last_activity,
            "by_question_type": list(by_type),
        }

    # ─── 2. إحصائيات كل Section ───────────────────────────────
    ielts_stats = _section_stats(
        StudentIELTSProgress.objects.filter(student=user),
        StudentIELTSQuestionAttempt.objects.filter(student=user),
    )
    step_stats = _section_stats(
        StudentSTEPProgress.objects.filter(student=user),
        StudentSTEPQuestionAttempt.objects.filter(student=user),
    )
    esp_stats = _section_stats(
        StudentEspProgress.objects.filter(student=user),
        StudentEspQuestionAttempt.objects.filter(student=user),
    )
    general_stats = _section_stats(
        StudentGeneralProgress.objects.filter(student=user),
        StudentGeneralQuestionAttempt.objects.filter(student=user),
    )

    # ─── 3. الإجماليات الكلية ─────────────────────────────────
    total_score_all = (
        ielts_stats["total_score"] +
        step_stats["total_score"] +
        esp_stats["total_score"] +
        general_stats["total_score"]
    )
    total_solved_all = (
        ielts_stats["total_questions_solved"] +
        step_stats["total_questions_solved"] +
        esp_stats["total_questions_solved"] +
        general_stats["total_questions_solved"]
    )
    total_attempts_all = (
        ielts_stats["total_attempts"] +
        step_stats["total_attempts"] +
        esp_stats["total_attempts"] +
        general_stats["total_attempts"]
    )
    total_correct_all = (
        ielts_stats["correct_answers"] +
        step_stats["correct_answers"] +
        esp_stats["correct_answers"] +
        general_stats["correct_answers"]
    )

    overall_correct_pct = round((total_correct_all / total_attempts_all * 100), 1) if total_attempts_all else 0

    # آخر نشاط كلي
    activity_dates = [
        s["last_activity"] for s in [ielts_stats, step_stats, esp_stats, general_stats]
        if s["last_activity"]
    ]
    last_activity_overall = max(activity_dates) if activity_dates else None

    # ─── 4. الاشتراكات ────────────────────────────────────────
    subscriptions = (
        Subscription.objects
        .filter(student=user)
        .select_related('program__teacher')
        .prefetch_related('program__schedules')
        .order_by('-created_at')
    )
    subscriptions_data = []
    for sub in subscriptions:
        subscriptions_data.append({
            "subscription_id": sub.id,
            "reference_number": sub.reference_number,
            "program_title": sub.program.title,
            "teacher_name": sub.program.teacher.name,
            "amount": sub.amount,
            "payment_status": sub.payment_status,
            "created_at": sub.created_at,
        })

    # ─── 5. إحصائيات إضافية ───────────────────────────────────
    # أكتر question_type الطالب بيحله
    all_attempts_by_type = {}
    for section_stats in [ielts_stats, step_stats, esp_stats, general_stats]:
        for item in section_stats["by_question_type"]:
            qtype = item["question_type"]
            if qtype not in all_attempts_by_type:
                all_attempts_by_type[qtype] = {"attempts": 0, "solved": 0, "score": 0}
            all_attempts_by_type[qtype]["attempts"] += item["attempts"]
            all_attempts_by_type[qtype]["solved"]   += item["solved"]
            all_attempts_by_type[qtype]["score"]    += item["score"] or 0

    # ترتيب الـ question types بالـ score
    sorted_by_score = sorted(
        [{"question_type": k, **v} for k, v in all_attempts_by_type.items()],
        key=lambda x: x["score"],
        reverse=True,
    )

    strongest_skill = sorted_by_score[0]["question_type"] if sorted_by_score else None
    weakest_skill   = sorted_by_score[-1]["question_type"] if len(sorted_by_score) > 1 else None

    # أكتر section نشاطاً
    sections_by_score = sorted([
        {"section": "IELTS",   "score": ielts_stats["total_score"]},
        {"section": "STEP",    "score": step_stats["total_score"]},
        {"section": "ESP",     "score": esp_stats["total_score"]},
        {"section": "General", "score": general_stats["total_score"]},
    ], key=lambda x: x["score"], reverse=True)

    most_active_section = sections_by_score[0]["section"] if sections_by_score else None

    # ─── 6. تجميع التقرير ─────────────────────────────────────
    return {
        "generated_at": timezone.now(),
        "basic_info": basic_info,

        "overall_summary": {
            "total_score": total_score_all,
            "total_questions_solved": total_solved_all,
            "total_attempts": total_attempts_all,
            "correct_answers": total_correct_all,
            "correct_percentage": overall_correct_pct,
            "wrong_percentage": round(100 - overall_correct_pct, 1) if total_attempts_all else 0,
            "last_activity": last_activity_overall,
            "strongest_skill": strongest_skill,
            "weakest_skill": weakest_skill,
            "most_active_section": most_active_section,
            "sections_ranking": sections_by_score,
            "skills_breakdown": sorted_by_score,
        },

        "sections": {
            "ielts":   ielts_stats,
            "step":    step_stats,
            "esp":     esp_stats,
            "general": general_stats,
        },

        "subscriptions": {
            "total": len(subscriptions_data),
            "paid": sum(1 for s in subscriptions_data if s["payment_status"] == "paid"),
            "list": subscriptions_data,
        },
    }


# ─── Endpoint للأدمن ──────────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_report_admin(request, student_id):
    """
    تقرير شامل لطالب معين — للأدمن فقط
    GET /reports/students/{student_id}/

    ⚠️ أضف IsAdminUser لو عندك permission system
    """
    user = get_object_or_404(User, id=student_id, user_type='student')
    report = _build_student_report(user)
    return Response(report, status=status.HTTP_200_OK)


# ─── Endpoint للطالب نفسه ─────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_report(request):
    """
    تقرير الطالب لنفسه
    GET /reports/me/
    """
    report = _build_student_report(request.user)
    return Response(report, status=status.HTTP_200_OK)

# في views.py — أضف الاتنين دول

from django.http import HttpResponse
from .report_pdf import generate_student_report_pdf

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_report_pdf_admin(request, student_id):
    """
    PDF تقرير طالب معين — للأدمن
    GET /reports/students/{student_id}/pdf/
    """
    user = get_object_or_404(User, id=student_id, user_type='student')
    report = _build_student_report(user)
    pdf_bytes = generate_student_report_pdf(report)

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="report_{user.id}.pdf"'
    return response


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_report_pdf(request):
    """
    الطالب يحمل تقرير نفسه PDF
    GET /reports/me/pdf/
    """
    report = _build_student_report(request.user)
    pdf_bytes = generate_student_report_pdf(report)

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="my_report.pdf"'
    return response