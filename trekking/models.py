# trekking/models.py

from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.utils import timezone
import os
import datetime
from django.conf import settings

class Difficulty(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Nome Difficoltà")
    icon_class = models.CharField(max_length=50, blank=True, null=True, verbose_name="Classe Icona", help_text="Es. 'fas fa-shoe-prints' per Font Awesome o nome file SVG.")
    description = models.TextField(blank=True, null=True, verbose_name="Descrizione")
    # color_hex = models.CharField(max_length=7, blank=True, null=True, help_text="Es. #FF5733 per colorare eventi nel calendario")

    class Meta:
        verbose_name = "Grado di Difficoltà"
        verbose_name_plural = "Gradi di Difficoltà"
        ordering = ['id']

    def __str__(self):
        return self.name

class Trek(models.Model):
    name = models.CharField(max_length=200, verbose_name="Nome Trekking")
    slug = models.SlugField(max_length=220, unique=True, blank=True, help_text="Lasciare vuoto per generare automaticamente dal nome.")
    description_short = models.TextField(verbose_name="Descrizione Breve", help_text="Anteprima per le liste dei trekking.")
    description_long = models.TextField(verbose_name="Descrizione Completa")
    difficulty = models.ForeignKey(Difficulty, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Grado di Difficoltà")

    def get_main_image_upload_path(instance, filename):
        return os.path.join('trek_images', instance.slug, filename)
    main_image = models.ImageField(upload_to=get_main_image_upload_path, verbose_name="Immagine Principale", help_text="Immagine rappresentativa del trekking.")

    def get_gpx_upload_path(instance, filename):
        return os.path.join('gpx_tracks', instance.slug, filename)
    gpx_file = models.FileField(upload_to=get_gpx_upload_path, blank=True, null=True, verbose_name="File Traccia GPX")

    length_km = models.FloatField(verbose_name="Lunghezza (km)", blank=True, null=True)
    elevation_gain_meters = models.PositiveIntegerField(verbose_name="Dislivello Positivo (m)", blank=True, null=True)
    elevation_loss_meters = models.PositiveIntegerField(verbose_name="Dislivello Negativo (m)", blank=True, null=True, help_text="Se diverso da quello positivo (es. traversate).")
    estimated_duration = models.CharField(max_length=100, verbose_name="Durata Stimata", blank=True, null=True, help_text="Es: '3-4 ore', '1 giorno'")
    estimated_duration_hours = models.FloatField(verbose_name="Durata Stimata (ore numerico)", blank=True, null=True, help_text="Solo numero, es. 3.5 per 3 ore e mezza. Utile per calcoli.")
    location_area = models.CharField(max_length=150, verbose_name="Area Geografica", blank=True, null=True, help_text="Es: Dolomiti Bellunesi, Appennino Ligure")
    meeting_point_general_info = models.TextField(verbose_name="Info Generali Punto di Ritrovo", blank=True, null=True, help_text="Indicazioni generiche se il trekking non è schedulato.")
    equipment_mandatory = models.TextField(verbose_name="Equipaggiamento Obbligatorio", blank=True, null=True)
    equipment_recommended = models.TextField(verbose_name="Equipaggiamento Consigliato", blank=True, null=True)
    notes = models.TextField(verbose_name="Note Aggiuntive", blank=True, null=True, help_text="Eventuali particolarità, fonti d'acqua, rifugi, ecc.")
    is_published = models.BooleanField(default=True, verbose_name="Pubblicato")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data Creazione")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Data Aggiornamento")

    class Meta:
        verbose_name = "Trekking / Percorso"
        verbose_name_plural = "Trekking / Percorsi"
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
            original_slug = self.slug
            counter = 1
            while Trek.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f'{original_slug}-{counter}'
                counter += 1
        super().save(*args, **kwargs)

class TrekImage(models.Model):
    trek = models.ForeignKey(Trek, related_name='gallery_images', on_delete=models.CASCADE, verbose_name="Trekking di Riferimento")
    def get_gallery_image_upload_path(instance, filename):
        return os.path.join('trek_images', instance.trek.slug, 'gallery', filename)
    image = models.ImageField(upload_to=get_gallery_image_upload_path, verbose_name="Immagine Galleria")
    caption = models.CharField(max_length=200, blank=True, null=True, verbose_name="Didascalia")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Immagine Galleria Trekking"
        verbose_name_plural = "Immagini Galleria Trekking"
        ordering = ['uploaded_at']

    def __str__(self):
        return f"Immagine per {self.trek.name} - {self.caption if self.caption else os.path.basename(self.image.name)}"

class ScheduledTrek(models.Model):
    EVENT_STATUS_CHOICES = [
        ('PIANIFICATO', 'Pianificato'),
        ('CONFERMATO', 'Confermato'),
        ('ANNULLATO_METEO', 'Annullato (Meteo)'),
        ('ANNULLATO_ORGANIZZATORE', 'Annullato (Organizzatore)'),
        ('COMPLETATO', 'Completato'),
    ]

    trek = models.ForeignKey(Trek, on_delete=models.CASCADE, verbose_name="Trekking di Riferimento")
    date = models.DateField(verbose_name="Data Uscita")
    start_time = models.TimeField(verbose_name="Orario di Ritrovo", blank=True, null=True)
    meeting_point_specific = models.TextField(verbose_name="Punto di Ritrovo Specifico", help_text="Indirizzo preciso, coordinate, link Google Maps per questa uscita.")
    guide_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="Nome Guida/Accompagnatore")
    max_participants = models.PositiveIntegerField(verbose_name="Numero Massimo Partecipanti")
    price = models.DecimalField(max_digits=7, decimal_places=2, verbose_name="Quota di Partecipazione (€)", blank=True, null=True, help_text="Lasciare vuoto o 0 se gratuito.")
    is_active = models.BooleanField(default=True, verbose_name="Visibile Pubblicamente nelle Liste Future", help_text="Controlla la visibilità nelle liste di uscite future attive. Viene gestito anche dal metodo save() in base allo stato.")
    registration_open = models.BooleanField(default=True, verbose_name="Iscrizioni Aperte (Manuale)")
    registration_deadline = models.DateTimeField(blank=True, null=True, verbose_name="Termine Iscrizioni", help_text="Opzionale: specifica data e ora esatta di chiusura. Se non impostato, le iscrizioni chiudono con l'inizio dell'evento o se 'Iscrizioni Aperte' è deselezionato.")
    event_status = models.CharField(max_length=30, choices=EVENT_STATUS_CHOICES, default='PIANIFICATO', verbose_name="Stato Uscita")
    additional_info_specific = models.TextField(blank=True, null=True, verbose_name="Info Aggiuntive Specifiche per l'Uscita")

    class Meta:
        verbose_name = "Uscita Programmata"
        verbose_name_plural = "Uscite Programmate"
        ordering = ['date', 'start_time']

    def __str__(self):
        return f"{self.trek.name} - {self.date.strftime('%d/%m/%Y')} ({self.get_event_status_display()})"

    @property
    def current_participants_count(self):
        return self.registrations.filter(status='CONFERMATA').count()

    @property
    def spots_available(self):
        available = self.max_participants - self.current_participants_count
        return max(0, available)

    @property
    def is_cancelled(self): # NUOVA PROPRIETÀ
        return self.event_status in ['ANNULLATO_METEO', 'ANNULLATO_ORGANIZZATORE']

    @property
    def is_completed(self): # NUOVA PROPRIETÀ
        return self.event_status == 'COMPLETATO'

    @property
    def can_register(self):
        now = timezone.now()
        # Per fare un confronto consapevole tra data e datetime, costruisci un datetime per l'evento
        event_datetime_start = datetime.datetime.combine(self.date, self.start_time if self.start_time else datetime.time.min)
        if settings.USE_TZ and timezone.is_naive(event_datetime_start): # Rendi l'orario consapevole del fuso orario se USE_TZ è True
            event_datetime_start = timezone.make_aware(event_datetime_start, timezone.get_current_timezone())
        
        if self.is_cancelled or self.is_completed: return False
        if not self.registration_open: return False
        if now >= event_datetime_start : return False
        if self.registration_deadline and now > self.registration_deadline: return False
        if self.spots_available <= 0: return False
        return True

    def save(self, *args, **kwargs):
        now = timezone.now()
        event_datetime_start = datetime.datetime.combine(self.date, self.start_time if self.start_time else datetime.time.min)
        if settings.USE_TZ and timezone.is_naive(event_datetime_start):
             event_datetime_start = timezone.make_aware(event_datetime_start, timezone.get_current_timezone())
        
        is_past_event = event_datetime_start < now

        if self.is_cancelled or self.is_completed or is_past_event:
            self.is_active = False
            self.registration_open = False
            if is_past_event and not self.is_cancelled and not self.is_completed: # Se è passato e non era già annullato/completato
                 self.event_status = 'COMPLETATO'
        elif self.event_status in ['PIANIFICATO', 'CONFERMATO']:
            if not is_past_event:
                self.is_active = True
            else: # Non dovrebbe succedere se la logica sopra è corretta, ma per sicurezza
                self.is_active = False
                self.registration_open = False
                self.event_status = 'COMPLETATO'

        if self.registration_deadline and now > self.registration_deadline:
            self.registration_open = False
            
        super().save(*args, **kwargs)

