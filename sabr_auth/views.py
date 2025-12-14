from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.conf import settings
from .models import EmailVerification, User, Student
from .serializers import (
    StudentRegistrationSerializer, 
    LoginSerializer, 
    LogoutSerializer,
    ChangePasswordSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer,
    EmailVerificationSerializer,
    ResendVerificationSerializer,
    CompleteStudentProfileSerializer, 
    StudentProfileSerializer,
)
from .utils import send_password_reset_email, send_password_reset_confirmation_email, send_verification_email
from django.utils import timezone
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser


def format_error_response(serializer_errors):
    """Helper function to format serializer errors"""
    if isinstance(serializer_errors, dict):
        for field, messages in serializer_errors.items():
            if isinstance(messages, list):
                return messages[0] if messages else "حدث خطأ في التحقق من البيانات"
            elif isinstance(messages, dict):
                return format_error_response(messages)
            else:
                return str(messages)
    return "حدث خطأ في التحقق من البيانات"


class StudentRegistrationView(APIView):
    """View for student registration"""
    
    permission_classes = [AllowAny]
    serializer_class = StudentRegistrationSerializer
    
    def post(self, request):
        """Handle student registration"""
        serializer = self.serializer_class(data=request.data)
        
        if serializer.is_valid():
            user = serializer.save()
            
            # توليد رمز التحقق
            verification_code = EmailVerification.generate_code()
            
            # حفظ رمز التحقق في قاعدة البيانات
            EmailVerification.objects.create(
                user=user,
                code=verification_code
            )
            
            # إرسال البريد الإلكتروني
            email_sent = send_verification_email(user, verification_code)
            
            if email_sent:
                return Response({
                    'message': 'تم إرسال رمز التحقق إلى بريدك الإلكتروني',
                    'email': user.email,
                    'note': 'يرجى التحقق من بريدك الإلكتروني وإدخال رمز التحقق لإكمال التسجيل'
                }, status=status.HTTP_201_CREATED)
            else:
                # حذف المستخدم إذا فشل إرسال البريد
                user.delete()
                return Response({
                    'error_message': 'حدث خطأ في إرسال البريد الإلكتروني. يرجى المحاولة مرة أخرى.'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'error_message': format_error_response(serializer.errors)
        }, status=status.HTTP_400_BAD_REQUEST)


