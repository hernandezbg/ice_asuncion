from django.urls import path
from . import views

app_name = 'eventos'

urlpatterns = [
    # Panel (staff) - primero para que no los capture <slug>
    path('panel/', views.panel_lista, name='panel_lista'),
    path('panel/nuevo/', views.panel_form, name='panel_crear'),
    path('panel/<int:pk>/', views.panel_detalle, name='panel_detalle'),
    path('panel/<int:pk>/editar/', views.panel_form, name='panel_editar'),
    path('panel/<int:pk>/exportar/', views.panel_exportar, name='panel_exportar'),
    path('panel/inscripcion/<int:pk>/pagado/', views.panel_inscripcion_pagado, name='panel_inscripcion_pagado'),
    path('panel/inscripcion/<int:pk>/eliminar/', views.panel_inscripcion_eliminar, name='panel_inscripcion_eliminar'),

    # Publico
    path('<slug:slug>/', views.inscripcion_form, name='inscripcion'),
    path('<slug:slug>/listo/', views.inscripcion_exito, name='exito'),
    path('<slug:slug>/buscar/', views.buscar_personas, name='buscar'),
]
