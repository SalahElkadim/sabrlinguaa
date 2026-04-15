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

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def leaderboard(request):
    """
    GET /api/leaderboard/
    أعلى 4 طلاب في إجمالي النقاط
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

    # جمع كل الـ student IDs
    all_student_ids = set(general_scores) | set(ielts_scores) | set(step_scores) | set(esp_scores)

    # حساب الـ grand total لكل طالب
    totals = []
    for sid in all_student_ids:
        grand = (
            general_scores.get(sid, 0) +
            ielts_scores.get(sid, 0) +
            step_scores.get(sid, 0) +
            esp_scores.get(sid, 0)
        )
        totals.append({'student_id': sid, 'grand_total': grand})

    # ترتيب تنازلي وأخذ أول 4
    top4 = sorted(totals, key=lambda x: x['grand_total'], reverse=True)[:4]

    # جلب بيانات الطلاب
    top4_ids = [t['student_id'] for t in top4]
    students_map = {u.id: u for u in User.objects.filter(id__in=top4_ids)}

    results = []
    for rank, entry in enumerate(top4, start=1):
        user = students_map.get(entry['student_id'])
        results.append({
            'rank':        rank,
            'name':        user.get_full_name() or user.username if user else 'Unknown',
            'total_score': entry['grand_total'],
        })

    return Response({'leaderboard': results}, status=status.HTTP_200_OK)