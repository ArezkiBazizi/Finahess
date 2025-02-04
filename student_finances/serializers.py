from rest_framework import serializers
from .models import Student, Transaction, Investment, BudgetPlan, BudgetCategory

class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = '__all__'

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = '__all__'

class InvestmentSerializer(serializers.ModelSerializer):
    roi = serializers.SerializerMethodField()

    class Meta:
        model = Investment
        fields = '__all__'

    def get_roi(self, obj):
        return obj.calculate_roi()

class BudgetPlanSerializer(serializers.ModelSerializer):
    progress = serializers.SerializerMethodField()

    class Meta:
        model = BudgetPlan
        fields = '__all__'

    def get_progress(self, obj):
        return obj.get_progress()

class BudgetCategorySerializer(serializers.ModelSerializer):
    spending_status = serializers.SerializerMethodField()

    class Meta:
        model = BudgetCategory
        fields = '__all__'

    def get_spending_status(self, obj):
        return obj.get_spending_status() 