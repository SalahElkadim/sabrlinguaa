# ielts/utils.py
from django.utils import timezone
from .models import IELTSSubscription, StudentIELTSQuestionAttempt

FREE_QUESTIONS_LIMIT = 20

def get_student_solved_count(student):
    """إجمالي الأسئلة المحلولة للطالب في IELTS"""
    return StudentIELTSQuestionAttempt.objects.filter(
        student=student,
        is_solved=True,
    ).count()

def has_active_ielts_subscription(student):
    return IELTSSubscription.objects.filter(
        student=student,
        payment_status='paid',
        expires_at__gt=timezone.now(),
    ).exists()

def can_solve_question(student):
    """هل الطالب مسموحله يحل سؤال جديد؟"""
    if has_active_ielts_subscription(student):
        return True
    return get_student_solved_count(student) < FREE_QUESTIONS_LIMIT



