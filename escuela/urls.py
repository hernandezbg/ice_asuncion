from django.urls import path
from . import views

app_name = 'escuela'

urlpatterns = [
    # Acceso de maestros
    path('', views.acceso, name='acceso'),
    path('alumnos/', views.lista_alumnos, name='lista_alumnos'),
    path('alumnos/nuevo/', views.alumno_crear, name='alumno_crear'),
    path('alumnos/<int:alumno_id>/editar/', views.alumno_editar, name='alumno_editar'),
    path('alumnos/<int:alumno_id>/eliminar/', views.alumno_eliminar, name='alumno_eliminar'),
    path('api/buscar-hermanos/', views.buscar_hermanos, name='buscar_hermanos'),
    path('api/asistencia-registrar/', views.asistencia_registrar, name='asistencia_registrar'),
    path('asistencia/', views.asistencia_inicio, name='asistencia_inicio'),
    path('asistencia/<str:fecha_str>/', views.asistencia_pasar, name='asistencia_pasar'),
    path('asistencia-historial/', views.asistencia_historial, name='asistencia_historial'),
    path('asistencia-detalle/<str:fecha_str>/', views.asistencia_detalle, name='asistencia_detalle'),
    path('salir/', views.cerrar_sesion, name='salir'),
]
