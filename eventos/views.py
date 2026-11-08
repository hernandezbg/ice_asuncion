import base64
import io
from collections import defaultdict

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from miembros.models import Hermano
from miembros.views import quitar_acentos, verificar_recaptcha
from escuela.models import Alumno

from .forms import EventoForm
from .models import (Evento, Inscripcion, Inscripto,
                     CATEGORIA_ADULTO, CATEGORIA_NINO, CATEGORIA_GRATIS)


MAX_PERSONAS = 20
MAX_SUGERENCIAS = 8


def es_staff(user):
    return user.is_staff


def _norm(texto):
    return ' '.join(quitar_acentos(texto or '').split())


# =============================================================================
# Publico
# =============================================================================

def _leer_personas(request, evento):
    """
    Leo las filas de personas del POST. La fila 0 es el responsable.
    Devuelvo (personas, errores). Cada persona es un dict listo para crear Inscripto.
    """
    apellidos = request.POST.getlist('apellido')
    nombres = request.POST.getlist('nombre')
    parentescos = request.POST.getlist('parentesco')
    edades = request.POST.getlist('edad')
    hermano_ids = request.POST.getlist('hermano_id')
    alumno_ids = request.POST.getlist('alumno_id')

    parentescos_validos = {k for k, _ in Inscripto.PARENTESCO_CHOICES} - {Inscripto.RESPONSABLE}

    def get(lista, i):
        return lista[i].strip() if i < len(lista) else ''

    personas = []
    errores = []
    for i in range(len(apellidos)):
        apellido = get(apellidos, i)
        nombre = get(nombres, i)
        es_responsable = (i == 0)

        if not es_responsable and not apellido and not nombre:
            continue  # fila vacia, la ignoro

        n = 'El responsable' if es_responsable else f'La persona {i + 1}'
        if len(apellido) < 2 or len(nombre) < 2:
            errores.append(f'{n}: completá apellido y nombre.')
            continue

        edad_str = get(edades, i)
        if not (edad_str.isdigit() and int(edad_str) <= 120):
            errores.append(f'{apellido}, {nombre}: ingresá la edad.')
            continue
        edad = int(edad_str)

        if es_responsable:
            parentesco = Inscripto.RESPONSABLE
            if edad <= evento.edad_max_nino:
                errores.append(f'El responsable debe tener {evento.edad_max_nino + 1} años o más.')
                continue
        else:
            parentesco = get(parentescos, i)
            if parentesco not in parentescos_validos:
                parentesco = 'otro'

        # Vinculo con la base solo si el nombre coincide con el registro elegido
        hermano = alumno = None
        hid, aid = get(hermano_ids, i), get(alumno_ids, i)
        if hid.isdigit():
            h = Hermano.objects.filter(pk=int(hid)).first()
            if h and _norm(h.apellidos) == _norm(apellido) and _norm(h.nombres) == _norm(nombre):
                hermano = h
        if aid.isdigit() and not hermano:
            a = Alumno.objects.filter(pk=int(aid)).first()
            if a and _norm(a.apellidos) == _norm(apellido) and _norm(a.nombres) == _norm(nombre):
                alumno = a

        personas.append({
            'apellido': apellido[:200],
            'nombre': nombre[:200],
            'parentesco': parentesco,
            'edad': edad,
            'hermano': hermano,
            'alumno': alumno,
        })

    if len(personas) > MAX_PERSONAS:
        errores.append(f'Máximo {MAX_PERSONAS} personas por inscripción.')
    return personas, errores


MSJ_CELULAR_AR = ('Ingresá el celular con código de área sin el 0 y el número sin el 15 '
                  '(10 números en total). Ej: 351 1234567')


