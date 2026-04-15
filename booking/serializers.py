from rest_framework import serializers
from .models import Teacher, Booking


# ============================================
# TEACHER SERIALIZERS
# ============================================

class TeacherListSerializer(serializers.ModelSerializer):
    """
    Serializer مختصر لعرض قائمة المدرسين
    """
    profile_picture_url = serializers.SerializerMethodField()

    class Meta:
        model = Teacher
        fields = [
            'id',
            'name',
            'profile_picture_url',
            'subject',
            'years_of_experience',
            'session_price',
            'is_active',
            'bio',
            'average_rating','reviews_count',
        ]

    def get_profile_picture_url(self, obj):
        if obj.profile_picture:
            return obj.profile_picture.url
        return None


class TeacherDetailSerializer(serializers.ModelSerializer):
    profile_picture_url = serializers.SerializerMethodField()
    average_rating = serializers.FloatField(read_only=True)
    reviews_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Teacher
        fields = [
            'id', 'name', 'profile_picture_url', 'subject',
            'years_of_experience', 'session_price', 'bio',
            'is_active', 'created_at', 'updated_at',
            'average_rating', 'reviews_count',  # ← جديد
        ]

    def get_profile_picture_url(self, obj):
        if obj.profile_picture:
            return obj.profile_picture.url
        return None


class TeacherCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer لإنشاء وتعديل المدرس
    """
    class Meta:
        model = Teacher
        fields = [
            'name',
            'profile_picture',
            'subject',
            'years_of_experience',
            'session_price',
            'bio',
            'is_active',
        ]


# ============================================
# BOOKING SERIALIZERS
# ============================================

class BookingCreateSerializer(serializers.ModelSerializer):
    """
    Serializer لإنشاء حجز جديد
    """
    class Meta:
        model = Booking
        fields = [
            'teacher',
            'phone_number',
            'requested_datetime',
            'notes',
        ]

    def validate_requested_datetime(self, value):
        from django.utils import timezone
        if value < timezone.now():
            raise serializers.ValidationError("لا يمكن الحجز في تاريخ سابق")
        return value


class BookingDetailSerializer(serializers.ModelSerializer):
    """
    Serializer تفصيلي للحجز
    """
    teacher = TeacherListSerializer(read_only=True)
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    student_email = serializers.CharField(source='student.email', read_only=True)

    class Meta:
        model = Booking
        fields = [
            'id',
            'student_name',
            'student_email',
            'teacher',
            'phone_number',
            'requested_datetime',
            'notes',
            'created_at',
        ]

from .models import Teacher, Booking, Review

from .models import Teacher, Booking, Review

class ReviewSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.full_name', read_only=True)

    class Meta:
        model = Review
        fields = ['id', 'student_name', 'rating', 'comment', 'created_at']
        read_only_fields = ['id', 'student_name', 'created_at']


class ReviewCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['teacher', 'rating', 'comment']

    def validate(self, data):
        student = self.context['request'].user
        teacher = data['teacher']

        # الطالب لازم يكون عمل حجز مع المدرس ده
        has_booking = Booking.objects.filter(
            student=student, teacher=teacher
        ).exists()
        if not has_booking:
            raise serializers.ValidationError(
                "لا يمكنك تقييم مدرس لم تحجز معه حصة"
            )

        # مينفعش يقيّم أكتر من مرة
        already_reviewed = Review.objects.filter(
            student=student, teacher=teacher
        ).exists()
        if already_reviewed:
            raise serializers.ValidationError(
                "لقد قمت بتقييم هذا المدرس من قبل"
            )

        return data