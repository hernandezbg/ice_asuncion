from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
import unicodedata

import json

from .models import ClaseEscuela, Alumno, Asistencia, GRADO_CHOICES
from miembros.models import Hermano
from datetime import date, timedelta


def _quitar_acentos(texto):
    """Quita acentos de un texto para busqueda flexible"""
    if not texto:
        return ''
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    ).lower()


def _parsear_fecha_selects(post_data):
    """Parsea fecha de nacimiento desde 3 selects (dia, mes, anio)"""
    dia = post_data.get('nacimiento_dia', '').strip()
    mes = post_data.get('nacimiento_mes', '').strip()
    anio = post_data.get('nacimiento_anio', '').strip()

    if dia and mes and anio:
        try:
            from datetime import date
            return date(int(anio), int(mes), int(dia))
        except (ValueError, TypeError):
            return None
    return None


def acceso(request):
    """
    Pantalla de acceso: el maestro ingresa el codigo de su clase
    """
    # Si ya tiene acceso, ir a lista
    if request.session.get('escuela_clase_id'):
        return redirect('escuela:lista_alumnos')

    error = None
    clases = ClaseEscuela.objects.filter(activo=True)

    if request.method == 'POST':
        codigo = request.POST.get('codigo', '').strip().upper()

        if not codigo:
            error = 'Ingresa el código de acceso.'
        else:
            # Buscar clase por código
            try:
                clase = ClaseEscuela.objects.get(codigo_acceso__iexact=codigo, activo=True)
                request.session['escuela_clase_id'] = clase.id
                return redirect('escuela:lista_alumnos')
            except ClaseEscuela.DoesNotExist:
                error = 'Código de acceso incorrecto.'

    return render(request, 'escuela/acceso.html', {
        'error': error,
        'clases': clases,
    })


def lista_alumnos(request):
    """
    Lista de alumnos de la clase del maestro
    """
    clase_id = request.session.get('escuela_clase_id')
    if not clase_id:
        return redirect('escuela:acceso')

    clase = get_object_or_404(ClaseEscuela, id=clase_id, activo=True)
    alumnos = Alumno.objects.filter(clase=clase, activo=True)

    return render(request, 'escuela/lista_alumnos.html', {
        'clase': clase,
        'alumnos': alumnos,
    })


def alumno_crear(request):
    """
    Crear nuevo alumno - optimizado para carga rapida desde celular
    """
    clase_id = request.session.get('escuela_clase_id')
    if not clase_id:
        return redirect('escuela:acceso')

    clase = get_object_or_404(ClaseEscuela, id=clase_id, activo=True)

    if request.method == 'POST':
        apellidos = request.POST.get('apellidos', '').strip()
        nombres = request.POST.get('nombres', '').strip()
        grado_nivel = request.POST.get('grado_nivel', '').strip()
        observaciones = request.POST.get('observaciones', '').strip()

        fecha_nacimiento = _parsear_fecha_selects(request.POST)

        if not apellidos or not nombres:
            messages.error(request, 'Apellidos y nombres son obligatorios.')
        else:
            # Verificar duplicado en cualquier clase
            duplicado = Alumno.objects.filter(
                apellidos__iexact=apellidos,
                nombres__iexact=nombres,
                activo=True,
            ).first()

            if duplicado and 'confirmar_duplicado' not in request.POST:
                # Hay duplicado y no confirmo: mostrar advertencia
                return render(request, 'escuela/alumno_form.html', {
                    'clase': clase,
                    'grado_choices': GRADO_CHOICES,
                    'dias': range(1, 32),
                    'es_nuevo': True,
                    'duplicado': duplicado,
                    'form_data': request.POST,
                })

            Alumno.objects.create(
                apellidos=apellidos,
                nombres=nombres,
                fecha_nacimiento=fecha_nacimiento,
                grado_nivel=grado_nivel,
                clase=clase,
                observaciones=observaciones,
            )

            # Si pidio "guardar y cargar otro"
            if 'guardar_otro' in request.POST:
                messages.success(request, f'{nombres} {apellidos} registrado correctamente.')
                return redirect('escuela:alumno_crear')

            messages.success(request, f'{nombres} {apellidos} registrado correctamente.')
            return redirect('escuela:lista_alumnos')

    return render(request, 'escuela/alumno_form.html', {
        'clase': clase,
        'grado_choices': GRADO_CHOICES,
        'dias': range(1, 32),
        'es_nuevo': True,
    })


