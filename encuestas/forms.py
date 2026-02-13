from django import forms
from .models import Encuesta, Pregunta


class EncuestaForm(forms.ModelForm):
    """Formulario para crear/editar encuestas."""

    class Meta:
        model = Encuesta
        fields = ['titulo', 'descripcion', 'rango_excelente', 'rango_bueno', 'rango_regular', 'rango_bajo']
        widgets = {
            'titulo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Evaluación de Salud de la Iglesia'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción opcional de la encuesta...'
            }),
            'rango_excelente': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'max': 100
            }),
            'rango_bueno': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'max': 100
            }),
            'rango_regular': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'max': 100
            }),
            'rango_bajo': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'max': 100
            }),
        }


class PreguntaForm(forms.ModelForm):
    """Formulario para crear/editar preguntas."""

    class Meta:
        model = Pregunta
        fields = ['texto', 'etiqueta_1', 'etiqueta_2', 'etiqueta_3', 'etiqueta_4', 'etiqueta_5']
        widgets = {
            'texto': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Escribe la pregunta aquí...'
            }),
            'etiqueta_1': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Etiqueta para valor 1'
            }),
            'etiqueta_2': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Etiqueta para valor 2'
            }),
            'etiqueta_3': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Etiqueta para valor 3'
            }),
            'etiqueta_4': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Etiqueta para valor 4'
            }),
            'etiqueta_5': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Etiqueta para valor 5'
            }),
        }


class UnirseEncuestaForm(forms.Form):
    """Formulario para unirse a una encuesta."""

    nombre = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Tu nombre',
            'autofocus': True
        })
    )


class AccesoEncuestaForm(forms.Form):
    """Formulario para acceder a una encuesta con código."""

    codigo = forms.CharField(
        max_length=6,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg text-center',
            'placeholder': 'CODIGO',
            'style': 'letter-spacing: 0.5em; text-transform: uppercase;',
            'maxlength': '6',
            'autofocus': True
        })
    )

    def clean_codigo(self):
        codigo = self.cleaned_data['codigo'].upper()
        if len(codigo) != 6:
            raise forms.ValidationError('El código debe tener 6 caracteres.')
        return codigo
