from django import template

register = template.Library()


@register.filter
def pesos(valor):
    """15000 -> 15.000"""
    try:
        return f'{int(valor):,}'.replace(',', '.')
    except (TypeError, ValueError):
        return valor


@register.filter
def whatsapp(celular):
    """'+54 9 3811234567' -> '5493811234567' para armar el link wa.me"""
    from eventos.models import numero_whatsapp
    return numero_whatsapp(celular or '')