def normalizar_celular(valor):
    """
    Devuelvo (celular_normalizado, error).
    Argentina: codigo de area sin 0 + numero sin 15 = 10 digitos -> '+54 9 3511234567'.
    Otros paises: '+<codigo><numero>' con 8 a 15 digitos.
    """
    valor = (valor or '').strip()
    digitos = ''.join(c for c in valor if c.isdigit())
    if valor.startswith('+') and not digitos.startswith('54'):
        if 8 <= len(digitos) <= 15:
            return f'+{digitos}', None
        return None, 'Ingresá un celular válido.'

    nacional = digitos[2:] if valor.startswith('+') else digitos
    if valor.startswith('+') and len(nacional) == 11 and nacional.startswith('9'):
        nacional = nacional[1:]  # +54 9 ...
    if nacional.startswith('0'):
        return None, 'Ingresá el código de área sin el 0. ' + MSJ_CELULAR_AR
    if len(nacional) == 10 and not nacional.startswith('15'):
        return f'+54 9 {nacional}', None
    if len(nacional) == 12 and '15' in nacional[2:6]:
        return None, 'Ingresá el número sin el 15. ' + MSJ_CELULAR_AR
    return None, MSJ_CELULAR_AR


def _filas_previas(request):
    """Filas enviadas, para volver a mostrarlas si hubo errores"""
    if request.method != 'POST':
        return []
    campos = ['apellido', 'nombre', 'parentesco', 'edad', 'hermano_id', 'alumno_id']
    listas = {c: request.POST.getlist(c) for c in campos}
    n = min(len(listas['apellido']), MAX_PERSONAS + 1)
    return [{c: (listas[c][i] if i < len(listas[c]) else '') for c in campos} for i in range(n)]


def inscripcion_form(request, slug):
    evento = get_object_or_404(Evento, slug=slug)
    motivo_cerrado = evento.motivo_cerrado()
    errores = []

    if request.method == 'POST' and not motivo_cerrado:
        celular = request.POST.get('celular', '').strip()
        observaciones = request.POST.get('observaciones', '').strip()[:1000]

        if settings.RECAPTCHA_SITE_KEY and not verificar_recaptcha(request.POST.get('g-recaptcha-response', '')):
            errores.append('Por favor, completá la verificación de seguridad.')

        personas, errores_personas = _leer_personas(request, evento)
        errores += errores_personas

        celular_ok, error_celular = normalizar_celular(celular)
        if error_celular:
            errores.append(error_celular)

        if not errores:
            with transaction.atomic():
                ev = Evento.objects.select_for_update().get(pk=evento.pk)
                motivo_cerrado = ev.motivo_cerrado()
                disponible = ev.cupo_disponible()
                if motivo_cerrado:
                    errores.append(motivo_cerrado)
                elif disponible is not None and len(personas) > disponible:
                    errores.append(f'Solo quedan {disponible} lugares disponibles.')
                else:
                    inscripcion = Inscripcion.objects.create(
                        evento=ev, celular=celular_ok[:30], observaciones=observaciones,
                    )
                    Inscripto.objects.bulk_create(
                        [Inscripto(inscripcion=inscripcion, **p) for p in personas]
                    )
                    request.session[f'evento_insc_{ev.pk}'] = inscripcion.pk
                    return redirect('eventos:exito', slug=ev.slug)

    context = {
        'evento': evento,
        'motivo_cerrado': motivo_cerrado,
        'errores': errores,
        'parentescos': [p for p in Inscripto.PARENTESCO_CHOICES if p[0] != Inscripto.RESPONSABLE],
        'cupo_disponible': evento.cupo_disponible(),
        'recaptcha_site_key': settings.RECAPTCHA_SITE_KEY,
        'filas_previas': _filas_previas(request),
        'celular': request.POST.get('celular', '') if request.method == 'POST' else '',
        'observaciones': request.POST.get('observaciones', '') if request.method == 'POST' else '',
    }
    return render(request, 'eventos/inscripcion.html', context)


def inscripcion_exito(request, slug):
    evento = get_object_or_404(Evento, slug=slug)
    insc_id = request.session.get(f'evento_insc_{evento.pk}')
    inscripcion = Inscripcion.objects.filter(pk=insc_id, evento=evento).first() if insc_id else None
    if not inscripcion:
        return redirect('eventos:inscripcion', slug=slug)
    return render(request, 'eventos/exito.html', {
        'evento': evento,
        'inscripcion': inscripcion,
        'personas': inscripcion.personas.all(),
    })