class TrekRegistration(models.Model):
    STATUS_CHOICES = [
        ('CONFERMATA', 'Confermata'),
        ('ANNULLATA_UTENTE', 'Annullata (Utente)'),
        ('ANNULLATA_ADMIN', 'Annullata (Admin)'),
        ('COMPLETATA', 'Completata'),
    ]
    scheduled_trek = models.ForeignKey(ScheduledTrek, related_name='registrations', on_delete=models.CASCADE, verbose_name="Uscita Programmata")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, verbose_name="Utente Registrato")
    first_name = models.CharField(max_length=100, verbose_name="Nome")
    last_name = models.CharField(max_length=100, verbose_name="Cognome")
    email = models.EmailField(verbose_name="Email")
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Telefono")
    registration_date = models.DateTimeField(auto_now_add=True, verbose_name="Data Iscrizione")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='CONFERMATA', verbose_name="Stato Iscrizione")
    notes_user = models.TextField(blank=True, null=True, verbose_name="Note dall'Utente")
    admin_notes = models.TextField(blank=True, null=True, verbose_name="Note Admin (interne)")

    class Meta:
        verbose_name = "Iscrizione Trekking"
        verbose_name_plural = "Iscrizioni Trekking"
        ordering = ['-registration_date']
        unique_together = [['scheduled_trek', 'email']]

    def __str__(self):
        user_info = self.user.username if self.user else f"{self.first_name} {self.last_name}"
        return f"Iscrizione di {user_info} a {self.scheduled_trek}"

    def save(self, *args, **kwargs):
        if self.user and not self.first_name and not self.last_name and not self.email:
            self.first_name = self.user.first_name if self.user.first_name else ''
            self.last_name = self.user.last_name if self.user.last_name else ''
            self.email = self.user.email if self.user.email else ''
        super().save(*args, **kwargs)