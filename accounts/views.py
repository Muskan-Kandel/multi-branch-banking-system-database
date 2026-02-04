from django.shortcuts import redirect, render
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, authenticate, logout


from django.contrib.auth.decorators import login_required





def base_view(request):
    return render(request, 'base.html')

def IBANK(request):
    return render(request, 'IBANK.html')

def register_view(request):
    if request.method == 'POST':
        form=UserCreationForm(request.POST)
        if form.is_valid():
            user=form.save()
            login(request, user)
            return redirect('dashboard')
        else:
            print(form.errors)
    else:
        form=UserCreationForm()
    return render(request, 'register.html', {'form':form})   

def login_view(request):
    if request.method == 'POST':
        form=AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user=form.get_user()
            login(request, user)
            return redirect('dashboard')
        else :
            print(form.errors)
    else:
        form=AuthenticationForm()
    return render(request, 'login.html', {'form':form})   

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def dashboard(request):
    return render(request, 'dashboard.html')

@login_required
def accounts(request):
    return render(request, 'accounts.html')

@login_required
def send_money(request):
    return render(request, 'send money.html')

@login_required
def transactions(request):
    return render(request, 'transactions.html')

@login_required
def beneficiaries(request):
    return render(request, 'beneficiaries.html')

@login_required
def profile_and_settings(request):
    return render(request, 'profile and settings.html')