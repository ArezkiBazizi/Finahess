from django.utils import timezone
from .models import Transaction

def create_recurring_transactions():
    today = timezone.now()
    
    # Récupérer toutes les transactions récurrentes dont le jour correspond à aujourd'hui
    recurring_transactions = Transaction.objects.filter(
        is_recurring=True,
        recurring_day=today.day
    )
    
    # Créer les nouvelles transactions
    for transaction in recurring_transactions:
        Transaction.objects.create(
            student=transaction.student,
            category=transaction.category,
            amount=transaction.amount,
            date=today,
            description=transaction.description,
            transaction_type=transaction.transaction_type,
            is_recurring=False  # La nouvelle transaction n'est pas récurrente
        ) 