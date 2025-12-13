from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout, update_session_auth_hash
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .models import Visita
from .forms import HermanoForm, NoticiaForm, MensajeForm, PaginaForm, SeccionForm, SliderForm, OfrendaForm, DatosIceForm
from contenido.models import Noticia, Mensaje, Pagina, Galeria, Slider, DatosIce, Seccion, Ofrenda
from miembros.models import Hermano, Provincia, EstadoCivil, Clase, Grupo, Don


def es_staff(user):
    """Verifica que el usuario sea staff"""
    return user.is_staff


def es_superuser(user):
    """Verifica que el usuario sea superusuario (para contenido web)"""
    return user.is_superuser


@login_required
@user_passes_test(es_staff)
def dashboard(request):
    """Dashboard principal con estadísticas"""
    hoy = timezone.now()
    hace_30_dias = hoy - timedelta(days=30)
    hace_7_dias = hoy - timedelta(days=7)

    # Estadísticas de contenido
    stats = {
        'total_noticias': Noticia.objects.count(),
        'total_mensajes': Mensaje.objects.count(),
        'total_hermanos': Hermano.objects.filter(activo=True).count(),
        'total_paginas': Pagina.objects.filter(activo=True).count(),
        'total_visitas': Visita.objects.count(),
        'visitas_mes': Visita.objects.filter(fecha__gte=hace_30_dias).count(),
        'visitas_semana': Visita.objects.filter(fecha__gte=hace_7_dias).count(),
        'visitas_hoy': Visita.objects.filter(fecha__date=hoy.date()).count(),
    }

    # Visitas por dispositivo
    visitas_dispositivo = Visita.objects.filter(
        fecha__gte=hace_30_dias
    ).values('dispositivo').annotate(total=Count('id')).order_by('-total')

    # Visitas por día (últimos 7 días)
    visitas_por_dia = []
    for i in range(6, -1, -1):
        dia = hoy - timedelta(days=i)
        count = Visita.objects.filter(fecha__date=dia.date()).count()
        visitas_por_dia.append({
            'fecha': dia.strftime('%d/%m'),
            'count': count
        })

    # Últimas noticias y cumpleaños
    ultimas_noticias = Noticia.objects.filter(activo=True).order_by('-fecha_publicacion')[:5]
    mes_actual = hoy.month
    cumpleaños_mes = Hermano.objects.filter(
        activo=True, cumpleaños__month=mes_actual
    ).order_by('cumpleaños__day')[:10]

    # Estadísticas de dones
    estadisticas_dones = []
    for don in Don.objects.all():
        count = Hermano.objects.filter(activo=True, dones=don).count()
        if count > 0:
            estadisticas_dones.append({
                'nombre': don.nombre,
                'count': count
            })
    # Ordenar por cantidad descendente
    estadisticas_dones.sort(key=lambda x: x['count'], reverse=True)

    context = {
        **stats,
        'visitas_dispositivo': visitas_dispositivo,
        'visitas_por_dia': visitas_por_dia,
        'ultimas_noticias': ultimas_noticias,
        'cumpleaños_mes': cumpleaños_mes,
        'estadisticas_dones': estadisticas_dones,
    }

    return render(request, 'panel/dashboard.html', context)


