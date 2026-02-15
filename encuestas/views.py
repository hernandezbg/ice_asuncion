import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.views.decorators.http import require_POST, require_GET
from django.utils import timezone
from django.db.models import Avg, Count


def superuser_required(view_func):
    """Decorador que requiere que el usuario sea superusuario."""
    decorated_view = user_passes_test(
        lambda u: u.is_authenticated and u.is_superuser,
        login_url='/panel/login/'
    )(view_func)
    return decorated_view

from .models import Encuesta, Pregunta, Participante, Respuesta
from .forms import (EncuestaForm, PreguntaOpinionForm, PreguntaTriviaForm,
                    PreguntaVotacionForm, UnirseEncuestaForm)


# =============================================================================
# VISTAS PÚBLICAS (PARTICIPANTES)
# =============================================================================

def acceso_encuesta(request, codigo):
    """Página de acceso para participantes con código de encuesta."""
    encuesta = get_object_or_404(Encuesta, codigo=codigo.upper())

    # Verificar que la encuesta esté activa o en vivo
    if encuesta.estado not in ['activa', 'en_vivo']:
        return render(request, 'encuestas/encuesta_no_disponible.html', {
            'encuesta': encuesta
        })

    if request.method == 'POST':
        form = UnirseEncuestaForm(request.POST)
        if form.is_valid():
            nombre = form.cleaned_data['nombre']

            # Crear participante
            participante = Participante.objects.create(
                encuesta=encuesta,
                nombre=nombre
            )

            return redirect('encuestas:participar', session_id=participante.session_id)
    else:
        form = UnirseEncuestaForm()

    return render(request, 'encuestas/acceso.html', {
        'encuesta': encuesta,
        'form': form
    })


def participar(request, session_id):
    """Vista principal del participante para responder preguntas."""
    participante = get_object_or_404(Participante, session_id=session_id)
    encuesta = participante.encuesta

    # Actualizar última actividad
    participante.ultima_actividad = timezone.now()
    participante.save(update_fields=['ultima_actividad'])

    # Si la encuesta finalizó, mostrar resultado
    if encuesta.estado == 'finalizada':
        return redirect('encuestas:resultado_participante', session_id=session_id)

    # Si no está en vivo, mostrar espera
    if encuesta.estado != 'en_vivo':
        return render(request, 'encuestas/espera.html', {
            'participante': participante,
            'encuesta': encuesta
        })

    # Obtener pregunta actual
    pregunta_actual = encuesta.pregunta_actual_obj()

    # Verificar si ya respondió esta pregunta
    ya_respondio = False
    if pregunta_actual:
        ya_respondio = participante.ha_respondido_pregunta(pregunta_actual)

    # Seleccionar template según tipo de encuesta
    if encuesta.tipo == 'trivia':
        template = 'encuestas/participante_trivia.html'
    elif encuesta.tipo == 'votacion':
        template = 'encuestas/participante_votacion.html'
    else:
        template = 'encuestas/participante.html'

    return render(request, template, {
        'participante': participante,
        'encuesta': encuesta,
        'pregunta': pregunta_actual,
        'ya_respondio': ya_respondio,
        'pregunta_num': encuesta.pregunta_actual + 1,
        'total_preguntas': encuesta.total_preguntas()
    })


