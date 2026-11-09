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


CONTACTOS_PAGO_DEFAULT = 'Santy, 543813419795\nPaula, 543816621117'


def numero_whatsapp(numero):
    """Numero para wa.me: solo digitos; en celulares de Argentina agrego el 9 despues del 54"""
    digitos = ''.join(c for c in numero if c.isdigit())
    if digitos.startswith('54') and not digitos.startswith('549') and len(digitos) == 12:
        digitos = '549' + digitos[2:]
    return digitos


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

    # Descuento por pago anticipado (opcional, precio fijo)
    fecha_limite_descuento = models.DateField(null=True, blank=True, verbose_name='Pagando hasta el (inclusive)',
                                              help_text='Vacío = sin descuento')
    precio_adulto_descuento = models.PositiveIntegerField(null=True, blank=True,
                                                          verbose_name='Precio adulto con descuento ($)')
    precio_nino_descuento = models.PositiveIntegerField(null=True, blank=True,
                                                        verbose_name='Precio niño con descuento ($)')
    nota_comprobante = models.TextField(blank=True, verbose_name='Nota del comprobante',
                                        help_text='Se muestra en el comprobante final. Ej: alias o CBU para transferir')

    fecha_cierre = models.DateTimeField(null=True, blank=True, verbose_name='Cierre de inscripción',
                                        help_text='Vacío = sin fecha de cierre')
    cupo = models.PositiveIntegerField(null=True, blank=True, verbose_name='Cupo (personas)',
                                       help_text='Vacío = sin límite. Cuenta todas las personas inscriptas')
    activo = models.BooleanField(default=True, verbose_name='Inscripción habilitada')
    contactos_pago = models.TextField(
        blank=True, default=CONTACTOS_PAGO_DEFAULT, verbose_name='Contactos para el pago',
        help_text='Uno por línea: Nombre, número de WhatsApp. Ej: Santy, 543813419795')
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

    def precio_categoria(self, categoria, descuento=False):
        if descuento and self.tiene_descuento():
            return {
                CATEGORIA_ADULTO: self.precio_adulto_descuento,
                CATEGORIA_NINO: self.precio_nino_descuento,
                CATEGORIA_GRATIS: 0,
            }[categoria]
        return {
            CATEGORIA_ADULTO: self.precio_adulto,
            CATEGORIA_NINO: self.precio_nino,
            CATEGORIA_GRATIS: 0,
        }[categoria]

    # --- Descuento por pago anticipado ---

    def tiene_descuento(self):
        return (self.fecha_limite_descuento is not None
                and self.precio_adulto_descuento is not None
                and self.precio_nino_descuento is not None)

    def descuento_vigente(self, dia=None):
        """True si hoy (o el dia indicado) todavia se paga con descuento"""
        dia = dia or timezone.localdate()
        return self.tiene_descuento() and dia <= self.fecha_limite_descuento

    def lineas_nota_comprobante(self):
        """
        Lineas de la nota del comprobante. Las que son 'Alias...: valor', 'CBU...: valor'
        o 'CVU...: valor' devuelven tambien el valor para mostrar un boton de copiar.
        [(etiqueta, valor_copiable o None), ...]
        """
        import re
        lineas = []
        for linea in (self.nota_comprobante or '').splitlines():
            linea = linea.strip()
            if not linea:
                continue
            m = re.match(r'^((?:alias|cbu|cvu)\b[^:]*):\s*(\S+)\s*$', linea, re.IGNORECASE)
            if m:
                lineas.append((m.group(1).strip(), m.group(2)))
            else:
                lineas.append((linea, None))
        return lineas

    def lista_contactos_pago(self):
        """[(nombre, numero_para_whatsapp), ...] a partir del texto 'Nombre, numero' por linea"""
        contactos = []
        for linea in (self.contactos_pago or '').splitlines():
            if ',' not in linea:
                continue
            nombre, numero = linea.rsplit(',', 1)
            numero = numero_whatsapp(numero)
            if nombre.strip() and len(numero) >= 8:
                contactos.append((nombre.strip(), numero))
        return contactos

    # --- Cupo y cierre ---

    def personas_inscriptas(self):
        return Inscripto.objects.filter(inscripcion__evento=self).count()

    def cupo_disponible(self):
        if self.cupo is None:
            return None
        return max(self.cupo - self.personas_inscriptas(), 0)

    def motivo_cerrado(self, ignorar_cupo=False):
        """
        Devuelvo None si la inscripcion esta abierta, o el motivo si esta cerrada.
        ignorar_cupo: con el cupo lleno igual se pueden modificar inscripciones existentes.
        """
        if not self.activo:
            return 'La inscripción no está habilitada.'
        if self.fecha_cierre and timezone.now() > self.fecha_cierre:
            return 'La inscripción ya cerró.'
        if not ignorar_cupo and self.cupo_lleno():
            return 'Se completó el cupo del evento.'
        return None

    def cupo_lleno(self):
        return self.cupo is not None and self.cupo_disponible() <= 0


class Inscripcion(models.Model):
    """
    Una inscripcion = una familia (responsable + familiares)
    """
    evento = models.ForeignKey(Evento, on_delete=models.CASCADE, related_name='inscripciones')
    celular = models.CharField(max_length=30, verbose_name='Celular')
    observaciones = models.TextField(blank=True, verbose_name='Observaciones')
    fecha = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de inscripción')
    fecha_modificacion = models.DateTimeField(auto_now=True, null=True, verbose_name='Última modificación')
    pagado = models.BooleanField(default=False, verbose_name='Pagado')
    con_descuento = models.BooleanField(default=False, verbose_name='Pagó con descuento')
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

    def total(self, descuento=False):
        return sum(p.precio(descuento) for p in self.personas.all())

    def total_descuento(self):
        return self.total(descuento=True)

    def total_vigente(self):
        """Lo que tiene que pagar hoy (con descuento si todavia esta vigente)"""
        return self.total(descuento=self.evento.descuento_vigente())

    def total_pagado(self):
        return self.total(descuento=self.con_descuento) if self.pagado else 0

    def fue_modificada(self):
        from datetime import timedelta
        return bool(self.fecha_modificacion and self.fecha_modificacion - self.fecha > timedelta(minutes=1))

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

    def precio(self, descuento=False):
        return self.inscripcion.evento.precio_categoria(self.categoria(), descuento)

    def precio_descuento(self):
        return self.precio(descuento=True)

    def en_base(self):
        return bool(self.hermano_id or self.alumno_id)

    def origen(self):
        if self.hermano_id:
            return 'Hermano'
        if self.alumno_id:
            return 'Alumno EB'
        return ''
