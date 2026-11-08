from django import template

register = template.Library()


@register.filter
def pesos(valor):
    """15000 -> 15.000"""
    try:
        return f'{int(valor):,}'.replace(',', '.')
    except (TypeError, ValueError):
        return valor