# ========== HERMANOS ==========
@login_required
@user_passes_test(es_staff)
def hermanos_lista(request):
    """Lista de hermanos con búsqueda y filtros"""
    busqueda = request.GET.get('q', '')
    clase = request.GET.get('clase', '')
    grupo = request.GET.get('grupo', '')
    orden = request.GET.get('orden', 'apellidos')

    hermanos = Hermano.objects.all()

    if busqueda:
        hermanos = hermanos.filter(
            Q(apellidos__icontains=busqueda) |
            Q(nombres__icontains=busqueda) |
            Q(email__icontains=busqueda) |
            Q(celular__icontains=busqueda)
        )

    if clase:
        hermanos = hermanos.filter(clase_id=clase)
    if grupo:
        hermanos = hermanos.filter(grupo_id=grupo)

    # Aplicar ordenamiento
    if orden == 'apellidos':
        hermanos = hermanos.order_by('apellidos', 'nombres')
    elif orden == 'edad':
        hermanos = hermanos.order_by('fecha_nacimiento')
    elif orden == 'clase':
        hermanos = hermanos.order_by('clase__nombre', 'apellidos')
    elif orden == 'grupo':
        hermanos = hermanos.order_by('grupo__nombre', 'apellidos')
    elif orden == 'actualizacion':
        hermanos = hermanos.order_by('-fecha_modificacion')
    else:
        hermanos = hermanos.order_by('apellidos', 'nombres')

    # Calcular estadísticas
    total_hermanos = hermanos.count()
    total_hombres = hermanos.filter(sexo='M').count()
    total_mujeres = hermanos.filter(sexo='F').count()

    # Estadísticas por estado civil
    estadisticas_estado_civil = []
    for estado in EstadoCivil.objects.all():
        count = hermanos.filter(estado_civil=estado).count()
        if count > 0:
            estadisticas_estado_civil.append({
                'nombre': estado.nombre,
                'count': count
            })

    # Hermanos activos vs inactivos
    total_activos = hermanos.filter(activo=True).count()
    total_inactivos = hermanos.filter(activo=False).count()

    paginator = Paginator(hermanos, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'busqueda': busqueda,
        'clase_seleccionada': clase,
        'grupo_seleccionado': grupo,
        'orden_seleccionado': orden,
        'clases': Clase.objects.all(),
        'grupos': Grupo.objects.all(),
        'form': HermanoForm(),
        # Estadísticas
        'total_hermanos': total_hermanos,
        'total_hombres': total_hombres,
        'total_mujeres': total_mujeres,
        'estadisticas_estado_civil': estadisticas_estado_civil,
        'total_activos': total_activos,
        'total_inactivos': total_inactivos,
    }

    return render(request, 'panel/hermanos_lista.html', context)


@login_required
@user_passes_test(es_staff)
def hermano_crear(request):
    """Crea un nuevo hermano"""
    if request.method == 'POST':
        form = HermanoForm(request.POST)
        if form.is_valid():
            hermano = form.save()
            messages.success(request, f'Hermano {hermano.apellidos}, {hermano.nombres} creado correctamente.')
            return redirect('panel:hermanos_lista')
        else:
            # Mostrar errores específicos de validación
            errores = []
            for field, errors in form.errors.items():
                field_name = form.fields[field].label if field in form.fields else field
                for error in errors:
                    errores.append(f"{field_name}: {error}")
            error_msg = " | ".join(errores) if errores else "Error al crear el hermano. Verifica los datos."
            messages.error(request, error_msg)
    return redirect('panel:hermanos_lista')


@login_required
@user_passes_test(es_staff)
def hermano_datos(request, pk):
    """Retorna los datos de un hermano en JSON para edición y visualización"""
    hermano = get_object_or_404(Hermano, pk=pk)
    data = {
        # Datos para edición (IDs)
        'apellidos': hermano.apellidos,
        'nombres': hermano.nombres,
        'sexo': hermano.sexo,
        'fecha_nacimiento': hermano.fecha_nacimiento.strftime('%Y-%m-%d') if hermano.fecha_nacimiento else '',
        'domicilio': hermano.domicilio or '',
        'barrio': hermano.barrio or '',
        'localidad': hermano.localidad or '',
        'telefono_fijo': hermano.telefono_fijo or '',
        'celular': hermano.celular or '',
        'email': hermano.email or '',
        'estado_civil': hermano.estado_civil.id if hermano.estado_civil else '',
        'clase': hermano.clase.id if hermano.clase else '',
        'grupo': hermano.grupo.id if hermano.grupo else '',
        'activo': hermano.activo,
        'observaciones': hermano.observaciones or '',
        # Datos adicionales para visualización
        'foto_url': hermano.foto.url if hermano.foto else '',
        'sexo_display': hermano.get_sexo_display(),
        'estado_civil_display': str(hermano.estado_civil) if hermano.estado_civil else '-',
        'clase_display': str(hermano.clase) if hermano.clase else '-',
        'grupo_display': str(hermano.grupo) if hermano.grupo else '-',
        'edad': hermano.edad(),
        'fecha_nacimiento_display': hermano.fecha_nacimiento.strftime('%d/%m/%Y') if hermano.fecha_nacimiento else '-',
        'ocupacion': hermano.ocupacion or '-',
        'provincia': str(hermano.provincia) if hermano.provincia else '-',
        'anio_bautismo': hermano.anio_bautismo or '-',
        'dones': [str(d) for d in hermano.dones.all()],
        'fecha_creacion': hermano.fecha_creacion.strftime('%d/%m/%Y %H:%M'),
        'fecha_modificacion': hermano.fecha_modificacion.strftime('%d/%m/%Y %H:%M'),
    }
    return JsonResponse(data)