@require_POST
def responder(request, session_id):
    """Procesa la respuesta de un participante."""
    participante = get_object_or_404(Participante, session_id=session_id)
    encuesta = participante.encuesta

    # Validar estado
    if encuesta.estado != 'en_vivo':
        return JsonResponse({'error': 'La encuesta no está en vivo'}, status=400)

    pregunta_actual = encuesta.pregunta_actual_obj()
    if not pregunta_actual:
        return JsonResponse({'error': 'No hay pregunta activa'}, status=400)

    # Verificar si ya respondió
    if participante.ha_respondido_pregunta(pregunta_actual):
        return JsonResponse({'error': 'Ya respondiste esta pregunta'}, status=400)

    # Procesar según tipo de encuesta
    if encuesta.tipo == 'opinion':
        # Obtener valor de respuesta (1-5)
        try:
            valor = int(request.POST.get('valor', 0))
            if valor < 1 or valor > 5:
                raise ValueError()
        except (ValueError, TypeError):
            return JsonResponse({'error': 'Valor de respuesta inválido'}, status=400)

        # Crear respuesta de opinión
        Respuesta.objects.create(
            participante=participante,
            pregunta=pregunta_actual,
            valor=valor
        )

        return JsonResponse({'success': True, 'mensaje': 'Respuesta registrada'})

    elif encuesta.tipo == 'trivia':
        # Obtener opción elegida y tiempo de respuesta
        opcion = request.POST.get('opcion', '').upper()
        tiempo_respuesta = request.POST.get('tiempo', None)

        if opcion not in ['A', 'B', 'C', 'D']:
            return JsonResponse({'error': 'Opción inválida'}, status=400)

        # Verificar si es correcta
        es_correcta = opcion == pregunta_actual.respuesta_correcta

        # Calcular tiempo de respuesta
        tiempo_float = None
        if tiempo_respuesta:
            try:
                tiempo_float = float(tiempo_respuesta)
            except (ValueError, TypeError):
                pass

        # Crear respuesta
        respuesta = Respuesta.objects.create(
            participante=participante,
            pregunta=pregunta_actual,
            opcion_elegida=opcion,
            es_correcta=es_correcta,
            tiempo_respuesta=tiempo_float
        )

        # Calcular y asignar puntos
        puntos = respuesta.calcular_puntos_trivia()
        respuesta.puntos_obtenidos = puntos
        respuesta.save(update_fields=['puntos_obtenidos'])

        # Actualizar puntos del participante
        participante.agregar_puntos(puntos, es_correcta)

        return JsonResponse({
            'success': True,
            'es_correcta': es_correcta,
            'respuesta_correcta': pregunta_actual.respuesta_correcta,
            'puntos_obtenidos': puntos,
            'puntos_totales': participante.puntos_totales,
            'posicion': participante.posicion_ranking()
        })

    else:  # votacion
        # Obtener opción elegida
        opcion = request.POST.get('opcion', '').upper()

        if opcion not in ['A', 'B', 'C', 'D']:
            return JsonResponse({'error': 'Opción inválida'}, status=400)

        # Crear respuesta de votación
        Respuesta.objects.create(
            participante=participante,
            pregunta=pregunta_actual,
            opcion_elegida=opcion
        )

        return JsonResponse({'success': True, 'mensaje': 'Voto registrado'})


@require_GET
def poll_participante(request, session_id):
    """Long polling para actualizar estado del participante."""
    participante = get_object_or_404(Participante, session_id=session_id)
    encuesta = participante.encuesta

    # Actualizar última actividad
    participante.ultima_actividad = timezone.now()
    participante.save(update_fields=['ultima_actividad'])

    # Obtener pregunta actual
    pregunta_actual = encuesta.pregunta_actual_obj()
    pregunta_data = None

    if pregunta_actual:
        pregunta_data = {
            'id': pregunta_actual.id,
            'texto': pregunta_actual.texto,
            'numero': encuesta.pregunta_actual + 1,
            'imagen_url': pregunta_actual.imagen_url,
            'ya_respondio': participante.ha_respondido_pregunta(pregunta_actual)
        }

        if encuesta.tipo == 'opinion':
            pregunta_data['etiquetas'] = [
                pregunta_actual.etiqueta_1,
                pregunta_actual.etiqueta_2,
                pregunta_actual.etiqueta_3,
                pregunta_actual.etiqueta_4,
                pregunta_actual.etiqueta_5,
            ]
        else:
            pregunta_data['opciones'] = pregunta_actual.get_opciones()
            pregunta_data['tiempo_limite'] = pregunta_actual.get_tiempo_limite()

    # Datos adicionales para trivia
    trivia_data = None
    if encuesta.tipo == 'trivia':
        trivia_data = {
            'puntos_totales': participante.puntos_totales,
            'posicion': participante.posicion_ranking(),
            'racha': participante.racha_actual
        }

    return JsonResponse({
        'estado': encuesta.estado,
        'tipo': encuesta.tipo,
        'pregunta_actual': encuesta.pregunta_actual,
        'mostrar_resultados': encuesta.mostrar_resultados,
        'total_preguntas': encuesta.total_preguntas(),
        'pregunta': pregunta_data,
        'trivia': trivia_data
    })


