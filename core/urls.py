from django.urls import path
from django.views.generic import TemplateView
urlpatterns = [
    path('', TemplateView.as_view(template_name='dashboard.html')),
    path('accounts/', TemplateView.as_view(template_name='accounts.html')),
    path('send money/', TemplateView.as_view(template_name='send money.html')),
    path('transactions/', TemplateView.as_view(template_name='transactions.html')),
    path('beneficiaries/', TemplateView.as_view(template_name='beneficiaries.html')),
    path('profile and settings/', TemplateView.as_view(template_name='profile and settings.html')),
    path('login/', TemplateView.as_view(template_name='login.html')),
    path('register/', TemplateView.as_view(template_name='register.html')),
]