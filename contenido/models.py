from django.db import models
from django.contrib.auth.models import User
from django.core.validators import URLValidator


class ModeloBase(models.Model):
    """
    Modelo base abstracto con campos comunes para todos los modelos
    """
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')
    fecha_modificacion = models.DateTimeField(auto_now=True, verbose_name='Última modificación')
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Usuario')
    activo = models.BooleanField(default=True, verbose_name='Activo')

    class Meta:
        abstract = True


class Pagina(ModeloBase):
    """
    Páginas estáticas del sitio web
    """
    titulo = models.CharField(max_length=200, verbose_name='Título')
    descripcion = models.CharField(max_length=300, blank=True, verbose_name='Descripción breve')
    contenido = models.TextField(verbose_name='Contenido')
    imagen = models.ImageField(upload_to='paginas/', blank=True, null=True, verbose_name='Imagen')
    orden = models.IntegerField(default=0, verbose_name='Orden de visualización')

    class Meta:
        verbose_name = 'Página'
        verbose_name_plural = 'Páginas'
        ordering = ['orden', 'titulo']

    def __str__(self):
        return self.titulo


class Slider(ModeloBase):
    """
    Carrusel de imágenes del inicio
    """
    titulo = models.CharField(max_length=200, verbose_name='Título')
    descripcion = models.TextField(blank=True, verbose_name='Descripción')
    imagen = models.ImageField(upload_to='slider/', verbose_name='Imagen')
    enlace = models.CharField(max_length=500, blank=True, validators=[URLValidator()], verbose_name='Enlace (URL)')
    pagina = models.ForeignKey(Pagina, on_delete=models.SET_NULL, null=True, blank=True,
                               verbose_name='Página interna', help_text='Si no hay URL externa, enlazar a página interna')
    orden = models.IntegerField(default=0, verbose_name='Orden de visualización')

    class Meta:
        verbose_name = 'Slider'
        verbose_name_plural = 'Sliders'
        ordering = ['orden']

    def __str__(self):
        return self.titulo

    def obtener_enlace(self):
        """Devuelvo el enlace externo o interno según corresponda"""
        if self.enlace:
            return self.enlace
        elif self.pagina:
            return f'/pagina/{self.pagina.id}/'
        return '#'


class Breve(ModeloBase):
    """
    Cards/breves informativos de la página principal
    """
    titulo = models.CharField(max_length=200, verbose_name='Título')
    descripcion = models.TextField(verbose_name='Descripción')
    imagen = models.ImageField(upload_to='breves/', blank=True, null=True, verbose_name='Imagen')
    icono = models.CharField(max_length=100, blank=True, verbose_name='Ícono (clase CSS)',
                            help_text='Ej: fa fa-heart, bi bi-house')
    enlace = models.CharField(max_length=500, blank=True, validators=[URLValidator()], verbose_name='Enlace')
    orden = models.IntegerField(default=0, verbose_name='Orden de visualización')

    class Meta:
        verbose_name = 'Breve'
        verbose_name_plural = 'Breves'
        ordering = ['orden']

    def __str__(self):
        return self.titulo


class Noticia(ModeloBase):
    """
    Noticias y boletines de la iglesia
    """
    TIPO_CHOICES = [
        (1, 'Noticia'),
        (2, 'Boletín'),
    ]

    tipo = models.IntegerField(choices=TIPO_CHOICES, default=1, verbose_name='Tipo')
    titulo = models.CharField(max_length=300, verbose_name='Título')
    introduccion = models.TextField(verbose_name='Introducción')
    contenido = models.TextField(verbose_name='Contenido completo')
    imagen_principal = models.ImageField(upload_to='noticias/', blank=True, null=True, verbose_name='Imagen principal')
    imagen_secundaria = models.ImageField(upload_to='noticias/', blank=True, null=True, verbose_name='Imagen secundaria')
    fecha_publicacion = models.DateField(verbose_name='Fecha de publicación')
    vistas = models.PositiveIntegerField(default=0, verbose_name='Visitas')

    class Meta:
        verbose_name = 'Noticia'
        verbose_name_plural = 'Noticias'
        ordering = ['-fecha_publicacion']

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.titulo}"


class Galeria(ModeloBase):
    """
    Galería de imágenes
    """
    titulo = models.CharField(max_length=200, verbose_name='Título')
    descripcion = models.TextField(blank=True, verbose_name='Descripción')
    imagen = models.ImageField(upload_to='galeria/', verbose_name='Imagen')
    orden = models.IntegerField(default=0, verbose_name='Orden de visualización')

    class Meta:
        verbose_name = 'Imagen de galería'
        verbose_name_plural = 'Galería'
        ordering = ['orden', '-fecha_creacion']

    def __str__(self):
        return self.titulo


