# trekking/admin.py

from django.contrib import admin, messages # AGGIUNTO messages
from .models import Difficulty, Trek, TrekImage, ScheduledTrek, TrekRegistration
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.urls import path, reverse # SPOSTATO reverse qui
from django.shortcuts import get_object_or_404, redirect # AGGIUNTO redirect
from django.utils.html import format_html

class TrekImageInline(admin.TabularInline):
    model = TrekImage
    extra = 1
    readonly_fields = ('uploaded_at',)

class ScheduledTrekInline(admin.TabularInline): # Questo inline è per mostrare le uscite dentro la pagina di un Trek
    model = ScheduledTrek
    extra = 0 # Metti 0 per non mostrare form vuoti di default
    fields = ('date', 'start_time', 'event_status', 'meeting_point_specific', 'max_participants', 'price', 'is_active', 'registration_open', 'registration_deadline')
    show_change_link = True
    # readonly_fields = ('spots_available', 'current_participants_count') # Non puoi avere campi readonly qui che sono property
    ordering = ['-date']

@admin.register(Difficulty)
class DifficultyAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon_class', 'id')
    search_fields = ('name',)

@admin.register(Trek)
class TrekAdmin(admin.ModelAdmin):
    list_display = ('name', 'difficulty', 'location_area', 'length_km', 'elevation_gain_meters', 'is_published', 'updated_at')
    list_filter = ('difficulty', 'location_area', 'is_published')
    search_fields = ('name', 'description_short', 'description_long', 'location_area')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'difficulty', 'is_published')
        }),
        ('Descrizione e Media', {
            'fields': ('description_short', 'description_long', 'main_image', 'gpx_file')
        }),
        ('Dettagli Tecnici', {
            'fields': ('length_km', 'elevation_gain_meters', 'elevation_loss_meters', 'estimated_duration', 'estimated_duration_hours', 'location_area')
        }),
        ('Logistica e Equipaggiamento', {
            'fields': ('meeting_point_general_info', 'equipment_mandatory', 'equipment_recommended', 'notes')
        }),
        ('Date (Automatiche)', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    inlines = [TrekImageInline, ScheduledTrekInline] # Ora ScheduledTrekInline è qui

@admin.register(TrekImage)
class TrekImageAdmin(admin.ModelAdmin):
    list_display = ('trek', 'caption', 'image', 'uploaded_at')
    list_filter = ('trek',)
    search_fields = ('trek__name', 'caption')
    readonly_fields = ('uploaded_at',)

@admin.register(ScheduledTrek) # UNICA REGISTRAZIONE PER ScheduledTrek
class ScheduledTrekAdmin(admin.ModelAdmin):
    list_display = ('trek', 'date', 'start_time', 'event_status', 'guide_name', 'max_participants', 'current_participants_count', 'spots_available', 'registration_deadline', 'is_active', 'registration_open', 'view_participant_list_link') # Aggiunto view_participant_list_link
    list_filter = ('event_status', 'date', 'trek__difficulty', 'trek__location_area', 'is_active', 'registration_open', 'guide_name')
    search_fields = ('trek__name', 'meeting_point_specific', 'guide_name')
    autocomplete_fields = ['trek']
    readonly_fields = ('current_participants_count', 'spots_available') # spots_available è una property, quindi readonly
    fieldsets = (
        (None, {
            'fields': ('trek', 'date', 'start_time', 'meeting_point_specific', 'guide_name')
        }),
        ('Stato e Visibilità', {
            'fields': ('event_status', 'is_active', 'registration_open', 'registration_deadline') # Aggiunto registration_deadline
        }),
        ('Partecipanti e Costi', {
            'fields': ('max_participants', 'price') # Rimosso current_participants_count da qui, è in readonly_fields e list_display
        }),
        ('Info Calcolate (Solo Lettura)', { # Sezione per i campi readonly
            'fields': ('current_participants_count', 'spots_available'),
             'classes': ('collapse',),
        }),
        ('Altre Informazioni', {
            'fields': ('additional_info_specific',)
        }),
    )
    list_editable = ('event_status', 'is_active', 'registration_open', 'registration_deadline') # Aggiunto registration_deadline

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('registrations')

    def view_participant_list_link(self, obj):
        if obj.pk:
            # Assumendo che l'URL sia nell'app trekking con il nome 'event_participant_list'
            url = reverse('trekking:event_participant_list', args=[obj.pk])
            return format_html('<a href="{}" target="_blank">Vedi Lista</a>', url)
        return "-"
    view_participant_list_link.short_description = "Lista Partecipanti"


@admin.register(TrekRegistration)
class TrekRegistrationAdmin(admin.ModelAdmin):
    list_display = ('scheduled_trek', 'first_name', 'last_name', 'email', 'is_member', 'has_car', 'status', 'registration_date', 'view_print_link') # Aggiunto view_print_link
    list_filter = ('status', 'scheduled_trek__date', 'scheduled_trek__trek__name', 'is_member', 'has_car', 'scheduled_trek__event_status')
    search_fields = ('first_name', 'last_name', 'email', 'phone', 'scheduled_trek__trek__name')
    readonly_fields = ('registration_date',)
    list_editable = ('status', 'is_member', 'has_car')
    autocomplete_fields = ['scheduled_trek', 'user']
    actions = ['print_selected_registrations_action'] # Rinominata l'azione per chiarezza
    fieldsets = (
        ('Dettagli Iscrizione', {'fields': ('scheduled_trek', 'user', 'status', 'registration_date')}),
        ('Dati Partecipante', {'fields': ('first_name', 'last_name', 'email', 'phone', 'is_member')}),
        ('Dati Non Socio (Compilare se "È Socio?" è No)', {
            'fields': ('birth_date', 'birth_place', 'address', 'city', 'postal_code', 'fiscal_code'),
            'classes': ('collapse',),
        }),
        ('Disponibilità Auto', {'fields': ('has_car', 'available_seats')}),
        ('Note', {'fields': ('notes_user', 'admin_notes')}),
    )

    # Vista per la stampa singola
    def print_registration_view(self, request, registration_id): # Rinominata per chiarezza
        registration = get_object_or_404(TrekRegistration, pk=registration_id)
        html = render_to_string('admin/trekking/trekregistration/print_registration.html', {'registration': registration})
        return HttpResponse(html)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:registration_id>/print/', # Usato int per pk
                self.admin_site.admin_view(self.print_registration_view), # Chiamata alla vista corretta
                name='trekking_trekregistration_print', # Namespace dell'app per coerenza
            )
        ]
        return custom_urls + urls

    @admin.action(description="Stampa Modulo(i) di Iscrizione Selezionato(i)")
    def print_selected_registrations_action(self, request, queryset): # Rinominata
        if queryset.count() == 1:
            registration = queryset.first()
            # Usa il nome dell'URL definito in get_urls, con il namespace 'admin'
            return redirect('admin:trekking_trekregistration_print', registration_id=registration.id)
        else:
            self.message_user(request, "Seleziona una sola iscrizione alla volta per la stampa del modulo.", messages.WARNING)

    def view_print_link(self, obj):
        # Usa il nome dell'URL definito in get_urls, con il namespace 'admin'
        url = reverse('admin:trekking_trekregistration_print', args=[obj.pk])
        return format_html('<a href="{}" target="_blank">Stampa Modulo</a>', url)
    view_print_link.short_description = "Modulo Stampa"