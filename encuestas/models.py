import uuid
import random
import string
from django.db import models
from django.utils import timezone


def generar_codigo():
    """Genera un código único de 6 caracteres alfanuméricos (mayúsculas)."""
    while True:
        codigo = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        if not Encuesta.objects.filter(codigo=codigo).exists():
            return codigo


class Encuesta(models.Model):
    """Modelo principal de encuesta."""

    ESTADO_CHOICES = [
        ('borrador', 'Borrador'),
        ('activa', 'Activa'),
        ('en_vivo', 'En Vivo'),
        ('finalizada', 'Finalizada'),
    ]

    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    codigo = models.CharField(max_length=6, unique=True, default=generar_codigo)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='borrador')

    # Control en vivo
    pregunta_actual = models.PositiveIntegerField(default=0)
    mostrar_resultados = models.BooleanField(default=False)

    # Rangos de interpretación (porcentajes)
    rango_excelente = models.PositiveIntegerField(default=85, help_text="Porcentaje mínimo para 'Excelente'")
    rango_bueno = models.PositiveIntegerField(default=70, help_text="Porcentaje mínimo para 'Bueno'")
    rango_regular = models.PositiveIntegerField(default=55, help_text="Porcentaje mínimo para 'Regular'")
    rango_bajo = models.PositiveIntegerField(default=40, help_text="Porcentaje mínimo para 'Bajo'")

    # Timestamps
    creado = models.DateTimeField(auto_now_add=True)
    modificado = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-creado']
        verbose_name = 'Encuesta'
        verbose_name_plural = 'Encuestas'

    def __str__(self):
        return f"{self.titulo} ({self.codigo})"

    def total_preguntas(self):
        return self.preguntas.count()

    def total_participantes(self):
        return self.participantes.count()

    def participantes_conectados(self):
        """Participantes activos en los últimos 30 segundos."""
        limite = timezone.now() - timezone.timedelta(seconds=30)
        return self.participantes.filter(ultima_actividad__gte=limite).count()

    def pregunta_actual_obj(self):
        """Retorna el objeto de la pregunta actual."""
        preguntas = list(self.preguntas.order_by('orden'))
        if 0 <= self.pregunta_actual < len(preguntas):
            return preguntas[self.pregunta_actual]
        return None

    def interpretar_porcentaje(self, porcentaje):
        """Interpreta un porcentaje según los rangos configurados."""
        if porcentaje >= self.rango_excelente:
            return {'nivel': 'Excelente', 'color': 'success', 'icono': 'star-fill'}
        elif porcentaje >= self.rango_bueno:
            return {'nivel': 'Bueno', 'color': 'primary', 'icono': 'hand-thumbs-up-fill'}
        elif porcentaje >= self.rango_regular:
            return {'nivel': 'Regular', 'color': 'warning', 'icono': 'dash-circle-fill'}
        elif porcentaje >= self.rango_bajo:
            return {'nivel': 'Bajo', 'color': 'orange', 'icono': 'exclamation-triangle-fill'}
        else:
            return {'nivel': 'Crítico', 'color': 'danger', 'icono': 'x-circle-fill'}


class Pregunta(models.Model):
    """Pregunta de una encuesta con escala 1-5."""

    encuesta = models.ForeignKey(Encuesta, on_delete=models.CASCADE, related_name='preguntas')
    texto = models.CharField(max_length=500)
    orden = models.PositiveIntegerField(default=0)

    # Etiquetas personalizables para escala 1-5
    etiqueta_1 = models.CharField(max_length=100, default="Todavía no hemos pensado en eso")
    etiqueta_2 = models.CharField(max_length=100, default="Apenas comenzando")
    etiqueta_3 = models.CharField(max_length=100, default="En progreso")
    etiqueta_4 = models.CharField(max_length=100, default="Bien encaminados")
    etiqueta_5 = models.CharField(max_length=100, default="En excelente forma")

    class Meta:
        ordering = ['orden']
        verbose_name = 'Pregunta'
        verbose_name_plural = 'Preguntas'

    def __str__(self):
        return f"{self.orden + 1}. {self.texto[:50]}"

    def get_etiqueta(self, valor):
        """Retorna la etiqueta para un valor dado."""
        etiquetas = {
            1: self.etiqueta_1,
            2: self.etiqueta_2,
            3: self.etiqueta_3,
            4: self.etiqueta_4,
            5: self.etiqueta_5,
        }
        return etiquetas.get(valor, '')

    def estadisticas(self):
        """Calcula estadísticas de respuestas para esta pregunta."""
        respuestas = self.respuestas.all()
        total = respuestas.count()

        if total == 0:
            return {
                'total': 0,
                'promedio': 0,
                'porcentaje': 0,
                'distribucion': {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            }

        suma = sum(r.valor for r in respuestas)
        promedio = suma / total
        # Porcentaje: (promedio - 1) / 4 * 100 para escala 1-5
        porcentaje = ((promedio - 1) / 4) * 100

        # Distribución
        distribucion = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for r in respuestas:
            distribucion[r.valor] += 1

        return {
            'total': total,
            'promedio': round(promedio, 2),
            'porcentaje': round(porcentaje, 1),
            'distribucion': distribucion
        }


class Participante(models.Model):
    """Participante de una encuesta."""

    encuesta = models.ForeignKey(Encuesta, on_delete=models.CASCADE, related_name='participantes')
    nombre = models.CharField(max_length=100)
    session_id = models.UUIDField(default=uuid.uuid4, unique=True)

    # Estado del participante
    pregunta_actual = models.PositiveIntegerField(default=0)
    conectado = models.BooleanField(default=True)
    ultima_actividad = models.DateTimeField(auto_now=True)

    # Timestamps
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['creado']
        verbose_name = 'Participante'
        verbose_name_plural = 'Participantes'

    def __str__(self):
        return f"{self.nombre} - {self.encuesta.titulo}"

    def respuestas_completadas(self):
        return self.respuestas.count()

    def ha_respondido_pregunta(self, pregunta):
        return self.respuestas.filter(pregunta=pregunta).exists()

    def calcular_resultado_final(self):
        """Calcula el resultado final del participante."""
        respuestas = self.respuestas.all()
        total = respuestas.count()

        if total == 0:
            return {'promedio': 0, 'porcentaje': 0}

        suma = sum(r.valor for r in respuestas)
        promedio = suma / total
        porcentaje = ((promedio - 1) / 4) * 100

        return {
            'promedio': round(promedio, 2),
            'porcentaje': round(porcentaje, 1)
        }


class Respuesta(models.Model):
    """Respuesta de un participante a una pregunta."""

    participante = models.ForeignKey(Participante, on_delete=models.CASCADE, related_name='respuestas')
    pregunta = models.ForeignKey(Pregunta, on_delete=models.CASCADE, related_name='respuestas')
    valor = models.PositiveSmallIntegerField(choices=[(i, str(i)) for i in range(1, 6)])

    # Timestamp
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['participante', 'pregunta']
        ordering = ['creado']
        verbose_name = 'Respuesta'
        verbose_name_plural = 'Respuestas'

    def __str__(self):
        return f"{self.participante.nombre} - P{self.pregunta.orden + 1}: {self.valor}"
