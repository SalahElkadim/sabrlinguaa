# step/utils.py
from django.utils import timezone
from .models import STEPSubscription, StudentSTEPQuestionAttempt

FREE_QUESTIONS_LIMIT = 20

def get_student_solved_count(student):
    """إجمالي الأسئلة المحلولة للطالب في STEP"""
    return StudentSTEPQuestionAttempt.objects.filter(
        student=student,
        is_solved=True,
    ).count()

def has_active_step_subscription(student):
    return STEPSubscription.objects.filter(
        student=student,
        payment_status='paid',
        expires_at__gt=timezone.now(),
    ).exists()

def can_solve_question(student):
    """هل الطالب مسموحله يحل سؤال جديد؟"""
    if has_active_step_subscription(student):
        return True
    return get_student_solved_count(student) < FREE_QUESTIONS_LIMIT