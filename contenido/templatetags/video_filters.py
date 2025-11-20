from django import template

register = template.Library()


@register.filter
def youtube_embed_url(url):
    """
    Convierte una URL de YouTube a formato embed usando youtube-nocookie.com
    para mejor soporte en localhost y privacidad.
    """
    if not url:
        return ''

    # Convertir a youtube-nocookie.com
    url = url.replace('youtube.com', 'youtube-nocookie.com')

    return url


@register.filter
def youtube_watch_url(url):
    """
    Convierte una URL de YouTube embed a formato watch para abrir en YouTube.
    """
    if not url:
        return ''

    # Convertir de embed a watch
    url = url.replace('youtube-nocookie.com', 'youtube.com')
    url = url.replace('/embed/', '/watch?v=')

    # Limpiar parámetros de start si existen
    if '?start=' in url:
        url = url.split('?')[0].replace('/watch', '/watch?v=')

    return url
