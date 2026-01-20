from django.urls import path

from . import views

# urlpatterns = [
#     path('', views.home, name='home'),
# ]
urlpatterns = [
    path('', views.IBANK, name='IBANK'),
    path('accounts/', views.accounts, name='accounts'),
    path('send money/', views.send_money, name='send money'),
    path('transactions/', views.transactions, name='transactions'),
    path('beneficiaries/', views.beneficiaries, name='beneficiaries'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile and settings/', views.profile_and_settings, name='profile and settings'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register, name='register'),
]