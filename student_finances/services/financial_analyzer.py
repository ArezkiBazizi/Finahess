from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta

class FinancialAnalyzer:
    def __init__(self, student):
        self.student = student

    def analyze_spending_patterns(self):
        """Analyse les habitudes de dépenses"""
        current_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        spending_by_category = self.student.transaction_set.filter(
            transaction_type='EXPENSE',
            date__gte=current_month
        ).values('category').annotate(
            total=Sum('amount')
        ).order_by('-total')

        return {
            'spending_by_category': list(spending_by_category),
            'total_spending': sum(item['total'] for item in spending_by_category),
        }

    def recommend_investments(self):
        """Génère des recommandations d'investissement"""
        monthly_income = self.student.transaction_set.filter(
            transaction_type='INCOME',
            date__gte=timezone.now() - timedelta(days=30)
        ).aggregate(total=Sum('amount'))['total'] or 0

        monthly_expenses = self.student.transaction_set.filter(
            transaction_type='EXPENSE',
            date__gte=timezone.now() - timedelta(days=30)
        ).aggregate(total=Sum('amount'))['total'] or 0

        savings_potential = monthly_income - monthly_expenses

        recommendations = []
        if savings_potential > 1000:
            recommendations.append({
                'type': 'STOCKS',
                'amount': savings_potential * 0.3,
                'reason': 'Potentiel de croissance à long terme'
            })
        if savings_potential > 500:
            recommendations.append({
                'type': 'SAVINGS',
                'amount': savings_potential * 0.5,
                'reason': 'Fonds de sécurité recommandé'
            })
        
        return {
            'savings_potential': savings_potential,
            'recommendations': recommendations
        }

    def get_budget_overview(self):
        """Donne une vue d'ensemble du budget"""
        current_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        income = self.student.transaction_set.filter(
            transaction_type='INCOME',
            date__gte=current_month
        ).aggregate(total=Sum('amount'))['total'] or 0

        expenses = self.student.transaction_set.filter(
            transaction_type='EXPENSE',
            date__gte=current_month
        ).aggregate(total=Sum('amount'))['total'] or 0

        return {
            'income': income,
            'expenses': expenses,
            'balance': income - expenses,
            'savings_rate': ((income - expenses) / income * 100) if income > 0 else 0
        } 