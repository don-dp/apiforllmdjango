from django.views import View
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .forms import EmailUpdateForm, EmailRequiredUserCreationForm
from django.contrib.auth.views import LoginView, PasswordResetView
from .helpers import check_turnstile
from main.models import UserBalance
from decimal import Decimal

def handler400(request, exception, template_name="base/error.html"):
    return render(request, template_name, status=400)

def handler403(request, exception, template_name="base/error.html"):
    return render(request, template_name, status=403)

def handler404(request, exception, template_name="base/error.html"):
    return render(request, template_name, status=404)

def handler500(request, template_name="base/error.html"):
    return render(request, template_name, status=500)

class AboutPage(View):
    def get(self, request):
        return render(request, "base/aboutpage.html", {})

class SignupView(View):
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.info(request, 'You are already logged in, so you can\'t signup. If you want to create a new account logout first.')
            return redirect('homepage')
        
        form = EmailRequiredUserCreationForm()
        return render(request, 'registration/signup.html', {'form': form})

    def post(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.info(request, 'You are already logged in, so you can\'t signup. If you want to create a new account, logout first.')
            return redirect('homepage')
        
        if not check_turnstile(request):
            return redirect('signup')
        
        form = EmailRequiredUserCreationForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            if 'dinesh' in username.lower() or 'admin' in username.lower():
                messages.error(request, "Username cannot contain 'dinesh' or 'admin'")
                return redirect('signup')
            
            if User.objects.filter(email=email).exists():
                messages.error(request, 'This email is already in use. Please use a different email. If someone else added your email id to their account, please email dinesh@apiforllm.com')
                return render(request, 'registration/signup.html', {'form': form})

            user = form.save()
            UserBalance.objects.create(user=user, balance=Decimal('0.05'))
            login(request, user)
            messages.info(request, 'Successfully registered. You can update your email in the profile page.')
            return redirect('homepage')
        return render(request, 'registration/signup.html', {'form': form})

class ProfileView(LoginRequiredMixin, View):
    login_url = reverse_lazy('login')

    def get(self, request, *args, **kwargs):
        form = EmailUpdateForm(initial={'email': request.user.email})
        user_balance = UserBalance.objects.get(user=request.user)
        return render(request, 'base/profile.html', {'user': request.user, 'form': form, 'user_balance': user_balance})

    def post(self, request, *args, **kwargs):
        form = EmailUpdateForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            if email and User.objects.filter(email=email).exclude(username=request.user.username).exists():
                messages.error(request, 'This email is already in use. Please use a different email. If someone else added your email id to their account, please email dinesh@apiforllm.com')
            else:
                request.user.email = email
                request.user.save()
                messages.success(request, 'Email updated successfully')
        else:
            messages.error(request, 'Invalid email')
        return redirect('profile')

class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    
    def post(self, request, *args, **kwargs):
        if check_turnstile(request):
            return super().post(request, *args, **kwargs)
        else:
            return redirect('login')

class CustomPasswordResetView(PasswordResetView):
    def post(self, request, *args, **kwargs):
        if not check_turnstile(request):
            return redirect('password_reset')
        return super().post(request, *args, **kwargs)