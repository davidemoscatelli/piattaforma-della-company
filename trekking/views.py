# trekking/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Trek, Difficulty, ScheduledTrek, TrekImage, TrekRegistration
from .forms import TrekRegistrationForm
from django.utils import timezone
from django.urls import reverse
from django.http import JsonResponse # Per API FullCalendar (se la usi)
import datetime # Per API FullCalendar (se la usi)
from django.http import JsonResponse
from django.urls import reverse
from datetime import datetime, time # Aggiungi time

def home_page(request):
    featured_treks = Trek.objects.filter(is_published=True).order_by('-created_at')[:3]
    context = {
        'featured_treks': featured_treks,
        'page_title': 'Homepage La Company'
    }
    return render(request, 'trekking/home.html', context)

def trek_list(request):
    treks_queryset = Trek.objects.filter(is_published=True)
    difficulties = Difficulty.objects.all()

    selected_difficulty_id = request.GET.get('difficulty')
    search_location = request.GET.get('location_area', '').strip()

    if selected_difficulty_id:
        try:
            difficulty_id = int(selected_difficulty_id)
            treks_queryset = treks_queryset.filter(difficulty_id=difficulty_id)
        except ValueError:
            pass

    if search_location:
        treks_queryset = treks_queryset.filter(location_area__icontains=search_location)

    sort_by = request.GET.get('sort', 'name')
    if sort_by == 'name':
        treks_queryset = treks_queryset.order_by('name')
    elif sort_by == '-name':
        treks_queryset = treks_queryset.order_by('-name')
    elif sort_by == 'difficulty':
        treks_queryset = treks_queryset.order_by('difficulty__name', 'name')
    elif sort_by == 'length':
        treks_queryset = treks_queryset.order_by('length_km', 'name')
    elif sort_by == '-length':
        treks_queryset = treks_queryset.order_by('-length_km', 'name')

    context = {
        'treks': treks_queryset,
        'difficulties': difficulties,
        'selected_difficulty_id': int(selected_difficulty_id) if selected_difficulty_id and selected_difficulty_id.isdigit() else None,
        'search_location_value': search_location,
        'current_sort': sort_by,
        'page_title': 'Tutti i Nostri Percorsi'
    }
    return render(request, 'trekking/trek_list.html', context)

def trek_detail(request, trek_slug):
    trek = get_object_or_404(Trek, slug=trek_slug, is_published=True)
    gallery_images = TrekImage.objects.filter(trek=trek).order_by('uploaded_at')
    # Mostra tutte le uscite (anche quelle non attive o passate) nella pagina di dettaglio del trekking,
    # lo stato dell'evento indicherà la loro condizione.
    scheduled_treks_for_this = ScheduledTrek.objects.filter(trek=trek).order_by('date', 'start_time')

    context = {
        'trek': trek,
        'gallery_images': gallery_images,
        'scheduled_treks': scheduled_treks_for_this,
        'page_title': trek.name,
    }
    return render(request, 'trekking/trek_detail.html', context)

def scheduled_trek_list(request):
    current_date = timezone.now().date()
    # Mostra uscite attive, future, e il cui stato non sia ANNULLATO o COMPLETATO
    all_scheduled_treks = ScheduledTrek.objects.filter(
        is_active=True, # is_active ora è gestito dal save() del modello in base a event_status
        date__gte=current_date
    ).exclude(
        event_status__in=['ANNULLATO_METEO', 'ANNULLATO_ORGANIZZATORE', 'COMPLETATO']
    ).order_by('date', 'start_time').select_related('trek', 'trek__difficulty')

    context = {
        'scheduled_treks': all_scheduled_treks,
        'page_title': 'Calendario Uscite Programmate'
    }
    return render(request, 'trekking/scheduled_trek_list_page.html', context)

