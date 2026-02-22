
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('sabr_auth.urls')),
    path('questions/', include('sabr_questions.urls')),
    path('place/', include('placement_test.urls')),
    path('levels/', include('levels.urls')),
    path('ielts/', include('ielts.urls')),
    path('step/', include('step.urls')),





]
