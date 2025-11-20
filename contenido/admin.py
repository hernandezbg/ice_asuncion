from django.contrib import admin
from django_summernote.admin import SummernoteModelAdmin
from .models import Pagina, Slider, Breve, Noticia, Galeria, Mensaje, DatosIce, Seccion, Ofrenda


@admin.register(Pagina)
class PaginaAdmin(SummernoteModelAdmin):
    """
    Admin para páginas estáticas
    """
    list_display = ['titulo', 'orden', 'activo', 'fecha_modificacion']
    list_filter = ['activo', 'fecha_creacion']
    search_fields = ['titulo', 'descripcion', 'contenido']
    list_editable = ['orden', 'activo']
    summernote_fields = ('contenido',)

    fieldsets = (
        ('Información General', {
            'fields': ('titulo', 'descripcion', 'orden')
        }),
        ('Contenido', {
            'fields': ('contenido', 'imagen')
        }),
        ('Estado', {
            'fields': ('activo',),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        # Asigno el usuario actual si es nuevo
        if not change:
            obj.usuario = request.user
        super().save_model(request, obj, form, change)


@admin.register(Slider)
class SliderAdmin(admin.ModelAdmin):
    """
    Admin para sliders del inicio
    """
    list_display = ['titulo', 'orden', 'activo', 'fecha_modificacion']
    list_filter = ['activo', 'fecha_creacion']
    search_fields = ['titulo', 'descripcion']
    list_editable = ['orden', 'activo']

    fieldsets = (
        ('Información General', {
            'fields': ('titulo', 'descripcion', 'orden')
        }),
        ('Imagen y Enlaces', {
            'fields': ('imagen', 'enlace', 'pagina'),
            'description': 'Puede enlazar a una URL externa o a una página interna del sitio'
        }),
        ('Estado', {
            'fields': ('activo',),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.usuario = request.user
        super().save_model(request, obj, form, change)


@admin.register(Breve)
class BreveAdmin(SummernoteModelAdmin):
    """
    Admin para breves/cards informativos
    """
    list_display = ['titulo', 'orden', 'activo', 'fecha_modificacion']
    list_filter = ['activo', 'fecha_creacion']
    search_fields = ['titulo', 'descripcion']
    list_editable = ['orden', 'activo']
    summernote_fields = ('descripcion',)

    fieldsets = (
        ('Información General', {
            'fields': ('titulo', 'orden')
        }),
        ('Contenido', {
            'fields': ('descripcion', 'imagen', 'icono', 'enlace')
        }),
        ('Estado', {
            'fields': ('activo',),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.usuario = request.user
        super().save_model(request, obj, form, change)


@admin.register(Noticia)
class NoticiaAdmin(SummernoteModelAdmin):
    """
    Admin para noticias y boletines
    """
    list_display = ['titulo', 'tipo', 'fecha_publicacion', 'activo', 'fecha_modificacion']
    list_filter = ['tipo', 'activo', 'fecha_publicacion']
    search_fields = ['titulo', 'introduccion', 'contenido']
    list_editable = ['activo']
    date_hierarchy = 'fecha_publicacion'
    summernote_fields = ('introduccion', 'contenido')

    fieldsets = (
        ('Información General', {
            'fields': ('tipo', 'titulo', 'fecha_publicacion')
        }),
        ('Contenido', {
            'fields': ('introduccion', 'contenido')
        }),
        ('Imágenes', {
            'fields': ('imagen_principal', 'imagen_secundaria')
        }),
        ('Estado', {
            'fields': ('activo',),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.usuario = request.user
        super().save_model(request, obj, form, change)


@admin.register(Galeria)
class GaleriaAdmin(admin.ModelAdmin):
    """
    Admin para galería de imágenes
    """
    list_display = ['titulo', 'orden', 'activo', 'fecha_creacion']
    list_filter = ['activo', 'fecha_creacion']
    search_fields = ['titulo', 'descripcion']
    list_editable = ['orden', 'activo']

    fieldsets = (
        ('Información General', {
            'fields': ('titulo', 'descripcion', 'orden')
        }),
        ('Imagen', {
            'fields': ('imagen',)
        }),
        ('Estado', {
            'fields': ('activo',),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.usuario = request.user
        super().save_model(request, obj, form, change)


@admin.register(Mensaje)
class MensajeAdmin(SummernoteModelAdmin):
    """
    Admin para mensajes predicados y videos
    """
    list_display = ['titulo', 'tipo', 'autor', 'fecha_publicacion', 'activo']
    list_filter = ['tipo', 'activo', 'fecha_publicacion', 'autor']
    search_fields = ['titulo', 'autor', 'introduccion', 'contenido']
    list_editable = ['activo']
    date_hierarchy = 'fecha_publicacion'
    summernote_fields = ('introduccion', 'contenido')

    fieldsets = (
        ('Información General', {
            'fields': ('tipo', 'titulo', 'autor', 'fecha_publicacion')
        }),
        ('Contenido', {
            'fields': ('introduccion', 'contenido', 'imagen'),
            'description': 'El contenido completo es solo para mensajes escritos'
        }),
        ('Video', {
            'fields': ('enlace_video',),
            'description': 'URL de YouTube o Vimeo (solo para tipo Video)'
        }),
        ('Estado', {
            'fields': ('activo',),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.usuario = request.user
        super().save_model(request, obj, form, change)


@admin.register(DatosIce)
class DatosIceAdmin(admin.ModelAdmin):
    """
    Admin para datos centrales de ICE (singleton)
    """
    fieldsets = (
        ('Información de Contacto', {
            'fields': ('email', 'telefono', 'direccion')
        }),
        ('Redes Sociales', {
            'fields': ('facebook', 'twitter', 'youtube', 'instagram')
        }),
        ('Transmisiones', {
            'fields': ('stream_youtube',)
        }),
    )

    def has_add_permission(self, request):
        # Solo permito un registro
        return not DatosIce.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # No permito eliminar el único registro
        return False

    def save_model(self, request, obj, form, change):
        if not change:
            obj.usuario = request.user
        super().save_model(request, obj, form, change)


@admin.register(Seccion)
class SeccionAdmin(SummernoteModelAdmin):
    """
    Admin para secciones flexibles de la homepage
    """
    list_display = ['titulo', 'tipo', 'estilo', 'orden', 'mostrar_en_home', 'activo']
    list_filter = ['tipo', 'estilo', 'mostrar_en_home', 'activo']
    search_fields = ['titulo', 'subtitulo', 'contenido']
    list_editable = ['orden', 'mostrar_en_home', 'activo']
    summernote_fields = ('contenido',)

    fieldsets = (
        ('Información General', {
            'fields': ('titulo', 'subtitulo', 'orden')
        }),
        ('Contenido', {
            'fields': ('contenido', 'imagen', 'tipo')
        }),
        ('Diseño', {
            'fields': ('estilo', 'mostrar_en_home')
        }),
        ('Estado', {
            'fields': ('activo',),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.usuario = request.user
        super().save_model(request, obj, form, change)


@admin.register(Ofrenda)
class OfrendaAdmin(SummernoteModelAdmin):
    """
    Admin para información de ofrendas y donaciones
    """
    list_display = ['titulo', 'banco', 'orden', 'activo']
    list_filter = ['activo']
    search_fields = ['titulo', 'descripcion', 'banco']
    list_editable = ['orden', 'activo']
    summernote_fields = ('descripcion',)

    fieldsets = (
        ('Información General', {
            'fields': ('titulo', 'descripcion', 'orden')
        }),
        ('Datos Bancarios', {
            'fields': ('banco', 'cuenta', 'titular')
        }),
        ('Mercado Pago', {
            'fields': ('mercadopago_link', 'mercadopago_alias')
        }),
        ('Estado', {
            'fields': ('activo',),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.usuario = request.user
        super().save_model(request, obj, form, change)