def resultado_participante(request, session_id):
    """Muestra el resultado final del participante."""
    participante = get_object_or_404(Participante, session_id=session_id)
    encuesta = participante.encuesta

    resultado = participante.calcular_resultado_final()

    if encuesta.tipo == 'trivia':
        # Para trivia, mostrar ranking
        ranking = list(encuesta.ranking_participantes()[:10])
        return render(request, 'encuestas/resultado_trivia.html', {
            'participante': participante,
            'encuesta': encuesta,
            'resultado': resultado,
            'ranking': ranking,
            'es_ganador': resultado.get('posicion') == 1
        })

    elif encuesta.tipo == 'votacion':
        # Para votación, mostrar resultados de opciones
        resultados_preguntas = []
        for pregunta in encuesta.preguntas.order_by('orden'):
            stats = pregunta.estadisticas()
            resultados_preguntas.append({
                'pregunta': pregunta,
                'stats': stats
            })

        return render(request, 'encuestas/resultado_votacion.html', {
            'participante': participante,
            'encuesta': encuesta,
            'resultados_preguntas': resultados_preguntas
        })

    else:
        # Para opinión (comportamiento original)
        interpretacion = encuesta.interpretar_porcentaje(resultado['porcentaje'])

        respuestas = []
        for pregunta in encuesta.preguntas.order_by('orden'):
            respuesta = participante.respuestas.filter(pregunta=pregunta).first()
            respuestas.append({
                'pregunta': pregunta,
                'respuesta': respuesta,
                'etiqueta': pregunta.get_etiqueta(respuesta.valor) if respuesta and respuesta.valor else None
            })

        return render(request, 'encuestas/resultado_final.html', {
            'participante': participante,
            'encuesta': encuesta,
            'resultado': resultado,
            'interpretacion': interpretacion,
            'respuestas': respuestas
        })


# =============================================================================
# VISTAS DE PANEL (ADMIN)
# =============================================================================

@superuser_required
def panel_lista(request):
    """Lista de encuestas para administradores."""
    encuestas = Encuesta.objects.all()

    return render(request, 'encuestas/panel/lista.html', {
        'encuestas': encuestas
    })


@superuser_required
def panel_crear(request):
    """Crear nueva encuesta."""
    if request.method == 'POST':
        form = EncuestaForm(request.POST)
        if form.is_valid():
            encuesta = form.save()
            messages.success(request, f'Encuesta "{encuesta.titulo}" creada exitosamente.')
            return redirect('encuestas:panel_preguntas', encuesta_id=encuesta.id)
    else:
        form = EncuestaForm()

    return render(request, 'encuestas/panel/crear.html', {
        'form': form
    })


@superuser_required
def panel_editar(request, encuesta_id):
    """Editar encuesta existente."""
    encuesta = get_object_or_404(Encuesta, id=encuesta_id)

    if request.method == 'POST':
        form = EncuestaForm(request.POST, instance=encuesta)
        if form.is_valid():
            form.save()
            messages.success(request, 'Encuesta actualizada exitosamente.')
            return redirect('encuestas:panel_lista')
    else:
        form = EncuestaForm(instance=encuesta)

    return render(request, 'encuestas/panel/crear.html', {
        'form': form,
        'encuesta': encuesta,
        'editar': True
    })


@superuser_required
def panel_eliminar(request, encuesta_id):
    """Eliminar encuesta."""
    encuesta = get_object_or_404(Encuesta, id=encuesta_id)

    if request.method == 'POST':
        titulo = encuesta.titulo
        encuesta.delete()
        messages.success(request, f'Encuesta "{titulo}" eliminada.')
        return redirect('encuestas:panel_lista')

    return render(request, 'encuestas/panel/confirmar_eliminar.html', {
        'encuesta': encuesta
    })


