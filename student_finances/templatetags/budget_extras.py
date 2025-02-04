from django import template
from django.db.models import Sum

register = template.Library()

@register.filter
def sum_amounts(transactions):
    """Calcule la somme des montants d'une liste de transactions"""
    return sum(t.amount for t in transactions)

@register.filter
def filter_by_category(transactions, category):
    """Filtre les transactions par catégorie"""
    return transactions.filter(category=category)

@register.filter
def filter_by_type(transactions, transaction_type):
    """Filtre les transactions par type (INCOME ou EXPENSE)"""
    return [t for t in transactions if t.transaction_type == transaction_type] 