@login_required
@user_passes_test(es_staff)
def hermano_editar(request, pk):
    """Edita un hermano existente"""
    hermano = get_object_or_404(Hermano, pk=pk)
    if request.method == 'POST':
        form = HermanoForm(request.POST, instance=hermano)
        if form.is_valid():
            hermano = form.save()
            messages.success(request, f'Hermano {hermano.apellidos}, {hermano.nombres} actualizado correctamente.')
            return redirect('panel:hermanos_lista')
        else:
            messages.error(request, 'Error al actualizar el hermano. Verifica los datos.')
    return redirect('panel:hermanos_lista')


@login_required
@user_passes_test(es_staff)
@require_POST
def hermano_eliminar(request, pk):
    """Elimina un hermano"""
    hermano = get_object_or_404(Hermano, pk=pk)
    nombre = f'{hermano.apellidos}, {hermano.nombres}'
    hermano.delete()
    messages.success(request, f'Hermano {nombre} eliminado correctamente.')
    return redirect('panel:hermanos_lista')


# ========== NOTICIAS ==========
@login_required
@user_passes_test(es_staff)
def noticias_lista(request):
    """Lista de noticias"""
    tipo = request.GET.get('tipo', '')
    busqueda = request.GET.get('q', '')

    noticias = Noticia.objects.all()

    if tipo:
        noticias = noticias.filter(tipo=tipo)
    if busqueda:
        noticias = noticias.filter(Q(titulo__icontains=busqueda) | Q(contenido__icontains=busqueda))

    noticias = noticias.order_by('-fecha_publicacion')

    paginator = Paginator(noticias, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'busqueda': busqueda,
        'form': NoticiaForm(),
    }

    return render(request, 'panel/noticias_lista.html', context)


@login_required
@user_passes_test(es_staff)
def noticia_crear(request):
    """Crea una nueva noticia"""
    if request.method == 'POST':
        print("=== DEBUG: Iniciando creación de noticia ===")
        print(f"POST data: {request.POST}")
        print(f"FILES data: {request.FILES}")

        form = NoticiaForm(request.POST, request.FILES)
        print(f"Form is valid: {form.is_valid()}")

        if form.is_valid():
            noticia = form.save()
            print(f"Noticia creada: {noticia.id}")
            messages.success(request, f'Noticia "{noticia.titulo}" creada correctamente.')
            return redirect('panel:noticias_lista')
        else:
            print(f"Form errors: {form.errors}")
            # Mostrar errores específicos del formulario
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
            if not form.errors:
                messages.error(request, 'Error al crear la noticia. Verifica los datos.')
    else:
        print(f"=== DEBUG: Request method is {request.method}, not POST ===")
    return redirect('panel:noticias_lista')


@login_required
@user_passes_test(es_staff)
def noticia_datos(request, pk):
    """Retorna datos de noticia en JSON"""
    n = get_object_or_404(Noticia, pk=pk)
    return JsonResponse({
        'titulo': n.titulo,
        'introduccion': n.introduccion or '',
        'contenido': n.contenido or '',
        'tipo': n.tipo,
        'fecha_publicacion': n.fecha_publicacion.strftime('%Y-%m-%d') if n.fecha_publicacion else '',
        'activo': n.activo,
        'imagen_principal': n.imagen_principal.url if n.imagen_principal else '',
        'imagen_secundaria': n.imagen_secundaria.url if n.imagen_secundaria else '',
    })