@superuser_required
def panel_preguntas(request, encuesta_id):
    """Gestión de preguntas de una encuesta."""
    encuesta = get_object_or_404(Encuesta, id=encuesta_id)
    preguntas = encuesta.preguntas.order_by('orden')

    # Seleccionar formulario según tipo
    if encuesta.tipo == 'trivia':
        FormClass = PreguntaTriviaForm
    elif encuesta.tipo == 'votacion':
        FormClass = PreguntaVotacionForm
    else:
        FormClass = PreguntaOpinionForm

    if request.method == 'POST':
        form = FormClass(request.POST)
        if form.is_valid():
            pregunta = form.save(commit=False)
            pregunta.encuesta = encuesta
            pregunta.orden = encuesta.preguntas.count()
            pregunta.save()
            messages.success(request, 'Pregunta agregada.')
            return redirect('encuestas:panel_preguntas', encuesta_id=encuesta.id)
    else:
        form = FormClass()

    # Seleccionar template según tipo
    if encuesta.tipo == 'trivia':
        template = 'encuestas/panel/preguntas_trivia.html'
    elif encuesta.tipo == 'votacion':
        template = 'encuestas/panel/preguntas_votacion.html'
    else:
        template = 'encuestas/panel/preguntas.html'

    return render(request, template, {
        'encuesta': encuesta,
        'preguntas': preguntas,
        'form': form
    })


@superuser_required
@require_POST
def panel_pregunta_eliminar(request, encuesta_id, pregunta_id):
    """Eliminar pregunta."""
    encuesta = get_object_or_404(Encuesta, id=encuesta_id)
    pregunta = get_object_or_404(Pregunta, id=pregunta_id, encuesta=encuesta)

    pregunta.delete()

    # Reordenar preguntas
    for i, p in enumerate(encuesta.preguntas.order_by('orden')):
        p.orden = i
        p.save(update_fields=['orden'])

    messages.success(request, 'Pregunta eliminada.')
    return redirect('encuestas:panel_preguntas', encuesta_id=encuesta.id)


@superuser_required
def panel_pregunta_editar(request, encuesta_id, pregunta_id):
    """Editar pregunta existente."""
    encuesta = get_object_or_404(Encuesta, id=encuesta_id)
    pregunta = get_object_or_404(Pregunta, id=pregunta_id, encuesta=encuesta)

    # Seleccionar formulario según tipo
    if encuesta.tipo == 'trivia':
        FormClass = PreguntaTriviaForm
    elif encuesta.tipo == 'votacion':
        FormClass = PreguntaVotacionForm
    else:
        FormClass = PreguntaOpinionForm

    if request.method == 'POST':
        form = FormClass(request.POST, instance=pregunta)
        if form.is_valid():
            form.save()
            messages.success(request, 'Pregunta actualizada.')
            return redirect('encuestas:panel_preguntas', encuesta_id=encuesta.id)
    else:
        form = FormClass(instance=pregunta)

    return render(request, 'encuestas/panel/pregunta_editar.html', {
        'encuesta': encuesta,
        'pregunta': pregunta,
        'form': form
    })


@superuser_required
@require_POST
def panel_pregunta_mover(request, encuesta_id, pregunta_id):
    """Mover pregunta arriba o abajo."""
    encuesta = get_object_or_404(Encuesta, id=encuesta_id)
    pregunta = get_object_or_404(Pregunta, id=pregunta_id, encuesta=encuesta)
    direccion = request.POST.get('direccion')

    preguntas = list(encuesta.preguntas.order_by('orden'))
    idx = preguntas.index(pregunta)

    if direccion == 'arriba' and idx > 0:
        preguntas[idx], preguntas[idx - 1] = preguntas[idx - 1], preguntas[idx]
    elif direccion == 'abajo' and idx < len(preguntas) - 1:
        preguntas[idx], preguntas[idx + 1] = preguntas[idx + 1], preguntas[idx]

    for i, p in enumerate(preguntas):
        p.orden = i
        p.save(update_fields=['orden'])

    return redirect('encuestas:panel_preguntas', encuesta_id=encuesta.id)


