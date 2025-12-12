from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.conf import settings
from django.contrib import messages
from django.db.models import Q
from django.db.models.functions import Lower
import requests
import unicodedata

from .models import Hermano, Provincia, EstadoCivil, Clase, Grupo, Don
from contenido.models import DatosIce


def quitar_acentos(texto):
    """Quita acentos de un texto para búsqueda flexible"""
    if not texto:
        return ''
    # Normaliza a forma NFD (separa caracteres base de diacríticos)
    # Luego filtra solo caracteres que no son diacríticos
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    ).lower()


def verificar_recaptcha(token):
    """Verificar token de reCAPTCHA con Google"""
    if not settings.RECAPTCHA_SECRET_KEY:
        return True  # Si no hay key configurada, skip verificación

    try:
        response = requests.post(
            'https://www.google.com/recaptcha/api/siteverify',
            data={
                'secret': settings.RECAPTCHA_SECRET_KEY,
                'response': token
            }
        )
        result = response.json()
        return result.get('success', False)
    except Exception:
        return False


def actualizar_datos_acceso(request):
    """
    Paso 1: Verificar código de acceso + reCAPTCHA
    """
    # Si ya tiene acceso en sesión, ir a búsqueda
    if request.session.get('acceso_miembros_verificado'):
        return redirect('miembros:buscar')

    datos_ice = DatosIce.load()
    error = None

    if request.method == 'POST':
        codigo = request.POST.get('codigo', '').strip()
        recaptcha_token = request.POST.get('g-recaptcha-response', '')

        # Verificar reCAPTCHA
        if settings.RECAPTCHA_SITE_KEY and not verificar_recaptcha(recaptcha_token):
            error = 'Por favor, completa la verificación de seguridad.'
        # Verificar código de acceso
        elif codigo != datos_ice.codigo_acceso_miembros:
            error = 'Código de acceso incorrecto.'
        else:
            # Código correcto, guardar en sesión
            request.session['acceso_miembros_verificado'] = True
            return redirect('miembros:buscar')

    context = {
        'error': error,
        'recaptcha_site_key': settings.RECAPTCHA_SITE_KEY,
    }
    return render(request, 'miembros/actualizar_acceso.html', context)


def actualizar_datos_buscar(request):
    """
    Paso 2: Buscar por apellido Y nombre (insensible a acentos)
    Busca coincidencias en cualquiera de los campos para encontrar registros
    aunque estén con apellido de casada o variaciones.
    """
    # Verificar acceso
    if not request.session.get('acceso_miembros_verificado'):
        return redirect('miembros:acceso')

    resultados = None
    apellido_buscar = ''
    nombre_buscar = ''
    busqueda_realizada = False

    if request.method == 'POST':
        apellido_buscar = request.POST.get('apellido', '').strip()
        nombre_buscar = request.POST.get('nombre', '').strip()

        if len(apellido_buscar) >= 2 and len(nombre_buscar) >= 2:
            busqueda_realizada = True
            apellido_norm = quitar_acentos(apellido_buscar)
            nombre_norm = quitar_acentos(nombre_buscar)

            # Buscar donde coincida apellido O nombre en cualquier campo
            # Incluye apellido_soltera para encontrar personas con apellido de casada
            todos_hermanos = Hermano.objects.filter(activo=True).order_by('apellidos', 'nombres')
            resultados = [
                h for h in todos_hermanos
                if (apellido_norm in quitar_acentos(h.apellidos)
                    or apellido_norm in quitar_acentos(h.apellido_soltera or '')
                    or apellido_norm in quitar_acentos(h.nombres))
                or (nombre_norm in quitar_acentos(h.nombres)
                    or nombre_norm in quitar_acentos(h.apellidos)
                    or nombre_norm in quitar_acentos(h.apellido_soltera or ''))
            ][:20]

    context = {
        'resultados': resultados,
        'apellido_buscar': apellido_buscar,
        'nombre_buscar': nombre_buscar,
        'busqueda_realizada': busqueda_realizada,
    }
    return render(request, 'miembros/actualizar_buscar.html', context)


