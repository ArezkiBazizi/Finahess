from django.views.generic import TemplateView
from django.views.decorators.cache import never_cache
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Student, Transaction, Investment, BudgetPlan, BudgetCategory, SavingsGoal, MonthlyBudget, BudgetAllocation, MonthlyRecurringItem, PatrimonySimulation, TravelPlan, PlannedPurchase
from .serializers import (
    StudentSerializer, TransactionSerializer,
    InvestmentSerializer, BudgetPlanSerializer
)
from .services import FinancialAnalyzer, FinancialAPIService
from .services.investment_advisor import InvestmentAdvisor
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.utils import timezone
from datetime import datetime, timedelta
import json
from django.contrib import messages
from django.contrib.auth.views import LoginView
import calendar
from decimal import Decimal
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .services.savings import calculate_monthly_savings_average

# Vue pour servir l'application React
index_view = never_cache(TemplateView.as_view(template_name='index.html'))

class StudentViewSet(viewsets.ModelViewSet):
    serializer_class = StudentSerializer
    
    def get_queryset(self):
        return Student.objects.filter(user=self.request.user)

class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer

    def get_queryset(self):
        return Transaction.objects.filter(student__user=self.request.user)

    @action(detail=False, methods=['get'])
    def spending_analysis(self, request):
        student = request.user.student
        analyzer = FinancialAnalyzer(student)
        return Response(analyzer.analyze_spending_patterns())

class InvestmentViewSet(viewsets.ModelViewSet):
    serializer_class = InvestmentSerializer

    def get_queryset(self):
        return Investment.objects.filter(student__user=self.request.user)

    @action(detail=False, methods=['get'])
    def recommendations(self, request):
        student = request.user.student
        analyzer = FinancialAnalyzer(student)
        return Response(analyzer.recommend_investments())

class BudgetPlanViewSet(viewsets.ModelViewSet):
    serializer_class = BudgetPlanSerializer

    def get_queryset(self):
        return BudgetPlan.objects.filter(student__user=self.request.user)

@login_required
def dashboard(request):
    try:
        student = request.user.student
    except Student.DoesNotExist:
        student = Student.objects.create(user=request.user)

    today = timezone.now()
    current_month = today.month
    current_year = today.year
    start_of_month = timezone.datetime(current_year, current_month, 1)
    end_of_month = (start_of_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)

    # Calcul des totaux
    transactions = Transaction.objects.filter(student=student)
    
    # Calcul du solde total
    incomes = transactions.filter(transaction_type='INCOME').aggregate(Sum('amount'))['amount__sum'] or 0
    expenses = transactions.filter(transaction_type='EXPENSE').aggregate(Sum('amount'))['amount__sum'] or 0
    total_balance = incomes - expenses
    
    # Dépenses mensuelles
    monthly_expenses = Transaction.objects.filter(
        student=student,
        date__range=(start_of_month, end_of_month),
        transaction_type='EXPENSE'
    ).aggregate(Sum('amount'))['amount__sum'] or 0

    # Revenus mensuels
    monthly_incomes = Transaction.objects.filter(
        student=student,
        date__range=(start_of_month, end_of_month),
        transaction_type='INCOME'
    ).aggregate(Sum('amount'))['amount__sum'] or 0

    # Investissements
    total_investments = Investment.objects.filter(
        student=student
    ).aggregate(Sum('current_value'))['current_value__sum'] or 0

    # Données pour les graphiques
    monthly_expenses_by_category = Transaction.objects.filter(
        student=student,
        date__range=(start_of_month, end_of_month),
        transaction_type='EXPENSE'
    ).values('category').annotate(
        total=Sum('amount')
    ).order_by('-total')

    expense_categories = [item['category'] for item in monthly_expenses_by_category]
    expense_amounts = [float(item['total']) for item in monthly_expenses_by_category]

    # Évolution du solde sur 30 jours
    balance_dates = []
    balance_amounts = []
    current_balance = total_balance
    
    # Récupérer les voyages prévus
    upcoming_travels = TravelPlan.objects.filter(
        student=student,
        start_date__gte=today
    ).order_by('start_date')[:3]

    # Récupérer le budget voyages
    travel_budget = TravelPlan.objects.filter(student=student).aggregate(
        total_cost=Sum('transport_cost') + Sum('accommodation_cost') + Sum('activities_budget') + Sum('food_budget') + Sum('other_costs')
    )['total_cost'] or 0

    # Récupérer les achats planifiés
    planned_purchases = PlannedPurchase.objects.filter(student=student, planned_date__year=current_year)
    total_planned = planned_purchases.aggregate(Sum('amount'))['amount__sum'] or 0

    # Calculer le patrimoine estimé
    # Supposons que la projection annuelle est une valeur fixe ou calculée ailleurs
    annual_projection = 10000  # Remplacez ceci par votre logique de projection annuelle

    estimated_patrimony = annual_projection - total_planned - travel_budget

    context = {
        'total_balance': total_balance,
        'monthly_expenses': monthly_expenses,
        'monthly_incomes': monthly_incomes,
        'total_investments': total_investments,
        'expense_categories': json.dumps(expense_categories),
        'expense_amounts': json.dumps(expense_amounts),
        'balance_dates': json.dumps(balance_dates),
        'balance_amounts': json.dumps(balance_amounts),
        'upcoming_travels': upcoming_travels,
        'current_month': today.strftime('%B %Y'),
        'estimated_patrimony': estimated_patrimony,
    }

    return render(request, 'dashboard.html', context)

