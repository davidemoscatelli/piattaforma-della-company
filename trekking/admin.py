# trekking/admin.py

from django.contrib import admin
from .models import Difficulty, Trek, TrekImage, ScheduledTrek, TrekRegistration

class TrekImageInline(admin.TabularInline):
    model = TrekImage
    extra = 1
    readonly_fields = ('uploaded_at',)

class ScheduledTrekInline(admin.TabularInline):
    model = ScheduledTrek
    extra = 1
    fields = ('date', 'start_time', 'event_status', 'meeting_point_specific', 'max_participants', 'price', 'is_active', 'registration_open')
    show_change_link = True

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
    inlines = [TrekImageInline, ScheduledTrekInline]

@admin.register(TrekImage)
class TrekImageAdmin(admin.ModelAdmin):
    list_display = ('trek', 'caption', 'image', 'uploaded_at')
    list_filter = ('trek',)
    search_fields = ('trek__name', 'caption')
    readonly_fields = ('uploaded_at',)

@admin.register(ScheduledTrek)
class ScheduledTrekAdmin(admin.ModelAdmin):
    list_display = ('trek', 'date', 'start_time', 'event_status', 'guide_name', 'max_participants', 'spots_available', 'price', 'is_active', 'registration_open') # AGGIUNTO event_status
    list_filter = ('event_status', 'date', 'trek__difficulty', 'trek__location_area', 'is_active', 'registration_open', 'guide_name') # AGGIUNTO event_status
    search_fields = ('trek__name', 'meeting_point_specific', 'guide_name')
    autocomplete_fields = ['trek']
    readonly_fields = ('current_participants_count',)
    fieldsets = (
        (None, {
            'fields': ('trek', 'date', 'start_time', 'meeting_point_specific', 'guide_name')
        }),
        ('Stato e Visibilità', { # NUOVA SEZIONE o aggiungi a esistente
            'fields': ('event_status', 'is_active', 'registration_open')
        }),
        ('Partecipanti e Costi', {
            'fields': ('max_participants', 'current_participants_count', 'price')
        }),
        ('Altre Informazioni', {
            'fields': ('additional_info_specific',)
        }),
    )
    list_editable = ('event_status', 'is_active', 'registration_open') # AGGIUNTO event_status

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('registrations')


@admin.register(TrekRegistration)
class TrekRegistrationAdmin(admin.ModelAdmin):
    list_display = ('scheduled_trek', 'first_name', 'last_name', 'email', 'phone', 'status', 'registration_date')
    list_filter = ('status', 'scheduled_trek__date', 'scheduled_trek__trek__name', 'scheduled_trek__event_status') # Aggiunto filtro per stato evento
    search_fields = ('first_name', 'last_name', 'email', 'phone', 'scheduled_trek__trek__name')
    readonly_fields = ('registration_date',)
    list_editable = ('status',)
    autocomplete_fields = ['scheduled_trek', 'user']
    fieldsets = (
        ('Dettagli Iscrizione', {
            'fields': ('scheduled_trek', 'user', 'status', 'registration_date')
        }),
        ('Dati Partecipante', {
            'fields': ('first_name', 'last_name', 'email', 'phone')
        }),
        ('Note', {
            'fields': ('notes_user', 'admin_notes')
        }),
    )