from decimal import Decimal
from django.db.models import Sum, Avg
from .models import Transaction, Investment, BudgetPlan
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

class FinancialAnalyzer:
    def __init__(self, student):
        self.student = student

    def analyze_spending_patterns(self):
        """Analyse les habitudes de dépenses"""
        return Transaction.objects.filter(
            student=self.student,
            transaction_type='EXPENSE'
        ).values('category').annotate(
            total=Sum('amount'),
            avg=Avg('amount')
        )

    def recommend_investments(self):
        """Recommande des investissements basés sur le profil"""
        monthly_savings = self.calculate_monthly_savings()
        recommendations = []
        
        if monthly_savings > 500:
            recommendations.append({
                'type': 'STOCKS',
                'amount': monthly_savings * Decimal('0.4'),
                'reason': 'Potentiel de croissance à long terme'
            })
        if monthly_savings > 200:
            recommendations.append({
                'type': 'SAVINGS',
                'amount': monthly_savings * Decimal('0.3'),
                'reason': 'Fonds de sécurité'
            })
        
        return recommendations

    def calculate_monthly_savings(self):
        """Calcule les économies mensuelles moyennes"""
        income = Transaction.objects.filter(
            student=self.student,
            transaction_type='INCOME'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        expenses = Transaction.objects.filter(
            student=self.student,
            transaction_type='EXPENSE'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        return (income - expenses) / 12

    def get_best_performing_investments(self):
        """Identifie les meilleurs investissements"""
        return Investment.objects.filter(
            student=self.student
        ).order_by('-actual_return')[:5]

class InvestmentAdvisor:
    def __init__(self, student):
        self.student = student
        
    def get_market_data(self):
        """Récupère les données des principaux indices et actions"""
        try:
            # Indices majeurs
            indices = ['^FCHI', '^STOXX50E', '^GSPC']  # CAC40, EURO STOXX 50, S&P500
            indices_data = []
            
            for index in indices:
                ticker = yf.Ticker(index)
                hist = ticker.history(period='1d')
                if not hist.empty:
                    indices_data.append({
                        'symbol': index,
                        'name': self._get_index_name(index),
                        'price': round(hist['Close'].iloc[-1], 2),
                        'change': round(((hist['Close'].iloc[-1] / hist['Close'].iloc[-2]) - 1) * 100, 2)
                    })
            
            # Meilleures performances du CAC40
            cac40 = self._get_cac40_top_performers()
            
            return {
                'indices': indices_data,
                'top_performers': cac40
            }
        except Exception as e:
            print(f"Erreur lors de la récupération des données de marché: {str(e)}")
            return {'indices': [], 'top_performers': []}
    
    def get_investment_recommendations(self):
        """Génère des recommandations d'investissement personnalisées"""
        monthly_savings = self._calculate_monthly_savings()
        risk_profile = self._determine_risk_profile()
        
        recommendations = []
        
        if monthly_savings > 0:
            if risk_profile == 'conservative':
                recommendations.extend([
                    {
                        'type': 'SAVINGS',
                        'name': 'Livret A',
                        'description': 'Épargne sécurisée avec un taux garanti',
                        'expected_return': '3%',
                        'risk_level': 'Très faible',
                        'min_amount': 10
                    },
                    {
                        'type': 'BONDS',
                        'name': 'Obligations d\'État',
                        'description': 'Investissement sûr à long terme',
                        'expected_return': '2-4%',
                        'risk_level': 'Faible',
                        'min_amount': 100
                    }
                ])
            elif risk_profile == 'moderate':
                recommendations.extend([
                    {
                        'type': 'STOCKS',
                        'name': 'ETF World',
                        'description': 'Diversification mondiale',
                        'expected_return': '5-8%',
                        'risk_level': 'Moyen',
                        'min_amount': 50
                    },
                    {
                        'type': 'REAL_ESTATE',
                        'name': 'SCPI',
                        'description': 'Investissement immobilier collectif',
                        'expected_return': '4-6%',
                        'risk_level': 'Moyen',
                        'min_amount': 500
                    }
                ])
            else:  # aggressive
                recommendations.extend([
                    {
                        'type': 'STOCKS',
                        'name': 'Actions individuelles',
                        'description': 'Sélection d\'entreprises à fort potentiel',
                        'expected_return': '8-15%',
                        'risk_level': 'Élevé',
                        'min_amount': 100
                    },
                    {
                        'type': 'CRYPTO',
                        'name': 'Bitcoin/Ethereum',
                        'description': 'Exposition aux cryptomonnaies majeures',
                        'expected_return': '10-30%',
                        'risk_level': 'Très élevé',
                        'min_amount': 50
                    }
                ])
        
        return {
            'profile': risk_profile,
            'monthly_savings': monthly_savings,
            'recommendations': recommendations
        }
    
    def _calculate_monthly_savings(self):
        """Calcule la capacité d'épargne mensuelle"""
        monthly_transactions = self.student.transaction_set.filter(frequency='MONTHLY')
        income = monthly_transactions.filter(transaction_type='INCOME').aggregate(Sum('amount'))['amount__sum'] or 0
        expenses = monthly_transactions.filter(transaction_type='EXPENSE').aggregate(Sum('amount'))['amount__sum'] or 0
        return income - expenses
    
    def _determine_risk_profile(self):
        """Détermine le profil de risque basé sur l'âge et les investissements existants"""
        age = self.student.age if hasattr(self.student, 'age') else 25
        existing_investments = self.student.investment_set.all()
        
        # Calcul du score de risque
        risk_score = 0
        
        # Facteur âge
        if age < 30:
            risk_score += 3
        elif age < 40:
            risk_score += 2
        else:
            risk_score += 1
            
        # Facteur expérience d'investissement
        if existing_investments.filter(investment_type='CRYPTO').exists():
            risk_score += 3
        if existing_investments.filter(investment_type='STOCKS').exists():
            risk_score += 2
        if existing_investments.filter(investment_type='BONDS').exists():
            risk_score += 1
            
        if risk_score >= 5:
            return 'aggressive'
        elif risk_score >= 3:
            return 'moderate'
        else:
            return 'conservative'
    
    def _get_index_name(self, symbol):
        """Retourne le nom complet de l'indice"""
        names = {
            '^FCHI': 'CAC 40',
            '^STOXX50E': 'EURO STOXX 50',
            '^GSPC': 'S&P 500'
        }
        return names.get(symbol, symbol)
    
    def _get_cac40_top_performers(self):
        """Récupère les meilleures performances du CAC40"""
        try:
            # Liste des principales actions du CAC40
            cac40_stocks = ['AI.PA', 'AIR.PA', 'BNP.PA', 'CS.PA', 'KER.PA']  # Exemple réduit
            performers = []
            
            for symbol in cac40_stocks:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period='1mo')
                if not hist.empty:
                    monthly_return = ((hist['Close'].iloc[-1] / hist['Close'].iloc[0]) - 1) * 100
                    performers.append({
                        'symbol': symbol.replace('.PA', ''),
                        'name': ticker.info.get('longName', symbol),
                        'price': round(hist['Close'].iloc[-1], 2),
                        'monthly_return': round(monthly_return, 2)
                    })
            
            return sorted(performers, key=lambda x: x['monthly_return'], reverse=True)[:5]
        except Exception:
            return [] 