@superuser_required
@require_POST
def panel_activar(request, encuesta_id):
    """Activar encuesta (permite que participantes se unan)."""
    encuesta = get_object_or_404(Encuesta, id=encuesta_id)

    if encuesta.preguntas.count() == 0:
        messages.error(request, 'La encuesta debe tener al menos una pregunta.')
        return redirect('encuestas:panel_preguntas', encuesta_id=encuesta.id)

    # Validaciones adicionales según tipo
    if encuesta.tipo == 'trivia':
        # Verificar que todas las preguntas tengan respuesta correcta
        for pregunta in encuesta.preguntas.all():
            if not pregunta.respuesta_correcta:
                messages.error(request, f'La pregunta "{pregunta.texto[:30]}..." no tiene respuesta correcta.')
                return redirect('encuestas:panel_preguntas', encuesta_id=encuesta.id)

    encuesta.estado = 'activa'
    encuesta.save(update_fields=['estado'])
    messages.success(request, f'Encuesta activada. Código: {encuesta.codigo}')

    return redirect('encuestas:panel_lista')


@superuser_required
def panel_presentador(request, encuesta_id):
    """Vista del presentador para controlar la encuesta en vivo."""
    encuesta = get_object_or_404(Encuesta, id=encuesta_id)
    preguntas = encuesta.preguntas.order_by('orden')

    # Seleccionar template según tipo
    if encuesta.tipo == 'trivia':
        template = 'encuestas/panel/presentador_trivia.html'
    elif encuesta.tipo == 'votacion':
        template = 'encuestas/panel/presentador_votacion.html'
    else:
        template = 'encuestas/panel/presentador.html'

    return render(request, template, {
        'encuesta': encuesta,
        'preguntas': preguntas
    })


@superuser_required
@require_POST
def panel_iniciar(request, encuesta_id):
    """Inicia la encuesta en vivo."""
    encuesta = get_object_or_404(Encuesta, id=encuesta_id)

    if encuesta.preguntas.count() == 0:
        return JsonResponse({'error': 'La encuesta no tiene preguntas'}, status=400)

    encuesta.estado = 'en_vivo'
    encuesta.pregunta_actual = 0
    encuesta.mostrar_resultados = False
    encuesta.save(update_fields=['estado', 'pregunta_actual', 'mostrar_resultados'])

    # Marcar timestamp de inicio de la primera pregunta (para trivia)
    primera_pregunta = encuesta.pregunta_actual_obj()
    if primera_pregunta:
        primera_pregunta.activada_en = timezone.now()
        primera_pregunta.save(update_fields=['activada_en'])

    return JsonResponse({'success': True, 'mensaje': 'Encuesta iniciada'})


@superuser_required
@require_POST
def panel_siguiente(request, encuesta_id):
    """Avanza a la siguiente pregunta."""
    encuesta = get_object_or_404(Encuesta, id=encuesta_id)

    if encuesta.estado != 'en_vivo':
        return JsonResponse({'error': 'La encuesta no está en vivo'}, status=400)

    total_preguntas = encuesta.preguntas.count()

    if encuesta.pregunta_actual < total_preguntas - 1:
        encuesta.pregunta_actual += 1
        encuesta.mostrar_resultados = False
        encuesta.save(update_fields=['pregunta_actual', 'mostrar_resultados'])

        # Marcar timestamp de la nueva pregunta (para trivia)
        nueva_pregunta = encuesta.pregunta_actual_obj()
        if nueva_pregunta:
            nueva_pregunta.activada_en = timezone.now()
            nueva_pregunta.save(update_fields=['activada_en'])

        return JsonResponse({
            'success': True,
            'pregunta_actual': encuesta.pregunta_actual,
            'es_ultima': encuesta.pregunta_actual >= total_preguntas - 1
        })
    else:
        return JsonResponse({
            'success': False,
            'mensaje': 'Ya es la última pregunta',
            'es_ultima': True
        })


