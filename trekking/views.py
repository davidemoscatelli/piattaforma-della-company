# trekking/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Trek, Difficulty, ScheduledTrek, TrekImage, TrekRegistration # Assicurati USE_TZ sia importato se lo usi
from .forms import TrekRegistrationForm
from django.utils import timezone # Importa timezone
from django.urls import reverse
from django.http import JsonResponse
import datetime # Per timedelta e combine
from django.conf import settings




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
        except ValueError: pass
    if search_location:
        treks_queryset = treks_queryset.filter(location_area__icontains=search_location)

    sort_by = request.GET.get('sort', 'name')
    if sort_by == '-name': treks_queryset = treks_queryset.order_by('-name')
    elif sort_by == 'difficulty': treks_queryset = treks_queryset.order_by('difficulty__name', 'name')
    elif sort_by == 'length': treks_queryset = treks_queryset.order_by('length_km', 'name')
    elif sort_by == '-length': treks_queryset = treks_queryset.order_by('-length_km', 'name')
    else: treks_queryset = treks_queryset.order_by('name')

    context = {
        'treks': treks_queryset, 'difficulties': difficulties,
        'selected_difficulty_id': int(selected_difficulty_id) if selected_difficulty_id and selected_difficulty_id.isdigit() else None,
        'search_location_value': search_location, 'current_sort': sort_by,
        'page_title': 'Tutti i Nostri Percorsi'
    }
    return render(request, 'trekking/trek_list.html', context)

def trek_detail(request, trek_slug):
    trek = get_object_or_404(Trek, slug=trek_slug, is_published=True)
    gallery_images = TrekImage.objects.filter(trek=trek).order_by('uploaded_at')
    scheduled_treks_for_this = ScheduledTrek.objects.filter(trek=trek).order_by('date', 'start_time')
    context = {
        'trek': trek, 'gallery_images': gallery_images,
        'scheduled_treks': scheduled_treks_for_this,
        'page_title': trek.name,
    }
    return render(request, 'trekking/trek_detail.html', context)

def scheduled_trek_list(request):
    current_date = timezone.now().date()
    all_scheduled_treks = ScheduledTrek.objects.filter(
        is_active=True, # Lasciamo questo, il save() del modello gestisce la sua coerenza
        date__gte=current_date, # Mostra solo da oggi in poi
        # event_status__in=['PIANIFICATO', 'CONFERMATO'] # Rimosso, is_active dovrebbe gestirlo
    ).order_by('date', 'start_time').select_related('trek', 'trek__difficulty')

    context = {
        'scheduled_treks': all_scheduled_treks,
        'page_title': 'Calendario Uscite Programmate'
    }
    return render(request, 'trekking/scheduled_trek_list_page.html', context)

def trek_registration_create(request, scheduled_trek_id):
    scheduled_trek = get_object_or_404(ScheduledTrek, pk=scheduled_trek_id)

    if not scheduled_trek.can_register:
        error_msg = "Spiacenti, non è possibile iscriversi a questa uscita al momento."
        if scheduled_trek.is_cancelled: error_msg = "Questa uscita è stata annullata."
        elif scheduled_trek.is_completed: error_msg = "Questa uscita è già terminata."
        # Altri controlli specifici già dentro can_register
        elif scheduled_trek.registration_deadline and timezone.now() > scheduled_trek.registration_deadline : error_msg = "Il termine per le iscrizioni è scaduto."
        elif not scheduled_trek.registration_open : error_msg = "Le iscrizioni per questa uscita sono chiuse."
        elif scheduled_trek.spots_available <= 0 : error_msg = "I posti per questa uscita sono esauriti."
        
        messages.error(request, error_msg)
        return redirect('trekking:trek_detail', trek_slug=scheduled_trek.trek.slug)

    if request.method == 'POST':
        form = TrekRegistrationForm(request.POST)
        if form.is_valid():
            if not scheduled_trek.can_register:
                messages.error(request, "Siamo spiacenti, le condizioni per l'iscrizione sono cambiate. Riprova.")
                return redirect('trekking:trek_detail', trek_slug=scheduled_trek.trek.slug)
            
            registration = form.save(commit=False)
            registration.scheduled_trek = scheduled_trek
            try:
                registration.save()
                messages.success(request, f"Grazie {registration.first_name}! La tua iscrizione per '{scheduled_trek.trek.name}' del {scheduled_trek.date.strftime('%d/%m/%Y')} è confermata.")
                return redirect('trekking:registration_success')
            except Exception as e:
                print(f"Errore durante il salvataggio della registrazione: {e}")
                if 'UNIQUE constraint failed' in str(e):
                    error_message = "Questa email risulta già iscritta a questa uscita."
                else:
                    error_message = "Spiacenti, si è verificato un problema tecnico. Riprova."
                messages.error(request, error_message)
                context = {'form': form, 'scheduled_trek': scheduled_trek, 'page_title': f"Iscrizione: {scheduled_trek.trek.name} ({scheduled_trek.date.strftime('%d/%m/%Y')})"}
                return render(request, 'trekking/trek_registration_form.html', context)
        else:
            messages.error(request, "Per favore, correggi gli errori evidenziati nel modulo.")
    else: # GET
        form = TrekRegistrationForm()

    context = {
        'form': form, 'scheduled_trek': scheduled_trek,
        'page_title': f"Iscrizione: {scheduled_trek.trek.name} ({scheduled_trek.date.strftime('%d/%m/%Y')})"
    }
    return render(request, 'trekking/trek_registration_form.html', context)

