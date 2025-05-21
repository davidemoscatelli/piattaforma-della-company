# trekking/forms.py
from django import forms
from .models import TrekRegistration

class TrekRegistrationForm(forms.ModelForm):
    # Campi per NON SOCI che vogliamo rendere obbligatori via JavaScript se is_member è False
    NON_MEMBER_REQUIRED_FIELDS = ['birth_date', 'birth_place', 'address', 'city', 'postal_code', 'fiscal_code']

    class Meta:
        model = TrekRegistration
        fields = [
            'first_name', 'last_name', 'email', 'phone', 
            'is_member', 
            'birth_date', 'birth_place', 'address', 'city', 'postal_code', 'fiscal_code',
            'has_car', 'available_seats',
            'notes_user'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Il tuo nome'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Il tuo cognome'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'latua@email.com'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Es. 3331234567'}),
            'is_member': forms.RadioSelect(choices=[(True, 'Sì, sono socio'), (False, 'No, non sono socio')]), # Radio button per scelta più chiara
            'birth_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
            'birth_place': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Es. Roma (RM)'}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Es. Via Appia Nuova, 123'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Es. Roma'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Es. 00100'}),
            'fiscal_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Il tuo codice fiscale', 'style': 'text-transform: uppercase;'}),
            'has_car': forms.RadioSelect(choices=[(True, 'Sì'), (False, 'No')]),
            'available_seats': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0', 'min': '0'}),
            'notes_user': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Eventuali allergie, preferenze, o se offri passaggi...'}),
        }
        labels = {
            'first_name': 'Nome',
            'last_name': 'Cognome',
            'email': 'Indirizzo Email',
            'phone': 'Numero di Telefono (consigliato)',
            'is_member': 'Sei socio "La Company"?',
            'birth_date': 'Data di Nascita (solo se non socio)',
            'birth_place': 'Luogo di Nascita (solo se non socio)',
            'address': 'Indirizzo di Residenza (solo se non socio)',
            'city': 'Città (solo se non socio)',
            'postal_code': 'CAP (solo se non socio)',
            'fiscal_code': 'Codice Fiscale (solo se non socio)',
            'has_car': 'Metterai a disposizione la tua auto per il car pooling?',
            'available_seats': 'Se sì, quanti posti offri (oltre a te)?',
            'notes_user': 'Note aggiuntive',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['phone'].required = False # Il telefono rimane opzionale
        self.fields['available_seats'].required = False # Posti auto opzionali (diventano 0 se has_car=False)

        # Inizialmente i campi per non soci non sono obbligatori a livello di form Django,
        # la logica JS e la validazione clean() si occuperanno di questo.
        for field_name in self.NON_MEMBER_REQUIRED_FIELDS:
            if field_name in self.fields: # Controlla se il campo esiste prima di modificarlo
                 self.fields[field_name].required = False
        
        # Se l'istanza esiste (cioè siamo in modifica e non socio è selezionato), 
        # allora rendi i campi obbligatori
        if self.instance and self.instance.pk and not self.instance.is_member:
            for field_name in self.NON_MEMBER_REQUIRED_FIELDS:
                 if field_name in self.fields:
                    self.fields[field_name].required = True
        
        # Logica per available_seats in base a has_car (più per JS, ma impostiamo lo stato iniziale)
        if self.instance and self.instance.pk and not self.instance.has_car:
            self.fields['available_seats'].widget.attrs['disabled'] = True
            self.fields['available_seats'].widget.attrs['value'] = 0 # O `initial` se in creazione
        elif self.initial and not self.initial.get('has_car', False):
             self.fields['available_seats'].widget.attrs['disabled'] = True
        
    def clean(self):
        cleaned_data = super().clean()
        is_member = cleaned_data.get('is_member')
        has_car = cleaned_data.get('has_car')

        if not is_member: # Se NON è socio
            for field_name in self.NON_MEMBER_REQUIRED_FIELDS:
                if not cleaned_data.get(field_name):
                    self.add_error(field_name, "Questo campo è obbligatorio per i non soci.")
        
        if has_car:
            available_seats = cleaned_data.get('available_seats')
            if available_seats is None or available_seats < 0: # Potrebbe essere 0 se offre l'auto ma non posti
                self.add_error('available_seats', "Indica un numero valido di posti (0 o più).")
        else: # Se non ha auto, i posti disponibili sono 0
            cleaned_data['available_seats'] = 0 
            # Non c'è bisogno di un errore qui perché il modello lo gestirà o il widget sarà disabilitato

        return cleaned_data