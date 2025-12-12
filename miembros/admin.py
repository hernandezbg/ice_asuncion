from django.contrib import admin
from .models import Provincia, EstadoCivil, Clase, Grupo, Don, Hermano


@admin.register(Provincia)
class ProvinciaAdmin(admin.ModelAdmin):
    """
    Admin para provincias
    """
    list_display = ['nombre']
    search_fields = ['nombre']


@admin.register(EstadoCivil)
class EstadoCivilAdmin(admin.ModelAdmin):
    """
    Admin para estados civiles
    """
    list_display = ['nombre']
    search_fields = ['nombre']


@admin.register(Clase)
class ClaseAdmin(admin.ModelAdmin):
    """
    Admin para clases de miembros
    """
    list_display = ['nombre', 'descripcion']
    search_fields = ['nombre', 'descripcion']


@admin.register(Grupo)
class GrupoAdmin(admin.ModelAdmin):
    """
    Admin para grupos
    """
    list_display = ['nombre', 'descripcion']
    search_fields = ['nombre', 'descripcion']


@admin.register(Don)
class DonAdmin(admin.ModelAdmin):
    """
    Admin para dones espirituales
    """
    list_display = ['nombre', 'descripcion', 'icono']
    search_fields = ['nombre', 'descripcion']


@admin.register(Hermano)
class HermanoAdmin(admin.ModelAdmin):
    """
    Admin para hermanos/miembros
    """
    list_display = ['apellidos', 'nombres', 'sexo', 'celular', 'email', 'grupo', 'clase', 'activo']
    list_filter = ['sexo', 'activo', 'estado_civil', 'grupo', 'clase', 'provincia', 'dones']
    search_fields = ['apellidos', 'apellido_soltera', 'nombres', 'email', 'celular', 'domicilio', 'ocupacion']
    list_editable = ['activo']
    date_hierarchy = 'fecha_nacimiento'
    filter_horizontal = ['dones']

    fieldsets = (
        ('Datos Personales', {
            'fields': ('foto', 'apellidos', 'apellido_soltera', 'nombres', 'sexo',
                      'fecha_nacimiento', 'cumpleaños', 'estado_civil', 'ocupacion')
        }),
        ('Datos de Contacto', {
            'fields': ('telefono_fijo', 'celular', 'email')
        }),
        ('Ubicación', {
            'fields': ('provincia', 'localidad', 'domicilio', 'barrio')
        }),
        ('Clasificación Espiritual', {
            'fields': ('grupo', 'clase', 'anio_bautismo', 'dones', 'marca_1', 'marca_2', 'marca_3')
        }),
        ('Observaciones', {
            'fields': ('observaciones',),
            'classes': ('collapse',)
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
