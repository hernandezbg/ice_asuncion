from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
import re


# Validador para celular argentino (formato internacional)
celular_validator = RegexValidator(
    regex=r'^\+?54?\s?9?\s?\d{2,4}\s?\d{6,8}$',
    message='Ingrese un número válido. Ej: +54 9 351 1234567 o 351 1234567'
)


class ModeloBase(models.Model):
    """
    Modelo base abstracto con campos comunes
    """
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')
    fecha_modificacion = models.DateTimeField(auto_now=True, verbose_name='Última modificación')
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Usuario')
    activo = models.BooleanField(default=True, verbose_name='Activo')

    class Meta:
        abstract = True


class Provincia(models.Model):
    """
    Provincias de Argentina
    """
    nombre = models.CharField(max_length=100, unique=True, verbose_name='Provincia')

    class Meta:
        verbose_name = 'Provincia'
        verbose_name_plural = 'Provincias'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class EstadoCivil(models.Model):
    """
    Estados civiles
    """
    nombre = models.CharField(max_length=50, unique=True, verbose_name='Estado civil')

    class Meta:
        verbose_name = 'Estado civil'
        verbose_name_plural = 'Estados civiles'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Clase(models.Model):
    """
    Clases/categorías de miembros
    """
    nombre = models.CharField(max_length=100, unique=True, verbose_name='Clase')
    descripcion = models.TextField(blank=True, verbose_name='Descripción')

    class Meta:
        verbose_name = 'Clase'
        verbose_name_plural = 'Clases'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Grupo(models.Model):
    """
    Grupos de reunión
    """
    nombre = models.CharField(max_length=100, unique=True, verbose_name='Grupo')
    descripcion = models.TextField(blank=True, verbose_name='Descripción')

    class Meta:
        verbose_name = 'Grupo'
        verbose_name_plural = 'Grupos'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Don(models.Model):
    """
    Dones espirituales que pueden tener los miembros
    """
    nombre = models.CharField(max_length=100, unique=True, verbose_name='Don')
    descripcion = models.TextField(blank=True, verbose_name='Descripción')
    icono = models.CharField(max_length=50, blank=True, verbose_name='Icono Bootstrap',
                            help_text='Ej: bi-music-note, bi-book, bi-heart')

    class Meta:
        verbose_name = 'Don'
        verbose_name_plural = 'Dones'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Hermano(ModeloBase):
    """
    Registro de miembros de la iglesia
    """
    SEXO_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Femenino'),
    ]

    # Datos personales
    apellidos = models.CharField(max_length=200, verbose_name='Apellidos')
    apellido_soltera = models.CharField(max_length=200, blank=True, verbose_name='Apellido de soltera',
                                        help_text='Apellido de nacimiento (opcional, para búsquedas)')
    nombres = models.CharField(max_length=200, verbose_name='Nombres')
    foto = models.ImageField(upload_to='hermanos/', blank=True, null=True, verbose_name='Foto de perfil')
    sexo = models.CharField(max_length=1, choices=SEXO_CHOICES, verbose_name='Sexo')
    fecha_nacimiento = models.DateField(null=True, blank=True, verbose_name='Fecha de nacimiento')
    cumpleaños = models.DateField(null=True, blank=True, verbose_name='Cumpleaños',
                                  help_text='Solo mes y día (año puede ser ficticio)')
    estado_civil = models.ForeignKey(EstadoCivil, on_delete=models.SET_NULL, null=True, blank=True,
                                     verbose_name='Estado civil')
    ocupacion = models.CharField(max_length=200, blank=True, verbose_name='Ocupación/Profesión')

    # Datos de contacto
    telefono_fijo = models.CharField(max_length=50, blank=True, verbose_name='Teléfono fijo')
    celular = models.CharField(max_length=25, blank=True, verbose_name='Celular',
                               validators=[celular_validator],
                               help_text='Formato: +54 9 351 1234567')
    email = models.EmailField(blank=True, verbose_name='Email')

    # Ubicación
    provincia = models.ForeignKey(Provincia, on_delete=models.SET_NULL, null=True, blank=True,
                                 verbose_name='Provincia')
    localidad = models.CharField(max_length=200, blank=True, verbose_name='Localidad')
    domicilio = models.CharField(max_length=300, blank=True, verbose_name='Domicilio')
    barrio = models.CharField(max_length=200, blank=True, verbose_name='Barrio')

    # Clasificación espiritual
    grupo = models.ForeignKey(Grupo, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Grupo')
    clase = models.ForeignKey(Clase, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Clase')
    anio_bautismo = models.PositiveIntegerField(null=True, blank=True, verbose_name='Año de bautismo')
    dones = models.ManyToManyField(Don, blank=True, verbose_name='Dones',
                                   help_text='Seleccione uno o más dones')

    # Marcas espirituales (del proyecto antiguo)
    marca_1 = models.BooleanField(default=False, verbose_name='Marca 1')
    marca_2 = models.BooleanField(default=False, verbose_name='Marca 2')
    marca_3 = models.BooleanField(default=False, verbose_name='Marca 3')

    # Observaciones
    observaciones = models.TextField(blank=True, verbose_name='Observaciones')

    class Meta:
        verbose_name = 'Hermano'
        verbose_name_plural = 'Hermanos'
        ordering = ['apellidos', 'nombres']

    def __str__(self):
        return f"{self.apellidos}, {self.nombres}"

    def nombre_completo(self):
        """Devuelvo nombre completo"""
        return f"{self.nombres} {self.apellidos}"

    def edad(self):
        """Calculo edad si tiene fecha de nacimiento"""
        if self.fecha_nacimiento:
            from datetime import date
            hoy = date.today()
            return hoy.year - self.fecha_nacimiento.year - (
                (hoy.month, hoy.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day)
            )
        return None