def buscar_personas(request, slug):
    """
    Sugerencias de hermanos y alumnos para autocompletar (solo nombres).
    Parametros: apellido, nombre y modo ('responsable' o 'familiar').
    - Busco que todas las palabras escritas aparezcan en apellido/nombre.
    - Si no hay resultados y hay un nombre escrito, busco solo por nombre
      (caso tipico: el apellido precompletado del responsable no es el del chico).
    - Ordeno por mejor coincidencia; para familiares priorizo alumnos.
    """
    evento = get_object_or_404(Evento, slug=slug)
    if evento.motivo_cerrado():
        return JsonResponse({'resultados': []})

    apellido = request.GET.get('apellido')
    nombre = request.GET.get('nombre')
    if apellido is None and nombre is None:  # compatibilidad con ?q=
        apellido, nombre = request.GET.get('q', ''), ''
    tokens_ap = _norm(apellido).split()
    tokens_no = _norm(nombre).split()
    tokens = tokens_ap + tokens_no
    if sum(len(t) for t in tokens) < 3:
        return JsonResponse({'resultados': []})
    familiar = request.GET.get('modo') == 'familiar'

    personas = []
    for h in Hermano.objects.filter(activo=True).only('id', 'apellidos', 'nombres', 'apellido_soltera', 'fecha_nacimiento'):
        personas.append(('hermano', h, _norm(f'{h.apellidos} {h.apellido_soltera or ""}'), _norm(h.nombres)))
    for a in Alumno.objects.filter(activo=True).only('id', 'apellidos', 'nombres', 'fecha_nacimiento'):
        personas.append(('alumno', a, _norm(a.apellidos), _norm(a.nombres)))

    def puntaje(toks, texto):
        """None si falta alguna palabra; si no, cuantas coinciden al inicio de una palabra"""
        palabras = texto.split()
        if not all(t in texto for t in toks):
            return None
        return sum(1 for t in toks if any(p.startswith(t) for p in palabras))

    def buscar(toks, solo_nombre):
        encontrados = []
        for tipo, obj, ap_norm, no_norm in personas:
            texto = no_norm if solo_nombre else f'{ap_norm} {no_norm}'
            pts = puntaje(toks, texto)
            if pts is not None:
                prioridad = 0 if (tipo == 'alumno') == familiar else 1
                encontrados.append((-pts, prioridad, ap_norm, no_norm, tipo, obj))
        encontrados.sort(key=lambda x: x[:4])
        return encontrados

    aproximado = False
    encontrados = buscar(tokens, solo_nombre=False)
    if not encontrados and tokens_ap and sum(len(t) for t in tokens_no) >= 3:
        encontrados = buscar(tokens_no, solo_nombre=True)
        aproximado = True

    resultados = [{
        'tipo': tipo, 'id': obj.id, 'apellido': obj.apellidos, 'nombre': obj.nombres,
        'edad': evento.edad_a_la_fecha(obj.fecha_nacimiento),
    } for *_, tipo, obj in encontrados[:MAX_SUGERENCIAS]]
    return JsonResponse({'resultados': resultados, 'aproximado': aproximado})


# =============================================================================
# Panel
# =============================================================================

def _url_publica(request, evento):
    return request.build_absolute_uri(reverse('eventos:inscripcion', args=[evento.slug]))


def _qr_b64(url):
    import qrcode
    buf = io.BytesIO()
    qrcode.make(url, box_size=8, border=2).save(buf, format='PNG')
    return base64.b64encode(buf.getvalue()).decode()


