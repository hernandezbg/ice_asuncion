from .models import DatosIce, Pagina


def datos_ice(request):
    """
    Context processor para hacer disponibles los datos de ICE en todos los templates
    """
    return {
        'datos_ice': DatosIce.load()
    }


def paginas_menu(request):
    """
    Context processor para hacer disponibles las páginas en el menú de navegación
    """
    return {
        'paginas_menu': Pagina.objects.filter(activo=True).order_by('orden')
    }
