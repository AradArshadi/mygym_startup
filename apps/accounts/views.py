from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import redirect, render
from .models import User
from apps.emails.services import send_welcome_email
from apps.systemlogs.services import log_event


class RegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'role', 'password1', 'password2')


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            send_welcome_email(user, request=request)
            log_event(level='INFO', category='AUTH', event='user_registered', message=f'{user.username} registered as {user.role}', actor=user, request=request, related_model='User', related_id=user.id)
            login(request, user)
            messages.success(request, 'Welcome to myGym!')
            return redirect('gym_list')
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})
