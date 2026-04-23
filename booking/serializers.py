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
            'years_of_experience', 'bio',
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
            'email',  # ← أضف
            'profile_picture',
            'subject',
            'years_of_experience',
            'bio',
            'is_active',
        ]


from .models import Teacher, Review

from .models import Teacher, Review

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
    

from .models import Program, ProgramSchedule, Subscription, CustomProgram, CustomProgramSchedule


# ============================================
# PROGRAM SERIALIZERS
# ============================================

class ProgramScheduleSerializer(serializers.ModelSerializer):
    day_display = serializers.CharField(source='get_day_of_week_display', read_only=True)

    class Meta:
        model = ProgramSchedule
        fields = ['id', 'day_of_week', 'day_display', 'time']


class ProgramListSerializer(serializers.ModelSerializer):
    schedules = ProgramScheduleSerializer(many=True, read_only=True)
    teacher_name = serializers.CharField(source='teacher.name', read_only=True)

    class Meta:
        model = Program
        fields = [
            'id', 'teacher', 'teacher_name', 'title', 'description',
            'schedules', 'recurrence', 'duration', 'price', 'is_active',
        ]


class ProgramCreateUpdateSerializer(serializers.ModelSerializer):
    schedules = ProgramScheduleSerializer(many=True)

    class Meta:
        model = Program
        fields = [
            'teacher', 'title', 'description',
            'recurrence', 'duration', 'price', 'is_active', 'schedules',
        ]

    def create(self, validated_data):
        schedules_data = validated_data.pop('schedules')
        program = Program.objects.create(**validated_data)
        for schedule in schedules_data:
            ProgramSchedule.objects.create(program=program, **schedule)
        return program

    def update(self, instance, validated_data):
        schedules_data = validated_data.pop('schedules', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if schedules_data is not None:
            instance.schedules.all().delete()
            for schedule in schedules_data:
                ProgramSchedule.objects.create(program=instance, **schedule)

        return instance


# ============================================
# SUBSCRIPTION SERIALIZERS
# ============================================

class SubscriptionSerializer(serializers.ModelSerializer):
    program = ProgramListSerializer(read_only=True)
    student_name = serializers.CharField(source='student.full_name', read_only=True)

    class Meta:
        model = Subscription
        fields = [
            'id', 'student_name', 'program',
            'payment_id', 'payment_status', 'amount', 'created_at',
        ]


class SubscriptionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ['program', 'payment_id', 'amount']


# ============================================
# CUSTOM PROGRAM SERIALIZERS
# ============================================

class CustomProgramScheduleSerializer(serializers.ModelSerializer):
    day_display = serializers.CharField(source='get_day_of_week_display', read_only=True)

    class Meta:
        model = CustomProgramSchedule
        fields = ['id', 'day_of_week', 'day_display', 'time']


class CustomProgramCreateSerializer(serializers.ModelSerializer):
    schedules = CustomProgramScheduleSerializer(many=True)

    class Meta:
        model = CustomProgram
        fields = [
            'teacher', 'whatsapp_number', 'recurrence',
            'duration', 'curriculum', 'schedules',
        ]

    def create(self, validated_data):
        schedules_data = validated_data.pop('schedules')
        custom_program = CustomProgram.objects.create(**validated_data)
        for schedule in schedules_data:
            CustomProgramSchedule.objects.create(
                custom_program=custom_program, **schedule
            )
        return custom_program


class CustomProgramDetailSerializer(serializers.ModelSerializer):
    schedules = CustomProgramScheduleSerializer(many=True, read_only=True)
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    teacher_name = serializers.CharField(source='teacher.name', read_only=True)

    class Meta:
        model = CustomProgram
        fields = [
            'id', 'student_name', 'teacher_name', 'whatsapp_number',
            'recurrence', 'duration', 'curriculum', 'schedules', 'created_at',
        ]