class VerifyEmailView(APIView):
    """View for email verification"""
    
    permission_classes = [AllowAny]
    serializer_class = EmailVerificationSerializer
    
    def post(self, request):
        """Verify email with code"""
        serializer = self.serializer_class(data=request.data)
        
        if serializer.is_valid():
            email = serializer.validated_data['email']
            code = serializer.validated_data['code']
            
            try:
                user = User.objects.get(email=email, is_email_verified=False)
            except User.DoesNotExist:
                return Response({
                    'error_message': 'البريد الإلكتروني غير موجود أو تم التحقق منه بالفعل'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # البحث عن رمز التحقق
            try:
                verification = EmailVerification.objects.filter(
                    user=user,
                    code=code,
                    is_verified=False
                ).latest('created_at')
            except EmailVerification.DoesNotExist:
                return Response({
                    'error_message': 'رمز التحقق غير صحيح'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # التحقق من انتهاء صلاحية الرمز
            if verification.is_expired():
                return Response({
                    'error_message': 'انتهت صلاحية رمز التحقق. يرجى طلب رمز جديد'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # تفعيل الحساب
            user.is_email_verified = True
            user.is_active = True
            user.save()
            
            # تحديث حالة التحقق
            verification.is_verified = True
            verification.save()
            
            # إنشاء token للمستخدم
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'message': 'تم التحقق من البريد الإلكتروني بنجاح',
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'full_name': user.full_name,
                    'user_type': user.user_type,
                },
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            }, status=status.HTTP_200_OK)
        
        return Response({
            'error_message': format_error_response(serializer.errors)
        }, status=status.HTTP_400_BAD_REQUEST)


class ResendVerificationView(APIView):
    """View for resending verification code"""
    
    permission_classes = [AllowAny]
    serializer_class = ResendVerificationSerializer
    
    def post(self, request):
        """Resend verification code"""
        serializer = self.serializer_class(data=request.data)
        
        if serializer.is_valid():
            email = serializer.validated_data['email']
            
            try:
                user = User.objects.get(email=email, is_email_verified=False)
            except User.DoesNotExist:
                return Response({
                    'error_message': 'البريد الإلكتروني غير موجود أو تم التحقق منه بالفعل'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # التحقق من عدم إرسال رمز خلال الدقيقة الأخيرة
            last_verification = EmailVerification.objects.filter(
                user=user
            ).order_by('-created_at').first()
            
            if last_verification:
                time_diff = timezone.now() - last_verification.created_at
                if time_diff.total_seconds() < 60:
                    return Response({
                        'error_message': 'يرجى الانتظار دقيقة واحدة قبل طلب رمز جديد'
                    }, status=status.HTTP_429_TOO_MANY_REQUESTS)
            
            # توليد رمز جديد
            verification_code = EmailVerification.generate_code()
            
            # حفظ الرمز الجديد
            EmailVerification.objects.create(
                user=user,
                code=verification_code
            )
            
            # إرسال البريد
            email_sent = send_verification_email(user, verification_code)
            
            if email_sent:
                return Response({
                    'message': 'تم إرسال رمز التحقق الجديد إلى بريدك الإلكتروني'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'error_message': 'حدث خطأ في إرسال البريد الإلكتروني'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'error_message': format_error_response(serializer.errors)
        }, status=status.HTTP_400_BAD_REQUEST)


class ForgotPasswordView(APIView):
    """View for requesting password reset (send email with reset link)"""
    
    permission_classes = [AllowAny]
    serializer_class = ForgotPasswordSerializer
    
    def post(self, request):
        """Send password reset email"""
        serializer = self.serializer_class(data=request.data)
        
        if serializer.is_valid():
            user = serializer.context.get('user')
            
            # Generate reset token
            token_generator = PasswordResetTokenGenerator()
            token = token_generator.make_token(user)
            uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
            
            # Create reset URL
            reset_url = f"{settings.FRONTEND_URL}/reset-password/{uidb64}/{token}/"
            
            # Send email
            email_sent = send_password_reset_email(user, reset_url)
            
            if email_sent:
                return Response({
                    'message': 'تم إرسال رابط إعادة تعيين كلمة المرور إلى بريدك الإلكتروني'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'error_message': 'حدث خطأ أثناء إرسال البريد الإلكتروني. يرجى المحاولة مرة أخرى'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'error_message': format_error_response(serializer.errors)
        }, status=status.HTTP_400_BAD_REQUEST)


class ResetPasswordView(APIView):
    """View for resetting password using token from email"""
    
    permission_classes = [AllowAny]
    serializer_class = ResetPasswordSerializer
    
    def post(self, request):
        """Reset password with token"""
        serializer = self.serializer_class(data=request.data)
        
        if serializer.is_valid():
            user = serializer.save()
            
            # Send confirmation email
            send_password_reset_confirmation_email(user)
            
            return Response({
                'message': 'تم إعادة تعيين كلمة المرور بنجاح. يمكنك الآن العودة للتطبيق وتسجيل الدخول'
            }, status=status.HTTP_200_OK)
        
        return Response({
            'error_message': format_error_response(serializer.errors)
        }, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    """View for changing user password"""
    
    permission_classes = [IsAuthenticated]
    serializer_class = ChangePasswordSerializer
    
    def post(self, request):
        """Handle password change"""
        serializer = self.serializer_class(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            
            return Response({
                'message': 'تم تغيير كلمة المرور بنجاح'
            }, status=status.HTTP_200_OK)
        
        return Response({
            'error_message': format_error_response(serializer.errors)
        }, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """View for user login"""
    
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer
    
    def post(self, request):
        """Handle user login and generate JWT tokens"""
        serializer = self.serializer_class(data=request.data)
        
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            # Get student profile if user is student
            additional_data = {}
            if user.user_type == 'student' and hasattr(user, 'student_profile'):
                student = user.student_profile
                additional_data['student_profile'] = {
                    'overall_level': student.overall_level,
                    'placement_test_taken': student.placement_test_taken,
                }
            
            return Response({
                'message': 'تم تسجيل الدخول بنجاح',
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                },
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'full_name': user.full_name,
                    'user_type': user.user_type,
                    **additional_data
                }
            }, status=status.HTTP_200_OK)
        
        return Response({
            'error_message': format_error_response(serializer.errors)
        }, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    """View for user logout"""
    
    permission_classes = [IsAuthenticated]
    serializer_class = LogoutSerializer
    
    def post(self, request):
        """Handle user logout by blacklisting refresh token"""
        serializer = self.serializer_class(data=request.data)
        
        if serializer.is_valid():
            try:
                serializer.save()
                return Response({
                    'message': 'تم تسجيل الخروج بنجاح'
                }, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({
                    'error_message': 'حدث خطأ أثناء تسجيل الخروج'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'error_message': format_error_response(serializer.errors)
        }, status=status.HTTP_400_BAD_REQUEST)


class CompleteStudentProfileView(APIView):
    """
    POST endpoint for completing student profile after first login
    Allows student to add personal information
    """
    
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    serializer_class = CompleteStudentProfileSerializer
    
    def post(self, request):
        """Complete student profile with additional information"""
        
        # التحقق من أن المستخدم طالب
        if request.user.user_type != 'student':
            return Response({
                'error_message': 'هذا الحساب ليس حساب طالب'
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            student = Student.objects.get(user=request.user)
        except Student.DoesNotExist:
            return Response({
                'error_message': 'لم يتم العثور على ملف الطالب'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # التحقق من البيانات
        serializer = self.serializer_class(data=request.data)
        
        if serializer.is_valid():
            # تحديث بيانات الطالب
            validated_data = serializer.validated_data
            
            if 'phone_number' in validated_data:
                student.phone_number = validated_data['phone_number']
            
            if 'birth_date' in validated_data:
                student.birth_date = validated_data['birth_date']
            
            if 'bio' in validated_data:
                student.bio = validated_data['bio']
            
            if 'profile_picture' in validated_data:
                student.profile_picture = validated_data['profile_picture']
            
            student.save()
            
            # إرجاع البيانات الكاملة
            profile_serializer = StudentProfileSerializer(student, context={'request': request})
            
            return Response({
                'success': True,
                'message': 'تم إكمال الملف الشخصي بنجاح',
                'data': profile_serializer.data
            }, status=status.HTTP_200_OK)
        
        return Response({
            'error_message': format_error_response(serializer.errors)
        }, status=status.HTTP_400_BAD_REQUEST)


class StudentProfileView(APIView):
    """
    GET endpoint for retrieving complete student profile data
    Requires authentication
    """
    
    permission_classes = [IsAuthenticated]
    serializer_class = StudentProfileSerializer
    
    def get(self, request):
        """Get current authenticated student's profile"""
        
        # التحقق من أن المستخدم طالب
        if request.user.user_type != 'student':
            return Response({
                'error_message': 'هذا الحساب ليس حساب طالب'
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            # الحصول على ملف الطالب
            student = Student.objects.select_related('user').get(user=request.user)
            
            # تحويل البيانات باستخدام Serializer
            serializer = self.serializer_class(student, context={'request': request})
            
            return Response({
                'success': True,
                'message': 'تم جلب بيانات الملف الشخصي بنجاح',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Student.DoesNotExist:
            return Response({
                'error_message': 'لم يتم العثور على ملف الطالب'
            }, status=status.HTTP_404_NOT_FOUND)


class UpdateStudentProfileView(APIView):
    """
    PUT/PATCH endpoint for updating student profile
    Requires authentication
    """
    
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    serializer_class = CompleteStudentProfileSerializer
    
    def put(self, request):
        """Update student profile"""
        
        if request.user.user_type != 'student':
            return Response({
                'error_message': 'هذا الحساب ليس حساب طالب'
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            student = Student.objects.get(user=request.user)
        except Student.DoesNotExist:
            return Response({
                'error_message': 'لم يتم العثور على ملف الطالب'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # التحقق من البيانات
        serializer = self.serializer_class(data=request.data, partial=True)
        
        if serializer.is_valid():
            validated_data = serializer.validated_data
            updated_fields = []
            
            # تحديث الحقول المرسلة فقط
            for field in ['phone_number', 'birth_date', 'bio', 'profile_picture']:
                if field in validated_data:
                    setattr(student, field, validated_data[field])
                    updated_fields.append(field)
            
            if updated_fields:
                student.save()
                profile_serializer = StudentProfileSerializer(student, context={'request': request})
                
                return Response({
                    'success': True,
                    'message': 'تم تحديث الملف الشخصي بنجاح',
                    'updated_fields': updated_fields,
                    'data': profile_serializer.data
                }, status=status.HTTP_200_OK)
            
            return Response({
                'error_message': 'لم يتم تقديم أي بيانات للتحديث'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'error_message': format_error_response(serializer.errors)
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def patch(self, request):
        """Partial update for student profile"""
        return self.put(request)