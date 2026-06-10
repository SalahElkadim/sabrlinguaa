import logging
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt

from .models import IELTSSubscriptionPlan, IELTSSubscription
from .utils import get_student_solved_count, has_active_ielts_subscription, FREE_QUESTIONS_LIMIT
from booking.moyasar_service import create_payment, get_payment, verify_webhook_signature
from django.conf import settings

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ielts_subscription_status(request):
    """
    GET /api/ielts/subscription/status/
    بيرجع حالة الطالب: كام سؤال حل، هل عنده subscription، وهل محتاج يشترك
    """
    student = request.user
    solved_count = get_student_solved_count(student)
    is_subscribed = has_active_ielts_subscription(student)

    # جيب الـ subscription الحالية لو موجودة
    active_sub = IELTSSubscription.objects.filter(
        student=student,
        payment_status='paid',
        expires_at__gt=timezone.now(),
    ).order_by('-expires_at').first()

    response_data = {
        'solved_questions': solved_count,
        'free_limit': FREE_QUESTIONS_LIMIT,
        'is_subscribed': is_subscribed,
        'show_paywall': not is_subscribed and solved_count >= FREE_QUESTIONS_LIMIT,
        'remaining_free': max(0, FREE_QUESTIONS_LIMIT - solved_count) if not is_subscribed else None,
        'subscription': None,
    }

    if active_sub:
        response_data['subscription'] = {
            'plan': active_sub.plan.get_plan_type_display(),
            'expires_at': active_sub.expires_at,
            'amount': active_sub.amount,
        }

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_ielts_plans(request):
    """
    GET /api/ielts/subscription/plans/
    بيرجع الخطط المتاحة
    """
    plans = IELTSSubscriptionPlan.objects.filter(is_active=True).order_by('price')
    return Response({
        'plans': [
            {
                'id': p.id,
                'plan_type': p.plan_type,
                'name': p.get_plan_type_display(),
                'price': p.price,
                'duration_days': p.duration_days,
                'description': p.description,
                'price_halalas': int(p.price * 100),
            }
            for p in plans
        ]
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def initiate_ielts_payment(request):
    """
    POST /api/ielts/subscription/pay/
    Body: { "plan_id": 1, "token": "tok_xxx" }
    """
    plan_id = request.data.get('plan_id')
    token   = request.data.get('token')

    if not plan_id:
        return Response({'error': 'plan_id مطلوب'}, status=status.HTTP_400_BAD_REQUEST)
    if not token:
        return Response({'error': 'token مطلوب'}, status=status.HTTP_400_BAD_REQUEST)

    plan = get_object_or_404(IELTSSubscriptionPlan, id=plan_id, is_active=True)

    # لو عنده اشتراك نشط بالفعل
    if has_active_ielts_subscription(request.user):
        return Response(
            {'error': 'لديك اشتراك نشط بالفعل'},
            status=status.HTTP_400_BAD_REQUEST
        )

    amount_halalas = int(plan.price * 100)
    callback_url   = f"{settings.FRONTEND_URL}/ielts/payment/callback"

    try:
        payment_data = create_payment(
            amount_halalas=amount_halalas,
            description=f"اشتراك IELTS - {plan.get_plan_type_display()}",
            callback_url=callback_url,
            token=token,
            metadata={
                'plan_id': str(plan.id),
                'student_id': str(request.user.id),
                'source': 'ielts_subscription',
            }
        )
    except Exception as e:
        logger.error(f"[IELTS payment] Moyasar error: {e}")
        return Response(
            {'error': 'تعذر إنشاء طلب الدفع، حاول مرة أخرى'},
            status=status.HTTP_502_BAD_GATEWAY
        )

    moyasar_id    = payment_data.get('id')
    payment_status = payment_data.get('status')
    transaction_url = payment_data.get('source', {}).get('transaction_url')

    # إنشاء record للاشتراك بحالة pending
    subscription = IELTSSubscription.objects.create(
        student=request.user,
        plan=plan,
        payment_id=moyasar_id,
        payment_status='pending',
        amount=plan.price,
    )

    # لو اتأكد على طول (بدون 3DS)
    if payment_status == 'paid':
        _activate_subscription(subscription, plan)

    return Response({
        'payment_id': moyasar_id,
        'status': payment_status,
        'transaction_url': transaction_url,
        'amount': plan.price,
        'subscription_id': subscription.id,
    }, status=status.HTTP_200_OK)


@csrf_exempt
@api_view(['GET', 'POST'])
def ielts_payment_callback(request):
    """
    GET/POST /api/ielts/subscription/callback/
    Moyasar بيعمل redirect هنا بعد 3DS
    """
    from rest_framework.permissions import AllowAny
    payment_id = (
        request.data.get('id') or
        request.query_params.get('id')
    )

    if not payment_id:
        return Response({'error': 'payment_id مطلوب'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        payment_data = get_payment(payment_id)
    except Exception as e:
        logger.error(f"[IELTS callback] get_payment failed: {e}")
        return Response({'error': 'تعذر التحقق من الدفع'}, status=status.HTTP_502_BAD_GATEWAY)

    payment_status = payment_data.get('status')
    metadata       = payment_data.get('metadata') or {}
    plan_id        = metadata.get('plan_id')

    subscription = IELTSSubscription.objects.filter(payment_id=payment_id).first()

    if not subscription and plan_id:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        student_id = metadata.get('student_id')
        plan = get_object_or_404(IELTSSubscriptionPlan, id=plan_id)
        student = get_object_or_404(User, id=student_id)
        amount = payment_data.get('amount', 0) / 100
        subscription = IELTSSubscription.objects.create(
            student=student,
            plan=plan,
            payment_id=payment_id,
            payment_status='pending',
            amount=amount,
        )

    if subscription and payment_status == 'paid' and subscription.payment_status != 'paid':
        _activate_subscription(subscription, subscription.plan)
    elif subscription and payment_status != 'paid':
        subscription.payment_status = 'failed'
        subscription.save()

    return Response({
        'status': payment_status,
        'subscription_id': subscription.id if subscription else None,
        'is_active': subscription.is_active if subscription else False,
    }, status=status.HTTP_200_OK)


@csrf_exempt
@api_view(['POST'])
def ielts_moyasar_webhook(request):
    """
    POST /api/ielts/subscription/webhook/
    """
    from rest_framework.permissions import AllowAny
    signature = request.headers.get('X-Moyasar-Signature', '')
    if not verify_webhook_signature(request.body, signature):
        return Response({'error': 'Invalid signature'}, status=status.HTTP_400_BAD_REQUEST)

    event        = request.data
    event_type   = event.get('type')
    payment      = event.get('data', {})
    payment_id   = payment.get('id')

    subscription = IELTSSubscription.objects.filter(payment_id=payment_id).first()
    if not subscription:
        return Response({'message': 'ok'}, status=status.HTTP_200_OK)

    if event_type == 'payment_paid' and subscription.payment_status != 'paid':
        _activate_subscription(subscription, subscription.plan)
    elif event_type == 'payment_failed':
        subscription.payment_status = 'failed'
        subscription.save()

    return Response({'message': 'ok'}, status=status.HTTP_200_OK)


# ─── Helper ───────────────────────────────────────────────────

def _activate_subscription(subscription: IELTSSubscription, plan: IELTSSubscriptionPlan):
    now = timezone.now()
    subscription.payment_status = 'paid'
    subscription.starts_at = now
    subscription.expires_at = now + timedelta(days=plan.duration_days)
    subscription.save()