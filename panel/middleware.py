from .models import Visita


def get_client_ip(request):
    """Obtiene la IP real del cliente"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def parse_user_agent(user_agent_string):
    """Parsea el user agent para obtener info del dispositivo"""
    # Detección simple sin librerías externas
    ua = user_agent_string.lower()

    # Navegador
    if 'chrome' in ua and 'edg' not in ua:
        navegador = 'Chrome'
    elif 'firefox' in ua:
        navegador = 'Firefox'
    elif 'safari' in ua and 'chrome' not in ua:
        navegador = 'Safari'
    elif 'edg' in ua:
        navegador = 'Edge'
    else:
        navegador = 'Otro'

    # Sistema Operativo
    if 'windows' in ua:
        sistema = 'Windows'
    elif 'mac' in ua:
        sistema = 'MacOS'
    elif 'linux' in ua:
        sistema = 'Linux'
    elif 'android' in ua:
        sistema = 'Android'
    elif 'iphone' in ua or 'ipad' in ua:
        sistema = 'iOS'
    else:
        sistema = 'Otro'

    # Dispositivo
    if 'mobile' in ua or 'android' in ua or 'iphone' in ua:
        dispositivo = 'mobile'
    elif 'tablet' in ua or 'ipad' in ua:
        dispositivo = 'tablet'
    else:
        dispositivo = 'pc'

    return navegador, sistema, dispositivo


class VisitasMiddleware:
    """
    Middleware para rastrear visitas al sitio
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Solo rastrea vistas GET que no sean del panel de admin ni archivos estáticos
        if (request.method == 'GET' and
            not request.path.startswith('/panel/') and
            not request.path.startswith('/admin/') and
            not request.path.startswith('/static/') and
            not request.path.startswith('/media/')):

            try:
                ip = get_client_ip(request)
                user_agent = request.META.get('HTTP_USER_AGENT', '')
                navegador, sistema, dispositivo = parse_user_agent(user_agent)

                Visita.objects.create(
                    ip=ip,
                    user_agent=user_agent,
                    navegador=navegador,
                    sistema_operativo=sistema,
                    dispositivo=dispositivo,
                    url=request.path,
                    referrer=request.META.get('HTTP_REFERER', ''),
                )
            except Exception:
                # Si falla el registro de visita, no afecta la respuesta
                pass

        response = self.get_response(request)
        return response
