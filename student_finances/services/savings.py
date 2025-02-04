from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum
from ..models import Transaction

def calculate_monthly_savings_average(student):
    # Récupérer les transactions d'épargne du mois
    current_date = timezone.now().date()
    month_start = current_date.replace(day=1)
    month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)

    total_savings = Transaction.objects.filter(
        student=student,
        transaction_type='SAVINGS',
        date__range=(month_start, month_end)
    ).aggregate(Sum('amount'))['amount__sum'] or 0

    return total_savings 