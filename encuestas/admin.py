from django.contrib import admin
from .models import Encuesta, Pregunta, Participante, Respuesta


class PreguntaInline(admin.TabularInline):
    model = Pregunta
    extra = 1
    ordering = ['orden']


@admin.register(Encuesta)
class EncuestaAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'codigo', 'estado', 'total_preguntas', 'total_participantes', 'creado']
    list_filter = ['estado', 'creado']
    search_fields = ['titulo', 'codigo']
    readonly_fields = ['codigo', 'creado', 'modificado']
    inlines = [PreguntaInline]


@admin.register(Pregunta)
class PreguntaAdmin(admin.ModelAdmin):
    list_display = ['texto', 'encuesta', 'orden']
    list_filter = ['encuesta']
    ordering = ['encuesta', 'orden']


@admin.register(Participante)
class ParticipanteAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'encuesta', 'respuestas_completadas', 'creado']
    list_filter = ['encuesta', 'creado']
    search_fields = ['nombre']
    readonly_fields = ['session_id', 'creado']


@admin.register(Respuesta)
class RespuestaAdmin(admin.ModelAdmin):
    list_display = ['participante', 'pregunta', 'valor', 'creado']
    list_filter = ['pregunta__encuesta', 'valor', 'creado']
    readonly_fields = ['creado']
