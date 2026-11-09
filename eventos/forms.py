from django import forms
from .models import Evento


class EventoForm(forms.ModelForm):
    class Meta:
        model = Evento
        fields = [
            'nombre', 'slug', 'fecha', 'lugar', 'informacion',
            'precio_adulto', 'precio_nino', 'edad_max_nino', 'edad_min_paga',
            'fecha_cierre', 'cupo', 'activo', 'contactos_pago',
            'fecha_limite_descuento', 'precio_adulto_descuento', 'precio_nino_descuento',
            'nota_comprobante',
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
            'fecha_limite_descuento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
            'precio_adulto_descuento': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'precio_nino_descuento': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'nota_comprobante': forms.Textarea(attrs={'class': 'form-control', 'rows': 3,
                                                      'placeholder': 'Ej: Alias para transferir: ICE.ASUNCION.EVENTOS'}),
            'contactos_pago': forms.Textarea(attrs={'class': 'form-control', 'rows': 3,
                                                    'placeholder': 'Santy, 543813419795\nPaula, 543816621117'}),
        }

    def clean(self):
        data = super().clean()
        max_nino, min_paga = data.get('edad_max_nino'), data.get('edad_min_paga')
        if max_nino is not None and min_paga is not None and min_paga > max_nino:
            self.add_error('edad_min_paga', 'Debe ser menor o igual a la edad máxima de niño.')

        # Descuento: o se completan los tres campos o ninguno
        campos_desc = ['fecha_limite_descuento', 'precio_adulto_descuento', 'precio_nino_descuento']
        completos = [data.get(c) is not None for c in campos_desc]
        if any(completos) and not all(completos):
            for c, ok in zip(campos_desc, completos):
                if not ok:
                    self.add_error(c, 'Completá los tres datos del descuento (o dejalos todos vacíos).')
        for normal, desc in [('precio_adulto', 'precio_adulto_descuento'), ('precio_nino', 'precio_nino_descuento')]:
            if data.get(desc) is not None and data.get(normal) is not None and data[desc] > data[normal]:
                self.add_error(desc, 'El precio con descuento no puede ser mayor al precio normal.')
        return data
