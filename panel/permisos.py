"""
Permisos del panel.

- Superusuario: todo.
- Staff: todo el panel menos Contenido Web / Configuración / Usuarios.
- Grupo "Eventos" (sin staff): solo la sección Eventos.
"""
GRUPO_EVENTOS = 'Eventos'

ROL_ADMIN = 'admin'
ROL_STAFF = 'staff'
ROL_EVENTOS = 'eventos'

ROL_LABELS = {
    ROL_ADMIN: 'Administrador',
    ROL_STAFF: 'Staff',
    ROL_EVENTOS: 'Solo Eventos',
}


def en_grupo_eventos(user):
    if not user.is_authenticated:
        return False
    if not hasattr(user, '_en_grupo_eventos'):
        user._en_grupo_eventos = user.groups.filter(name=GRUPO_EVENTOS).exists()
    return user._en_grupo_eventos


def puede_eventos(user):
    return user.is_authenticated and user.is_active and (user.is_staff or en_grupo_eventos(user))


def puede_entrar_panel(user):
    return puede_eventos(user)


def rol_usuario(user):
    if user.is_superuser:
        return ROL_ADMIN
    if user.is_staff:
        return ROL_STAFF
    if en_grupo_eventos(user):
        return ROL_EVENTOS
    return None


def inicio_panel(user):
    """Nombre de la URL a la que va cada usuario al entrar al panel"""
    return 'panel:dashboard' if user.is_staff else 'eventos:panel_lista'
