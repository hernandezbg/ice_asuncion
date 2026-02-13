from django.urls import path
from . import views

app_name = 'encuestas'

urlpatterns = [
    # Vistas públicas (participantes)
    path('<str:codigo>/', views.acceso_encuesta, name='acceso'),
    path('participar/<uuid:session_id>/', views.participar, name='participar'),
    path('participar/<uuid:session_id>/responder/', views.responder, name='responder'),
    path('participar/<uuid:session_id>/poll/', views.poll_participante, name='poll_participante'),
    path('participar/<uuid:session_id>/resultado/', views.resultado_participante, name='resultado_participante'),

    # Vistas de panel (admin)
    path('panel/', views.panel_lista, name='panel_lista'),
    path('panel/crear/', views.panel_crear, name='panel_crear'),
    path('panel/<int:encuesta_id>/editar/', views.panel_editar, name='panel_editar'),
    path('panel/<int:encuesta_id>/eliminar/', views.panel_eliminar, name='panel_eliminar'),
    path('panel/<int:encuesta_id>/preguntas/', views.panel_preguntas, name='panel_preguntas'),
    path('panel/<int:encuesta_id>/preguntas/<int:pregunta_id>/eliminar/', views.panel_pregunta_eliminar, name='panel_pregunta_eliminar'),
    path('panel/<int:encuesta_id>/preguntas/<int:pregunta_id>/mover/', views.panel_pregunta_mover, name='panel_pregunta_mover'),
    path('panel/<int:encuesta_id>/activar/', views.panel_activar, name='panel_activar'),
    path('panel/<int:encuesta_id>/presentador/', views.panel_presentador, name='panel_presentador'),
    path('panel/<int:encuesta_id>/presentador/iniciar/', views.panel_iniciar, name='panel_iniciar'),
    path('panel/<int:encuesta_id>/presentador/siguiente/', views.panel_siguiente, name='panel_siguiente'),
    path('panel/<int:encuesta_id>/presentador/anterior/', views.panel_anterior, name='panel_anterior'),
    path('panel/<int:encuesta_id>/presentador/mostrar-resultados/', views.panel_mostrar_resultados, name='panel_mostrar_resultados'),
    path('panel/<int:encuesta_id>/presentador/finalizar/', views.panel_finalizar, name='panel_finalizar'),
    path('panel/<int:encuesta_id>/presentador/poll/', views.panel_poll, name='panel_poll'),
    path('panel/<int:encuesta_id>/reiniciar/', views.panel_reiniciar, name='panel_reiniciar'),
    path('panel/<int:encuesta_id>/resultados/', views.panel_resultados, name='panel_resultados'),
    path('panel/<int:encuesta_id>/exportar/', views.panel_exportar, name='panel_exportar'),
]
