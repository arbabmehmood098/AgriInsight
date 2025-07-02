"""
URL configuration for frontend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from django.urls import path
from app import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path('', views.home_view, name='home'),
    path('home/', views.home_view, name='home'),
    path('about/', views.about, name='about'),
    path('model/', views.model, name='model'),
    path('feedback/', views.feedback, name='feedback'),
    path('feedback/history/', views.user_feedback_history, name='feedback_history'),
    path('admin/feedback/', views.admin_feedback_view, name='admin_feedback'),
    path('online_advise/', views.online_advise, name='online_advise'),
    path('advice/history/', views.user_advice_history, name='advice_history'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('blogpost/', views.blogpost, name='blogpost'),
    path('profile/', views.profile, name='profile'),
    path('debug/users/', views.debug_users, name='debug_users'),
    path('test/database/', views.test_database, name='test_database'),
    path('predict/', views.predict_plant_disease, name='predict_plant_disease'),
    path('store/', views.store, name='store'),
    path('workings/', views.workings, name='workings'),
    path('my_orders/', views.my_orders, name='my_orders'),
]
