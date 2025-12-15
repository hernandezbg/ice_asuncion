import requests
from .models import Visita


# Cache simple para geolocalización (evita llamadas repetidas a la API)
_geo_cache = {}


def get_geolocation(ip):
    """Obtiene la geolocalización de una IP usando ip-api.com (gratuito)"""
    # No geolocalizar IPs locales
    if ip in ('127.0.0.1', 'localhost', '::1') or ip.startswith('192.168.') or ip.startswith('10.'):
        return {'pais': '', 'region': '', 'ciudad': ''}

    # Verificar cache
    if ip in _geo_cache:
        return _geo_cache[ip]

    try:
        response = requests.get(
            f'http://ip-api.com/json/{ip}?fields=status,country,regionName,city',
            timeout=2
        )
        data = response.json()

        if data.get('status') == 'success':
            result = {
                'pais': data.get('country', ''),
                'region': data.get('regionName', ''),
                'ciudad': data.get('city', '')
            }
        else:
            result = {'pais': '', 'region': '', 'ciudad': ''}

        # Guardar en cache (máximo 1000 entradas)
        if len(_geo_cache) < 1000:
            _geo_cache[ip] = result

        return result
    except Exception:
        return {'pais': '', 'region': '', 'ciudad': ''}


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

                # Obtener geolocalización
                geo = get_geolocation(ip)

                Visita.objects.create(
                    ip=ip,
                    user_agent=user_agent,
                    navegador=navegador,
                    sistema_operativo=sistema,
                    dispositivo=dispositivo,
                    pais=geo.get('pais', ''),
                    region=geo.get('region', ''),
                    ciudad=geo.get('ciudad', ''),
                    url=request.path,
                    referrer=request.META.get('HTTP_REFERER', ''),
                )
            except Exception:
                # Si falla el registro de visita, no afecta la respuesta
                pass

        response = self.get_response(request)
        return response