@login_required
def investment_list(request):
    student = request.user.student
    advisor = InvestmentAdvisor(student)
    
    try:
        # Récupérer les investissements existants
        investments = Investment.objects.filter(student=student)
        
        # Récupérer les données de marché et recommandations
        market_data = advisor.get_market_data()
        recommendations = advisor.get_investment_recommendations()
        
        # Calculer les statistiques d'investissement
        total_invested = sum(inv.initial_amount for inv in investments)
        total_current_value = sum(inv.current_value for inv in investments)
        
        # Calculer le ROI global
        if total_invested > 0:
            total_roi = ((total_current_value - total_invested) / total_invested * 100)
        else:
            total_roi = 0
        
        # Préparer les données pour l'affichage
        investments_data = []
        for inv in investments:
            roi = ((inv.current_value - inv.initial_amount) / inv.initial_amount * 100) if inv.initial_amount > 0 else 0
            investments_data.append({
                'id': inv.id,
                'name': inv.name,
                'type': inv.get_investment_type_display(),
                'initial_amount': inv.initial_amount,
                'current_value': inv.current_value,
                'roi': roi,
                'start_date': inv.start_date,
                'description': inv.description
            })
        
    except Exception as e:
        messages.error(request, f"Erreur lors de la récupération des données: {str(e)}")
        total_invested = 0
        total_current_value = 0
        total_roi = 0
        investments_data = []
        market_data = {'indices': [], 'top_performers': []}
        recommendations = {'profile': 'conservative', 'recommendations': []}
    
    context = {
        'investments': investments_data,
        'total_invested': total_invested,
        'total_current_value': total_current_value,
        'total_roi': total_roi,
        'has_investments': len(investments_data) > 0,
        'market_data': market_data,
        'investment_recommendations': recommendations
    }
    
    return render(request, 'investments/list.html', context)

@login_required
def budget_plan(request):
    student = request.user.student
    current_date = timezone.now().date()
    current_month = current_date.replace(day=1)
    
    # Récupérer le budget du mois
    budget = MonthlyBudget.objects.filter(
        student=student,
        month=current_month
    ).first()

    # Récupérer l'épargne totale depuis les transactions
    total_savings = Transaction.objects.filter(
        student=student,
        transaction_type='SAVINGS',
        category='EMERGENCY_FUND'
    ).aggregate(Sum('amount'))['amount__sum'] or 0

    # Récupérer les transactions du mois
    month_transactions = Transaction.objects.filter(
        student=student,
        date__year=current_date.year,
        date__month=current_date.month
    )
    
    # Séparer les revenus et dépenses
    incomes = month_transactions.filter(transaction_type='INCOME').order_by('-date')
    expenses = month_transactions.filter(transaction_type='EXPENSE').order_by('-date')

    context = {
        'budget': budget,
        'monthly_income': budget.total_income if budget else 0,
        'monthly_expenses': budget.total_expenses if budget else 0,
        'monthly_leisure': budget.total_leisure if budget else 0,
        'savings_amount': total_savings,  # Utiliser l'épargne totale ici
        'savings_progress': (total_savings / budget.savings_target * 100) if budget and budget.savings_target else 0,
        'incomes': incomes,  # Ajouter les revenus au contexte
        'expenses': expenses,  # Ajouter les dépenses au contexte
    }
    
    return render(request, 'budget/monthly_budget.html', context)