class Mensaje(ModeloBase):
    """
    Mensajes predicados y videos
    """
    TIPO_CHOICES = [
        (1, 'Fundamento (Mensaje escrito)'),
        (2, 'Video'),
    ]

    tipo = models.IntegerField(choices=TIPO_CHOICES, default=1, verbose_name='Tipo de mensaje')
    titulo = models.CharField(max_length=300, verbose_name='Título')
    autor = models.CharField(max_length=200, verbose_name='Autor/Predicador')
    introduccion = models.TextField(verbose_name='Introducción')
    contenido = models.TextField(blank=True, verbose_name='Contenido completo',
                                 help_text='Solo para mensajes escritos')
    imagen = models.ImageField(upload_to='mensajes/', blank=True, null=True, verbose_name='Imagen')
    enlace_video = models.CharField(max_length=500, blank=True, validators=[URLValidator()],
                                    verbose_name='Enlace del video (YouTube/Vimeo)')
    fecha_publicacion = models.DateField(verbose_name='Fecha de publicación')

    class Meta:
        verbose_name = 'Mensaje'
        verbose_name_plural = 'Mensajes'
        ordering = ['-fecha_publicacion']

    def __str__(self):
        return f"{self.titulo} - {self.autor}"


class DatosIce(ModeloBase):
    """
    Datos centrales de la iglesia (singleton - solo un registro)
    """
    # Información de contacto
    email = models.EmailField(verbose_name='Email de contacto')
    direccion = models.CharField(max_length=300, verbose_name='Dirección')
    telefono = models.CharField(max_length=50, verbose_name='Teléfono')

    # Redes sociales
    facebook = models.CharField(max_length=300, blank=True, verbose_name='Facebook URL')
    twitter = models.CharField(max_length=300, blank=True, verbose_name='Twitter URL')
    youtube = models.CharField(max_length=300, blank=True, verbose_name='YouTube URL')
    instagram = models.CharField(max_length=300, blank=True, verbose_name='Instagram URL')

    # Otros enlaces
    stream_youtube = models.CharField(max_length=500, blank=True, verbose_name='Stream en vivo YouTube')

    class Meta:
        verbose_name = 'Datos de ICE'
        verbose_name_plural = 'Datos de ICE'

    def __str__(self):
        return 'Datos de ICE Asunción'

    def save(self, *args, **kwargs):
        # Aseguro que solo exista un registro
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        """Obtengo o creo el único registro de datos"""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj


class Seccion(ModeloBase):
    """
    Secciones flexibles para la homepage (Visión, Misión, Bienvenida, etc.)
    Permite crear cualquier bloque de contenido editable
    """
    ESTILO_CHOICES = [
        ('light', 'Fondo Claro'),
        ('dark', 'Fondo Oscuro'),
        ('primary', 'Color Primario'),
        ('secondary', 'Color Secundario'),
    ]

    TIPO_CHOICES = [
        ('texto', 'Solo Texto'),
        ('texto_imagen', 'Texto con Imagen'),
        ('cards', 'Tarjetas/Cards'),
    ]

    titulo = models.CharField(max_length=200, verbose_name='Título')
    subtitulo = models.CharField(max_length=300, blank=True, verbose_name='Subtítulo')
    contenido = models.TextField(verbose_name='Contenido', help_text='Puede usar HTML')
    imagen = models.ImageField(upload_to='secciones/', blank=True, null=True, verbose_name='Imagen')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='texto', verbose_name='Tipo de sección')
    estilo = models.CharField(max_length=20, choices=ESTILO_CHOICES, default='light', verbose_name='Estilo de fondo')
    orden = models.IntegerField(default=0, verbose_name='Orden en homepage')
    mostrar_en_home = models.BooleanField(default=True, verbose_name='Mostrar en inicio')

    class Meta:
        verbose_name = 'Sección'
        verbose_name_plural = 'Secciones'
        ordering = ['orden', 'titulo']

    def __str__(self):
        return f"{self.titulo} (Orden: {self.orden})"


class Ofrenda(ModeloBase):
    """
    Información de ofrendas y donaciones
    """
    titulo = models.CharField(max_length=200, verbose_name='Título')
    descripcion = models.TextField(verbose_name='Descripción')

    # Información bancaria
    banco = models.CharField(max_length=200, blank=True, verbose_name='Nombre del banco')
    cuenta = models.CharField(max_length=200, blank=True, verbose_name='Número de cuenta')
    titular = models.CharField(max_length=200, blank=True, verbose_name='Titular de la cuenta')

    # Mercado Pago
    mercadopago_link = models.CharField(max_length=500, blank=True, verbose_name='Link de Mercado Pago')
    mercadopago_alias = models.CharField(max_length=100, blank=True, verbose_name='Alias de Mercado Pago')

    orden = models.IntegerField(default=0, verbose_name='Orden de visualización')

    class Meta:
        verbose_name = 'Ofrenda'
        verbose_name_plural = 'Ofrendas'
        ordering = ['orden']

    def __str__(self):
        return self.titulo
