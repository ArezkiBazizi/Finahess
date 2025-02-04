from django.urls import path
from . import views

urlpatterns = [
    # Pages principales
    path('', views.budget_plan, name='budget_plan'),
    path('savings/', views.savings_goals, name='savings_goals'),
    path('planned-purchases/', views.planned_purchases, name='planned_purchases'),
    path('add-planned-purchase/', views.add_planned_purchase, name='add_planned_purchase'),
    
    path('api/investments/<int:pk>/', views.investment_detail_api, name='investment_detail_api'),
    
    # Actions sur les investissements
    path('investments/<int:pk>/update/', views.update_investment, name='update_investment'),
    path('investments/<int:pk>/delete/', views.delete_investment, name='delete_investment'),
    
    # URLs pour le planificateur de voyages
    path('travel/', views.travel_planner, name='travel_planner'),
    path('travel/add/', views.add_travel, name='add_travel'),
    path('travel/<int:pk>/edit/', views.edit_travel, name='edit_travel'),
    path('travel/<int:pk>/delete/', views.delete_travel, name='delete_travel'),
    path('budget/<int:budget_id>/delete/', views.delete_budget, name='delete_budget'),
    path('budget/add-income/', views.add_income, name='add_income'),
    path('budget/set-savings-target/', views.set_savings_target, name='set_savings_target'),
    path('budget/add-expense/', views.add_expense, name='add_expense'),
    path('budget/update-initial-savings/', views.update_initial_savings, name='update_initial_savings'),
] 