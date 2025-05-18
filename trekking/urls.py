# trekking/urls.py

from django.urls import path
from . import views # Importeremo le viste che creeremo tra poco

app_name = 'trekking' # Definisce un namespace per gli URL di questa app

urlpatterns = [
    path('', views.home_page, name='home_page'), # L'URL radice della nostra app (che useremo come homepage del sito)
    path('percorsi/', views.trek_list, name='trek_list'), # Pagina per la lista di tutti i trekking
    path('percorsi/<slug:trek_slug>/', views.trek_detail, name='trek_detail'),
    path('calendario-uscite/', views.scheduled_trek_list, name='scheduled_trek_list'),
    path('iscrizione/<int:scheduled_trek_id>/', views.trek_registration_create, name='trek_registration_create'),
    path('iscrizione/successo/', views.registration_success, name='registration_success'),
    path('api/trekking-events/', views.trekking_events_json, name='trekking_events_json'),
]