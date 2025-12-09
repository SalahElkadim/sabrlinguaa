from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    StudentRegistrationView, 
    LoginView, 
    LogoutView,
    ChangePasswordView,
    ForgotPasswordView,
    ResetPasswordView
)

urlpatterns = [
    path('register/', StudentRegistrationView.as_view(), name='student-register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),
]