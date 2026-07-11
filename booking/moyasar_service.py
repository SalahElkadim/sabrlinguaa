import hmac
import hashlib
import requests
from django.conf import settings

MOYASAR_BASE_URL = "https://api.moyasar.com/v1"


def create_payment(amount_halalas: int, description: str, callback_url: str, token: str, metadata: dict = None) -> dict:
    """
    إنشاء دفعة باستخدام Tokenization
    - token: الـ token الجاي من Moyasar.js في الـ Frontend
    """
    payload = {
        "amount": amount_halalas,
        "currency": "SAR",
        "description": description,
        "callback_url": callback_url,
        "source": {
            "type": "token",
            "token": token,  # ← الـ token من Moyasar.js
        },
    }

    if metadata:
        payload["metadata"] = metadata

    response = requests.post(
        f"{MOYASAR_BASE_URL}/payments",
        json=payload,
        auth=(settings.MOYASAR_SECRET_KEY, ""),
        timeout=10,
    )

    if not response.ok:
        raise Exception(f"Moyasar error {response.status_code}: {response.text}")

    return response.json()


def get_payment(payment_id: str) -> dict:
    """
    جلب تفاصيل الدفع من Moyasar عن طريق payment_id
    """
    response = requests.get(
        f"{MOYASAR_BASE_URL}/payments/{payment_id}",
        auth=(settings.MOYASAR_SECRET_KEY, ""),
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    if not signature or not secret:
        return True  # أو False لو عايز تكون صارم أكتر أمنياً — شوف الملاحظة تحت

    expected = hmac.HMAC(
        key=secret.encode(),
        msg=payload,
        digestmod=hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)