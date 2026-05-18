from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Sum
from django.contrib.auth import get_user_model
from general.models import StudentGeneralProgress
from ielts.models import StudentIELTSProgress
from step.models import StudentSTEPProgress
from esp.models import StudentEspProgress
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Sum
from general.models import StudentGeneralProgress
from ielts.models import StudentIELTSProgress
from step.models import StudentSTEPProgress
from esp.models import StudentEspProgress

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Sum
from django.contrib.auth import get_user_model

from general.models import StudentGeneralProgress, GeneralCategory
from ielts.models import StudentIELTSProgress, IELTSSkill
from step.models import StudentSTEPProgress, STEPSkill
from esp.models import StudentEspProgress, EspSkill

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_total_score(request):
    

    student = request.user

    def get_total(model):
        result = model.objects.filter(student=student).aggregate(
            total=Sum('total_score')
        )
        return result['total'] or 0

    general_score = get_total(StudentGeneralProgress)
    ielts_score   = get_total(StudentIELTSProgress)
    step_score    = get_total(StudentSTEPProgress)
    esp_score     = get_total(StudentEspProgress)

    grand_total = general_score + ielts_score + step_score + esp_score

    return Response({
        'grand_total_score': grand_total,
        'breakdown': {
            'general': general_score,
            'ielts':   ielts_score,
            'step':    step_score,
            'esp':     esp_score,
        }
    }, status=status.HTTP_200_OK)


User = get_user_model()


# ============================================
# Helper
# ============================================

def _build_leaderboard(scores_per_student, top_n=10):
    """
    scores_per_student: dict {student_id: total_score}
    Returns ranked list of dicts.
    """
    sorted_entries = sorted(
        scores_per_student.items(),
        key=lambda x: x[1],
        reverse=True
    )[:top_n]

    student_ids = [sid for sid, _ in sorted_entries]
    students_map = {u.id: u for u in User.objects.filter(id__in=student_ids)}

    results = []
    for rank, (sid, score) in enumerate(sorted_entries, start=1):
        user = students_map.get(sid)
        results.append({
            'rank': rank,
            'name': user.get_full_name() or user.username if user else 'Unknown',
            'total_score': score,
        })
    return results


def _aggregate_scores(model, filter_kwargs):
    """
    Aggregate total_score grouped by student for a given queryset filter.
    Returns dict {student_id: total_score}
    """
    return {
        item['student']: item['total']
        for item in model.objects.filter(**filter_kwargs)
                         .values('student')
                         .annotate(total=Sum('total_score'))
    }


# ============================================
# Grand Total Leaderboard (existing)
# ============================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def leaderboard(request):
    """
    GET /api/leaderboard/
    أعلى 10 طلاب في إجمالي النقاط عبر كل التطبيقات
    """
    def get_scores_per_student(model):
        return {
            item['student']: item['total']
            for item in model.objects.values('student').annotate(total=Sum('total_score'))
        }

    general_scores = get_scores_per_student(StudentGeneralProgress)
    ielts_scores   = get_scores_per_student(StudentIELTSProgress)
    step_scores    = get_scores_per_student(StudentSTEPProgress)
    esp_scores     = get_scores_per_student(StudentEspProgress)

    all_student_ids = set(general_scores) | set(ielts_scores) | set(step_scores) | set(esp_scores)

    totals = {
        sid: (
            general_scores.get(sid, 0) +
            ielts_scores.get(sid, 0) +
            step_scores.get(sid, 0) +
            esp_scores.get(sid, 0)
        )
        for sid in all_student_ids
    }

    return Response({
        'leaderboard': _build_leaderboard(totals, top_n=10)
    }, status=status.HTTP_200_OK)


# ============================================
# IELTS Leaderboard
# ============================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ielts_leaderboard(request):
    """
    GET /api/leaderboard/ielts/
    أعلى 10 طلاب في نقاط IELTS
    """
    scores = _aggregate_scores(StudentIELTSProgress, {})

    return Response({
        'leaderboard': _build_leaderboard(scores, top_n=10)
    }, status=status.HTTP_200_OK)


# ============================================
# STEP Leaderboard
# ============================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def step_leaderboard(request):
    """
    GET /api/leaderboard/step/
    أعلى 10 طلاب في نقاط STEP
    """
    scores = _aggregate_scores(StudentSTEPProgress, {})

    return Response({
        'leaderboard': _build_leaderboard(scores, top_n=10)
    }, status=status.HTTP_200_OK)


# ============================================
# General — Per Category Leaderboard
# ============================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def general_category_leaderboard(request, category_id):
    """
    GET /api/leaderboard/general/categories/{category_id}/
    أعلى 10 طلاب في نقاط كاتيجوري معينة في General
    """
    category = GeneralCategory.objects.filter(id=category_id).first()
    if not category:
        return Response({'error': 'الكاتيجوري غير موجودة'}, status=status.HTTP_404_NOT_FOUND)

    # جيب كل الـ skills اللي تحت الكاتيجوري دي
    skill_ids = category.skills.filter(is_active=True).values_list('id', flat=True)

    scores = _aggregate_scores(
        StudentGeneralProgress,
        {'skill__id__in': skill_ids}
    )

    return Response({
        'category': {'id': category.id, 'name': category.name},
        'leaderboard': _build_leaderboard(scores, top_n=10)
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def general_all_categories_leaderboard(request):
    """
    GET /api/leaderboard/general/categories/
    leaderboard لكل كاتيجوري في General مرة واحدة
    """
    categories = GeneralCategory.objects.filter(is_active=True).order_by('order')

    result = []
    for category in categories:
        skill_ids = category.skills.filter(is_active=True).values_list('id', flat=True)
        scores = _aggregate_scores(
            StudentGeneralProgress,
            {'skill__id__in': skill_ids}
        )
        result.append({
            'category': {'id': category.id, 'name': category.name},
            'leaderboard': _build_leaderboard(scores, top_n=10)
        })

    return Response({'categories_leaderboard': result}, status=status.HTTP_200_OK)


# ============================================
# ESP — Per Category Leaderboard
# ============================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def esp_category_leaderboard(request, category_id):
    """
    GET /api/leaderboard/esp/categories/{category_id}/
    أعلى 10 طلاب في نقاط كاتيجوري معينة في ESP
    """
    # افترض إن ESP عندها EspCategory model مشابهة لـ GeneralCategory
    from esp.models import EspCategory

    category = EspCategory.objects.filter(id=category_id).first()
    if not category:
        return Response({'error': 'الكاتيجوري غير موجودة'}, status=status.HTTP_404_NOT_FOUND)

    skill_ids = category.skills.filter(is_active=True).values_list('id', flat=True)

    scores = _aggregate_scores(
        StudentEspProgress,
        {'skill__id__in': skill_ids}
    )

    return Response({
        'category': {'id': category.id, 'name': category.name},
        'leaderboard': _build_leaderboard(scores, top_n=10)
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def esp_all_categories_leaderboard(request):
    """
    GET /api/leaderboard/esp/categories/
    leaderboard لكل كاتيجوري في ESP مرة واحدة
    """
    from esp.models import EspCategory

    categories = EspCategory.objects.filter(is_active=True).order_by('order')

    result = []
    for category in categories:
        skill_ids = category.skills.filter(is_active=True).values_list('id', flat=True)
        scores = _aggregate_scores(
            StudentEspProgress,
            {'skill__id__in': skill_ids}
        )
        result.append({
            'category': {'id': category.id, 'name': category.name},
            'leaderboard': _build_leaderboard(scores, top_n=10)
        })

    return Response({'categories_leaderboard': result}, status=status.HTTP_200_OK)