@superuser_required
@require_POST
def panel_anterior(request, encuesta_id):
    """Retrocede a la pregunta anterior."""
    encuesta = get_object_or_404(Encuesta, id=encuesta_id)

    if encuesta.estado != 'en_vivo':
        return JsonResponse({'error': 'La encuesta no está en vivo'}, status=400)

    if encuesta.pregunta_actual > 0:
        encuesta.pregunta_actual -= 1
        encuesta.mostrar_resultados = False
        encuesta.save(update_fields=['pregunta_actual', 'mostrar_resultados'])
        return JsonResponse({
            'success': True,
            'pregunta_actual': encuesta.pregunta_actual,
            'es_primera': encuesta.pregunta_actual == 0
        })
    else:
        return JsonResponse({
            'success': False,
            'mensaje': 'Ya es la primera pregunta',
            'es_primera': True
        })


@superuser_required
@require_POST
def panel_mostrar_resultados(request, encuesta_id):
    """Toggle mostrar/ocultar resultados en tiempo real."""
    encuesta = get_object_or_404(Encuesta, id=encuesta_id)

    encuesta.mostrar_resultados = not encuesta.mostrar_resultados
    encuesta.save(update_fields=['mostrar_resultados'])

    return JsonResponse({
        'success': True,
        'mostrar_resultados': encuesta.mostrar_resultados
    })


@superuser_required
@require_POST
def panel_finalizar(request, encuesta_id):
    """Finaliza la encuesta."""
    encuesta = get_object_or_404(Encuesta, id=encuesta_id)

    encuesta.estado = 'finalizada'
    encuesta.save(update_fields=['estado'])

    return JsonResponse({'success': True, 'mensaje': 'Encuesta finalizada'})


@superuser_required
@require_POST
def panel_reiniciar(request, encuesta_id):
    """Reinicia la encuesta (elimina respuestas y participantes)."""
    encuesta = get_object_or_404(Encuesta, id=encuesta_id)

    # Eliminar todas las respuestas y participantes
    Respuesta.objects.filter(participante__encuesta=encuesta).delete()
    Participante.objects.filter(encuesta=encuesta).delete()

    # Reiniciar estado
    encuesta.estado = 'activa'
    encuesta.pregunta_actual = 0
    encuesta.mostrar_resultados = False
    encuesta.save(update_fields=['estado', 'pregunta_actual', 'mostrar_resultados'])

    # Limpiar timestamps de preguntas
    encuesta.preguntas.update(activada_en=None)

    messages.success(request, 'Encuesta reiniciada.')
    return redirect('encuestas:panel_lista')


@superuser_required
@require_GET
def panel_poll(request, encuesta_id):
    """Long polling para actualizar resultados del presentador."""
    encuesta = get_object_or_404(Encuesta, id=encuesta_id)

    # Obtener pregunta actual y estadísticas
    pregunta_actual = encuesta.pregunta_actual_obj()
    estadisticas = None

    if pregunta_actual:
        estadisticas = pregunta_actual.estadisticas()

    # Obtener participantes conectados
    limite = timezone.now() - timezone.timedelta(seconds=30)
    participantes_conectados = encuesta.participantes.filter(ultima_actividad__gte=limite).count()
    total_participantes = encuesta.participantes.count()

    # Contar respuestas de la pregunta actual
    respuestas_pregunta = 0
    todos_respondieron = False
    avanzo_automatico = False

    if pregunta_actual:
        respuestas_pregunta = Respuesta.objects.filter(pregunta=pregunta_actual).count()

        # Verificar si todos los participantes respondieron
        if total_participantes > 0 and respuestas_pregunta >= total_participantes:
            todos_respondieron = True

            # Auto-avanzar si está habilitado y no es la última pregunta
            auto_avanzar = request.GET.get('auto_avanzar', 'true') == 'true'
            total_preguntas = encuesta.preguntas.count()

            if auto_avanzar and encuesta.pregunta_actual < total_preguntas - 1:
                encuesta.pregunta_actual += 1
                encuesta.mostrar_resultados = False
                encuesta.save(update_fields=['pregunta_actual', 'mostrar_resultados'])
                avanzo_automatico = True

                # Marcar timestamp de la nueva pregunta
                nueva_pregunta = encuesta.pregunta_actual_obj()
                if nueva_pregunta:
                    nueva_pregunta.activada_en = timezone.now()
                    nueva_pregunta.save(update_fields=['activada_en'])

                # Actualizar pregunta actual y estadísticas después del avance
                pregunta_actual = nueva_pregunta
                if pregunta_actual:
                    estadisticas = pregunta_actual.estadisticas()
                    respuestas_pregunta = Respuesta.objects.filter(pregunta=pregunta_actual).count()

    # Lista de participantes con estado de conexión
    participantes_lista = []
    if encuesta.tipo == 'trivia':
        # Para trivia, ordenar por puntos
        for p in encuesta.participantes.order_by('-puntos_totales')[:20]:
            participantes_lista.append({
                'nombre': p.nombre,
                'conectado': p.ultima_actividad >= limite,
                'session_id': str(p.session_id)[:8],
                'puntos': p.puntos_totales,
                'posicion': p.posicion_ranking()
            })
    else:
        for p in encuesta.participantes.order_by('-creado')[:20]:
            participantes_lista.append({
                'nombre': p.nombre,
                'conectado': p.ultima_actividad >= limite,
                'session_id': str(p.session_id)[:8]
            })

    # Datos de ranking para trivia
    ranking = None
    if encuesta.tipo == 'trivia':
        ranking = [
            {
                'nombre': p.nombre,
                'puntos': p.puntos_totales,
                'session_id': str(p.session_id)[:8]
            }
            for p in encuesta.ranking_participantes()[:5]
        ]

    return JsonResponse({
        'estado': encuesta.estado,
        'tipo': encuesta.tipo,
        'pregunta_actual': encuesta.pregunta_actual,
        'mostrar_resultados': encuesta.mostrar_resultados,
        'total_preguntas': encuesta.total_preguntas(),
        'participantes_conectados': participantes_conectados,
        'total_participantes': total_participantes,
        'respuestas_pregunta': respuestas_pregunta,
        'estadisticas': estadisticas,
        'todos_respondieron': todos_respondieron,
        'avanzo_automatico': avanzo_automatico,
        'participantes': participantes_lista,
        'ranking': ranking
    })


