from django import forms
from contenido.models import Noticia, Mensaje, Pagina, Seccion, Slider, Ofrenda, DatosIce
from miembros.models import Hermano


class HermanoForm(forms.ModelForm):
    """Formulario para crear/editar hermanos"""

    class Meta:
        model = Hermano
        fields = [
            'nombres', 'apellidos', 'sexo', 'cumpleaños',
            'domicilio', 'barrio', 'localidad', 'telefono_fijo', 'celular',
            'email', 'estado_civil', 'clase', 'grupo',
            'activo', 'observaciones'
        ]
        widgets = {
            'nombres': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'apellidos': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'sexo': forms.Select(attrs={'class': 'form-select'}),
            'cumpleaños': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'domicilio': forms.TextInput(attrs={'class': 'form-control'}),
            'barrio': forms.TextInput(attrs={'class': 'form-control'}),
            'localidad': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono_fijo': forms.TextInput(attrs={'class': 'form-control'}),
            'celular': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'estado_civil': forms.Select(attrs={'class': 'form-select'}),
            'clase': forms.Select(attrs={'class': 'form-select'}),
            'grupo': forms.Select(attrs={'class': 'form-select'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class NoticiaForm(forms.ModelForm):
    """Formulario para crear/editar noticias"""

    class Meta:
        model = Noticia
        fields = [
            'titulo', 'introduccion', 'contenido', 'tipo',
            'imagen_principal', 'imagen_secundaria', 'fecha_publicacion', 'activo'
        ]
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'introduccion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'contenido': forms.Textarea(attrs={'class': 'form-control summernote', 'rows': 10}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'imagen_principal': forms.FileInput(attrs={'class': 'form-control'}),
            'imagen_secundaria': forms.FileInput(attrs={'class': 'form-control'}),
            'fecha_publicacion': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hacer campos opcionales
        self.fields['imagen_principal'].required = False
        self.fields['imagen_secundaria'].required = False
        self.fields['introduccion'].required = False
        self.fields['contenido'].required = False


class MensajeForm(forms.ModelForm):
    """Formulario para crear/editar mensajes"""

    class Meta:
        model = Mensaje
        fields = [
            'titulo', 'autor', 'introduccion', 'contenido', 'tipo',
            'imagen', 'enlace_video', 'fecha_publicacion', 'activo'
        ]
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'autor': forms.TextInput(attrs={'class': 'form-control'}),
            'introduccion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'contenido': forms.Textarea(attrs={'class': 'form-control summernote', 'rows': 10}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'imagen': forms.FileInput(attrs={'class': 'form-control'}),
            'enlace_video': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://...'}),
            'fecha_publicacion': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class PaginaForm(forms.ModelForm):
    """Formulario para crear/editar páginas"""

    class Meta:
        model = Pagina
        fields = [
            'titulo', 'descripcion', 'contenido',
            'orden', 'activo'
        ]
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'descripcion': forms.TextInput(attrs={'class': 'form-control'}),
            'contenido': forms.Textarea(attrs={'class': 'form-control summernote', 'rows': 10}),
            'orden': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class SeccionForm(forms.ModelForm):
    """Formulario para crear/editar secciones de la homepage"""

    class Meta:
        model = Seccion
        fields = [
            'titulo', 'subtitulo', 'contenido', 'imagen', 'tipo',
            'estilo', 'orden', 'mostrar_en_home', 'activo'
        ]
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'subtitulo': forms.TextInput(attrs={'class': 'form-control'}),
            'contenido': forms.Textarea(attrs={'class': 'form-control summernote', 'rows': 10}),
            'imagen': forms.FileInput(attrs={'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'estilo': forms.Select(attrs={'class': 'form-select'}),
            'orden': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'mostrar_en_home': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class SliderForm(forms.ModelForm):
    """Formulario para crear/editar sliders del hero"""

    class Meta:
        model = Slider
        fields = [
            'titulo', 'descripcion', 'imagen', 'enlace',
            'orden', 'activo'
        ]
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control summernote', 'rows': 3}),
            'imagen': forms.FileInput(attrs={'class': 'form-control', 'required': True}),
            'enlace': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://...'}),
            'orden': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class OfrendaForm(forms.ModelForm):
    """Formulario para crear/editar información de ofrendas"""

    class Meta:
        model = Ofrenda
        fields = [
            'titulo', 'descripcion', 'banco', 'cuenta', 'titular',
            'mercadopago_link', 'mercadopago_alias', 'orden', 'activo'
        ]
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control summernote', 'rows': 3}),
            'banco': forms.TextInput(attrs={'class': 'form-control'}),
            'cuenta': forms.TextInput(attrs={'class': 'form-control'}),
            'titular': forms.TextInput(attrs={'class': 'form-control'}),
            'mercadopago_link': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://...'}),
            'mercadopago_alias': forms.TextInput(attrs={'class': 'form-control'}),
            'orden': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class DatosIceForm(forms.ModelForm):
    """Formulario para editar datos de contacto y redes sociales"""

    class Meta:
        model = DatosIce
        fields = [
            'email', 'direccion', 'telefono', 'whatsapp',
            'facebook', 'twitter', 'youtube', 'instagram',
            'stream_youtube', 'codigo_acceso_miembros'
        ]
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control', 'required': True}),
            'direccion': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'whatsapp': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 595981123456'}),
            'facebook': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://facebook.com/...'}),
            'twitter': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://twitter.com/...'}),
            'youtube': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://youtube.com/...'}),
            'instagram': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://instagram.com/...'}),
            'stream_youtube': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://youtube.com/live/...'}),
            'codigo_acceso_miembros': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: ICE2024'}),
        }
