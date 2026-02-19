from django.urls import path


from . import views

from django.contrib.auth.decorators import login_required
from django.contrib.auth import views as auth_views




urlpatterns = [
    # path('base', views.base_view, name='base'),
    path('', views.IBANK, name='IBANK'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'), 
    path('accounts/', views.accounts, name='accounts'),
    path('send money/', views.send_money, name='send money'),
    path('transactions/', views.transactions, name='transactions'),
    path('beneficiaries/', views.beneficiaries, name='beneficiaries'),
    path('profile and settings/', views.profile_and_settings, name='profile and settings'),
    path('logout/', views.custom_logout, name='logout'),



]
 

