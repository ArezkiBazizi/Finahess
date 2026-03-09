from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from ..models import Transaction, MonthlyBudget


def calculate_monthly_savings_average(student):
    """
    Retourne la moyenne mensuelle d'épargne sur les 6 derniers mois
    (basée sur les MonthlyBudget : revenus - dépenses - loisirs).
    Utilisée pour les projections (ex. achats planifiés).
    """
    last_six_months = timezone.now().date() - timedelta(days=180)
    monthly_budgets = MonthlyBudget.objects.filter(
        student=student,
        month__gte=last_six_months
    )
    total = sum(budget.get_savings_amount() for budget in monthly_budgets)
    count = max(monthly_budgets.count(), 1)
    average = total / count
    return Decimal(str(average))


def get_current_month_savings_total(student):
    """Montant total des transactions d'épargne du mois en cours (toutes catégories)."""
    current_date = timezone.now().date()
    month_start = current_date.replace(day=1)
    month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    result = Transaction.objects.filter(
        student=student,
        transaction_type='SAVINGS',
        date__range=(month_start, month_end)
    ).aggregate(total=Sum('amount'))['total'] or 0
    return Decimal(str(result))