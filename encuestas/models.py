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

    TIPO_CHOICES = [
        ('opinion', 'Encuesta de Opinión'),
        ('trivia', 'Trivia/Quiz con Puntos'),
        ('votacion', 'Votación/Ranking'),
    ]

    ESTADO_CHOICES = [
        ('borrador', 'Borrador'),
        ('activa', 'Activa'),
        ('en_vivo', 'En Vivo'),
        ('finalizada', 'Finalizada'),
    ]

    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    codigo = models.CharField(max_length=6, unique=True, default=generar_codigo)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='opinion')
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='borrador')

    # Control en vivo
    pregunta_actual = models.PositiveIntegerField(default=0)
    mostrar_resultados = models.BooleanField(default=False)

    # Configuración para Trivia
    puntos_base = models.PositiveIntegerField(default=100, help_text="Puntos por respuesta correcta")
    bonus_tiempo = models.BooleanField(default=True, help_text="Bonus por responder rápido")
    tiempo_limite = models.PositiveIntegerField(default=30, help_text="Segundos para responder (trivia)")

    # Rangos de interpretación (para tipo opinion)
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

    def ranking_participantes(self):
        """Retorna ranking de participantes ordenado por puntos (para trivia)."""
        return self.participantes.order_by('-puntos_totales', 'nombre')

    def ranking_opciones_pregunta(self, pregunta):
        """Retorna ranking de opciones más votadas para una pregunta (para votacion)."""
        from django.db.models import Count
        return Respuesta.objects.filter(pregunta=pregunta).values(
            'opcion_elegida'
        ).annotate(
            total_votos=Count('id')
        ).order_by('-total_votos')


