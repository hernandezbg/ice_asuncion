"""
URL configuration for ice_project
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from escuela import views as escuela_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('summernote/', include('django_summernote.urls')),
    path('panel/', include('panel.urls')),  # Panel de administración personalizado
    path('miembros/', include('miembros.urls')),  # Actualización de datos de miembros
    path('chat/', include('chat.urls')),  # Chat con agente IA
    path('e/', include('encuestas.urls')),  # Encuestas en vivo (URL corta)
    path('escuela/', include('escuela.urls')),  # Escuela Biblica
    # URLs cortas de proyeccion (publico)
    path('p/<str:codigo>/', escuela_views.proyeccion_ver, name='proyeccion_ver'),
    path('p/<str:codigo>/stream/', escuela_views.proyeccion_stream, name='proyeccion_stream'),
    path('p/<str:codigo>/estado/', escuela_views.proyeccion_estado, name='proyeccion_estado'),
    path('p/<str:codigo>/pdf/', escuela_views.proyeccion_pdf, name='proyeccion_pdf'),
    path('', include('contenido.urls')),  # URLs del sitio público
]

# Sirvo archivos media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Personalizo el admin
admin.site.site_header = "ICE Asunción - Administración"
admin.site.site_title = "ICE Asunción"
admin.site.index_title = "Panel de Administración"