@superuser_required
def panel_resultados(request, encuesta_id):
    """Vista de resultados finales de la encuesta."""
    encuesta = get_object_or_404(Encuesta, id=encuesta_id)
    preguntas = encuesta.preguntas.order_by('orden')

    if encuesta.tipo == 'trivia':
        # Resultados de trivia
        ranking = encuesta.ranking_participantes()

        resultados_preguntas = []
        for pregunta in preguntas:
            stats = pregunta.estadisticas()
            stats['pregunta'] = pregunta
            resultados_preguntas.append(stats)

        return render(request, 'encuestas/panel/resultados_trivia.html', {
            'encuesta': encuesta,
            'ranking': ranking,
            'resultados_preguntas': resultados_preguntas
        })

    elif encuesta.tipo == 'votacion':
        # Resultados de votación
        resultados_preguntas = []
        for pregunta in preguntas:
            stats = pregunta.estadisticas()
            stats['pregunta'] = pregunta
            resultados_preguntas.append(stats)

        return render(request, 'encuestas/panel/resultados_votacion.html', {
            'encuesta': encuesta,
            'resultados_preguntas': resultados_preguntas
        })

    else:
        # Resultados de opinión (original)
        resultados_preguntas = []
        for pregunta in preguntas:
            stats = pregunta.estadisticas()
            stats['pregunta'] = pregunta
            stats['interpretacion'] = encuesta.interpretar_porcentaje(stats['porcentaje'])
            resultados_preguntas.append(stats)

        # Calcular promedio general
        total_respuestas = Respuesta.objects.filter(pregunta__encuesta=encuesta, valor__isnull=False)
        if total_respuestas.exists():
            promedio_general = total_respuestas.aggregate(avg=Avg('valor'))['avg']
            porcentaje_general = ((promedio_general - 1) / 4) * 100
        else:
            promedio_general = 0
            porcentaje_general = 0

        interpretacion_general = encuesta.interpretar_porcentaje(porcentaje_general)

        # Lista de participantes con sus resultados
        participantes = []
        for p in encuesta.participantes.all():
            resultado = p.calcular_resultado_final()
            participantes.append({
                'participante': p,
                'resultado': resultado,
                'interpretacion': encuesta.interpretar_porcentaje(resultado['porcentaje'])
            })

        return render(request, 'encuestas/panel/resultados.html', {
            'encuesta': encuesta,
            'resultados_preguntas': resultados_preguntas,
            'promedio_general': round(promedio_general, 2) if promedio_general else 0,
            'porcentaje_general': round(porcentaje_general, 1) if porcentaje_general else 0,
            'interpretacion_general': interpretacion_general,
            'participantes': participantes
        })