def trek_registration_create(request, scheduled_trek_id):
    # Recupera l'uscita, anche se non è 'is_active' per dare messaggi più specifici
    # Ma controlla che la data non sia passata per le nuove iscrizioni.
    scheduled_trek = get_object_or_404(ScheduledTrek, pk=scheduled_trek_id, date__gte=timezone.now().date())

    # Controlli sullo stato dell'evento e iscrizioni
    if scheduled_trek.event_status in ['ANNULLATO_METEO', 'ANNULLATO_ORGANIZZATORE', 'COMPLETATO']:
        messages.error(request, "Questa uscita è stata annullata o è già terminata. Non è possibile iscriversi.")
        return redirect('trekking:trek_detail', trek_slug=scheduled_trek.trek.slug)
    
    if not scheduled_trek.is_active : # Se non è attiva per altri motivi (es. l'admin l'ha disattivata manualmente)
        messages.error(request, "Questa uscita non è attualmente disponibile per l'iscrizione.")
        return redirect('trekking:trek_detail', trek_slug=scheduled_trek.trek.slug)

    if not scheduled_trek.registration_open:
        messages.error(request, "Le iscrizioni per questa uscita sono attualmente chiuse.")
        return redirect('trekking:trek_detail', trek_slug=scheduled_trek.trek.slug)

    if scheduled_trek.spots_available <= 0:
        messages.error(request, "Siamo spiacenti, ma i posti per questa uscita sono esauriti.")
        return redirect('trekking:trek_detail', trek_slug=scheduled_trek.trek.slug)

    if request.method == 'POST':
        form = TrekRegistrationForm(request.POST)
        if form.is_valid():
            # Ricontrolla i posti disponibili per evitare race conditions
            if scheduled_trek.spots_available <= 0:
                messages.error(request, "Siamo spiacenti, ma i posti si sono esauriti mentre compilavi il modulo.")
                return redirect('trekking:trek_detail', trek_slug=scheduled_trek.trek.slug)

            registration = form.save(commit=False)
            registration.scheduled_trek = scheduled_trek
            # Lo status è già 'CONFERMATA' di default dal modello

            # if request.user.is_authenticated:
            #     registration.user = request.user
            
            try:
                registration.save()
                messages.success(request, f"Grazie {registration.first_name}! La tua iscrizione per '{scheduled_trek.trek.name}' del {scheduled_trek.date.strftime('%d/%m/%Y')} è confermata.")
                return redirect('trekking:registration_success')
            except Exception as e:
                print(f"Errore durante il salvataggio della registrazione: {e}")
                print(f"Dati del form: {form.cleaned_data}")
                print(f"Uscita Programmata ID: {scheduled_trek_id}")

                if 'UNIQUE constraint failed' in str(e) or 'trek_registration.scheduled_trek_id, trek_registration.email' in str(e):
                    error_message = "Questa email risulta già iscritta a questa uscita. Non è possibile iscriversi più volte."
                else:
                    error_message = "Spiacenti, si è verificato un problema tecnico durante la registrazione. Riprova o contattaci se il problema persiste."
                
                messages.error(request, error_message)
                
                context = {
                    'form': form,
                    'scheduled_trek': scheduled_trek,
                    'page_title': f"Iscrizione: {scheduled_trek.trek.name} ({scheduled_trek.date.strftime('%d/%m/%Y')})"
                }
                return render(request, 'trekking/trek_registration_form.html', context)
        else:
            messages.error(request, "Per favore, correggi gli errori evidenziati nel modulo.")
    else:
        form = TrekRegistrationForm()

    context = {
        'form': form,
        'scheduled_trek': scheduled_trek,
        'page_title': f"Iscrizione: {scheduled_trek.trek.name} ({scheduled_trek.date.strftime('%d/%m/%Y')})"
    }
    return render(request, 'trekking/trek_registration_form.html', context)

def registration_success(request):
    context = {
        'page_title': 'Iscrizione Confermata!' # Modificato messaggio
    }
    return render(request, 'trekking/registration_success.html', context)

def trekking_events_json(request):
    """
    Fornisce le uscite programmate in formato JSON per FullCalendar.
    """
    # Considera di filtrare solo eventi futuri o rilevanti
    # scheduled_treks = ScheduledTrek.objects.filter(date__gte=datetime.today(), event_status__in=['PIANIFICATO', 'CONFERMATO']).order_by('date')
    scheduled_treks = ScheduledTrek.objects.filter(event_status__in=['PIANIFICATO', 'CONFERMATO', 'POSTI_ESAURITI']).order_by('date') # Mostra anche quelli pieni

    events = []
    for st in scheduled_treks:
        event_title = st.trek.name
        event_start_datetime = datetime.combine(st.date, st.start_time if st.start_time else time.min) # Combina data e ora, usa mezzanotte se l'ora non è specificata

        # Determina il colore dell'evento in base allo stato o disponibilità
        event_color = None
        if st.event_status == 'POSTI_ESAURITI':
            event_color = '#dc3545' # Rosso per posti esauriti
            event_title += " (Esaurito)"
        elif st.spots_available is not None and st.max_participants is not None and st.spots_available <= 5 and st.spots_available > 0 :
            event_color = '#ffc107' # Giallo per pochi posti
            event_title += f" (Solo {st.spots_available} posti!)"
        elif st.event_status == 'CONFERMATO':
            event_color = '#28a745' # Verde per confermato


        events.append({
            'id': st.pk,
            'title': event_title,
            'start': event_start_datetime.isoformat(), # Formato ISO per FullCalendar
            'url': reverse('trekking:trek_detail', args=[st.trek.slug]), # Link alla pagina di dettaglio del trek
            'extendedProps': { # Puoi aggiungere dati extra qui
                'description': st.trek.description_short,
                'spots_available': st.spots_available,
                'max_participants': st.max_participants,
                'status': st.get_event_status_display(),
                'registration_url': reverse('trekking:trek_registration_create', args=[st.pk])
            },
            'color': event_color, # Colore opzionale per l'evento
            # 'allDay': False se vuoi specificare orari, altrimenti FullCalendar lo gestisce
        })
    return JsonResponse(events, safe=False)