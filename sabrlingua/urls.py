
from django.contrib import admin
from django.urls import path, include
# myproject/urls.py
from django.http import FileResponse, HttpResponse
from django.urls import path
from django.conf import settings
import os

def apple_pay_domain_association(request):
    file_path = os.path.join(settings.BASE_DIR, '.well-known', 
                             'apple-developer-merchantid-domain-association')
    with open(file_path, 'rb') as f:
        return HttpResponse(f.read(), content_type='application/octet-stream')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('sabr_auth.urls')),
    path('questions/', include('sabr_questions.urls')),
    path('place/', include('placement_test.urls')),
    path('levels/', include('levels.urls')),
    path('ielts/', include('ielts.urls')),
    path('step/', include('step.urls')),
    path('booking/', include('booking.urls')),
    path('esp/', include('esp.urls')),
    path('general/', include('general.urls', namespace='general')),
    path('.well-known/apple-developer-merchantid-domain-association',apple_pay_domain_association),




]
