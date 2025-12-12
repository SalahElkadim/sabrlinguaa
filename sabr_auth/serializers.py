from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, Student
from datetime import date


class StudentRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for student registration"""
    
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    
    class Meta:
        model = User
        fields = ['email', 'full_name', 'password', 'password_confirm']
    
    def validate_email(self, value):
        """Check if email already exists"""
        if User.objects.filter(email=value, is_email_verified=True).exists():
            raise serializers.ValidationError("هذا البريد الإلكتروني مسجل بالفعل")
        return value.lower()
    
    def validate(self, attrs):
        """Validate password match and strength"""
        password = attrs.get('password')
        password_confirm = attrs.get('password_confirm')
        
        if password != password_confirm:
            raise serializers.ValidationError({
                'password_confirm': 'كلمتا المرور غير متطابقتين'
            })
        
        try:
            validate_password(password)
        except ValidationError as e:
            raise serializers.ValidationError({
                'password': list(e.messages)
            })
        
        return attrs
    
    def create(self, validated_data):
        """Create user (inactive) and student profile"""
        validated_data.pop('password_confirm')
        
        # حذف أي حساب غير مفعل بنفس الإيميل
        User.objects.filter(email=validated_data['email'], is_email_verified=False).delete()
        
        # إنشاء المستخدم (غير مفعل)
        user = User.objects.create_user(
            email=validated_data['email'],
            full_name=validated_data['full_name'],
            password=validated_data['password'],
            user_type='student',
            is_active=False,  # الحساب غير مفعل حتى يتم التحقق
            is_email_verified=False
        )
        
        # إنشاء ملف الطالب
        Student.objects.create(user=user)
        
        return user


class EmailVerificationSerializer(serializers.Serializer):
    """Serializer for email verification"""
    email = serializers.EmailField(required=True)
    code = serializers.CharField(required=True, max_length=6, min_length=6)
    
    def validate_code(self, value):
        """Validate code format"""
        if not value.isdigit():
            raise serializers.ValidationError("رمز التحقق يجب أن يكون أرقام فقط")
        return value


class ResendVerificationSerializer(serializers.Serializer):
    """Serializer for resending verification code"""
    email = serializers.EmailField(required=True)



class LoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    
    def validate(self, attrs):
        """Validate user credentials"""
        email = attrs.get('email', '').lower()
        password = attrs.get('password')
        
        # Check if user exists
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError({
                'email': 'البريد الإلكتروني غير مسجل'
            })
        
        # Check if user is active
        if not user.is_active:
            raise serializers.ValidationError({
                'non_field_errors': 'هذا الحساب غير نشط'
            })
        
        # Authenticate user
        user = authenticate(email=email, password=password)
        
        if user is None:
            raise serializers.ValidationError({
                'password': 'كلمة المرور غير صحيحة'
            })
        
        attrs['user'] = user
        return attrs


class LogoutSerializer(serializers.Serializer):
    """Serializer for user logout"""
    
    refresh = serializers.CharField(required=True)
    
    def validate(self, attrs):
        """Validate refresh token"""
        self.token = attrs.get('refresh')
        return attrs
    
    def save(self, **kwargs):
        """Blacklist the refresh token"""
        try:
            RefreshToken(self.token).blacklist()
        except Exception as e:
            raise serializers.ValidationError({
                'refresh': 'الرمز غير صالح أو منتهي الصلاحية'
            })


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing password"""
    
    old_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    
    def validate_old_password(self, value):
        """Validate that old password is correct"""
        user = self.context['request'].user
        
        if not user.check_password(value):
            raise serializers.ValidationError('كلمة المرور القديمة غير صحيحة')
        
        return value
    
    def validate(self, attrs):
        """Validate that new passwords match and meet requirements"""
        new_password = attrs.get('new_password')
        new_password_confirm = attrs.get('new_password_confirm')
        old_password = attrs.get('old_password')
        
        # Check if new passwords match
        if new_password != new_password_confirm:
            raise serializers.ValidationError({
                'new_password_confirm': 'كلمتا المرور الجديدة غير متطابقتين'
            })
        
        # Check if new password is different from old password
        if new_password == old_password:
            raise serializers.ValidationError({
                'new_password': 'كلمة المرور الجديدة يجب أن تكون مختلفة عن القديمة'
            })
        
        # Validate password strength
        try:
            validate_password(new_password, user=self.context['request'].user)
        except ValidationError as e:
            raise serializers.ValidationError({
                'new_password': list(e.messages)
            })
        
        return attrs
    
    def save(self, **kwargs):
        """Update user password"""
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class ForgotPasswordSerializer(serializers.Serializer):
    """Serializer for forgot password (request reset link)"""
    
    email = serializers.EmailField(required=True)
    
    def validate_email(self, value):
        """Check if email exists"""
        email = value.lower()
        try:
            user = User.objects.get(email=email)
            if not user.is_active:
                raise serializers.ValidationError('هذا الحساب غير نشط')
            self.context['user'] = user
        except User.DoesNotExist:
            raise serializers.ValidationError('هذا البريد الإلكتروني غير مسجل')
        
        return email