@login_required
@user_passes_test(es_staff)
def noticia_editar(request, pk):
    """Edita una noticia existente"""
    noticia = get_object_or_404(Noticia, pk=pk)
    if request.method == 'POST':
        # Verificar si se debe eliminar alguna imagen
        eliminar_principal = request.POST.get('eliminar_imagen_principal') == '1'
        eliminar_secundaria = request.POST.get('eliminar_imagen_secundaria') == '1'

        # Verificar si se subieron nuevas imágenes
        nueva_img_principal = 'imagen_principal' in request.FILES
        nueva_img_secundaria = 'imagen_secundaria' in request.FILES

        form = NoticiaForm(request.POST, request.FILES, instance=noticia)
        if form.is_valid():
            noticia = form.save(commit=False)

            # Eliminar imágenes solo si se solicitó Y NO se subió una nueva
            if eliminar_principal and not nueva_img_principal and noticia.imagen_principal:
                noticia.imagen_principal.delete(save=False)
                noticia.imagen_principal = None
            if eliminar_secundaria and not nueva_img_secundaria and noticia.imagen_secundaria:
                noticia.imagen_secundaria.delete(save=False)
                noticia.imagen_secundaria = None

            noticia.save()
            messages.success(request, f'Noticia "{noticia.titulo}" actualizada correctamente.')
            return redirect('panel:noticias_lista')
        else:
            messages.error(request, 'Error al actualizar la noticia. Verifica los datos.')
    return redirect('panel:noticias_lista')


@login_required
@user_passes_test(es_staff)
@require_POST
def noticia_eliminar(request, pk):
    """Elimina una noticia"""
    noticia = get_object_or_404(Noticia, pk=pk)
    titulo = noticia.titulo
    noticia.delete()
    messages.success(request, f'Noticia "{titulo}" eliminada correctamente.')
    return redirect('panel:noticias_lista')


@login_required
@user_passes_test(es_staff)
def noticia_toggle_activo(request, pk):
    """Activa/desactiva una noticia"""
    noticia = get_object_or_404(Noticia, pk=pk)
    noticia.activo = not noticia.activo
    noticia.save()
    estado = 'activada' if noticia.activo else 'desactivada'
    messages.success(request, f'Noticia "{noticia.titulo}" {estado}.')
    return redirect('panel:noticias_lista')


# ========== MENSAJES ==========
@login_required
@user_passes_test(es_staff)
def mensajes_lista(request):
    """Lista de mensajes"""
    tipo = request.GET.get('tipo', '')
    busqueda = request.GET.get('q', '')

    mensajes_list = Mensaje.objects.all()

    if tipo:
        mensajes_list = mensajes_list.filter(tipo=tipo)
    if busqueda:
        mensajes_list = mensajes_list.filter(
            Q(titulo__icontains=busqueda) |
            Q(autor__icontains=busqueda) |
            Q(contenido__icontains=busqueda)
        )

    mensajes_list = mensajes_list.order_by('-fecha_publicacion')

    paginator = Paginator(mensajes_list, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'busqueda': busqueda,
        'form': MensajeForm(),
    }

    return render(request, 'panel/mensajes_lista.html', context)


@login_required
@user_passes_test(es_staff)
def mensaje_crear(request):
    """Crea un nuevo mensaje"""
    if request.method == 'POST':
        form = MensajeForm(request.POST, request.FILES)
        if form.is_valid():
            mensaje = form.save()
            messages.success(request, f'Mensaje "{mensaje.titulo}" creado correctamente.')
            return redirect('panel:mensajes_lista')
        else:
            messages.error(request, 'Error al crear el mensaje. Verifica los datos.')
    return redirect('panel:mensajes_lista')


@login_required
@user_passes_test(es_staff)
def mensaje_datos(request, pk):
    """Retorna datos de mensaje en JSON"""
    m = get_object_or_404(Mensaje, pk=pk)
    return JsonResponse({
        'titulo': m.titulo,
        'autor': m.autor or '',
        'introduccion': m.introduccion or '',
        'contenido': m.contenido or '',
        'tipo': m.tipo,
        'enlace_video': m.enlace_video or '',
        'fecha_publicacion': m.fecha_publicacion.strftime('%Y-%m-%d') if m.fecha_publicacion else '',
        'activo': m.activo,
    })


@login_required
@user_passes_test(es_staff)
def mensaje_editar(request, pk):
    """Edita un mensaje existente"""
    mensaje = get_object_or_404(Mensaje, pk=pk)
    if request.method == 'POST':
        form = MensajeForm(request.POST, request.FILES, instance=mensaje)
        if form.is_valid():
            mensaje = form.save()
            messages.success(request, f'Mensaje "{mensaje.titulo}" actualizado correctamente.')
            return redirect('panel:mensajes_lista')
        else:
            messages.error(request, 'Error al actualizar el mensaje. Verifica los datos.')
    return redirect('panel:mensajes_lista')


