from django.db import models
from django.contrib.auth.models import User


class Visita(models.Model):
    """
    Modelo para rastrear visitas al sitio
    """
    fecha = models.DateTimeField(auto_now_add=True, verbose_name='Fecha y hora')
    ip = models.GenericIPAddressField(verbose_name='Dirección IP')
    user_agent = models.TextField(verbose_name='User Agent')
    navegador = models.CharField(max_length=100, blank=True, verbose_name='Navegador')
    sistema_operativo = models.CharField(max_length=100, blank=True, verbose_name='Sistema Operativo')
    dispositivo = models.CharField(max_length=50, blank=True, verbose_name='Dispositivo')  # mobile, tablet, pc
    pais = models.CharField(max_length=100, blank=True, verbose_name='País')
    ciudad = models.CharField(max_length=100, blank=True, verbose_name='Ciudad')
    url = models.CharField(max_length=500, verbose_name='URL visitada')
    referrer = models.CharField(max_length=500, blank=True, verbose_name='Referencia')

    class Meta:
        verbose_name = 'Visita'
        verbose_name_plural = 'Visitas'
        ordering = ['-fecha']
        indexes = [
            models.Index(fields=['-fecha']),
            models.Index(fields=['ip']),
        ]

    def __str__(self):
        return f"{self.ip} - {self.fecha.strftime('%Y-%m-%d %H:%M')}"