def alumno_editar(request, alumno_id):
    """
    Editar alumno existente
    """
    clase_id = request.session.get('escuela_clase_id')
    if not clase_id:
        return redirect('escuela:acceso')

    clase = get_object_or_404(ClaseEscuela, id=clase_id, activo=True)
    alumno = get_object_or_404(Alumno, id=alumno_id, clase=clase)

    if request.method == 'POST':
        apellidos = request.POST.get('apellidos', '').strip()
        nombres = request.POST.get('nombres', '').strip()
        grado_nivel = request.POST.get('grado_nivel', '').strip()
        observaciones = request.POST.get('observaciones', '').strip()

        fecha_nacimiento = _parsear_fecha_selects(request.POST)

        if not apellidos or not nombres:
            messages.error(request, 'Apellidos y nombres son obligatorios.')
        else:
            alumno.apellidos = apellidos
            alumno.nombres = nombres
            alumno.fecha_nacimiento = fecha_nacimiento
            alumno.grado_nivel = grado_nivel
            alumno.observaciones = observaciones
            alumno.save()

            messages.success(request, f'Datos de {nombres} {apellidos} actualizados.')
            return redirect('escuela:lista_alumnos')

    return render(request, 'escuela/alumno_form.html', {
        'clase': clase,
        'alumno': alumno,
        'grado_choices': GRADO_CHOICES,
        'dias': range(1, 32),
        'es_nuevo': False,
    })


def alumno_eliminar(request, alumno_id):
    """
    Eliminar (desactivar) alumno
    """
    clase_id = request.session.get('escuela_clase_id')
    if not clase_id:
        return redirect('escuela:acceso')

    clase = get_object_or_404(ClaseEscuela, id=clase_id, activo=True)
    alumno = get_object_or_404(Alumno, id=alumno_id, clase=clase)

    if request.method == 'POST':
        alumno.activo = False
        alumno.save()
        messages.success(request, f'{alumno.nombre_completo()} fue eliminado de la lista.')
        return redirect('escuela:lista_alumnos')

    return render(request, 'escuela/alumno_eliminar.html', {
        'clase': clase,
        'alumno': alumno,
    })


def buscar_hermanos(request):
    """
    API para autocompletado: busca hermanos por apellido/nombre
    """
    clase_id = request.session.get('escuela_clase_id')
    if not clase_id:
        return JsonResponse([], safe=False)

    q = request.GET.get('q', '').strip()
    if len(q) < 2:
        return JsonResponse([], safe=False)

    q_norm = _quitar_acentos(q)

    # Buscar en memoria con comparacion sin acentos
    todos = Hermano.objects.filter(activo=True).order_by('nombres', 'apellidos')
    resultados = []
    for h in todos:
        if (q_norm in _quitar_acentos(h.apellidos)
                or q_norm in _quitar_acentos(h.nombres)):
            resultados.append({
                'apellidos': h.apellidos,
                'nombres': h.nombres,
                'fecha_nacimiento': h.fecha_nacimiento.strftime('%Y-%m-%d') if h.fecha_nacimiento else '',
                'edad': h.edad(),
            })
            if len(resultados) >= 10:
                break

    return JsonResponse(resultados, safe=False)


def _domingo_mas_reciente():
    """Devuelve el domingo mas reciente (hoy si es domingo)"""
    hoy = date.today()
    dias_desde_domingo = hoy.weekday() + 1  # lunes=0 -> +1=1, domingo=6 -> +1=7
    if dias_desde_domingo == 7:
        return hoy
    return hoy - timedelta(days=dias_desde_domingo)


def _domingos_disponibles(n=8):
    """Devuelve los ultimos N domingos"""
    domingo = _domingo_mas_reciente()
    domingos = []
    for i in range(n):
        domingos.append(domingo - timedelta(weeks=i))
    return domingos


def asistencia_inicio(request):
    """
    Seleccionar domingo para pasar asistencia
    """
    clase_id = request.session.get('escuela_clase_id')
    if not clase_id:
        return redirect('escuela:acceso')

    clase = get_object_or_404(ClaseEscuela, id=clase_id, activo=True)
    total_alumnos = Alumno.objects.filter(clase=clase, activo=True).count()

    if total_alumnos < 5:
        messages.warning(request, 'Se necesitan al menos 5 alumnos para habilitar la asistencia.')
        return redirect('escuela:lista_alumnos')

    domingos = _domingos_disponibles()

    # Marcar domingos que ya tienen asistencia registrada
    domingos_info = []
    for domingo in domingos:
        registros = Asistencia.objects.filter(clase=clase, fecha=domingo).count()
        domingos_info.append({
            'fecha': domingo,
            'registros': registros,
            'completa': registros >= total_alumnos,
        })

    return render(request, 'escuela/asistencia_inicio.html', {
        'clase': clase,
        'domingos': domingos_info,
        'total_alumnos': total_alumnos,
    })


