# lacompany_project/urls.py

from django.contrib import admin
from django.urls import path, include # Assicurati che 'include' sia importato
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('trekking.urls', namespace='trekking')), # Includi gli URL della nostra app trekking
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)