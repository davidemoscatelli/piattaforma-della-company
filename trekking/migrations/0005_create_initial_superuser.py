import os
from django.db import migrations
from django.contrib.auth import get_user_model

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
        if user.is_superuser: # Rimuovi solo se è effettivamente il superutente che abbiamo creato
            # user.delete() # ATTENZIONE: questo cancellerebbe l'utente. Valuta se è desiderato.
            print(f"Operazione di rimozione per superutente {DJANGO_SUPERUSER_USERNAME} non implementata per sicurezza.")
            pass
    except User.DoesNotExist:
        pass


class Migration(migrations.Migration):

    dependencies = [
        # Assicurati che questa dipendenza sia l'ultima migrazione della tua app 'trekking'
        # o l'ultima migrazione dell'app 'auth' se non hai altre migrazioni in 'trekking'.
        # Se hai appena creato il campo 'registration_deadline', la dipendenza sarà quella.
        # Esempio: ('trekking', '0002_auto_YYYYMMDD_HHMM'), 
        # O se è la prima migrazione di trekking e non hai dipendenze da altre app:
        # ('auth', '0012_alter_user_first_name_max_length'), # Ultima migrazione di auth
        migrations.swappable_dependency(migrations. государмы('auth', 'user')), # Dipende dal modello User di auth
    ]

    operations = [
        migrations.RunPython(create_superuser, remove_superuser),
    ]