def registration_success(request):
    context = {'page_title': 'Iscrizione Confermata!'}
    return render(request, 'trekking/registration_success.html', context)

def trekking_events_json(request): # Rinominato per chiarezza se usi FullCalendar (era fullcalendar_events_json)
    start_range = timezone.now().date() - datetime.timedelta(days=60)
    end_range = timezone.now().date() + datetime.timedelta(days=180)

    scheduled_treks = ScheduledTrek.objects.filter(
        date__gte=start_range,
        date__lte=end_range
    ).order_by('date').select_related('trek', 'trek__difficulty')

    events = []
    for st in scheduled_treks:
        event_title = st.trek.name
        start_time_actual = st.start_time if st.start_time else datetime.time.min # Default a mezzanotte se non c'è ora
        event_start_datetime = datetime.datetime.combine(st.date, start_time_actual)
        
        event_color = None
        css_class_names = []

        if st.is_cancelled: # Usa la nuova proprietà
            event_color = '#dc3545'; event_title += f" ({st.get_event_status_display()})"; css_class_names.append('fc-event-cancelled')
        elif st.is_completed: # Usa la nuova proprietà
            event_color = '#6c757d'; event_title += " (Effettuato)"; css_class_names.append('fc-event-completed')
        elif not st.can_register and st.spots_available <=0 :
             event_color = '#fd7e14'; event_title += " (Esaurito)"; css_class_names.append('fc-event-full')
        elif not st.can_register :
             event_color = '#ffc107'; event_title += " (Iscriz. Chiuse)"; css_class_names.append('fc-event-closed')
        elif st.spots_available is not None and st.max_participants is not None and st.spots_available <= 5:
            event_color = '#ffc107'; event_title += f" (Solo {st.spots_available} posti!)"; css_class_names.append('fc-event-few-spots')
        elif st.event_status == 'CONFERMATO':
             event_color = '#198754'; css_class_names.append('fc-event-confirmed')
        else: # PIANIFICATO
            css_class_names.append('fc-event-planned')
            if not event_color: event_color = '#0dcaf0' # Colore di default per PIANIFICATO (azzurro info Bootstrap)


        event_url = reverse('trekking:trek_detail', args=[st.trek.slug])
        
        events.append({
            'id': st.pk, 'title': event_title, 'start': event_start_datetime.isoformat(),
            'url': event_url,
            'extendedProps': {
                'description_short': st.trek.description_short,
                'spots_available': st.spots_available, 'max_participants': st.max_participants,
                'status_display': st.get_event_status_display(),
                'start_time_display': st.start_time.strftime('%H:%M') if st.start_time else '',
                'date_display': st.date.strftime('%d/%m/%Y'),
                'is_bookable': st.can_register,
                'registration_url': reverse('trekking:trek_registration_create', args=[st.pk]) if st.can_register else None
            },
            'color': event_color, 'classNames': css_class_names,
            'allDay': not bool(st.start_time) # Considera allDay se non c'è un orario di inizio specifico
        })
    return JsonResponse(events, safe=False)