def asistencia_pasar(request, fecha_str):
    """
    Pasar lista: muestra alumno por alumno
    """
    clase_id = request.session.get('escuela_clase_id')
    if not clase_id:
        return redirect('escuela:acceso')

    clase = get_object_or_404(ClaseEscuela, id=clase_id, activo=True)

    try:
        from datetime import datetime
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
    except ValueError:
        return redirect('escuela:asistencia_inicio')

    alumnos = list(Alumno.objects.filter(clase=clase, activo=True).order_by('apellidos', 'nombres'))

    if len(alumnos) < 5:
        return redirect('escuela:lista_alumnos')

    # Obtener asistencias ya registradas para esta fecha
    asistencias_existentes = {
        a.alumno_id: a.presente
        for a in Asistencia.objects.filter(clase=clase, fecha=fecha)
    }

    # Armar lista con estado
    alumnos_data = []
    for alumno in alumnos:
        alumnos_data.append({
            'id': alumno.id,
            'nombres': alumno.nombres,
            'apellidos': alumno.apellidos,
            'edad': alumno.edad(),
            'estado': asistencias_existentes.get(alumno.id),  # None, True o False
        })

    return render(request, 'escuela/asistencia_pasar.html', {
        'clase': clase,
        'fecha': fecha,
        'alumnos_json': json.dumps(alumnos_data),
        'total': len(alumnos_data),
        'ya_registrados': len(asistencias_existentes),
    })


def asistencia_registrar(request):
    """
    API: registrar asistencia de un alumno (llamado via fetch)
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST requerido'}, status=405)

    clase_id = request.session.get('escuela_clase_id')
    if not clase_id:
        return JsonResponse({'error': 'Sin acceso'}, status=403)

    import json
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON invalido'}, status=400)

    alumno_id = data.get('alumno_id')
    fecha_str = data.get('fecha')
    presente = data.get('presente')

    if alumno_id is None or fecha_str is None or presente is None:
        return JsonResponse({'error': 'Datos incompletos'}, status=400)

    try:
        from datetime import datetime
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': 'Fecha invalida'}, status=400)

    clase = get_object_or_404(ClaseEscuela, id=clase_id, activo=True)
    alumno = get_object_or_404(Alumno, id=alumno_id, clase=clase)

    # Crear o actualizar
    asistencia, created = Asistencia.objects.update_or_create(
        alumno=alumno,
        fecha=fecha,
        defaults={
            'clase': clase,
            'presente': presente,
        }
    )

    return JsonResponse({'ok': True, 'created': created})


def asistencia_historial(request):
    """
    Historial de asistencias de la clase
    """
    clase_id = request.session.get('escuela_clase_id')
    if not clase_id:
        return redirect('escuela:acceso')

    clase = get_object_or_404(ClaseEscuela, id=clase_id, activo=True)

    # Ultimos 8 domingos con asistencia
    fechas = (Asistencia.objects.filter(clase=clase)
              .values_list('fecha', flat=True)
              .distinct()
              .order_by('-fecha')[:8])

    historial = []
    for fecha in fechas:
        registros = Asistencia.objects.filter(clase=clase, fecha=fecha)
        presentes = registros.filter(presente=True).count()
        ausentes = registros.filter(presente=False).count()
        total = presentes + ausentes
        historial.append({
            'fecha': fecha,
            'presentes': presentes,
            'ausentes': ausentes,
            'total': total,
            'porcentaje': round(presentes * 100 / total) if total > 0 else 0,
        })

    return render(request, 'escuela/asistencia_historial.html', {
        'clase': clase,
        'historial': historial,
    })


def asistencia_detalle(request, fecha_str):
    """
    Detalle de asistencia de un domingo: lista de presentes y ausentes
    """
    clase_id = request.session.get('escuela_clase_id')
    if not clase_id:
        return redirect('escuela:acceso')

    clase = get_object_or_404(ClaseEscuela, id=clase_id, activo=True)

    try:
        from datetime import datetime
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
    except ValueError:
        return redirect('escuela:asistencia_historial')

    registros = (Asistencia.objects.filter(clase=clase, fecha=fecha)
                 .select_related('alumno')
                 .order_by('alumno__apellidos', 'alumno__nombres'))

    presentes = [r for r in registros if r.presente]
    ausentes = [r for r in registros if not r.presente]
    total = len(registros)
    porcentaje = round(len(presentes) * 100 / total) if total > 0 else 0

    return render(request, 'escuela/asistencia_detalle.html', {
        'clase': clase,
        'fecha': fecha,
        'presentes': presentes,
        'ausentes': ausentes,
        'total': total,
        'porcentaje': porcentaje,
    })


def cerrar_sesion(request):
    """Cerrar sesion de escuela"""
    request.session.pop('escuela_clase_id', None)
    return redirect('escuela:acceso')