def _qr_png_grande(url):
    """QR grande para imprimir, con la URL escrita debajo"""
    import qrcode
    from PIL import Image, ImageDraw, ImageFont

    qr = qrcode.make(url, box_size=24, border=4).convert('RGB')
    ancho = qr.width
    margen = 40

    # Fuente: la mas grande que entre en el ancho
    draw_tmp = ImageDraw.Draw(qr)
    fuente = None
    for size in range(48, 15, -2):
        try:
            f = ImageFont.load_default(size=size)
        except TypeError:  # Pillow viejo sin fuentes escalables
            f = ImageFont.load_default()
        if draw_tmp.textlength(url, font=f) <= ancho - 2 * margen:
            fuente = f
            break
    fuente = fuente or f

    bbox = draw_tmp.textbbox((0, 0), url, font=fuente)
    alto_texto = bbox[3] - bbox[1]
    y_texto = qr.height - 48  # aprovecho parte del borde blanco del QR
    img = Image.new('RGB', (ancho, y_texto + alto_texto + margen * 2), 'white')
    img.paste(qr, (0, 0))
    draw = ImageDraw.Draw(img)
    x = (ancho - draw.textlength(url, font=fuente)) / 2
    draw.text((x, y_texto - bbox[1]), url, fill='black', font=fuente)

    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()


def _datos_evento(evento):
    """
    Cargo inscripciones con personas y marco las que hay que revisar:
    personas que no estan en la base y posibles duplicados (mismo nombre en otra inscripcion).
    """
    inscripciones = list(
        evento.inscripciones.prefetch_related('personas').select_related('evento').order_by('fecha')
    )

    claves = defaultdict(set)
    for insc in inscripciones:
        for p in insc.personas.all():
            claves[('n', _norm(p.apellido), _norm(p.nombre))].add(insc.pk)
            if p.hermano_id:
                claves[('h', p.hermano_id)].add(insc.pk)
            if p.alumno_id:
                claves[('a', p.alumno_id)].add(insc.pk)

    totales = {'familias': len(inscripciones), 'adultos': 0, 'ninos': 0, 'gratis': 0,
               'personas': 0, 'monto': 0, 'revisar': 0, 'cobrado': 0, 'pendiente': 0,
               'familias_pagadas': 0}
    for insc in inscripciones:
        insc.revisar = False
        for p in insc.personas.all():
            p.duplicado = (
                len(claves[('n', _norm(p.apellido), _norm(p.nombre))]) > 1
                or (p.hermano_id and len(claves[('h', p.hermano_id)]) > 1)
                or (p.alumno_id and len(claves[('a', p.alumno_id)]) > 1)
            )
            p.revisar = p.duplicado or not p.en_base()
            insc.revisar = insc.revisar or p.revisar
            cat = p.categoria()
            totales['adultos'] += cat == CATEGORIA_ADULTO
            totales['ninos'] += cat == CATEGORIA_NINO
            totales['gratis'] += cat == CATEGORIA_GRATIS
            totales['personas'] += 1
            totales['monto'] += p.precio()
        totales['revisar'] += insc.revisar
        total_insc = insc.total()
        if insc.pagado:
            totales['cobrado'] += total_insc
            totales['familias_pagadas'] += 1
        else:
            totales['pendiente'] += total_insc

    return inscripciones, totales


@login_required
@user_passes_test(es_staff)
def panel_lista(request):
    eventos = Evento.objects.all()
    for e in eventos:
        e.inscriptas = e.personas_inscriptas()
        e.familias = e.inscripciones.count()
        e.cerrado = e.motivo_cerrado()
    return render(request, 'eventos/panel/lista.html', {'eventos': eventos})


@login_required
@user_passes_test(es_staff)
def panel_form(request, pk=None):
    evento = get_object_or_404(Evento, pk=pk) if pk else None
    form = EventoForm(request.POST or None, instance=evento)
    if request.method == 'POST' and form.is_valid():
        evento = form.save()
        messages.success(request, 'Evento guardado.')
        return redirect('eventos:panel_detalle', pk=evento.pk)
    return render(request, 'eventos/panel/form.html', {'form': form, 'evento': evento})