@login_required
@user_passes_test(es_staff)
@require_POST
def mensaje_eliminar(request, pk):
    """Elimina un mensaje"""
    mensaje = get_object_or_404(Mensaje, pk=pk)
    titulo = mensaje.titulo
    mensaje.delete()
    messages.success(request, f'Mensaje "{titulo}" eliminado correctamente.')
    return redirect('panel:mensajes_lista')


@login_required
@user_passes_test(es_staff)
def mensaje_toggle_activo(request, pk):
    """Activa/desactiva un mensaje"""
    mensaje = get_object_or_404(Mensaje, pk=pk)
    mensaje.activo = not mensaje.activo
    mensaje.save()
    estado = 'activado' if mensaje.activo else 'desactivado'
    messages.success(request, f'Mensaje "{mensaje.titulo}" {estado}.')
    return redirect('panel:mensajes_lista')


# ========== PAGINAS ==========
@login_required
@user_passes_test(es_staff)
def paginas_lista(request):
    """Lista de páginas"""
    busqueda = request.GET.get('q', '')

    paginas = Pagina.objects.all()

    if busqueda:
        paginas = paginas.filter(Q(titulo__icontains=busqueda) | Q(contenido__icontains=busqueda))

    paginas = paginas.order_by('orden')

    paginator = Paginator(paginas, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'busqueda': busqueda,
        'form': PaginaForm(),
    }

    return render(request, 'panel/paginas_lista.html', context)


@login_required
@user_passes_test(es_staff)
def pagina_crear(request):
    """Crea una nueva página"""
    if request.method == 'POST':
        form = PaginaForm(request.POST)
        if form.is_valid():
            pagina = form.save()
            messages.success(request, f'Página "{pagina.titulo}" creada correctamente.')
            return redirect('panel:paginas_lista')
        else:
            messages.error(request, 'Error al crear la página. Verifica los datos.')
    return redirect('panel:paginas_lista')


@login_required
@user_passes_test(es_staff)
def pagina_datos(request, pk):
    """Retorna datos de página en JSON"""
    p = get_object_or_404(Pagina, pk=pk)
    return JsonResponse({
        'titulo': p.titulo,
        'descripcion': p.descripcion or '',
        'contenido': p.contenido or '',
        'orden': p.orden,
        'activo': p.activo,
    })


@login_required
@user_passes_test(es_staff)
def pagina_editar(request, pk):
    """Edita una página existente"""
    pagina = get_object_or_404(Pagina, pk=pk)
    if request.method == 'POST':
        form = PaginaForm(request.POST, instance=pagina)
        if form.is_valid():
            pagina = form.save()
            messages.success(request, f'Página "{pagina.titulo}" actualizada correctamente.')
            return redirect('panel:paginas_lista')
        else:
            messages.error(request, 'Error al actualizar la página. Verifica los datos.')
    return redirect('panel:paginas_lista')


@login_required
@user_passes_test(es_staff)
def pagina_toggle_activo(request, pk):
    """Activa/desactiva una página"""
    pagina = get_object_or_404(Pagina, pk=pk)
    pagina.activo = not pagina.activo
    pagina.save()
    estado = 'activada' if pagina.activo else 'desactivada'
    messages.success(request, f'Página "{pagina.titulo}" {estado}.')
    return redirect('panel:paginas_lista')


# ========== ESTADISTICAS ==========
@login_required
@user_passes_test(es_staff)
def estadisticas(request):
    """Estadísticas detalladas de visitas"""
    dias = int(request.GET.get('dias', 30))

    hoy = timezone.now()
    fecha_inicio = hoy - timedelta(days=dias)

    visitas = Visita.objects.filter(fecha__gte=fecha_inicio)

    stats = {
        'total_visitas': visitas.count(),
        'visitas_unicas': visitas.values('ip').distinct().count(),
    }

    # Estadísticas detalladas
    por_dispositivo = visitas.values('dispositivo').annotate(total=Count('id')).order_by('-total')
    por_navegador = visitas.values('navegador').annotate(total=Count('id')).order_by('-total')
    por_sistema = visitas.values('sistema_operativo').annotate(total=Count('id')).order_by('-total')
    urls_populares = visitas.values('url').annotate(total=Count('id')).order_by('-total')[:15]

    context = {
        'dias': dias,
        **stats,
        'por_dispositivo': por_dispositivo,
        'por_navegador': por_navegador,
        'por_sistema': por_sistema,
        'urls_populares': urls_populares,
    }

    return render(request, 'panel/estadisticas.html', context)