@superuser_required
def panel_exportar(request, encuesta_id):
    """Exportar resultados a CSV."""
    encuesta = get_object_or_404(Encuesta, id=encuesta_id)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="encuesta_{encuesta.codigo}.csv"'

    writer = csv.writer(response)

    preguntas = list(encuesta.preguntas.order_by('orden'))

    if encuesta.tipo == 'trivia':
        # Exportar trivia
        cabecera = ['Posición', 'Participante', 'Puntos', 'Correctas', 'Fecha']
        for i, p in enumerate(preguntas):
            cabecera.append(f'P{i+1}')
        writer.writerow(cabecera)

        for participante in encuesta.ranking_participantes():
            fila = [
                participante.posicion_ranking(),
                participante.nombre,
                participante.puntos_totales,
                participante.respuestas_correctas,
                participante.creado.strftime('%Y-%m-%d %H:%M')
            ]
            for pregunta in preguntas:
                respuesta = participante.respuestas.filter(pregunta=pregunta).first()
                if respuesta:
                    fila.append(f"{respuesta.opcion_elegida} ({'✓' if respuesta.es_correcta else '✗'})")
                else:
                    fila.append('')
            writer.writerow(fila)

    elif encuesta.tipo == 'votacion':
        # Exportar votación
        cabecera = ['Participante', 'Fecha']
        for i, p in enumerate(preguntas):
            cabecera.append(f'P{i+1}: {p.texto[:30]}')
        writer.writerow(cabecera)

        for participante in encuesta.participantes.all():
            fila = [participante.nombre, participante.creado.strftime('%Y-%m-%d %H:%M')]
            for pregunta in preguntas:
                respuesta = participante.respuestas.filter(pregunta=pregunta).first()
                fila.append(respuesta.opcion_elegida if respuesta else '')
            writer.writerow(fila)

        # Agregar resumen de votación
        writer.writerow([])
        writer.writerow(['RESUMEN DE VOTACIÓN'])
        for pregunta in preguntas:
            stats = pregunta.estadisticas()
            writer.writerow([f'Pregunta: {pregunta.texto}'])
            for item in stats.get('ranking', []):
                writer.writerow([f"  {item['letra']}: {item['texto']}", f"{item['votos']} votos"])

    else:
        # Exportar opinión (original)
        cabecera = ['Participante', 'Fecha']
        for i, p in enumerate(preguntas):
            cabecera.append(f'P{i+1}: {p.texto[:50]}')
        cabecera.extend(['Promedio', 'Porcentaje'])
        writer.writerow(cabecera)

        for participante in encuesta.participantes.all():
            fila = [participante.nombre, participante.creado.strftime('%Y-%m-%d %H:%M')]

            for pregunta in preguntas:
                respuesta = participante.respuestas.filter(pregunta=pregunta).first()
                fila.append(respuesta.valor if respuesta else '')

            resultado = participante.calcular_resultado_final()
            fila.extend([resultado['promedio'], f"{resultado['porcentaje']}%"])
            writer.writerow(fila)

        # Fila de promedios
        fila_promedios = ['PROMEDIO GENERAL', '']
        for pregunta in preguntas:
            stats = pregunta.estadisticas()
            fila_promedios.append(stats['promedio'])

        total_respuestas = Respuesta.objects.filter(pregunta__encuesta=encuesta, valor__isnull=False)
        if total_respuestas.exists():
            promedio_general = total_respuestas.aggregate(avg=Avg('valor'))['avg']
            porcentaje_general = ((promedio_general - 1) / 4) * 100
            fila_promedios.extend([round(promedio_general, 2), f"{round(porcentaje_general, 1)}%"])
        else:
            fila_promedios.extend(['', ''])

        writer.writerow(fila_promedios)

    return response
