from django.db import models
from datetime import date


class ClaseEscuela(models.Model):
    """
    Clases de la Escuela Biblica
    """
    nombre = models.CharField(max_length=100, verbose_name='Nombre de la clase')
    color = models.CharField(max_length=20, verbose_name='Color', help_text='Ej: verde, azul, amarilla')
    emoji = models.CharField(max_length=10, blank=True, verbose_name='Emoji')
    edad_desde = models.PositiveIntegerField(verbose_name='Edad desde')
    edad_hasta = models.PositiveIntegerField(null=True, blank=True, verbose_name='Edad hasta',
                                              help_text='Dejar vacío para "en adelante"')
    descripcion = models.CharField(max_length=300, blank=True, verbose_name='Descripción',
                                    help_text='Ej: 1ro, 2do y 3er grado')
    maestros = models.CharField(max_length=300, blank=True, verbose_name='Maestros')
    codigo_acceso = models.CharField(max_length=20, verbose_name='Código de acceso',
                                      help_text='Código que usan los maestros para entrar')
    orden = models.PositiveIntegerField(default=0, verbose_name='Orden')
    activo = models.BooleanField(default=True, verbose_name='Activa')

    class Meta:
        verbose_name = 'Clase'
        verbose_name_plural = 'Clases'
        ordering = ['orden', 'edad_desde']

    def __str__(self):
        if self.emoji:
            return f"{self.emoji} {self.nombre}"
        return self.nombre

    def rango_edad(self):
        if self.edad_hasta:
            return f"{self.edad_desde} - {self.edad_hasta} años"
        return f"{self.edad_desde} años en adelante"


GRADO_CHOICES = [
    ('', 'Sin especificar'),
    ('jardin', 'Jardín'),
    ('preescolar', 'Preescolar'),
    ('1_primaria', '1° Primaria'),
    ('2_primaria', '2° Primaria'),
    ('3_primaria', '3° Primaria'),
    ('4_primaria', '4° Primaria'),
    ('5_primaria', '5° Primaria'),
    ('6_primaria', '6° Primaria'),
    ('1_secundaria', '1° Secundaria'),
    ('2_secundaria', '2° Secundaria'),
    ('3_secundaria', '3° Secundaria'),
    ('4_secundaria', '4° Secundaria'),
    ('5_secundaria', '5° Secundaria'),
    ('6_secundaria', '6° Secundaria'),
    ('terciario', 'Terciario'),
    ('universitario', 'Universitario'),
    ('trabajando', 'Trabajando'),
]


class Alumno(models.Model):
    """
    Alumnos de la Escuela Biblica
    """
    apellidos = models.CharField(max_length=200, verbose_name='Apellidos')
    nombres = models.CharField(max_length=200, verbose_name='Nombres')
    fecha_nacimiento = models.DateField(null=True, blank=True, verbose_name='Fecha de nacimiento')
    grado_nivel = models.CharField(max_length=20, choices=GRADO_CHOICES, blank=True,
                                    verbose_name='Grado/Nivel')
    clase = models.ForeignKey(ClaseEscuela, on_delete=models.CASCADE, related_name='alumnos',
                              verbose_name='Clase')
    observaciones = models.TextField(blank=True, verbose_name='Observaciones')
    activo = models.BooleanField(default=True, verbose_name='Activo')
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de registro')
    fecha_modificacion = models.DateTimeField(auto_now=True, verbose_name='Última modificación')

    class Meta:
        verbose_name = 'Alumno'
        verbose_name_plural = 'Alumnos'
        ordering = ['apellidos', 'nombres']

    def __str__(self):
        return f"{self.apellidos}, {self.nombres}"

    def edad(self):
        if self.fecha_nacimiento:
            hoy = date.today()
            return hoy.year - self.fecha_nacimiento.year - (
                (hoy.month, hoy.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day)
            )
        return None

    def nombre_completo(self):
        return f"{self.nombres} {self.apellidos}"


class Asistencia(models.Model):
    """
    Registro de asistencia por domingo
    """
    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE, related_name='asistencias',
                                verbose_name='Alumno')
    clase = models.ForeignKey(ClaseEscuela, on_delete=models.CASCADE, related_name='asistencias',
                               verbose_name='Clase')
    fecha = models.DateField(verbose_name='Fecha (domingo)')
    presente = models.BooleanField(verbose_name='Presente')
    fecha_registro = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de registro')

    class Meta:
        verbose_name = 'Asistencia'
        verbose_name_plural = 'Asistencias'
        ordering = ['-fecha', 'alumno__apellidos']
        unique_together = ['alumno', 'fecha']

    def __str__(self):
        estado = 'Presente' if self.presente else 'Ausente'
        return f"{self.alumno} - {self.fecha} - {estado}"


def _generar_codigo_proyeccion():
    import random, string
    while True:
        codigo = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        if not Presentacion.objects.filter(codigo=codigo).exists():
            return codigo


class Presentacion(models.Model):
    """
    Presentaciones (PDF) para proyectar en el salon y replicar en celulares
    """
    titulo = models.CharField(max_length=200, verbose_name='Titulo')
    archivo = models.FileField(upload_to='proyecciones/', verbose_name='Archivo PDF')
    codigo = models.CharField(max_length=10, unique=True, blank=True,
                              verbose_name='Codigo de acceso',
                              help_text='Codigo corto para la URL publica')
    total_slides = models.PositiveIntegerField(default=1, verbose_name='Total de slides')
    activa = models.BooleanField(default=True, verbose_name='Activa')
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Presentacion'
        verbose_name_plural = 'Presentaciones'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f'{self.titulo} ({self.codigo})'

    def save(self, *args, **kwargs):
        if not self.codigo:
            self.codigo = _generar_codigo_proyeccion()
        super().save(*args, **kwargs)


class EstadoProyeccion(models.Model):
    """
    Slide actual de cada presentacion (para sincronizar celulares con el proyector)
    """
    presentacion = models.OneToOneField(Presentacion, on_delete=models.CASCADE,
                                         related_name='estado')
    slide_actual = models.PositiveIntegerField(default=1)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Estado de proyeccion'
        verbose_name_plural = 'Estados de proyeccion'

    def __str__(self):
        return f'{self.presentacion.codigo}: slide {self.slide_actual}'


class DomingoExcluido(models.Model):
    """
    Domingos en los que no se dictan clases (domingos especiales)
    """
    fecha = models.DateField(unique=True, verbose_name='Fecha (domingo)')
    motivo = models.CharField(max_length=200, verbose_name='Motivo',
                               help_text='Ej: Santa Cena, Culto especial, etc.')

    class Meta:
        verbose_name = 'Domingo excluido'
        verbose_name_plural = 'Domingos excluidos'
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.fecha.strftime('%d/%m/%Y')} - {self.motivo}"
