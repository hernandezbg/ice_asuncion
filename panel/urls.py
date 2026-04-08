from django.urls import path
from . import views

app_name = 'panel'

urlpatterns = [
    # Autenticación
    path('login/', views.panel_login, name='login'),
    path('logout/', views.panel_logout, name='logout'),
    path('cambiar-password/', views.cambiar_password, name='cambiar_password'),

    # Dashboard
    path('', views.dashboard, name='dashboard'),
    path('estadisticas/', views.estadisticas, name='estadisticas'),

    # Hermanos
    path('hermanos/', views.hermanos_lista, name='hermanos_lista'),
    path('hermanos/crear/', views.hermano_crear, name='hermano_crear'),
    path('hermanos/<int:pk>/datos/', views.hermano_datos, name='hermano_datos'),
    path('hermanos/<int:pk>/editar/', views.hermano_editar, name='hermano_editar'),
    path('hermanos/<int:pk>/eliminar/', views.hermano_eliminar, name='hermano_eliminar'),
    path('hermanos/<int:pk>/inactivar/', views.hermano_inactivar, name='hermano_inactivar'),

    # Noticias
    path('noticias/', views.noticias_lista, name='noticias_lista'),
    path('noticias/crear/', views.noticia_crear, name='noticia_crear'),
    path('noticias/<int:pk>/datos/', views.noticia_datos, name='noticia_datos'),
    path('noticias/<int:pk>/editar/', views.noticia_editar, name='noticia_editar'),
    path('noticias/<int:pk>/eliminar/', views.noticia_eliminar, name='noticia_eliminar'),
    path('noticias/<int:pk>/toggle/', views.noticia_toggle_activo, name='noticia_toggle'),

    # Mensajes
    path('mensajes/', views.mensajes_lista, name='mensajes_lista'),
    path('mensajes/crear/', views.mensaje_crear, name='mensaje_crear'),
    path('mensajes/<int:pk>/datos/', views.mensaje_datos, name='mensaje_datos'),
    path('mensajes/<int:pk>/editar/', views.mensaje_editar, name='mensaje_editar'),
    path('mensajes/<int:pk>/eliminar/', views.mensaje_eliminar, name='mensaje_eliminar'),
    path('mensajes/<int:pk>/toggle/', views.mensaje_toggle_activo, name='mensaje_toggle'),

    # Páginas
    path('paginas/', views.paginas_lista, name='paginas_lista'),
    path('paginas/crear/', views.pagina_crear, name='pagina_crear'),
    path('paginas/<int:pk>/datos/', views.pagina_datos, name='pagina_datos'),
    path('paginas/<int:pk>/editar/', views.pagina_editar, name='pagina_editar'),
    path('paginas/<int:pk>/toggle/', views.pagina_toggle_activo, name='pagina_toggle'),

    # Secciones
    path('secciones/', views.secciones_lista, name='secciones_lista'),
    path('secciones/crear/', views.seccion_crear, name='seccion_crear'),
    path('secciones/<int:pk>/datos/', views.seccion_datos, name='seccion_datos'),
    path('secciones/<int:pk>/editar/', views.seccion_editar, name='seccion_editar'),
    path('secciones/<int:pk>/eliminar/', views.seccion_eliminar, name='seccion_eliminar'),
    path('secciones/<int:pk>/toggle/', views.seccion_toggle_activo, name='seccion_toggle_activo'),

    # Sliders
    path('sliders/', views.sliders_lista, name='sliders_lista'),
    path('sliders/crear/', views.slider_crear, name='slider_crear'),
    path('sliders/<int:pk>/datos/', views.slider_datos, name='slider_datos'),
    path('sliders/<int:pk>/editar/', views.slider_editar, name='slider_editar'),
    path('sliders/<int:pk>/eliminar/', views.slider_eliminar, name='slider_eliminar'),
    path('sliders/<int:pk>/toggle/', views.slider_toggle_activo, name='slider_toggle_activo'),

    # Ofrendas
    path('ofrendas/', views.ofrendas_lista, name='ofrendas_lista'),
    path('ofrendas/crear/', views.ofrenda_crear, name='ofrenda_crear'),
    path('ofrendas/<int:pk>/datos/', views.ofrenda_datos, name='ofrenda_datos'),
    path('ofrendas/<int:pk>/editar/', views.ofrenda_editar, name='ofrenda_editar'),
    path('ofrendas/<int:pk>/eliminar/', views.ofrenda_eliminar, name='ofrenda_eliminar'),
    path('ofrendas/<int:pk>/toggle/', views.ofrenda_toggle_activo, name='ofrenda_toggle_activo'),

    # Configuración (DatosICE)
    path('configuracion/', views.datosice_editar, name='datosice_editar'),

    # Escuela Biblica
    path('escuela/', views.escuela_alumnos_lista, name='escuela_alumnos'),
    path('escuela/clases/', views.escuela_clases_lista, name='escuela_clases'),
    path('escuela/clases/<int:pk>/codigo/', views.escuela_clase_actualizar_codigo, name='escuela_clase_codigo'),
    path('escuela/asistencia/', views.escuela_asistencia_dashboard, name='escuela_asistencia'),
]