@login_required
@user_passes_test(es_staff)
def panel_detalle(request, pk):
    evento = get_object_or_404(Evento, pk=pk)
    inscripciones, totales = _datos_evento(evento)
    solo_revisar = request.GET.get('revisar') == '1'
    if solo_revisar:
        inscripciones = [i for i in inscripciones if i.revisar]
    filtro_pago = request.GET.get('pago', '')
    if filtro_pago == 'pendiente':
        inscripciones = [i for i in inscripciones if not i.pagado]
    elif filtro_pago == 'pagado':
        inscripciones = [i for i in inscripciones if i.pagado]
    url = _url_publica(request, evento)
    return render(request, 'eventos/panel/detalle.html', {
        'evento': evento,
        'inscripciones': inscripciones,
        'totales': totales,
        'solo_revisar': solo_revisar,
        'filtro_pago': filtro_pago,
        'url_publica': url,
        'qr_b64': _qr_b64(url),
        'motivo_cerrado': evento.motivo_cerrado(),
    })


@login_required
@user_passes_test(es_staff)
def panel_qr(request, pk):
    evento = get_object_or_404(Evento, pk=pk)
    response = HttpResponse(_qr_png_grande(_url_publica(request, evento)), content_type='image/png')
    response['Content-Disposition'] = f'attachment; filename="qr_{evento.slug}.png"'
    return response


@login_required
@user_passes_test(es_staff)
@require_POST
def panel_inscripcion_eliminar(request, pk):
    inscripcion = get_object_or_404(Inscripcion, pk=pk)
    evento_pk = inscripcion.evento_id
    inscripcion.delete()
    messages.success(request, 'Inscripción eliminada.')
    return redirect('eventos:panel_detalle', pk=evento_pk)


@login_required
@user_passes_test(es_staff)
@require_POST
def panel_inscripcion_pagado(request, pk):
    inscripcion = get_object_or_404(Inscripcion, pk=pk)
    inscripcion.pagado = not inscripcion.pagado
    inscripcion.fecha_pago = timezone.now() if inscripcion.pagado else None
    inscripcion.save(update_fields=['pagado', 'fecha_pago'])
    resp = inscripcion.responsable()
    estado = 'pagada' if inscripcion.pagado else 'pendiente de pago'
    messages.success(request, f'Inscripción de {resp} marcada como {estado}.')
    destino = reverse('eventos:panel_detalle', args=[inscripcion.evento_id])
    filtros = request.POST.get('filtros', '')
    return redirect(f'{destino}?{filtros}#insc-{inscripcion.pk}' if filtros else f'{destino}#insc-{inscripcion.pk}')


