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
        ]

    def get_profile_picture_url(self, obj):
        if obj.profile_picture:
            return obj.profile_picture.url
        return None


class TeacherDetailSerializer(serializers.ModelSerializer):
    """
    Serializer تفصيلي للمدرس
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
            'bio',
            'is_active',
            'created_at',
            'updated_at',
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