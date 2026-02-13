"""
URL configuration for ice_project
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('summernote/', include('django_summernote.urls')),
    path('panel/', include('panel.urls')),  # Panel de administración personalizado
    path('miembros/', include('miembros.urls')),  # Actualización de datos de miembros
    path('chat/', include('chat.urls')),  # Chat con agente IA
    path('encuestas/', include('encuestas.urls')),  # Encuestas en vivo tipo Kahoot
    path('', include('contenido.urls')),  # URLs del sitio público
]

# Sirvo archivos media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Personalizo el admin
admin.site.site_header = "ICE Asunción - Administración"
admin.site.site_title = "ICE Asunción"
admin.site.index_title = "Panel de Administración"
