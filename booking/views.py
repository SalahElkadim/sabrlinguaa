from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from .models import Teacher, Booking
from .serializers import (
    TeacherListSerializer,
    TeacherDetailSerializer,
    TeacherCreateUpdateSerializer,
    BookingCreateSerializer,
    BookingDetailSerializer,
)

import logging
logger = logging.getLogger(__name__)


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


# ============================================
# 2. BOOKING
# ============================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_booking(request):
    """
    إنشاء حجز جديد مع إرسال إيميل للشركة

    POST /booking/create/

    Body:
    {
        "teacher": 1,
        "phone_number": "01012345678",
        "requested_datetime": "2025-06-15T14:00:00",
        "notes": "أريد التركيز على المحادثة"
    }
    """
    serializer = BookingCreateSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        booking = serializer.save(student=request.user)

        # ============================================
        # إرسال إيميل للشركة
        # ============================================
        try:
            teacher = booking.teacher
            student = request.user

            subject = f"🎓 حجز حصة جديد - {student.full_name}"

            message = f"""
تفاصيل الحجز الجديد:

━━━━━━━━━━━━━━━━━━━━━━━━━━
👤 بيانات الطالب:
━━━━━━━━━━━━━━━━━━━━━━━━━━
الاسم: {student.full_name}
البريد الإلكتروني: {student.email}
رقم التليفون: {booking.phone_number}

━━━━━━━━━━━━━━━━━━━━━━━━━━
👨‍🏫 بيانات المدرس:
━━━━━━━━━━━━━━━━━━━━━━━━━━
الاسم: {teacher.name}
المادة: {teacher.subject}
تكلفة الحصة: {teacher.session_price} جنيه

━━━━━━━━━━━━━━━━━━━━━━━━━━
📅 تفاصيل الحجز:
━━━━━━━━━━━━━━━━━━━━━━━━━━
التاريخ والوقت المطلوب: {booking.requested_datetime.strftime('%Y-%m-%d %H:%M')}
ملاحظات الطالب: {booking.notes or 'لا يوجد'}
تاريخ إنشاء الحجز: {booking.created_at.strftime('%Y-%m-%d %H:%M')}
━━━━━━━━━━━━━━━━━━━━━━━━━━

يرجى التواصل مع الطالب على الواتساب: {booking.phone_number}
            """

            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.COMPANY_EMAIL],
                fail_silently=False,
            )

        except Exception as email_error:
            logger.error(f"Failed to send booking notification email: {str(email_error)}")
            # مش هنرجع error للطالب لو الإيميل فشل - الحجز اتسجل بنجاح

        return Response({
            'message': 'تم إرسال طلب الحجز بنجاح، سيتم التواصل معك قريباً',
            'booking': BookingDetailSerializer(booking).data
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f"Error creating booking: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_bookings(request):
    """
    عرض حجوزات الطالب الحالي

    GET /booking/my-bookings/
    """
    bookings = Booking.objects.filter(
        student=request.user
    ).select_related('teacher').order_by('-created_at')

    serializer = BookingDetailSerializer(bookings, many=True)

    return Response({
        'total_bookings': bookings.count(),
        'bookings': serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_booking(request, booking_id):
    """
    عرض تفاصيل حجز معين

    GET /booking/{booking_id}/
    """
    booking = get_object_or_404(
        Booking,
        id=booking_id,
        student=request.user
    )
    serializer = BookingDetailSerializer(booking)

    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def cancel_booking(request, booking_id):
    """
    إلغاء حجز

    DELETE /booking/{booking_id}/cancel/
    """
    booking = get_object_or_404(
        Booking,
        id=booking_id,
        student=request.user
    )

    booking.delete()

    return Response({
        'message': 'تم إلغاء الحجز بنجاح'
    }, status=status.HTTP_200_OK)


# ============================================
# 3. ADMIN - عرض جميع الحجوزات
# ============================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_all_bookings(request):
    """
    عرض جميع الحجوزات (للأدمن)

    GET /booking/all/

    Query Parameters:
    - teacher_id: filter by teacher
    """
    teacher_id = request.query_params.get('teacher_id', None)

    bookings = Booking.objects.select_related(
        'student', 'teacher'
    ).order_by('-created_at')

    if teacher_id:
        bookings = bookings.filter(teacher_id=teacher_id)

    serializer = BookingDetailSerializer(bookings, many=True)

    return Response({
        'total_bookings': bookings.count(),
        'bookings': serializer.data
    }, status=status.HTTP_200_OK)