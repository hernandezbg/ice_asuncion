from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import resend
from .models import Pagina, Slider, Breve, Noticia, Galeria, Mensaje, Seccion, Ofrenda, DatosIce


def home(request):
    """
    Vista de la página principal moderna con todos los componentes editables
    """
    # Slider principal
    sliders = Slider.objects.filter(activo=True).order_by('orden')[:5]

    # Secciones flexibles (Visión, Misión, etc.)
    secciones = Seccion.objects.filter(activo=True, mostrar_en_home=True).order_by('orden')

    # Noticias y Mensajes recientes
    noticias_recientes = Noticia.objects.filter(activo=True)[:4]
    mensajes_recientes = Mensaje.objects.filter(activo=True)[:4]

    # Información de ofrendas
    ofrendas = Ofrenda.objects.filter(activo=True).order_by('orden')

    # Datos de contacto y redes sociales
    datos_ice = DatosIce.load()

    context = {
        'sliders': sliders,
        'secciones': secciones,
        'noticias_recientes': noticias_recientes,
        'mensajes_recientes': mensajes_recientes,
        'ofrendas': ofrendas,
        'datos_ice': datos_ice,
    }
    return render(request, 'contenido/home.html', context)


def pagina_detalle(request, pagina_id):
    """
    Vista para páginas estáticas
    """
    pagina = get_object_or_404(Pagina, id=pagina_id, activo=True)
    return render(request, 'contenido/pagina_detalle.html', {'pagina': pagina})


def noticias_lista(request):
    """
    Vista para listar todas las noticias
    """
    tipo = request.GET.get('tipo', '2')  # 1=Noticias, 2=Boletines (predeterminado: Boletines)
    noticias = Noticia.objects.filter(activo=True, tipo=tipo).order_by('-fecha_publicacion')

    # Paginación
    paginator = Paginator(noticias, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'tipo': tipo,
        'tipo_display': 'Noticias' if tipo == '1' else 'Boletines'
    }
    return render(request, 'contenido/noticias_lista.html', context)


def noticia_detalle(request, noticia_id):
    """
    Vista para el detalle de una noticia
    """
    noticia = get_object_or_404(Noticia, id=noticia_id, activo=True)
    noticias_relacionadas = Noticia.objects.filter(
        activo=True,
        tipo=noticia.tipo
    ).exclude(id=noticia.id)[:5]

    # Obtener noticia anterior y siguiente del mismo tipo
    noticia_anterior = Noticia.objects.filter(
        activo=True,
        tipo=noticia.tipo,
        fecha_publicacion__lt=noticia.fecha_publicacion
    ).order_by('-fecha_publicacion').first()

    noticia_siguiente = Noticia.objects.filter(
        activo=True,
        tipo=noticia.tipo,
        fecha_publicacion__gt=noticia.fecha_publicacion
    ).order_by('fecha_publicacion').first()

    context = {
        'noticia': noticia,
        'noticias_relacionadas': noticias_relacionadas,
        'noticia_anterior': noticia_anterior,
        'noticia_siguiente': noticia_siguiente,
    }
    return render(request, 'contenido/noticia_detalle.html', context)


def mensajes_lista(request):
    """
    Vista para listar mensajes y videos con búsqueda
    """
    tipo = request.GET.get('tipo', '')  # 1=Fundamentos, 2=Videos
    busqueda = request.GET.get('q', '')

    mensajes = Mensaje.objects.filter(activo=True)

    # Filtro por tipo
    if tipo:
        mensajes = mensajes.filter(tipo=tipo)

    # Búsqueda
    if busqueda:
        mensajes = mensajes.filter(
            titulo__icontains=busqueda
        ) | mensajes.filter(
            autor__icontains=busqueda
        )

    mensajes = mensajes.order_by('-fecha_publicacion')

    # Paginación
    paginator = Paginator(mensajes, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'tipo': tipo,
        'busqueda': busqueda,
    }
    return render(request, 'contenido/mensajes_lista.html', context)


def mensaje_detalle(request, mensaje_id):
    """
    Vista para el detalle de un mensaje
    """
    mensaje = get_object_or_404(Mensaje, id=mensaje_id, activo=True)
    mensajes_relacionados = Mensaje.objects.filter(
        activo=True,
        tipo=mensaje.tipo
    ).exclude(id=mensaje.id)[:3]

    context = {
        'mensaje': mensaje,
        'mensajes_relacionados': mensajes_relacionados
    }
    return render(request, 'contenido/mensaje_detalle.html', context)


def galeria(request):
    """
    Vista para la galería de imágenes
    """
    # Solo muestro imágenes que tienen archivo asociado
    imagenes = Galeria.objects.filter(activo=True).exclude(imagen='')

    # Paginación
    paginator = Paginator(imagenes, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'contenido/galeria.html', {'page_obj': page_obj})


def contacto(request):
    """
    Vista para el formulario de contacto usando Resend API
    """
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        email = request.POST.get('email')
        asunto = request.POST.get('asunto')
        mensaje_texto = request.POST.get('mensaje')

        # Validación básica
        if not all([nombre, email, asunto, mensaje_texto]):
            messages.error(request, 'Por favor completa todos los campos.')
        else:
            try:
                # Configurar Resend API
                resend.api_key = settings.RESEND_API_KEY

                # Preparar el contenido HTML del email
                html_content = f"""
                <h2>Nuevo mensaje desde el formulario de contacto</h2>
                <p><strong>Nombre:</strong> {nombre}</p>
                <p><strong>Email:</strong> {email}</p>
                <p><strong>Asunto:</strong> {asunto}</p>
                <hr>
                <p><strong>Mensaje:</strong></p>
                <p>{mensaje_texto}</p>
                """

                # Enviar email con Resend
                resend.Emails.send({
                    "from": settings.DEFAULT_FROM_EMAIL,
                    "to": [settings.CONTACT_EMAIL],
                    "subject": f"[ICE Web] {asunto}",
                    "html": html_content,
                    "reply_to": email
                })

                messages.success(request, '¡Mensaje enviado correctamente! Te responderemos pronto.')

            except Exception as e:
                messages.error(request, 'Hubo un error al enviar el mensaje. Por favor intenta nuevamente.')

    return render(request, 'contenido/contacto.html')


@require_POST
def noticia_vista(request, noticia_id):
    """
    Vista AJAX para incrementar el contador de vistas de una noticia
    """
    try:
        noticia = get_object_or_404(Noticia, id=noticia_id, activo=True)
        noticia.vistas += 1
        noticia.save(update_fields=['vistas'])
        return JsonResponse({'success': True, 'vistas': noticia.vistas})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
