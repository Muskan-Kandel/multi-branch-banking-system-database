from django.shortcuts import render

# def home(request):
#     return render(request, 'accounts/home.html')
def dashboard(request):
    return render(request, 'dashboard.html')

def accounts(request):
    return render(request, 'accounts.html')

def send_money(request):
    return render(request, 'send money.html')

def transactions(request):
    return render(request, 'transactions.html')

def beneficiaries(request):
    return render(request, 'beneficiaries.html')

def profile_and_settings(request):
    return render(request, 'profile and settings.html')

def login_view(request):
    return render(request, 'login.html')

def register(request):
    return render(request, 'register.html')