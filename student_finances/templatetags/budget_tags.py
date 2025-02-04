from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def percentage(value, total):
    if total:
        return f"{(Decimal(value) / Decimal(total) * 100):.1f}%"
    return "0%" 