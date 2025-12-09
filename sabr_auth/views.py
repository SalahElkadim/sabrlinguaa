from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.conf import settings
from .serializers import (
    StudentRegistrationSerializer, 
    LoginSerializer, 
    LogoutSerializer,
    ChangePasswordSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer
)
from .utils import send_password_reset_email, send_password_reset_confirmation_email


class StudentRegistrationView(APIView):
    """View for student registration"""
    
    permission_classes = [AllowAny]
    serializer_class = StudentRegistrationSerializer
    
    def post(self, request):
        """Handle student registration"""
        serializer = self.serializer_class(data=request.data)
        
        if serializer.is_valid():
            user = serializer.save()
            
            return Response({
                'message': 'تم إنشاء الحساب بنجاح',
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'full_name': user.full_name,
                    'user_type': user.user_type,
                }
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'errors': serializer.errors
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
                    'error': 'حدث خطأ أثناء إرسال البريد الإلكتروني. يرجى المحاولة مرة أخرى'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'errors': serializer.errors
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
                'message': 'تم إعادة تعيين كلمة المرور بنجاح. يمكنك الآن تسجيل الدخول'
            }, status=status.HTTP_200_OK)
        
        return Response({
            'errors': serializer.errors
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
            'errors': serializer.errors
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
            'errors': serializer.errors
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
                    'error': 'حدث خطأ أثناء تسجيل الخروج'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)