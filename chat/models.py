from django.db import models
import uuid
from django.utils import timezone
from datetime import timedelta


class PhoneVerification(models.Model):
    """
    Modelo para almacenar códigos de verificación de teléfono
    """
    phone = models.CharField(max_length=20, verbose_name='Teléfono')
    code = models.CharField(max_length=6, verbose_name='Código')
    verified = models.BooleanField(default=False, verbose_name='Verificado')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Creado')
    expires_at = models.DateTimeField(verbose_name='Expira')
    attempts = models.IntegerField(default=0, verbose_name='Intentos')

    class Meta:
        verbose_name = 'Verificación de Teléfono'
        verbose_name_plural = 'Verificaciones de Teléfono'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.expires_at:
            # El código expira en 10 minutos
            self.expires_at = timezone.now() + timedelta(minutes=10)
        super().save(*args, **kwargs)

    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"{self.phone} - {'Verificado' if self.verified else 'Pendiente'}"


class ICEChatSession(models.Model):
    """
    Modelo para almacenar sesiones de chat
    """
    session_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    phone = models.CharField(max_length=20, verbose_name='Teléfono')
    agent_thread_id = models.CharField(max_length=100, blank=True, verbose_name='ID Thread del Agente')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Creado')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Actualizado')
    is_active = models.BooleanField(default=True, verbose_name='Activo')

    class Meta:
        verbose_name = 'Sesión de Chat'
        verbose_name_plural = 'Sesiones de Chat'
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['session_id']),
            models.Index(fields=['phone']),
        ]

    def __str__(self):
        return f"Sesión {self.session_id} - {self.phone}"


class ICEChatMessage(models.Model):
    """
    Modelo para almacenar mensajes del chat
    """
    ROLE_CHOICES = [
        ('user', 'Usuario'),
        ('assistant', 'Asistente'),
    ]

    MESSAGE_TYPE_CHOICES = [
        ('text', 'Texto'),
        ('audio', 'Audio'),
    ]

    session = models.ForeignKey(
        ICEChatSession,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name='Sesión'
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, verbose_name='Rol')
    message_type = models.CharField(
        max_length=10,
        choices=MESSAGE_TYPE_CHOICES,
        default='text',
        verbose_name='Tipo'
    )
    content = models.TextField(verbose_name='Contenido')
    audio_url = models.URLField(blank=True, verbose_name='URL del Audio')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Creado')

    class Meta:
        verbose_name = 'Mensaje de Chat'
        verbose_name_plural = 'Mensajes de Chat'
        ordering = ['created_at']

    def __str__(self):
        return f"{self.get_role_display()}: {self.content[:50]}..."