@login_required
@user_passes_test(es_staff)
def panel_exportar(request, pk):
    import openpyxl
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
    from openpyxl.utils import get_column_letter

    evento = get_object_or_404(Evento, pk=pk)
    inscripciones, totales = _datos_evento(evento)

    header_font = Font(bold=True, color='FFFFFF', size=11)
    header_fill = PatternFill(start_color='2E7D32', end_color='2E7D32', fill_type='solid')
    revisar_fill = PatternFill(start_color='FFF3CD', end_color='FFF3CD', fill_type='solid')
    center = Alignment(horizontal='center', vertical='center')
    thin = Side(style='thin', color='CCCCCC')
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    money = '"$"#,##0'

    def encabezado(ws, titulo, headers, anchos):
        ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(headers))
        t = ws.cell(row=1, column=1, value=titulo)
        t.font = Font(bold=True, size=14, color='2E7D32')
        ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=len(headers))
        ws.cell(row=2, column=1, value=(
            f'{evento.fecha:%d/%m/%Y} · Adulto ${evento.precio_adulto:,} · '
            f'Niño ({evento.edad_min_paga} a {evento.edad_max_nino} años) ${evento.precio_nino:,} · '
            f'Menores de {evento.edad_min_paga} sin cargo'
        ).replace(',', '.')).font = Font(size=10, color='666666')
        for col, (h, ancho) in enumerate(zip(headers, anchos), 1):
            c = ws.cell(row=4, column=col, value=h)
            c.font, c.fill, c.alignment, c.border = header_font, header_fill, center, border
            ws.column_dimensions[get_column_letter(col)].width = ancho
        ws.freeze_panes = 'A5'

    wb = openpyxl.Workbook()

    # --- Hoja 1: Familias (para cobrar) ---
    ws = wb.active
    ws.title = 'Familias'
    headers = ['N°', 'Responsable', 'Celular', 'Adultos', 'Niños', 'Sin cargo', 'Personas',
               'Total a cobrar', 'Revisar', 'Inscripción', 'Pagado', 'Observaciones']
    encabezado(ws, f'{evento.nombre} - Inscripciones por familia', headers,
               [5, 30, 16, 9, 8, 10, 10, 15, 10, 16, 10, 40])
    r = 5
    for n, insc in enumerate(inscripciones, 1):
        resp = insc.responsable()
        valores = [
            n, str(resp) if resp else '', insc.celular,
            insc.cantidad(CATEGORIA_ADULTO), insc.cantidad(CATEGORIA_NINO), insc.cantidad(CATEGORIA_GRATIS),
            insc.personas.count(), insc.total(), 'SÍ' if insc.revisar else '',
            timezone.localtime(insc.fecha).strftime('%d/%m/%Y %H:%M'),
            ('SÍ ' + timezone.localtime(insc.fecha_pago).strftime('%d/%m')) if insc.pagado and insc.fecha_pago
            else ('SÍ' if insc.pagado else ''),
            insc.observaciones,
        ]
        for col, v in enumerate(valores, 1):
            c = ws.cell(row=r, column=col, value=v)
            c.border = border
            if col in (1, 4, 5, 6, 7, 9, 11):
                c.alignment = center
            if insc.revisar:
                c.fill = revisar_fill
        ws.cell(row=r, column=8).number_format = money
        r += 1
    # Totales
    for col, v in [(2, 'TOTAL'), (4, totales['adultos']), (5, totales['ninos']), (6, totales['gratis']),
                   (7, totales['personas']), (8, totales['monto']),
                   (11, f"{totales['familias_pagadas']}/{totales['familias']}")]:
        c = ws.cell(row=r, column=col, value=v)
        c.font = Font(bold=True)
        c.border = border
        if col != 2:
            c.alignment = center
    ws.cell(row=r, column=8).number_format = money
    for etiqueta, valor in [('Cobrado', totales['cobrado']), ('Pendiente', totales['pendiente'])]:
        r += 1
        ws.cell(row=r, column=7, value=etiqueta).font = Font(bold=True)
        c = ws.cell(row=r, column=8, value=valor)
        c.font = Font(bold=True)
        c.number_format = money

    # --- Hoja 2: Personas (detalle) ---
    ws2 = wb.create_sheet('Personas')
    headers = ['N° Fam.', 'Responsable', 'Apellido', 'Nombre', 'Parentesco', 'Edad', 'Categoría',
               'Precio', 'En base', 'Revisar']
    encabezado(ws2, f'{evento.nombre} - Detalle de personas', headers,
               [8, 30, 20, 20, 14, 8, 12, 12, 12, 30])
    r = 5
    for n, insc in enumerate(inscripciones, 1):
        resp = insc.responsable()
        for p in insc.personas.all():
            motivos = []
            if not p.en_base():
                motivos.append('No está en la base')
            if p.duplicado:
                motivos.append('Posible duplicado')
            valores = [
                n, str(resp) if resp else '', p.apellido, p.nombre, p.get_parentesco_display(),
                p.edad if p.edad is not None else '', p.categoria_label(), p.precio(),
                p.origen() or 'NO', ', '.join(motivos),
            ]
            for col, v in enumerate(valores, 1):
                c = ws2.cell(row=r, column=col, value=v)
                c.border = border
                if col in (1, 6, 7, 9):
                    c.alignment = center
                if p.revisar:
                    c.fill = revisar_fill
            ws2.cell(row=r, column=8).number_format = money
            r += 1

    buf = io.BytesIO()
    wb.save(buf)
    response = HttpResponse(
        buf.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = f'attachment; filename="inscripciones_{evento.slug}.xlsx"'
    return response
