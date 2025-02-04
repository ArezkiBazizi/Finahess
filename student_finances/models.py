from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.core.exceptions import ValidationError

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    student_id = models.CharField(max_length=20, unique=True, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username}"

    def save(self, *args, **kwargs):
        if not self.student_id:
            self.student_id = f"STU{self.user.id:06d}"
        super().save(*args, **kwargs)

@receiver(post_save, sender=User)
def create_student(sender, instance, created, **kwargs):
    if created:
        Student.objects.get_or_create(
            user=instance,
            defaults={
                'student_id': f"STU{instance.id:06d}",
            }
        )

@receiver(post_save, sender=User)
def save_student(sender, instance, **kwargs):
    try:
        instance.student.save()
    except Student.DoesNotExist:
        Student.objects.get_or_create(
            user=instance,
            defaults={
                'student_id': f"STU{instance.id:06d}",
            }
        )

class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('INCOME', 'Revenu'),
        ('EXPENSE', 'Dépense'),
        ('SAVINGS', 'Épargne'),
    ]
    
    CATEGORIES = [
        # Revenus fixes
        ('SALARY', 'Salaire'),
        ('SCHOLARSHIP', 'Bourse'),
        ('RENTAL', 'Revenus locatifs'),
        ('HOUSING_BENEFIT', 'APL/AL'),
        ('ACTIVITY_BONUS', 'Prime d\'activité'),
        ('MOBILITY_AID', 'Aide mobilité jeune'),
        ('OTHER_INCOME', 'Autres revenus'),
        # Dépenses fixes
        ('RENT', 'Loyer'),
        ('UTILITIES', 'Charges'),
        ('INSURANCE', 'Assurances'),
        ('PHONE', 'Téléphone/Internet'),
        ('TRANSPORT', 'Transport'),
        ('FOOD', 'Alimentation'),
        ('SPORT', 'Sport'),
        ('LEISURE', 'Loisirs'),
        ('GYM', 'Salle de sport'),
        ('LAUNDRY', 'Laverie'),
        ('SHOPPING', 'Shopping'),
        ('OTHER', 'Autre'),
        # Catégories d'épargne
        ('EMERGENCY_FUND', 'Épargne de précaution'),
        ('INVESTMENT_SAVINGS', 'Épargne investissement'),
        ('PROJECT_SAVINGS', 'Épargne projet'),
        ('RETIREMENT_SAVINGS', 'Épargne retraite'),
    ]
    
    FREQUENCY = [
        ('MONTHLY', 'Mensuel'),
        ('ONEOFF', 'Ponctuel'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=7, choices=TRANSACTION_TYPES)
    category = models.CharField(max_length=20, choices=CATEGORIES)
    description = models.TextField(blank=True)
    frequency = models.CharField(max_length=10, choices=FREQUENCY, default='ONEOFF')
    payment_day = models.IntegerField(null=True, blank=True, help_text="Jour du mois pour les transactions mensuelles")
    date = models.DateField(null=True, blank=True, help_text="Date uniquement pour les transactions ponctuelles")
    
    def __str__(self):
        if self.frequency == 'MONTHLY':
            return f"{self.get_transaction_type_display()} mensuel - {self.amount}€ (le {self.payment_day} du mois)"
        return f"{self.get_transaction_type_display()} ponctuel - {self.amount}€ - {self.date}"

    def clean(self):
        if self.frequency == 'MONTHLY' and not self.payment_day:
            raise ValidationError('Le jour de paiement est requis pour les transactions mensuelles')
        if self.frequency == 'ONEOFF' and not self.date:
            raise ValidationError('La date est requise pour les transactions ponctuelles')
        if self.payment_day and (self.payment_day < 1 or self.payment_day > 31):
            raise ValidationError('Le jour de paiement doit être entre 1 et 31')

    class Meta:
        ordering = ['frequency', 'payment_day', '-date']

    def get_return_on_investment(self):
        if self.category == 'INVESTMENT':
            return (self.current_value - self.amount) / self.amount * 100
        return 0

class Investment(models.Model):
    INVESTMENT_TYPES = [
        ('STOCKS', 'Actions'),
        ('SAVINGS', 'Épargne'),
        ('CRYPTO', 'Cryptomonnaie'),
        ('REAL_ESTATE', 'Immobilier'),
        ('OTHER', 'Autre'),
    ]
    
    RISK_LEVELS = [
        ('LOW', 'Faible'),
        ('MEDIUM', 'Moyen'),
        ('HIGH', 'Élevé'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    investment_type = models.CharField(max_length=20, choices=INVESTMENT_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    current_value = models.DecimalField(max_digits=10, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    risk_level = models.CharField(max_length=10, choices=RISK_LEVELS)
    expected_return = models.DecimalField(max_digits=5, decimal_places=2)
    actual_return = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    def calculate_roi(self):
        return ((self.current_value - self.amount) / self.amount) * 100
    
    def __str__(self):
        return f"{self.name} - {self.investment_type} - {self.amount}€"

class Budget(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    category = models.CharField(max_length=20, choices=Transaction.CATEGORIES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    month = models.DateField()
    
    def __str__(self):
        return f"{self.student.user.username} - Budget {self.category} : {self.amount} €"

class BudgetPlan(models.Model):
    PERIOD_CHOICES = [
        ('MONTHLY', 'Mensuel'),
        ('QUARTERLY', 'Trimestriel'),
        ('YEARLY', 'Annuel'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    total_budget = models.DecimalField(max_digits=10, decimal_places=2)
    period = models.CharField(max_length=10, choices=PERIOD_CHOICES)
    savings_goal = models.DecimalField(max_digits=10, decimal_places=2)
    
    def get_progress(self):
        actual_savings = Transaction.objects.filter(
            student=self.student,
            transaction_type='INCOME',
            date__range=[self.start_date, self.end_date]
        ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0')
        return (actual_savings / self.savings_goal) * 100

class BudgetCategory(models.Model):
    CATEGORY_TYPES = [
        ('EXPENSE', 'Dépense'),
        ('INCOME', 'Revenu'),
        ('LEISURE', 'Loisirs'),
        ('SAVINGS', 'Épargne')
    ]
    
    name = models.CharField(max_length=100)
    category_type = models.CharField(
        max_length=20, 
        choices=CATEGORY_TYPES,
        default='EXPENSE'
    )
    icon = models.CharField(max_length=50, default='bi-cash')
    
    def __str__(self):
        return f"{self.get_category_type_display()} - {self.name}"

class MonthlyBudget(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    month = models.DateField()
    total_income = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_expenses = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_leisure = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    savings_target = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def get_savings_amount(self):
        return self.total_income - self.total_expenses - self.total_leisure
    
    def get_savings_progress(self):
        if self.savings_target > 0:
            return (self.get_savings_amount() / self.savings_target) * 100
        return 0
    
    def get_yearly_savings_projection(self):
        monthly_savings = self.get_savings_amount()
        return {
            'monthly_amount': monthly_savings,
            'yearly_total': monthly_savings * 12,
            'monthly_projections': [monthly_savings * (i+1) for i in range(12)]
        }

    def __str__(self):
        return f"Budget de {self.student} pour {self.month}"

class BudgetAllocation(models.Model):
    budget = models.ForeignKey(MonthlyBudget, on_delete=models.CASCADE)
    category = models.ForeignKey(BudgetCategory, on_delete=models.CASCADE)
    allocated_amount = models.DecimalField(max_digits=10, decimal_places=2)
    spent_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    def get_remaining(self):
        return self.allocated_amount - self.spent_amount
    
    def get_progress_percentage(self):
        if self.allocated_amount > 0:
            return (self.spent_amount / self.allocated_amount) * 100
        return 0

class SavingsGoal(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    target_amount = models.DecimalField(max_digits=10, decimal_places=2)
    current_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    target_date = models.DateField()
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def get_progress_percentage(self):
        return (self.current_amount / self.target_amount) * 100 if self.target_amount > 0 else 0
    
    def get_remaining_amount(self):
        return self.target_amount - self.current_amount
    
    def get_monthly_target(self):
        remaining_months = (self.target_date - timezone.now().date()).days / 30
        if remaining_months <= 0:
            return 0
        return self.get_remaining_amount() / remaining_months

class MonthlyRecurringItem(models.Model):
    ITEM_TYPES = [
        ('INCOME', 'Revenu'),
        ('EXPENSE', 'Dépense'),
        ('SAVINGS', 'Épargne'),
    ]
    
    CATEGORIES = [
        # Revenus
        ('SALARY', 'Salaire'),
        ('SCHOLARSHIP', 'Bourse'),
        ('RENTAL', 'Revenus locatifs'),
        ('OTHER_INCOME', 'Autres revenus'),
        # Dépenses fixes
        ('RENT', 'Loyer'),
        ('UTILITIES', 'Charges'),
        ('INSURANCE', 'Assurances'),
        ('PHONE', 'Téléphone/Internet'),
        ('TRANSPORT', 'Transport'),
        # Dépenses variables
        ('GROCERIES', 'Courses'),
        ('LEISURE', 'Loisirs'),
        ('GYM', 'Salle de sport'),
        ('LAUNDRY', 'Laverie'),
        ('SHOPPING', 'Shopping'),
        ('HEALTH', 'Santé'),
        # Épargne
        ('EMERGENCY', 'Épargne de précaution'),
        ('INVESTMENT', 'Investissements'),
        ('PROJECTS', 'Projets'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    item_type = models.CharField(max_length=10, choices=ITEM_TYPES)
    category = models.CharField(max_length=20, choices=CATEGORIES)
    is_active = models.BooleanField(default=True)
    priority = models.IntegerField(default=0)  # 0 = haute priorité
    
    def __str__(self):
        return f"{self.name} ({self.get_item_type_display()}) - {self.amount}€/mois"

class PatrimonySimulation(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    start_date = models.DateField()
    duration_months = models.IntegerField()
    
    # Paramètres de simulation
    inflation_rate = models.DecimalField(max_digits=4, decimal_places=2, default=2.00)
    investment_return_rate = models.DecimalField(max_digits=4, decimal_places=2, default=5.00)
    salary_growth_rate = models.DecimalField(max_digits=4, decimal_places=2, default=2.00)
    
    def simulate_patrimony(self):
        monthly_items = MonthlyRecurringItem.objects.filter(
            student=self.student,
            is_active=True
        )
        
        # Initialisation
        current_patrimony = 0
        monthly_income = sum(item.amount for item in monthly_items if item.item_type == 'INCOME')
        monthly_expenses = sum(item.amount for item in monthly_items if item.item_type == 'EXPENSE')
        monthly_savings = sum(item.amount for item in monthly_items if item.item_type == 'SAVINGS')
        
        simulation_results = []
        
        for month in range(self.duration_months):
            # Appliquer l'inflation aux dépenses
            monthly_expenses *= (1 + self.inflation_rate/100/12)
            
            # Appliquer la croissance du salaire
            if month % 12 == 0 and month > 0:  # Une fois par an
                monthly_income *= (1 + self.salary_growth_rate/100)
            
            # Calculer l'épargne du mois
            month_savings = monthly_income - monthly_expenses + monthly_savings
            
            # Appliquer le rendement des investissements
            investment_return = current_patrimony * (self.investment_return_rate/100/12)
            current_patrimony += month_savings + investment_return
            
            simulation_results.append({
                'month': month + 1,
                'patrimony': round(current_patrimony, 2),
                'monthly_savings': round(month_savings, 2),
                'investment_return': round(investment_return, 2)
            })
        
        return simulation_results

class TravelPlan(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    destination = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField()
    transport_type = models.CharField(max_length=100)
    transport_cost = models.DecimalField(max_digits=10, decimal_places=2)
    accommodation_cost = models.DecimalField(max_digits=10, decimal_places=2)
    activities_budget = models.DecimalField(max_digits=10, decimal_places=2)
    food_budget = models.DecimalField(max_digits=10, decimal_places=2)
    other_costs = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def total_cost(self):
        return (
            self.transport_cost +
            self.accommodation_cost +
            self.activities_budget +
            self.food_budget +
            self.other_costs
        )

    @property
    def duration_days(self):
        return (self.end_date - self.start_date).days + 1

    def __str__(self):
        return f"{self.destination} ({self.start_date} - {self.end_date})"

class PlannedPurchase(models.Model):
    PRIORITY_CHOICES = [
        ('LOW', 'Faible'),
        ('MEDIUM', 'Moyenne'),
        ('HIGH', 'Haute')
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    planned_date = models.DateField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='MEDIUM')
    description = models.TextField(blank=True)
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['planned_date', '-priority'] 