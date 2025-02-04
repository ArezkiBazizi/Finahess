"""
URL configuration for finahess project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from student_finances import views
from django.conf import settings
from django.conf.urls.static import static
from student_finances.views import CustomLoginView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # URLs d'authentification
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    
    # URLs de l'application
    path('', views.dashboard, name='dashboard'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('investments/', views.investment_list, name='investment_list'),
    path('budget/', include('student_finances.urls')),
    path('budget/savings/', views.savings_goals, name='savings_goals'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