class ResetPasswordSerializer(serializers.Serializer):
    """Serializer for resetting password with token"""
    
    uidb64 = serializers.CharField(required=True)
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    
    def validate(self, attrs):
        """Validate token and passwords"""
        try:
            # Decode user id
            uid = force_str(urlsafe_base64_decode(attrs.get('uidb64')))
            user = User.objects.get(pk=uid)
            
            # Validate token
            token_generator = PasswordResetTokenGenerator()
            if not token_generator.check_token(user, attrs.get('token')):
                raise serializers.ValidationError({
                    'token': 'الرابط غير صالح أو منتهي الصلاحية'
                })
            
            # Check if passwords match
            new_password = attrs.get('new_password')
            new_password_confirm = attrs.get('new_password_confirm')
            
            if new_password != new_password_confirm:
                raise serializers.ValidationError({
                    'new_password_confirm': 'كلمتا المرور غير متطابقتين'
                })
            
            # Validate password strength
            try:
                validate_password(new_password, user=user)
            except ValidationError as e:
                raise serializers.ValidationError({
                    'new_password': list(e.messages)
                })
            
            attrs['user'] = user
            
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError({
                'token': 'الرابط غير صالح'
            })
        
        return attrs
    
    def save(self, **kwargs):
        """Reset user password"""
        user = self.validated_data['user']
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class CompleteStudentProfileSerializer(serializers.Serializer):
    """Serializer for completing student profile after first login"""
    
    phone_number = serializers.CharField(
        max_length=20,
        required=False,
        allow_blank=True,
        help_text="رقم الهاتف"
    )
    birth_date = serializers.DateField(
        required=False,
        allow_null=True,
        help_text="تاريخ الميلاد (YYYY-MM-DD)"
    )
    bio = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="نبذة عن الطالب"
    )
    profile_picture = serializers.ImageField(
        required=False,
        allow_null=True,
        help_text="صورة الملف الشخصي"
    )
    
    def validate_birth_date(self, value):
        """Validate birth date"""
        if value:
            # التحقق من أن التاريخ ليس في المستقبل
            if value > date.today():
                raise serializers.ValidationError("تاريخ الميلاد لا يمكن أن يكون في المستقبل")
            
            # التحقق من أن العمر معقول (على الأقل 5 سنوات)
            age = date.today().year - value.year
            if age < 5:
                raise serializers.ValidationError("العمر يجب أن يكون 5 سنوات على الأقل")
            
            # التحقق من أن العمر ليس أكثر من 120 سنة
            if age > 120:
                raise serializers.ValidationError("العمر غير صحيح")
        
        return value
    
    def validate_phone_number(self, value):
        """Validate phone number format"""
        if value:
            # إزالة المسافات والشرطات
            cleaned = value.replace(" ", "").replace("-", "")
            
            # التحقق من أن الرقم يحتوي على أرقام فقط (مع السماح بـ +)
            if not cleaned.replace("+", "").isdigit():
                raise serializers.ValidationError("رقم الهاتف يجب أن يحتوي على أرقام فقط")
            
            # التحقق من الطول (بين 10 و 15 رقم)
            digits_only = cleaned.replace("+", "")
            if len(digits_only) < 10 or len(digits_only) > 15:
                raise serializers.ValidationError("رقم الهاتف غير صحيح")
        
        return value
    
    def validate_profile_picture(self, value):
        """Validate profile picture"""
        if value:
            # التحقق من حجم الصورة (أقل من 5 ميجا)
            if value.size > 5 * 1024 * 1024:
                raise serializers.ValidationError("حجم الصورة يجب أن يكون أقل من 5 ميجابايت")
            
            # التحقق من نوع الملف
            allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
            if value.content_type not in allowed_types:
                raise serializers.ValidationError("نوع الصورة غير مدعوم. يرجى استخدام JPG, PNG أو WebP")
        
        return value


