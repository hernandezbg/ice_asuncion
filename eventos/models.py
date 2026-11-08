from django.db import models
from django.utils import timezone

from miembros.models import Hermano
from escuela.models import Alumno


CATEGORIA_ADULTO = 'adulto'
CATEGORIA_NINO = 'nino'
CATEGORIA_GRATIS = 'gratis'

CATEGORIA_LABELS = {
    CATEGORIA_ADULTO: 'Adulto',
    CATEGORIA_NINO: 'Niño',
    CATEGORIA_GRATIS: 'Sin cargo',
}


class Evento(models.Model):
    """
    Evento con inscripcion publica (ej: cena de fin de año)
    """
    nombre = models.CharField(max_length=200, verbose_name='Nombre del evento')
    slug = models.SlugField(max_length=80, unique=True, verbose_name='Dirección web',
                            help_text='Se usa en el link público. Ej: fin-de-anio-2026')
    fecha = models.DateField(verbose_name='Fecha del evento',
                             help_text='Las edades se calculan a esta fecha')
    lugar = models.CharField(max_length=200, blank=True, verbose_name='Lugar')
    informacion = models.TextField(blank=True, verbose_name='Información del evento',
                                   help_text='Se muestra al comienzo del formulario: fechas, descuentos, formas de pago, etc.')

    precio_adulto = models.PositiveIntegerField(verbose_name='Precio adulto ($)')
    precio_nino = models.PositiveIntegerField(verbose_name='Precio niño ($)')
    edad_max_nino = models.PositiveIntegerField(default=11, verbose_name='Edad máxima niño',
                                                help_text='Desde la edad siguiente paga como adulto')
    edad_min_paga = models.PositiveIntegerField(default=3, verbose_name='Edad mínima que paga',
                                                help_text='Menores a esta edad no pagan')

    fecha_cierre = models.DateTimeField(null=True, blank=True, verbose_name='Cierre de inscripción',
                                        help_text='Vacío = sin fecha de cierre')
    cupo = models.PositiveIntegerField(null=True, blank=True, verbose_name='Cupo (personas)',
                                       help_text='Vacío = sin límite. Cuenta todas las personas inscriptas')
    activo = models.BooleanField(default=True, verbose_name='Inscripción habilitada')
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Evento'
        verbose_name_plural = 'Eventos'
        ordering = ['-fecha']

    def __str__(self):
        return self.nombre

    # --- Edades y precios ---

    def edad_a_la_fecha(self, fecha_nacimiento):
        if not fecha_nacimiento:
            return None
        f = self.fecha
        return f.year - fecha_nacimiento.year - ((f.month, f.day) < (fecha_nacimiento.month, fecha_nacimiento.day))

    def categoria_para_edad(self, edad):
        """edad None = adulto"""
        if edad is None or edad > self.edad_max_nino:
            return CATEGORIA_ADULTO
        if edad < self.edad_min_paga:
            return CATEGORIA_GRATIS
        return CATEGORIA_NINO

    def precio_categoria(self, categoria):
        return {
            CATEGORIA_ADULTO: self.precio_adulto,
            CATEGORIA_NINO: self.precio_nino,
            CATEGORIA_GRATIS: 0,
        }[categoria]

    # --- Cupo y cierre ---

    def personas_inscriptas(self):
        return Inscripto.objects.filter(inscripcion__evento=self).count()

    def cupo_disponible(self):
        if self.cupo is None:
            return None
        return max(self.cupo - self.personas_inscriptas(), 0)

    def motivo_cerrado(self):
        """Devuelvo None si la inscripcion esta abierta, o el motivo si esta cerrada"""
        if not self.activo:
            return 'La inscripción no está habilitada.'
        if self.fecha_cierre and timezone.now() > self.fecha_cierre:
            return 'La inscripción ya cerró.'
        if self.cupo is not None and self.cupo_disponible() <= 0:
            return 'Se completó el cupo del evento.'
        return None


class Inscripcion(models.Model):
    """
    Una inscripcion = una familia (responsable + familiares)
    """
    evento = models.ForeignKey(Evento, on_delete=models.CASCADE, related_name='inscripciones')
    celular = models.CharField(max_length=30, verbose_name='Celular')
    observaciones = models.TextField(blank=True, verbose_name='Observaciones')
    fecha = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de inscripción')
    pagado = models.BooleanField(default=False, verbose_name='Pagado')
    fecha_pago = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de pago')

    class Meta:
        verbose_name = 'Inscripción'
        verbose_name_plural = 'Inscripciones'
        ordering = ['fecha']

    def __str__(self):
        r = self.responsable()
        return f'{r} - {self.evento}' if r else f'Inscripción #{self.pk}'

    def responsable(self):
        personas = list(self.personas.all())
        for p in personas:
            if p.parentesco == Inscripto.RESPONSABLE:
                return p
        return personas[0] if personas else None

    def total(self):
        return sum(p.precio() for p in self.personas.all())

    def cantidad(self, categoria):
        return sum(1 for p in self.personas.all() if p.categoria() == categoria)


class Inscripto(models.Model):
    """
    Cada persona de una inscripcion
    """
    RESPONSABLE = 'responsable'
    PARENTESCO_CHOICES = [
        (RESPONSABLE, 'Responsable'),
        ('conyuge', 'Esposo/a'),
        ('hijo', 'Hijo/a'),
        ('otro', 'Otro familiar'),
    ]

    inscripcion = models.ForeignKey(Inscripcion, on_delete=models.CASCADE, related_name='personas')
    apellido = models.CharField(max_length=200, verbose_name='Apellido')
    nombre = models.CharField(max_length=200, verbose_name='Nombre')
    parentesco = models.CharField(max_length=20, choices=PARENTESCO_CHOICES, default='otro')
    edad = models.PositiveIntegerField(null=True, blank=True, verbose_name='Edad',
                                       help_text='Edad a la fecha del evento')
    hermano = models.ForeignKey(Hermano, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='inscripciones_eventos', verbose_name='Hermano (base)')
    alumno = models.ForeignKey(Alumno, on_delete=models.SET_NULL, null=True, blank=True,
                               related_name='inscripciones_eventos', verbose_name='Alumno (base)')

    class Meta:
        verbose_name = 'Persona inscripta'
        verbose_name_plural = 'Personas inscriptas'
        ordering = ['id']

    def __str__(self):
        return f'{self.apellido}, {self.nombre}'

    def categoria(self):
        return self.inscripcion.evento.categoria_para_edad(self.edad)

    def categoria_label(self):
        return CATEGORIA_LABELS[self.categoria()]

    def precio(self):
        return self.inscripcion.evento.precio_categoria(self.categoria())

    def en_base(self):
        return bool(self.hermano_id or self.alumno_id)

    def origen(self):
        if self.hermano_id:
            return 'Hermano'
        if self.alumno_id:
            return 'Alumno EB'
        return ''
