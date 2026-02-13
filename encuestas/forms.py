from django import forms
from .models import Encuesta, Pregunta


class EncuestaForm(forms.ModelForm):
    """Formulario para crear/editar encuestas."""

    class Meta:
        model = Encuesta
        fields = ['titulo', 'descripcion', 'tipo', 'puntos_base', 'bonus_tiempo',
                  'tiempo_limite', 'rango_excelente', 'rango_bueno', 'rango_regular', 'rango_bajo']
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
            'tipo': forms.Select(attrs={
                'class': 'form-select',
                'id': 'tipo-encuesta'
            }),
            'puntos_base': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 10,
                'max': 1000
            }),
            'bonus_tiempo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'tiempo_limite': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 5,
                'max': 120
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


class PreguntaOpinionForm(forms.ModelForm):
    """Formulario para preguntas de tipo opinión (escala 1-5)."""

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


class PreguntaTriviaForm(forms.ModelForm):
    """Formulario para preguntas de tipo trivia (con respuesta correcta)."""

    class Meta:
        model = Pregunta
        fields = ['texto', 'imagen_url', 'opcion_a', 'opcion_b', 'opcion_c', 'opcion_d',
                  'respuesta_correcta', 'tiempo_limite_custom']
        widgets = {
            'texto': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': '¿Cuál es la pregunta?'
            }),
            'imagen_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://ejemplo.com/imagen.jpg (opcional)'
            }),
            'opcion_a': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Opción A'
            }),
            'opcion_b': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Opción B'
            }),
            'opcion_c': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Opción C (opcional)'
            }),
            'opcion_d': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Opción D (opcional)'
            }),
            'respuesta_correcta': forms.Select(attrs={
                'class': 'form-select'
            }),
            'tiempo_limite_custom': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Usar tiempo general',
                'min': 5,
                'max': 120
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        opcion_a = cleaned_data.get('opcion_a')
        opcion_b = cleaned_data.get('opcion_b')
        respuesta = cleaned_data.get('respuesta_correcta')

        if not opcion_a or not opcion_b:
            raise forms.ValidationError('Debes proporcionar al menos las opciones A y B.')

        if respuesta:
            # Verificar que la respuesta correcta tenga una opción válida
            if respuesta == 'A' and not opcion_a:
                raise forms.ValidationError('La opción A está vacía pero es la respuesta correcta.')
            if respuesta == 'B' and not opcion_b:
                raise forms.ValidationError('La opción B está vacía pero es la respuesta correcta.')
            if respuesta == 'C' and not cleaned_data.get('opcion_c'):
                raise forms.ValidationError('La opción C está vacía pero es la respuesta correcta.')
            if respuesta == 'D' and not cleaned_data.get('opcion_d'):
                raise forms.ValidationError('La opción D está vacía pero es la respuesta correcta.')

        return cleaned_data


class PreguntaVotacionForm(forms.ModelForm):
    """Formulario para preguntas de tipo votación (sin respuesta correcta)."""

    class Meta:
        model = Pregunta
        fields = ['texto', 'imagen_url', 'opcion_a', 'opcion_b', 'opcion_c', 'opcion_d']
        widgets = {
            'texto': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': '¿Cuál es tu preferencia?'
            }),
            'imagen_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://ejemplo.com/imagen.jpg (opcional)'
            }),
            'opcion_a': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Opción A'
            }),
            'opcion_b': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Opción B'
            }),
            'opcion_c': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Opción C (opcional)'
            }),
            'opcion_d': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Opción D (opcional)'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        opcion_a = cleaned_data.get('opcion_a')
        opcion_b = cleaned_data.get('opcion_b')

        if not opcion_a or not opcion_b:
            raise forms.ValidationError('Debes proporcionar al menos las opciones A y B.')

        return cleaned_data


# Mantener compatibilidad con el nombre anterior
PreguntaForm = PreguntaOpinionForm


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
