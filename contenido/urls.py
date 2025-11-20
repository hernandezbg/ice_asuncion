from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('pagina/<int:pagina_id>/', views.pagina_detalle, name='pagina_detalle'),
    path('noticias/', views.noticias_lista, name='noticias'),
    path('noticia/<int:noticia_id>/', views.noticia_detalle, name='noticia_detalle'),
    path('noticia/<int:noticia_id>/vista/', views.noticia_vista, name='noticia_vista'),
    path('mensajes/', views.mensajes_lista, name='mensajes'),
    path('mensaje/<int:mensaje_id>/', views.mensaje_detalle, name='mensaje_detalle'),
    path('galeria/', views.galeria, name='galeria'),
    path('contacto/', views.contacto, name='contacto'),
]
