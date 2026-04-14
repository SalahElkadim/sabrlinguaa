import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sabrlingua.settings')

app = Celery('sabrlingua')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks(['step.tasks','ielts.tasks','general.tasks','esp.tasks'])