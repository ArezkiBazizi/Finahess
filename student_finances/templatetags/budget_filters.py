from django import template
from decimal import Decimal
from student_finances.models import Transaction

register = template.Library()

@register.filter
def category_display(category_code):
    categories_dict = dict(Transaction.CATEGORIES)
    return categories_dict.get(category_code, category_code)

@register.filter
def percentage(value, total):
    """
    Calcule le pourcentage d'une valeur par rapport à un total
    """
    try:
        if not total:
            return "0%"
        value = float(value)
        total = float(total)
        return f"{(value / total * 100):.1f}%"
    except (ValueError, TypeError):
        return "0%" 