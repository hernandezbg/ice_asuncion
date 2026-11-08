from django import forms
from .models import Evento


class EventoForm(forms.ModelForm):
    class Meta:
        model = Evento
        fields = [
            'nombre', 'slug', 'fecha', 'lugar', 'informacion',
            'precio_adulto', 'precio_nino', 'edad_max_nino', 'edad_min_paga',
            'fecha_cierre', 'cupo', 'activo',
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Cena de fin de año 2026'}),
            'slug': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'fin-de-anio-2026'}),
            'fecha': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
            'lugar': forms.TextInput(attrs={'class': 'form-control'}),
            'informacion': forms.Textarea(attrs={'class': 'form-control', 'rows': 8}),
            'precio_adulto': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'precio_nino': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'edad_max_nino': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 17}),
            'edad_min_paga': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 17}),
            'fecha_cierre': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'},
                                                format='%Y-%m-%dT%H:%M'),
            'cupo': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean(self):
        data = super().clean()
        max_nino, min_paga = data.get('edad_max_nino'), data.get('edad_min_paga')
        if max_nino is not None and min_paga is not None and min_paga > max_nino:
            self.add_error('edad_min_paga', 'Debe ser menor o igual a la edad máxima de niño.')
        return data