@login_required
def delete_budget(request, budget_id):
    if request.method == 'POST':
        budget = get_object_or_404(MonthlyBudget, id=budget_id, student=request.user.student)
        budget.delete()
        messages.success(request, 'Budget supprimé avec succès')
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=405)

@login_required
def update_initial_savings(request):
    if request.method == 'POST':
        student = request.user.student
        initial_savings = Decimal(request.POST['initial_savings'])
        
        # Supprimer l'ancienne épargne initiale
        Transaction.objects.filter(
            student=student,
            transaction_type='SAVINGS',
            category='EMERGENCY_FUND'
        ).delete()
        
        # Créer une nouvelle transaction pour l'épargne initiale
        Transaction.objects.create(
            student=student,
            amount=initial_savings,
            transaction_type='SAVINGS',
            category='EMERGENCY_FUND',
            description="Épargne initiale",
            date=timezone.now().date()
        )
        
        messages.success(request, 'Montant d\'épargne initial mis à jour avec succès!')
        
    return redirect('savings_goals')

@login_required
def savings_goals(request):
    student = request.user.student
    
    # Récupérer l'épargne actuelle totale
    current_savings = Transaction.objects.filter(
        student=student,
        transaction_type='SAVINGS',
        category='EMERGENCY_FUND'
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Calculer la moyenne mensuelle (sur les 6 derniers mois)
    last_six_months = timezone.now().date() - timedelta(days=180)
    monthly_budgets = MonthlyBudget.objects.filter(
        student=student,
        month__gte=last_six_months
    )
    
    # Calculer la moyenne des épargnes mensuelles (sans l'épargne actuelle)
    total_monthly_savings = sum(budget.get_savings_amount() for budget in monthly_budgets)
    months_count = max(monthly_budgets.count(), 1)  # Éviter division par zéro
    monthly_average = total_monthly_savings / months_count
    
    # Calculer les statistiques d'épargne
    savings_stats = {
        'total_saved': current_savings,  # L'épargne totale actuelle
        'initial_savings': current_savings,  # Pour afficher dans le formulaire
        'monthly_average': monthly_average,  # Moyenne mensuelle sans l'épargne actuelle
        'yearly_projection': current_savings + (monthly_average * 12)  # Projection basée sur la moyenne mensuelle
    }

    # Préparer les données de simulation
    simulation_data = generate_savings_simulation(
        monthly_amount=monthly_average,  # Utiliser la vraie moyenne mensuelle
        months=12,
        initial_amount=current_savings  # Point de départ = épargne actuelle
    )
    
    context = {
        'stats': savings_stats,
        'simulation_data': simulation_data,
    }
    
    return render(request, 'budget/savings.html', context)

def generate_savings_simulation(monthly_amount, months, initial_amount=0):
    """
    Génère les données de simulation d'épargne
    initial_amount: montant total de l'épargne actuelle
    monthly_amount: moyenne mensuelle réelle calculée sur l'historique
    """
    labels = []
    conservative = []
    moderate = []
    aggressive = []
    
    current_date = timezone.now()
    conservative_amount = Decimal(str(initial_amount))
    moderate_amount = Decimal(str(initial_amount))
    aggressive_amount = Decimal(str(initial_amount))
    
    # Ajouter le point de départ (mois actuel)
    labels.append(current_date.strftime('%B %Y'))
    conservative.append(float(conservative_amount))
    moderate.append(float(moderate_amount))
    aggressive.append(float(aggressive_amount))
    
    # Simuler les mois suivants avec la moyenne mensuelle réelle
    for i in range(1, months + 1):
        next_date = current_date + timedelta(days=30*i)
        labels.append(next_date.strftime('%B %Y'))
        
        # Ajouter l'épargne mensuelle moyenne
        conservative_amount += monthly_amount
        moderate_amount += monthly_amount
        aggressive_amount += monthly_amount
        
        # Appliquer les rendements (mensuels)
        moderate_amount *= Decimal('1.0025')  # 3% annuel
        aggressive_amount *= Decimal('1.005')  # 6% annuel
        
        conservative.append(float(conservative_amount))
        moderate.append(float(moderate_amount))
        aggressive.append(float(aggressive_amount))
    
    return {
        'labels': labels,
        'conservative': conservative,
        'moderate': moderate,
        'aggressive': aggressive
    }

@login_required
def enhanced_dashboard(request):
    student = request.user.student
    api_service = FinancialAPIService()
    
    # Données financières de base
    current_month = timezone.now().replace(day=1)
    monthly_income = Transaction.objects.filter(
        student=student,
        transaction_type='INCOME',
        date__gte=current_month
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    monthly_expenses = Transaction.objects.filter(
        student=student,
        transaction_type='EXPENSE',
        date__gte=current_month
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Données d'investissement
    investments = Investment.objects.filter(student=student)
    total_invested = sum(inv.amount for inv in investments)
    total_current_value = sum(inv.current_value for inv in investments)
    roi = ((total_current_value - total_invested) / total_invested * 100) if total_invested > 0 else 0
    
    # Objectifs d'épargne
    savings_goals = SavingsGoal.objects.filter(student=student)
    total_saved = sum(goal.current_amount for goal in savings_goals)
    total_target = sum(goal.target_amount for goal in savings_goals)
    
    # Données externes
    financial_news = api_service.get_financial_news()[:5]  # 5 dernières news
    crypto_prices = api_service.get_crypto_prices()
    savings_rates = api_service.get_savings_rates()
    
    context = {
        'monthly_income': monthly_income,
        'monthly_expenses': monthly_expenses,
        'monthly_savings': monthly_income - monthly_expenses,
        'total_invested': total_invested,
        'total_current_value': total_current_value,
        'roi': roi,
        'savings_goals': savings_goals,
        'total_saved': total_saved,
        'total_target': total_target,
        'financial_news': financial_news,
        'crypto_prices': crypto_prices,
        'savings_rates': savings_rates,
    }
    
    return render(request, 'dashboard/enhanced.html', context)

@login_required
def monthly_budget(request):
    student = request.user.student
    today = timezone.now()
    current_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Récupérer ou créer le budget du mois
    budget, created = MonthlyBudget.objects.get_or_create(
        student=student,
        month=current_month
    )
    
    # Récupérer toutes les allocations
    allocations = BudgetAllocation.objects.filter(budget=budget).select_related('category')
    
    # Calculer les projections d'épargne
    savings_projection = budget.get_yearly_savings_projection()
    
    # Préparer les données pour les graphiques
    categories_data = {
        'EXPENSE': {'total': 0, 'items': []},
        'INCOME': {'total': 0, 'items': []},
        'LEISURE': {'total': 0, 'items': []},
        'SAVINGS': {'total': 0, 'items': []}
    }
    
    for allocation in allocations:
        cat_type = allocation.category.category_type
        categories_data[cat_type]['items'].append({
            'name': allocation.category.name,
            'allocated': float(allocation.allocated_amount),
            'spent': float(allocation.spent_amount),
            'remaining': float(allocation.get_remaining()),
            'progress': allocation.get_progress_percentage()
        })
        categories_data[cat_type]['total'] += float(allocation.allocated_amount)
    
    context = {
        'budget': budget,
        'categories_data': categories_data,
        'savings_projection': savings_projection,
        'months_labels': [
            (current_month + timedelta(days=30*i)).strftime('%B %Y')
            for i in range(12)
        ]
    }
    
    return render(request, 'budget/monthly_budget.html', context)

@login_required
def patrimony_simulation(request):
    student = request.user.student
    
    if request.method == 'POST':
        # Créer ou mettre à jour une simulation
        simulation = PatrimonySimulation.objects.create(
            student=student,
            name=request.POST['name'],
            start_date=request.POST['start_date'],
            duration_months=int(request.POST['duration_months']),
            inflation_rate=Decimal(request.POST['inflation_rate']),
            investment_return_rate=Decimal(request.POST['investment_return_rate']),
            salary_growth_rate=Decimal(request.POST['salary_growth_rate'])
        )
        
        results = simulation.simulate_patrimony()
        messages.success(request, 'Simulation créée avec succès!')
        return JsonResponse({'results': results})
    
    # Récupérer les éléments mensuels récurrents
    monthly_items = MonthlyRecurringItem.objects.filter(
        student=student,
        is_active=True
    ).order_by('item_type', 'priority')
    
    # Calculer les totaux mensuels
    totals = {
        'income': sum(item.amount for item in monthly_items if item.item_type == 'INCOME'),
        'expenses': sum(item.amount for item in monthly_items if item.item_type == 'EXPENSE'),
        'savings': sum(item.amount for item in monthly_items if item.item_type == 'SAVINGS')
    }
    
    context = {
        'monthly_items': monthly_items,
        'totals': totals,
        'simulations': PatrimonySimulation.objects.filter(student=student)
    }
    
    return render(request, 'budget/patrimony_simulation.html', context)

@login_required
def monthly_expenses(request):
    student = request.user.student
    
    if request.method == 'POST':
        # Ajouter une nouvelle dépense mensuelle
        Transaction.objects.create(
            student=student,
            amount=request.POST['amount'],
            transaction_type='EXPENSE',
            category=request.POST['category'],
            description=request.POST['description'],
            frequency='MONTHLY',
            payment_day=request.POST['payment_day']
        )
        messages.success(request, 'Dépense mensuelle ajoutée avec succès!')
        return redirect('monthly_expenses')
    
    # Récupérer toutes les transactions mensuelles
    monthly_transactions = Transaction.objects.filter(
        student=student,
        frequency='MONTHLY'
    ).order_by('transaction_type', 'payment_day')
    
    # Calculer les totaux mensuels
    monthly_income = sum(t.amount for t in monthly_transactions if t.transaction_type == 'INCOME')
    monthly_expenses = sum(t.amount for t in monthly_transactions if t.transaction_type == 'EXPENSE')
    monthly_balance = monthly_income - monthly_expenses
    
    # Grouper par catégorie
    expenses_by_category = {}
    for transaction in monthly_transactions.filter(transaction_type='EXPENSE'):
        category = transaction.get_category_display()
        if category not in expenses_by_category:
            expenses_by_category[category] = 0
        expenses_by_category[category] += transaction.amount
    
    context = {
        'monthly_transactions': monthly_transactions,
        'monthly_income': monthly_income,
        'monthly_expenses': monthly_expenses,
        'monthly_balance': monthly_balance,
        'expenses_by_category': expenses_by_category,
    }
    
    return render(request, 'budget/monthly_expenses.html', context)

@login_required
def add_monthly_savings(request):
    student = request.user.student
    
    if request.method == 'POST':
        Transaction.objects.create(
            student=student,
            category=request.POST['category'],
            amount=request.POST['amount'],
            description=request.POST.get('description', ''),
            transaction_type='SAVINGS',  # Nouveau type pour l'épargne
            frequency='MONTHLY',
            payment_day=int(request.POST.get('payment_day', 1))
        )
        messages.success(request, 'Épargne mensuelle ajoutée avec succès!')
    return redirect('budget_plan')

@login_required
def investment_detail_api(request, pk):
    """API endpoint pour récupérer les détails d'un investissement"""
    investment = get_object_or_404(Investment, id=pk, student=request.user.student)
    data = {
        'id': investment.id,
        'name': investment.name,
        'investment_type': investment.investment_type,
        'initial_amount': float(investment.initial_amount),
        'current_value': float(investment.current_value),
        'start_date': investment.start_date.strftime('%Y-%m-%d'),
        'description': investment.description
    }
    return JsonResponse(data)

@login_required
@require_http_methods(["POST"])
def update_investment(request, pk):
    """Vue pour mettre à jour un investissement"""
    investment = get_object_or_404(Investment, id=pk, student=request.user.student)
    
    try:
        investment.name = request.POST['name']
        investment.investment_type = request.POST['investment_type']
        investment.initial_amount = request.POST['initial_amount']
        investment.current_value = request.POST['current_value']
        investment.start_date = request.POST['start_date']
        investment.description = request.POST.get('description', '')
        investment.save()
        messages.success(request, 'Investissement mis à jour avec succès!')
    except Exception as e:
        messages.error(request, f'Erreur lors de la mise à jour: {str(e)}')
    
    return redirect('investment_list')

@login_required
@require_http_methods(["POST"])
def delete_investment(request, pk):
    """Vue pour supprimer un investissement"""
    investment = get_object_or_404(Investment, id=pk, student=request.user.student)
    investment.delete()
    messages.success(request, 'Investissement supprimé avec succès!')
    return redirect('investment_list')

@login_required
def travel_planner(request):
    student = request.user.student
    travels = TravelPlan.objects.filter(student=student).order_by('start_date')
    
    context = {
        'travels': travels,
    }
    
    return render(request, 'travel/planner.html', context)

@login_required
def add_travel(request):
    if request.method == 'POST':
        student = request.user.student
        destination = request.POST['destination']
        start_date = request.POST['start_date']
        end_date = request.POST['end_date']
        transport_type = request.POST['transport_type']
        transport_cost = Decimal(request.POST['transport_cost'])
        accommodation_cost = Decimal(request.POST['accommodation_cost'])
        activities_budget = Decimal(request.POST['activities_budget'])
        food_budget = Decimal(request.POST['food_budget'])
        other_costs = Decimal(request.POST.get('other_costs', 0))
        notes = request.POST.get('notes', '')

        try:
            travel = TravelPlan.objects.create(
                student=student,
                destination=destination,
                start_date=start_date,
                end_date=end_date,
                transport_type=transport_type,
                transport_cost=transport_cost,
                accommodation_cost=accommodation_cost,
                activities_budget=activities_budget,
                food_budget=food_budget,
                other_costs=other_costs,
                notes=notes
            )
            messages.success(request, 'Voyage ajouté avec succès!')
        except Exception as e:
            messages.error(request, f'Erreur lors de l\'ajout du voyage: {str(e)}')

    return redirect('travel_planner')

@login_required
def edit_travel(request, pk):
    travel = get_object_or_404(TravelPlan, pk=pk, student=request.user.student)

    if request.method == 'POST':
        travel.destination = request.POST['destination']
        travel.start_date = request.POST['start_date']
        travel.end_date = request.POST['end_date']
        travel.transport_type = request.POST['transport_type']
        travel.transport_cost = Decimal(request.POST['transport_cost'])
        travel.accommodation_cost = Decimal(request.POST['accommodation_cost'])
        travel.activities_budget = Decimal(request.POST['activities_budget'])
        travel.food_budget = Decimal(request.POST['food_budget'])
        travel.other_costs = Decimal(request.POST.get('other_costs', 0))
        travel.notes = request.POST.get('notes', '')

        travel.save()
        messages.success(request, 'Voyage mis à jour avec succès!')
        return redirect('travel_planner')

    context = {
        'travel': travel,
    }
    return render(request, 'travel/edit_travel.html', context)

@login_required
def delete_travel(request, pk):
    travel = get_object_or_404(TravelPlan, id=pk, student=request.user.student)
    travel.delete()
    messages.success(request, 'Voyage supprimé avec succès!')
    return redirect('travel_planner')

@login_required
def travel_detail_api(request, pk):
    """API endpoint pour récupérer les détails d'un voyage"""
    travel = get_object_or_404(TravelPlan, id=pk, student=request.user.student)
    data = {
        'id': travel.id,
        'destination': travel.destination,
        'start_date': travel.start_date.strftime('%Y-%m-%d'),
        'end_date': travel.end_date.strftime('%Y-%m-%d'),
        'transport_type': travel.transport_type,
        'transport_cost': float(travel.transport_cost),
        'accommodation_cost': float(travel.accommodation_cost),
        'activities_budget': float(travel.activities_budget),
        'food_budget': float(travel.food_budget),
        'other_costs': float(travel.other_costs),
        'notes': travel.notes
    }
    return JsonResponse(data)

@login_required
def add_income(request):
    if request.method == 'POST':
        student = request.user.student
        amount = Decimal(request.POST['amount'])
        title = request.POST['title']
        category = request.POST['category']
        description = request.POST.get('description', '')
        
        # Récupérer ou créer le budget du mois en cours
        current_month = timezone.now().date().replace(day=1)
        budget, created = MonthlyBudget.objects.get_or_create(
            student=student,
            month=current_month,
            defaults={
                'total_income': 0,
                'total_expenses': 0,
                'total_leisure': 0,
                'savings_target': 0
            }
        )
        
        # Créer la transaction
        Transaction.objects.create(
            student=student,
            amount=amount,
            transaction_type='INCOME',
            category=category,
            description=f"{title} - {description}".strip(),
            date=timezone.now().date()
        )
        
        # Mettre à jour le total des revenus
        budget.total_income += amount
        budget.save()
        
        messages.success(request, f'Revenu "{title}" ajouté avec succès!')
    return redirect('budget_plan')

@login_required
def set_savings_target(request):
    if request.method == 'POST':
        student = request.user.student
        target = Decimal(request.POST['target'])
        
        # Récupérer ou créer le budget du mois en cours
        current_month = timezone.now().date().replace(day=1)
        budget, created = MonthlyBudget.objects.get_or_create(
            student=student,
            month=current_month,
            defaults={
                'total_income': 0,
                'total_expenses': 0,
                'total_leisure': 0,
                'savings_target': 0
            }
        )
        
        # Mettre à jour l'objectif d'épargne
        budget.savings_target = target
        budget.save()
        
        messages.success(request, 'Objectif d\'épargne défini avec succès!')
    return redirect('budget_plan')

@login_required
def add_expense(request):
    if request.method == 'POST':
        student = request.user.student
        amount = Decimal(request.POST['amount'])
        title = request.POST['title']
        category = request.POST['category']
        description = request.POST.get('description', '')
        
        # Récupérer le budget du mois
        current_month = timezone.now().date().replace(day=1)
        budget, created = MonthlyBudget.objects.get_or_create(
            student=student,
            month=current_month,
            defaults={
                'total_income': 0,
                'total_expenses': 0,
                'total_leisure': 0,
                'savings_target': 0
            }
        )
        
        # Créer la transaction
        Transaction.objects.create(
            student=student,
            amount=amount,
            transaction_type='EXPENSE',
            category=category,
            description=f"{title} - {description}".strip(),
            date=timezone.now().date()
        )
        
        # Mettre à jour le total des dépenses
        if category == 'LEISURE':
            budget.total_leisure += amount
        else:
            budget.total_expenses += amount
        budget.save()
        
        messages.success(request, f'Dépense "{title}" ajoutée avec succès!')
    return redirect('budget_plan')

class CustomLoginView(LoginView):
    def form_valid(self, form):
        response = super().form_valid(form)
        # Créer un profil étudiant si nécessaire
        student, created = Student.objects.get_or_create(
            user=self.request.user,
            defaults={
                'student_id': f"STU{self.request.user.id:06d}",
                # date_of_birth reste null pour l'instant
            }
        )
        return response

def login_view(request):
    return render(request, 'registration/login.html')

@login_required
def planned_purchases(request):
    student = request.user.student
    current_date = timezone.now().date()
    
    # Récupérer les achats planifiés
    purchases = PlannedPurchase.objects.filter(
        student=student,
        planned_date__year=current_date.year,
        is_completed=False
    ).order_by('planned_date')
    
    # Calculer le total des achats planifiés
    total_planned = purchases.aggregate(Sum('amount'))['amount__sum'] or 0

    # Récupérer l'épargne totale pour comparaison
    total_savings = Transaction.objects.filter(
        student=student,
        transaction_type='SAVINGS',
        category='EMERGENCY_FUND'
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Calculer le patrimoine estimé en fin d'année
    monthly_savings = calculate_monthly_savings_average(student)
    months_remaining = 12 - current_date.month + 1
    estimated_savings = total_savings + (monthly_savings * months_remaining)
    estimated_patrimony = estimated_savings - total_planned
    
    context = {
        'purchases': purchases,
        'total_planned': total_planned,
        'total_savings': total_savings,
        'estimated_patrimony': estimated_patrimony,
        'monthly_savings': monthly_savings
    }
    
    return render(request, 'budget/planned_purchases.html', context)

@login_required
def add_planned_purchase(request):
    if request.method == 'POST':
        student = request.user.student
        name = request.POST['name']
        amount = Decimal(request.POST['amount'])
        planned_date = request.POST['planned_date']
        priority = request.POST['priority']
        description = request.POST.get('description', '')
        
        PlannedPurchase.objects.create(
            student=student,
            name=name,
            amount=amount,
            planned_date=planned_date,
            priority=priority,
            description=description
        )
        
        messages.success(request, f'Achat planifié "{name}" ajouté avec succès!')
    return redirect('planned_purchases') 