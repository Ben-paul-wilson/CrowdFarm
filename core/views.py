from django.shortcuts import render, redirect
from django.urls import reverse
from django.urls.exceptions import NoReverseMatch
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib import messages

def home(request):
    return render(request, 'core/home.html')

def login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        user = authenticate(request, email=email, password=password)
        
        if user is not None:
            auth_login(request, user)
            
            # Redirect based on role
            if user.role == 'ADMIN':
                return redirect('admin_dashboard')
            elif user.role == 'FARMER':
                try:
                    return redirect(reverse('farmer_dashboard'))
                except NoReverseMatch:
                    return redirect('home')
            elif user.role == 'AGENT':
                try:
                    return redirect(reverse('agent_dashboard'))
                except NoReverseMatch:
                    return redirect('home')
            elif user.role == 'INVESTOR':
                try:
                    return redirect(reverse('investor_dashboard'))
                except NoReverseMatch:
                    return redirect('home')
            else:
                return redirect('home')
        else:
            messages.error(request, 'Invalid email or password.')
            return redirect('login')

    return render(request, 'core/login.html')

def register(request):
    return render(request, 'core/register.html')

def farmer_dashboard(request):
    return render(request, 'core/user_pages/farmer/dashboard.html')

def agent_dashboard(request):
    return render(request, 'core/user_pages/agent/dashboard.html')

def investor_dashboard(request):
    return render(request, 'core/user_pages/investor/dashboard.html')

def logout_view(request):
    auth_logout(request)
    return redirect('login')

def admin_dashboard(request):
    return render(request, 'core/user_pages/admin/dashboard.html')