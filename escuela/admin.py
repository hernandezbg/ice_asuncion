from django.contrib import admin
from .models import ClaseEscuela, Alumno, Asistencia


@admin.register(ClaseEscuela)
class ClaseEscuelaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'rango_edad', 'maestros', 'codigo_acceso', 'activo')
    list_filter = ('activo',)
    ordering = ('orden', 'edad_desde')


@admin.register(Alumno)
class AlumnoAdmin(admin.ModelAdmin):
    list_display = ('apellidos', 'nombres', 'clase', 'edad', 'grado_nivel', 'activo')
    list_filter = ('clase', 'activo', 'grado_nivel')
    search_fields = ('apellidos', 'nombres')
    ordering = ('apellidos', 'nombres')


@admin.register(Asistencia)
class AsistenciaAdmin(admin.ModelAdmin):
    list_display = ('alumno', 'clase', 'fecha', 'presente')
    list_filter = ('clase', 'fecha', 'presente')
    ordering = ('-fecha', 'alumno__apellidos')
