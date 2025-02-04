from django.core.mail import send_mail
from django.conf import settings

class NotificationService:
    @staticmethod
    def send_budget_alert(user, category, spent_percentage):
        subject = f'Alerte budget : {category}'
        message = f'Vous avez dépensé {spent_percentage}% de votre budget {category}'
        send_mail(
            subject,
            message,
            settings.EMAIL_HOST_USER,
            [user.email],
            fail_silently=False,
        )
    
    @staticmethod
    def send_savings_milestone(user, goal_name, percentage):
        subject = f'Objectif épargne : {goal_name}'
        message = f'Félicitations ! Vous avez atteint {percentage}% de votre objectif {goal_name}'
        send_mail(
            subject,
            message,
            settings.EMAIL_HOST_USER,
            [user.email],
            fail_silently=False,
        ) 