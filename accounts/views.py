from django.shortcuts import redirect, render
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, authenticate, logout
def home(request):
    return render(request, 'accounts/base.html')


def register_view(request):
    if request.method == 'POST':
        form=UserCreationForm(request.POST)
        if form.is_valid():
            user=form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form=UserCreationForm()
    return render(request, 'accounts/register.html', {'form':form})   

def login_view(request):
    if request.method == 'POST':
        form=AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user=form.get_user()
            login(request, user)
            return redirect('dashboard')
    else:
        form=AuthenticationForm()
    return render(request, 'accounts/login.html', {'form':form})   

def logout_view(request):
    logout(request)
    return redirect('login')

def dashboard(request):
    return render(request, 'accounts/dashboard.html')

