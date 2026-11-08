from django.contrib import admin
from .models import Evento, Inscripcion, Inscripto


class InscriptoInline(admin.TabularInline):
    model = Inscripto
    extra = 0
    raw_id_fields = ['hermano', 'alumno']


@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'fecha', 'precio_adulto', 'precio_nino', 'cupo', 'fecha_cierre', 'activo']
    prepopulated_fields = {'slug': ('nombre',)}


@admin.register(Inscripcion)
class InscripcionAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'celular', 'fecha', 'pagado']
    list_filter = ['evento', 'pagado']
    search_fields = ['personas__apellido', 'personas__nombre', 'celular']
    inlines = [InscriptoInline]