class Pregunta(models.Model):
    """Pregunta de una encuesta - soporta los 3 tipos."""

    encuesta = models.ForeignKey(Encuesta, on_delete=models.CASCADE, related_name='preguntas')
    texto = models.CharField(max_length=500)
    orden = models.PositiveIntegerField(default=0)

    # Imagen opcional para la pregunta
    imagen_url = models.URLField(blank=True, help_text="URL de imagen para la pregunta")

    # Para tipo OPINION: Etiquetas de escala 1-5
    etiqueta_1 = models.CharField(max_length=100, default="Todavía no hemos pensado en eso")
    etiqueta_2 = models.CharField(max_length=100, default="Apenas comenzando")
    etiqueta_3 = models.CharField(max_length=100, default="En progreso")
    etiqueta_4 = models.CharField(max_length=100, default="Bien encaminados")
    etiqueta_5 = models.CharField(max_length=100, default="En excelente forma")

    # Para tipo TRIVIA y VOTACION: Opciones múltiples
    opcion_a = models.CharField(max_length=200, blank=True)
    opcion_b = models.CharField(max_length=200, blank=True)
    opcion_c = models.CharField(max_length=200, blank=True)
    opcion_d = models.CharField(max_length=200, blank=True)

    # Para tipo TRIVIA: Respuesta correcta
    RESPUESTA_CHOICES = [
        ('A', 'Opción A'),
        ('B', 'Opción B'),
        ('C', 'Opción C'),
        ('D', 'Opción D'),
    ]
    respuesta_correcta = models.CharField(max_length=1, choices=RESPUESTA_CHOICES, blank=True)

    # Tiempo límite específico para esta pregunta (override del general)
    tiempo_limite_custom = models.PositiveIntegerField(null=True, blank=True, help_text="Segundos (deja vacío para usar el general)")

    # Timestamp de cuando se activó la pregunta (para calcular bonus tiempo)
    activada_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['orden']
        verbose_name = 'Pregunta'
        verbose_name_plural = 'Preguntas'

    def __str__(self):
        return f"{self.orden + 1}. {self.texto[:50]}"

    def get_tiempo_limite(self):
        """Retorna el tiempo límite para esta pregunta."""
        if self.tiempo_limite_custom:
            return self.tiempo_limite_custom
        return self.encuesta.tiempo_limite

    def get_opciones(self):
        """Retorna lista de opciones disponibles."""
        opciones = []
        if self.opcion_a:
            opciones.append({'letra': 'A', 'texto': self.opcion_a})
        if self.opcion_b:
            opciones.append({'letra': 'B', 'texto': self.opcion_b})
        if self.opcion_c:
            opciones.append({'letra': 'C', 'texto': self.opcion_c})
        if self.opcion_d:
            opciones.append({'letra': 'D', 'texto': self.opcion_d})
        return opciones

    def get_etiqueta(self, valor):
        """Retorna la etiqueta para un valor dado (tipo opinion)."""
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

        if self.encuesta.tipo == 'opinion':
            # Estadísticas para encuesta de opinión
            if total == 0:
                return {
                    'total': 0,
                    'promedio': 0,
                    'porcentaje': 0,
                    'distribucion': {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
                }

            suma = sum(r.valor for r in respuestas if r.valor)
            promedio = suma / total
            porcentaje = ((promedio - 1) / 4) * 100

            distribucion = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            for r in respuestas:
                if r.valor:
                    distribucion[r.valor] += 1

            return {
                'total': total,
                'promedio': round(promedio, 2),
                'porcentaje': round(porcentaje, 1),
                'distribucion': distribucion
            }

        elif self.encuesta.tipo == 'trivia':
            # Estadísticas para trivia
            correctas = respuestas.filter(es_correcta=True).count()
            return {
                'total': total,
                'correctas': correctas,
                'incorrectas': total - correctas,
                'porcentaje_acierto': round((correctas / total * 100), 1) if total > 0 else 0,
                'distribucion': self._distribucion_opciones(respuestas)
            }

        else:  # votacion
            # Estadísticas para votación
            return {
                'total': total,
                'distribucion': self._distribucion_opciones(respuestas),
                'ranking': self._ranking_opciones(respuestas)
            }

    def _distribucion_opciones(self, respuestas):
        """Calcula distribución de respuestas por opción."""
        distribucion = {'A': 0, 'B': 0, 'C': 0, 'D': 0}
        for r in respuestas:
            if r.opcion_elegida in distribucion:
                distribucion[r.opcion_elegida] += 1
        return distribucion

    def _ranking_opciones(self, respuestas):
        """Genera ranking de opciones ordenado por votos."""
        distribucion = self._distribucion_opciones(respuestas)
        opciones = self.get_opciones()
        ranking = []
        for op in opciones:
            ranking.append({
                'letra': op['letra'],
                'texto': op['texto'],
                'votos': distribucion.get(op['letra'], 0)
            })
        return sorted(ranking, key=lambda x: x['votos'], reverse=True)


class Participante(models.Model):
    """Participante de una encuesta."""

    encuesta = models.ForeignKey(Encuesta, on_delete=models.CASCADE, related_name='participantes')
    nombre = models.CharField(max_length=100)
    session_id = models.UUIDField(default=uuid.uuid4, unique=True)

    # Estado del participante
    pregunta_actual = models.PositiveIntegerField(default=0)
    conectado = models.BooleanField(default=True)
    ultima_actividad = models.DateTimeField(auto_now=True)

    # Para trivia: puntos acumulados
    puntos_totales = models.PositiveIntegerField(default=0)
    respuestas_correctas = models.PositiveIntegerField(default=0)
    racha_actual = models.PositiveIntegerField(default=0)  # Respuestas correctas seguidas

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

    def agregar_puntos(self, puntos, es_correcta):
        """Agrega puntos y actualiza estadísticas de trivia."""
        if es_correcta:
            self.puntos_totales += puntos
            self.respuestas_correctas += 1
            self.racha_actual += 1
        else:
            self.racha_actual = 0
        self.save(update_fields=['puntos_totales', 'respuestas_correctas', 'racha_actual'])

    def posicion_ranking(self):
        """Retorna la posición en el ranking."""
        return self.encuesta.participantes.filter(
            puntos_totales__gt=self.puntos_totales
        ).count() + 1

    def calcular_resultado_final(self):
        """Calcula el resultado final del participante."""
        if self.encuesta.tipo == 'trivia':
            return {
                'puntos': self.puntos_totales,
                'correctas': self.respuestas_correctas,
                'total_preguntas': self.encuesta.total_preguntas(),
                'posicion': self.posicion_ranking()
            }

        # Para opinion
        respuestas = self.respuestas.all()
        total = respuestas.count()

        if total == 0:
            return {'promedio': 0, 'porcentaje': 0}

        suma = sum(r.valor for r in respuestas if r.valor)
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

    # Para tipo OPINION: valor 1-5
    valor = models.PositiveSmallIntegerField(null=True, blank=True, choices=[(i, str(i)) for i in range(1, 6)])

    # Para tipo TRIVIA y VOTACION: opción elegida
    opcion_elegida = models.CharField(max_length=1, blank=True)

    # Para tipo TRIVIA: resultado
    es_correcta = models.BooleanField(null=True, blank=True)
    puntos_obtenidos = models.PositiveIntegerField(default=0)
    tiempo_respuesta = models.FloatField(null=True, blank=True, help_text="Segundos que tardó en responder")

    # Timestamp
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['participante', 'pregunta']
        ordering = ['creado']
        verbose_name = 'Respuesta'
        verbose_name_plural = 'Respuestas'

    def __str__(self):
        if self.valor:
            return f"{self.participante.nombre} - P{self.pregunta.orden + 1}: {self.valor}"
        return f"{self.participante.nombre} - P{self.pregunta.orden + 1}: {self.opcion_elegida}"

    def calcular_puntos_trivia(self):
        """Calcula los puntos obtenidos en una respuesta de trivia."""
        if not self.es_correcta:
            return 0

        encuesta = self.pregunta.encuesta
        puntos = encuesta.puntos_base

        # Bonus por tiempo si está habilitado
        if encuesta.bonus_tiempo and self.tiempo_respuesta:
            tiempo_limite = self.pregunta.get_tiempo_limite()
            # Bonus máximo del 50% si responde en menos de 3 segundos
            # Bonus proporcional según el tiempo
            if self.tiempo_respuesta < tiempo_limite:
                factor_tiempo = 1 - (self.tiempo_respuesta / tiempo_limite)
                bonus = int(puntos * 0.5 * factor_tiempo)
                puntos += bonus

        # Bonus por racha (10% extra por cada respuesta correcta seguida, máx 50%)
        racha = self.participante.racha_actual
        if racha > 0:
            bonus_racha = min(racha * 0.1, 0.5)
            puntos = int(puntos * (1 + bonus_racha))

        return puntos