# ========== SECCIONES ==========
@login_required
@user_passes_test(es_superuser)
def secciones_lista(request):
    """Lista de secciones de la homepage"""
    busqueda = request.GET.get('q', '')

    secciones = Seccion.objects.all()

    if busqueda:
        secciones = secciones.filter(Q(titulo__icontains=busqueda) | Q(contenido__icontains=busqueda))

    secciones = secciones.order_by('orden')

    paginator = Paginator(secciones, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'busqueda': busqueda,
        'form': SeccionForm(),
    }

    return render(request, 'panel/secciones_lista.html', context)


@login_required
@user_passes_test(es_superuser)
def seccion_crear(request):
    """Crea una nueva sección"""
    if request.method == 'POST':
        form = SeccionForm(request.POST, request.FILES)
        if form.is_valid():
            seccion = form.save()
            messages.success(request, f'Sección "{seccion.titulo}" creada correctamente.')
            return redirect('panel:secciones_lista')
        else:
            messages.error(request, 'Error al crear la sección. Verifica los datos.')
    return redirect('panel:secciones_lista')


@login_required
@user_passes_test(es_superuser)
def seccion_datos(request, pk):
    """Retorna datos de sección en JSON"""
    s = get_object_or_404(Seccion, pk=pk)
    return JsonResponse({
        'titulo': s.titulo,
        'subtitulo': s.subtitulo or '',
        'contenido': s.contenido or '',
        'tipo': s.tipo,
        'estilo': s.estilo,
        'orden': s.orden,
        'mostrar_en_home': s.mostrar_en_home,
        'activo': s.activo,
    })


@login_required
@user_passes_test(es_superuser)
def seccion_editar(request, pk):
    """Edita una sección existente"""
    seccion = get_object_or_404(Seccion, pk=pk)
    if request.method == 'POST':
        form = SeccionForm(request.POST, request.FILES, instance=seccion)
        if form.is_valid():
            seccion = form.save()
            messages.success(request, f'Sección "{seccion.titulo}" actualizada correctamente.')
            return redirect('panel:secciones_lista')
        else:
            messages.error(request, 'Error al actualizar la sección. Verifica los datos.')
    return redirect('panel:secciones_lista')


@login_required
@user_passes_test(es_superuser)
@require_POST
def seccion_eliminar(request, pk):
    """Elimina una sección"""
    seccion = get_object_or_404(Seccion, pk=pk)
    titulo = seccion.titulo
    seccion.delete()
    messages.success(request, f'Sección "{titulo}" eliminada correctamente.')
    return redirect('panel:secciones_lista')


@login_required
@user_passes_test(es_superuser)
def seccion_toggle_activo(request, pk):
    """Activa/desactiva una sección"""
    seccion = get_object_or_404(Seccion, pk=pk)
    seccion.activo = not seccion.activo
    seccion.save()
    estado = 'activada' if seccion.activo else 'desactivada'
    messages.success(request, f'Sección "{seccion.titulo}" {estado}.')
    return redirect('panel:secciones_lista')


# ========== SLIDERS ==========
@login_required
@user_passes_test(es_superuser)
def sliders_lista(request):
    """Lista de sliders del hero"""
    busqueda = request.GET.get('q', '')

    sliders = Slider.objects.all()

    if busqueda:
        sliders = sliders.filter(Q(titulo__icontains=busqueda) | Q(descripcion__icontains=busqueda))

    sliders = sliders.order_by('orden')

    paginator = Paginator(sliders, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'busqueda': busqueda,
        'form': SliderForm(),
    }

    return render(request, 'panel/sliders_lista.html', context)


