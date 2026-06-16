from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.conf import settings
from .models import User


class RegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'role', 'password1', 'password2')


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            send_mail(
                subject='Welcome to myGym',
                message=f'Hi {user.username}, welcome to myGym. Your account type is {user.get_role_display()}.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email] if user.email else [],
                fail_silently=True,
            )
            login(request, user)
            messages.success(request, 'Welcome to myGym!')
            return redirect('gym_list')
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})
