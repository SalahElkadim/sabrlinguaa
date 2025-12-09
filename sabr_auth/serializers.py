from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, Student


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
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("هذا البريد الإلكتروني مسجل بالفعل")
        return value.lower()
    
    def validate(self, attrs):
        """Validate password match and strength"""
        password = attrs.get('password')
        password_confirm = attrs.get('password_confirm')
        
        # Check if passwords match
        if password != password_confirm:
            raise serializers.ValidationError({
                'password_confirm': 'كلمتا المرور غير متطابقتين'
            })
        
        # Validate password strength using Django's validators
        try:
            validate_password(password)
        except ValidationError as e:
            raise serializers.ValidationError({
                'password': list(e.messages)
            })
        
        return attrs
    
    def create(self, validated_data):
        """Create user and student profile"""
        # Remove password_confirm from validated data
        validated_data.pop('password_confirm')
        
        # Create user
        user = User.objects.create_user(
            email=validated_data['email'],
            full_name=validated_data['full_name'],
            password=validated_data['password'],
            user_type='student'
        )
        
        # Create student profile
        Student.objects.create(user=user)
        
        return user


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