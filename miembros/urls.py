from django.urls import path
from . import views

app_name = 'miembros'

urlpatterns = [
    path('actualizar-datos/', views.actualizar_datos_acceso, name='acceso'),
    path('actualizar-datos/buscar/', views.actualizar_datos_buscar, name='buscar'),
    path('actualizar-datos/editar/', views.actualizar_datos_editar, name='nuevo'),
    path('actualizar-datos/editar/<int:hermano_id>/', views.actualizar_datos_editar, name='editar'),
    path('actualizar-datos/exito/', views.actualizar_datos_exito, name='exito'),
    path('actualizar-datos/salir/', views.cerrar_sesion_miembros, name='salir'),
]
