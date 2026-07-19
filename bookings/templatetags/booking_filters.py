from django import template
from datetime import timedelta

register = template.Library()

@register.filter
def multiply(value, arg):
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return ''

@register.filter
def add_days(value, days):
    try:
        return value + timedelta(days=int(days))
    except (ValueError, TypeError, AttributeError):
        return value

@register.filter
def replace(value, arg):
    try:
        return str(value).replace(str(arg), '')
    except (ValueError, TypeError):
        return value
