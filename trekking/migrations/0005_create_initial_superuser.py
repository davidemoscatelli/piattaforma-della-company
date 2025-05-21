import os
from django.db import migrations
from django.contrib.auth import get_user_model
# from django.conf import settings # Aggiungi se usi migrations.swappable_dependency(settings.AUTH_USER_MODEL)

def create_superuser(apps, schema_editor):
    User = get_user_model()
    
    # Prendi le credenziali dalle variabili d'ambiente
    # Dovrai impostare queste variabili d'ambiente su Render.com
    DJANGO_SUPERUSER_USERNAME = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
    DJANGO_SUPERUSER_EMAIL = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')
    DJANGO_SUPERUSER_PASSWORD = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'complexpassword123')

    if not DJANGO_SUPERUSER_PASSWORD:
        print("Variabile d'ambiente DJANGO_SUPERUSER_PASSWORD non impostata. Impossibile creare il superutente.")
        return

    if not User.objects.filter(username=DJANGO_SUPERUSER_USERNAME).exists():
        print(f"Creazione superutente: {DJANGO_SUPERUSER_USERNAME}")
        User.objects.create_superuser(
            username=DJANGO_SUPERUSER_USERNAME,
            email=DJANGO_SUPERUSER_EMAIL,
            password=DJANGO_SUPERUSER_PASSWORD
        )
    else:
        print(f"Superutente {DJANGO_SUPERUSER_USERNAME} esiste già.")

def remove_superuser(apps, schema_editor):
    # Questa funzione viene chiamata se fai il unmigrate.
    # Potresti voler implementare la logica per rimuovere l'utente se necessario,
    # ma per ora la lasceremo vuota o con un semplice print.
    User = get_user_model()
    DJANGO_SUPERUSER_USERNAME = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
    try:
        user = User.objects.get(username=DJANGO_SUPERUSER_USERNAME)
        # Controlla se è un superutente prima di considerare la rimozione,
        # e magari solo se è quello che questa migrazione avrebbe creato.
        if user.is_superuser:
            # user.delete() # ATTENZIONE: questo cancellerebbe l'utente. Valuta se è desiderato.
            print(f"Operazione di rimozione per superutente {DJANGO_SUPERUSER_USERNAME} non implementata esplicitamente per sicurezza.")
            pass
    except User.DoesNotExist:
        print(f"Superutente {DJANGO_SUPERUSER_USERNAME} non trovato durante il tentativo di rimozione.")
        pass


class Migration(migrations.Migration):

    dependencies = [
        # Sostituisci '0004_nome_migrazione_precedente' con il nome effettivo 
        # della migrazione 0004 della tua app 'trekking'.
        # Se questa migrazione non dipende logicamente dalla 0004 per la creazione del superuser
        # (ad esempio, se la 0004 modifica modelli non correlati), potresti ometterla,
        # ma è prassi comune dipendere dalla migrazione precedente nella stessa app.
        ('trekking', '0004_nome_migrazione_precedente'), 
        
        # Dipendenza dall'ultima migrazione conosciuta dell'app 'auth' per assicurarsi
        # che il modello User e le tabelle relative siano create e aggiornate.
        # '0012_alter_user_first_name_max_length' è l'ultima migrazione per l'app auth
        # in versioni recenti di Django (incluso Django 5.0). Verifica se la tua versione
        # di Django ne ha una più recente se incontri problemi.
        ('auth', '0012_alter_user_first_name_max_length'),
        
        # Alternativa per la dipendenza dal modello User (più dinamica se usi un custom user model):
        # migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        # Se usi questa, assicurati di importare `from django.conf import settings`.
        # E probabilmente dovresti comunque dipendere dalla migrazione precedente della tua app 'trekking'.
    ]

    operations = [
        migrations.RunPython(create_superuser, remove_superuser),
    ]
