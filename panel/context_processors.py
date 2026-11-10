from .permisos import puede_eventos, rol_usuario, ROL_LABELS


def permisos_panel(request):
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        return {}
    rol = rol_usuario(user)
    return {
        'panel_es_staff': user.is_staff,
        'panel_puede_eventos': puede_eventos(user),
        'panel_rol_label': ROL_LABELS.get(rol, ''),
    }