class StudentProfileSerializer(serializers.ModelSerializer):
    """Serializer for complete student profile data"""
    
    # User fields
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    full_name = serializers.CharField(source='user.full_name', read_only=True)
    user_type = serializers.CharField(source='user.user_type', read_only=True)
    is_email_verified = serializers.BooleanField(source='user.is_email_verified', read_only=True)
    date_joined = serializers.DateTimeField(source='user.date_joined', read_only=True)
    last_login = serializers.DateTimeField(source='user.last_login', read_only=True)
    
    # Profile picture URL
    profile_picture_url = serializers.SerializerMethodField()
    
    # Check if profile is completed
    is_profile_completed = serializers.SerializerMethodField()
    
    # Readable level labels
    overall_level_display = serializers.CharField(source='get_overall_level_display', read_only=True)
    reading_level_display = serializers.CharField(source='get_reading_level_display', read_only=True)
    writing_level_display = serializers.CharField(source='get_writing_level_display', read_only=True)
    listening_level_display = serializers.CharField(source='get_listening_level_display', read_only=True)
    speaking_level_display = serializers.CharField(source='get_speaking_level_display', read_only=True)
    grammar_level_display = serializers.CharField(source='get_grammar_level_display', read_only=True)
    vocabulary_level_display = serializers.CharField(source='get_vocabulary_level_display', read_only=True)
    
    # Age calculation
    age = serializers.SerializerMethodField()
    
    class Meta:
        model = Student
        fields = [
            # User info
            'user_id',
            'email',
            'full_name',
            'user_type',
            'is_email_verified',
            'date_joined',
            'last_login',
            
            # Student profile
            'id',
            'profile_picture',
            'profile_picture_url',
            'is_profile_completed',
            
            # Levels (codes)
            'overall_level',
            'reading_level',
            'writing_level',
            'listening_level',
            'speaking_level',
            'grammar_level',
            'vocabulary_level',
            
            # Levels (readable)
            'overall_level_display',
            'reading_level_display',
            'writing_level_display',
            'listening_level_display',
            'speaking_level_display',
            'grammar_level_display',
            'vocabulary_level_display',
            
            # Placement test info
            'placement_test_taken',
            'placement_test_date',
            
            # Additional info
            'phone_number',
            'birth_date',
            'age',
            'bio',
        ]
    
    def get_profile_picture_url(self, obj):
        """Get full URL for profile picture"""
        if obj.profile_picture:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.profile_picture.url)
            return obj.profile_picture.url
        return None
    
    def get_is_profile_completed(self, obj):
        """Check if student has completed their profile"""
        # يعتبر الملف مكتمل إذا كان يحتوي على رقم الهاتف أو تاريخ الميلاد
        return bool(obj.phone_number or obj.birth_date)
    
    def get_age(self, obj):
        """Calculate age from birth_date"""
        if obj.birth_date:
            today = date.today()
            age = today.year - obj.birth_date.year
            if today.month < obj.birth_date.month or (today.month == obj.birth_date.month and today.day < obj.birth_date.day):
                age -= 1
            return age
        return None


