from django.urls import path
from .views import AppVersionUpsertView, CheckVersionView

urlpatterns = [
    path('app-versions/', AppVersionUpsertView.as_view(), name='app-version-upsert'),
    path('check-version/', CheckVersionView.as_view(), name='check-version'),
]