@login_required
@user_passes_test(es_superuser)
def slider_crear(request):
    """Crea un nuevo slider"""
    if request.method == 'POST':
        print("="*80)
        print("DEBUG SLIDER_CREAR - POST request received")
        print(f"POST data: {request.POST}")
        print(f"FILES data: {request.FILES}")
        print(f"Has imagen? {bool(request.FILES.get('imagen'))}")
        print("="*80)

        form = SliderForm(request.POST, request.FILES)
        print(f"Form created. Is valid? Checking...")

        if form.is_valid():
            print("✓ Form is VALID")
            try:
                slider = form.save()
                print(f"✓ Slider saved successfully! ID: {slider.id}, Title: {slider.titulo}")
                messages.success(request, f'Slider "{slider.titulo}" creado correctamente.')
                return redirect('panel:sliders_lista')
            except Exception as e:
                print(f"✗ ERROR saving slider: {e}")
                messages.error(request, f"Error al guardar el slider: {e}")
                return redirect('panel:sliders_lista')
        else:
            print("✗ Form is INVALID")
            print(f"Form errors: {form.errors}")
            print(f"Form errors as dict: {form.errors.as_data()}")
            # Mostrar errores específicos del formulario
            errores = []
            for field, errors in form.errors.items():
                field_name = form.fields[field].label if field in form.fields else field
                for error in errors:
                    errores.append(f"{field_name}: {error}")
            error_msg = " | ".join(errores) if errores else "Error al crear el slider. Verifica los datos."
            print(f"Error message to show: {error_msg}")
            messages.error(request, error_msg)
    return redirect('panel:sliders_lista')


@login_required
@user_passes_test(es_superuser)
def slider_datos(request, pk):
    """Retorna datos de slider en JSON"""
    s = get_object_or_404(Slider, pk=pk)
    return JsonResponse({
        'titulo': s.titulo,
        'descripcion': s.descripcion or '',
        'enlace': s.enlace or '',
        'orden': s.orden,
        'activo': s.activo,
    })


@login_required
@user_passes_test(es_superuser)
def slider_editar(request, pk):
    """Edita un slider existente"""
    slider = get_object_or_404(Slider, pk=pk)
    if request.method == 'POST':
        form = SliderForm(request.POST, request.FILES, instance=slider)
        if form.is_valid():
            slider = form.save()
            messages.success(request, f'Slider "{slider.titulo}" actualizado correctamente.')
            return redirect('panel:sliders_lista')
        else:
            # Mostrar errores específicos del formulario
            errores = []
            for field, errors in form.errors.items():
                field_name = form.fields[field].label if field in form.fields else field
                for error in errors:
                    errores.append(f"{field_name}: {error}")
            error_msg = " | ".join(errores) if errores else "Error al actualizar el slider. Verifica los datos."
            messages.error(request, error_msg)
    return redirect('panel:sliders_lista')


@login_required
@user_passes_test(es_superuser)
@require_POST
def slider_eliminar(request, pk):
    """Elimina un slider"""
    slider = get_object_or_404(Slider, pk=pk)
    titulo = slider.titulo
    slider.delete()
    messages.success(request, f'Slider "{titulo}" eliminado correctamente.')
    return redirect('panel:sliders_lista')


@login_required
@user_passes_test(es_superuser)
def slider_toggle_activo(request, pk):
    """Activa/desactiva un slider"""
    slider = get_object_or_404(Slider, pk=pk)
    slider.activo = not slider.activo
    slider.save()
    estado = 'activado' if slider.activo else 'desactivado'
    messages.success(request, f'Slider "{slider.titulo}" {estado}.')
    return redirect('panel:sliders_lista')


# ========== OFRENDAS ==========
@login_required
@user_passes_test(es_superuser)
def ofrendas_lista(request):
    """Lista de información de ofrendas"""
    busqueda = request.GET.get('q', '')

    ofrendas = Ofrenda.objects.all()

    if busqueda:
        ofrendas = ofrendas.filter(
            Q(titulo__icontains=busqueda) |
            Q(descripcion__icontains=busqueda) |
            Q(banco__icontains=busqueda)
        )

    ofrendas = ofrendas.order_by('orden')

    paginator = Paginator(ofrendas, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'busqueda': busqueda,
        'form': OfrendaForm(),
    }

    return render(request, 'panel/ofrendas_lista.html', context)


@login_required
@user_passes_test(es_superuser)
def ofrenda_crear(request):
    """Crea una nueva ofrenda"""
    if request.method == 'POST':
        form = OfrendaForm(request.POST)
        if form.is_valid():
            ofrenda = form.save()
            messages.success(request, f'Ofrenda "{ofrenda.titulo}" creada correctamente.')
            return redirect('panel:ofrendas_lista')
        else:
            messages.error(request, 'Error al crear la ofrenda. Verifica los datos.')
    return redirect('panel:ofrendas_lista')


