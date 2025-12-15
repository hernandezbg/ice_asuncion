from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    # API endpoints
    path('api/send-code/', views.send_verification_code, name='send_code'),
    path('api/verify-code/', views.verify_code, name='verify_code'),
    path('api/send-message/', views.send_message, name='send_message'),
    path('api/send-audio/', views.send_audio, name='send_audio'),
    path('api/history/<uuid:session_id>/', views.get_history, name='get_history'),
]
