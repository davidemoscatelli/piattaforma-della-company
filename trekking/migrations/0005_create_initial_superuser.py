import os
from django.db import migrations
from django.contrib.auth import get_user_model
# Se decidi di usare settings.AUTH_USER_MODEL per la dipendenza, decommenta:
# from django.conf import settings

def create_superuser(apps, schema_editor):
    User = get_user_model()
    
    # Prendi le credenziali dalle variabili d'ambiente
    # Dovrai impostare queste variabili d'ambiente su Render.com
    DJANGO_SUPERUSER_USERNAME = os.environ.get('DJANGO_SUPERUSER_USERNAME')
    DJANGO_SUPERUSER_EMAIL = os.environ.get('DJANGO_SUPERUSER_EMAIL')
    DJANGO_SUPERUSER_PASSWORD = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

    # Controlla se le variabili d'ambiente sono state impostate
    if not DJANGO_SUPERUSER_USERNAME:
        print("Variabile d'ambiente DJANGO_SUPERUSER_USERNAME non impostata. Impossibile creare il superutente.")
        return
    if not DJANGO_SUPERUSER_EMAIL:
        print("Variabile d'ambiente DJANGO_SUPERUSER_EMAIL non impostata. Impossibile creare il superutente.")
        return
    if not DJANGO_SUPERUSER_PASSWORD:
        print("Variabile d'ambiente DJANGO_SUPERUSER_PASSWORD non impostata. Impossibile creare il superutente.")
        return

    if not User.objects.filter(username=DJANGO_SUPERUSER_USERNAME).exists():
        print(f"Creazione superutente: {DJANGO_SUPERUSER_USERNAME} con email {DJANGO_SUPERUSER_EMAIL}")
        User.objects.create_superuser(
            username=DJANGO_SUPERUSER_USERNAME,
            email=DJANGO_SUPERUSER_EMAIL,
            password=DJANGO_SUPERUSER_PASSWORD
        )
    else:
        print(f"Superutente {DJANGO_SUPERUSER_USERNAME} esiste già.")

def remove_superuser(apps, schema_editor):
    # Questa funzione viene chiamata se fai l'unmigrate.
    # Potresti voler implementare la logica per rimuovere l'utente se necessario,
    # ma per ora la lasceremo con un semplice print per sicurezza.
    User = get_user_model()
    DJANGO_SUPERUSER_USERNAME = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin') # Usa un default se non specificato per la rimozione
    try:
        user = User.objects.get(username=DJANGO_SUPERUSER_USERNAME)
        if user.is_superuser:
            # Per sicurezza, non cancelliamo l'utente automaticamente durante un unmigrate.
            # Se vuoi cancellarlo, decommenta la riga qui sotto, ma fai attenzione.
            # user.delete()
            # print(f"Superutente {DJANGO_SUPERUSER_USERNAME} cancellato.")
            print(f"Operazione di rimozione per superutente {DJANGO_SUPERUSER_USERNAME} non implementata per cancellazione automatica (per sicurezza).")
        else:
            print(f"Utente {DJANGO_SUPERUSER_USERNAME} trovato, ma non è un superutente. Nessuna azione di rimozione specifica eseguita.")
    except User.DoesNotExist:
        print(f"Superutente {DJANGO_SUPERUSER_USERNAME} non trovato durante il tentativo di rimozione.")
        pass


class Migration(migrations.Migration):

    dependencies = [
        # IMPORTANTE: Sostituisci '0004_nome_migrazione_precedente' 
        # con il nome effettivo della migrazione 0004 della tua app 'trekking'.
        # Esempio: ('trekking', '0004_auto_20250522_1800'),
        ('trekking', '0004_alter_trekregistration_unique_together_and_more'), 
        
        # Dipendenza dall'ultima migrazione conosciuta dell'app 'auth' per assicurarsi
        # che il modello User e le tabelle relative siano create e aggiornate.
        # '0012_alter_user_first_name_max_length' è l'ultima migrazione per l'app auth
        # in versioni recenti di Django (incluso Django 5.0+).
        ('auth', '0012_alter_user_first_name_max_length'),
        
        # Alternativa più dinamica per la dipendenza dal modello User:
        # migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        # Se usi questa, assicurati di importare `from django.conf import settings`.
        # La tua app 'trekking' dovrebbe comunque dipendere dalla sua migrazione precedente.
    ]

    operations = [
        migrations.RunPython(create_superuser, remove_superuser),
    ]