@login_required
@user_passes_test(es_superuser)
def ofrenda_datos(request, pk):
    """Retorna datos de ofrenda en JSON"""
    o = get_object_or_404(Ofrenda, pk=pk)
    return JsonResponse({
        'titulo': o.titulo,
        'descripcion': o.descripcion or '',
        'banco': o.banco or '',
        'cuenta': o.cuenta or '',
        'titular': o.titular or '',
        'mercadopago_link': o.mercadopago_link or '',
        'mercadopago_alias': o.mercadopago_alias or '',
        'orden': o.orden,
        'activo': o.activo,
    })


@login_required
@user_passes_test(es_superuser)
def ofrenda_editar(request, pk):
    """Edita una ofrenda existente"""
    ofrenda = get_object_or_404(Ofrenda, pk=pk)
    if request.method == 'POST':
        form = OfrendaForm(request.POST, instance=ofrenda)
        if form.is_valid():
            ofrenda = form.save()
            messages.success(request, f'Ofrenda "{ofrenda.titulo}" actualizada correctamente.')
            return redirect('panel:ofrendas_lista')
        else:
            messages.error(request, 'Error al actualizar la ofrenda. Verifica los datos.')
    return redirect('panel:ofrendas_lista')


@login_required
@user_passes_test(es_superuser)
@require_POST
def ofrenda_eliminar(request, pk):
    """Elimina una ofrenda"""
    ofrenda = get_object_or_404(Ofrenda, pk=pk)
    titulo = ofrenda.titulo
    ofrenda.delete()
    messages.success(request, f'Ofrenda "{titulo}" eliminada correctamente.')
    return redirect('panel:ofrendas_lista')


@login_required
@user_passes_test(es_superuser)
def ofrenda_toggle_activo(request, pk):
    """Activa/desactiva una ofrenda"""
    ofrenda = get_object_or_404(Ofrenda, pk=pk)
    ofrenda.activo = not ofrenda.activo
    ofrenda.save()
    estado = 'activada' if ofrenda.activo else 'desactivada'
    messages.success(request, f'Ofrenda "{ofrenda.titulo}" {estado}.')
    return redirect('panel:ofrendas_lista')


# ========== DATOS ICE (Configuración) ==========
@login_required
@user_passes_test(es_superuser)
def datosice_editar(request):
    """Edita los datos de contacto y redes sociales (singleton)"""
    datos_ice = DatosIce.load()

    if request.method == 'POST':
        form = DatosIceForm(request.POST, instance=datos_ice)
        if form.is_valid():
            form.save()
            messages.success(request, 'Datos de contacto actualizados correctamente.')
            return redirect('panel:datosice_editar')
        else:
            messages.error(request, 'Error al actualizar los datos. Verifica los campos.')
    else:
        form = DatosIceForm(instance=datos_ice)

    context = {
        'form': form,
        'datos_ice': datos_ice,
    }

    return render(request, 'panel/datosice_editar.html', context)


# ========== AUTENTICACION ==========
def panel_login(request):
    """Vista de login para el panel"""
    if request.user.is_authenticated:
        return redirect('panel:dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').lower().strip()
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            if user.is_staff:
                auth_login(request, user)
                next_url = request.GET.get('next', 'panel:dashboard')
                return redirect(next_url)
            else:
                messages.error(request, 'No tienes permisos para acceder al panel.')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')

    return render(request, 'panel/login.html')


def panel_logout(request):
    """Vista de logout para el panel"""
    auth_logout(request)
    messages.success(request, 'Has cerrado sesión correctamente.')
    return redirect('panel:login')


@login_required(login_url='panel:login')
def cambiar_password(request):
    """Vista para cambiar contraseña del usuario"""
    if request.method == 'POST':
        password_actual = request.POST.get('password_actual', '')
        password_nuevo = request.POST.get('password_nuevo', '')
        password_confirmar = request.POST.get('password_confirmar', '')

        # Validaciones
        if not request.user.check_password(password_actual):
            messages.error(request, 'La contraseña actual es incorrecta.')
        elif len(password_nuevo) < 8:
            messages.error(request, 'La nueva contraseña debe tener al menos 8 caracteres.')
        elif password_nuevo != password_confirmar:
            messages.error(request, 'Las contraseñas nuevas no coinciden.')
        else:
            # Cambiar contraseña
            request.user.set_password(password_nuevo)
            request.user.save()
            # Mantener la sesión activa
            update_session_auth_hash(request, request.user)
            messages.success(request, 'Tu contraseña ha sido actualizada correctamente.')
            return redirect('panel:dashboard')

    return render(request, 'panel/cambiar_password.html')