def actualizar_datos_editar(request, hermano_id=None):
    """
    Paso 3: Editar datos existentes o crear nuevo registro
    """
    # Verificar acceso
    if not request.session.get('acceso_miembros_verificado'):
        return redirect('miembros:acceso')

    hermano = None
    es_nuevo = hermano_id is None

    if hermano_id:
        hermano = get_object_or_404(Hermano, id=hermano_id, activo=True)

    # Cargar opciones para selects
    provincias = Provincia.objects.all()
    estados_civiles = EstadoCivil.objects.all()
    clases = Clase.objects.all()
    grupos = Grupo.objects.all()
    dones = Don.objects.all()

    if request.method == 'POST':
        # Recoger datos del formulario
        datos = {
            'apellidos': request.POST.get('apellidos', '').strip(),
            'apellido_soltera': request.POST.get('apellido_soltera', '').strip(),
            'nombres': request.POST.get('nombres', '').strip(),
            'sexo': request.POST.get('sexo', ''),
            'fecha_nacimiento': request.POST.get('fecha_nacimiento') or None,
            'ocupacion': request.POST.get('ocupacion', '').strip(),
            'telefono_fijo': request.POST.get('telefono_fijo', '').strip(),
            'celular': request.POST.get('celular', '').strip(),
            'email': request.POST.get('email', '').strip(),
            'localidad': request.POST.get('localidad', '').strip(),
            'domicilio': request.POST.get('domicilio', '').strip(),
            'barrio': request.POST.get('barrio', '').strip(),
        }

        # Año de bautismo
        anio_bautismo = request.POST.get('anio_bautismo', '').strip()
        if anio_bautismo:
            try:
                datos['anio_bautismo'] = int(anio_bautismo)
            except ValueError:
                datos['anio_bautismo'] = None
        else:
            datos['anio_bautismo'] = None

        # Validación básica
        if not datos['apellidos'] or not datos['nombres']:
            messages.error(request, 'Apellidos y nombres son obligatorios.')
        elif not datos['sexo']:
            messages.error(request, 'Debe seleccionar el sexo.')
        else:
            # Procesar relaciones
            provincia_id = request.POST.get('provincia')
            estado_civil_id = request.POST.get('estado_civil')
            clase_id = request.POST.get('clase')
            grupo_id = request.POST.get('grupo')
            dones_ids = request.POST.getlist('dones')

            if es_nuevo:
                hermano = Hermano()

            # Asignar datos
            for campo, valor in datos.items():
                setattr(hermano, campo, valor)

            hermano.provincia_id = provincia_id if provincia_id else None
            hermano.estado_civil_id = estado_civil_id if estado_civil_id else None
            hermano.clase_id = clase_id if clase_id else None
            hermano.grupo_id = grupo_id if grupo_id else None

            # Manejar foto
            if 'foto' in request.FILES:
                hermano.foto = request.FILES['foto']

            hermano.save()

            # Asignar dones (ManyToMany requiere save primero)
            if dones_ids:
                hermano.dones.set(dones_ids)
            else:
                hermano.dones.clear()

            # Limpiar sesión y mostrar éxito
            request.session.pop('acceso_miembros_verificado', None)
            return redirect('miembros:exito')

    context = {
        'hermano': hermano,
        'es_nuevo': es_nuevo,
        'provincias': provincias,
        'estados_civiles': estados_civiles,
        'clases': clases,
        'grupos': grupos,
        'dones': dones,
    }
    return render(request, 'miembros/actualizar_editar.html', context)


def actualizar_datos_exito(request):
    """
    Paso 4: Mensaje de éxito
    """
    return render(request, 'miembros/actualizar_exito.html')


def cerrar_sesion_miembros(request):
    """Cerrar sesión de actualización de datos"""
    request.session.pop('acceso_miembros_verificado', None)
    return redirect('miembros:acceso')
