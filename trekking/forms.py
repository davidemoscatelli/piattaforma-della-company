# trekking/forms.py

from django import forms
from .models import TrekRegistration, ScheduledTrek

class TrekRegistrationForm(forms.ModelForm):
    # Campo di controllo per accettazione termini (opzionale ma buona pratica)
    # terms_accepted = forms.BooleanField(
    #     label="Dichiaro di aver letto e accettato le condizioni di partecipazione e l'informativa sulla privacy.",
    #     required=True
    # )

    class Meta:
        model = TrekRegistration
        # Scegliamo i campi che l'utente dovrà compilare.
        # 'scheduled_trek' e 'user' (se loggato) verranno gestiti dalla vista.
        # 'status' e 'registration_date' hanno valori di default o auto_now_add.
        fields = ['first_name', 'last_name', 'email', 'phone', 'notes_user'] #, 'terms_accepted']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Il tuo nome'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Il tuo cognome'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'latua@email.com'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Il tuo numero di telefono (opzionale)'}),
            'notes_user': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Eventuali comunicazioni o richieste (es. allergie, preferenze, ecc.)'}),
        }
        labels = {
            'first_name': 'Nome',
            'last_name': 'Cognome',
            'email': 'Indirizzo Email',
            'phone': 'Numero di Telefono',
            'notes_user': 'Note aggiuntive',
        }

    def __init__(self, *args, **kwargs):
        # Possiamo passare l'uscita programmata al form se necessario, ma per ora non serve qui.
        # self.scheduled_trek = kwargs.pop('scheduled_trek', None)
        super().__init__(*args, **kwargs)
        # Rendi il telefono non obbligatorio se blank=True nel modello
        self.fields['phone'].required = False

    def clean_email(self):
        # Esempio di validazione custom per l'email, se necessario
        email = self.cleaned_data.get('email')
        # if YourUserModel.objects.filter(email=email).exists() and not self.user_is_authenticated:
        #     raise forms.ValidationError("Questa email è già associata a un account. Effettua il login.")
        return email

    # Se avessimo un campo 'scheduled_trek' nel form (nascosto), potremmo validarlo qui.
    # Ma lo imposteremo direttamente nella vista.