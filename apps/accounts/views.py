from django import forms
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render

from .models import User
from apps.emails.services import send_welcome_email
from apps.systemlogs.services import log_event


class RegisterForm(UserCreationForm):
    """Public signup form.

    Security rule: nobody can create an ADMIN account from the public signup page.
    Admin users must be promoted later by an existing platform admin/superuser.
    """

    role = forms.ChoiceField(
        choices=(
            (User.Role.CUSTOMER, 'Customer'),
            (User.Role.OWNER, 'Gym Owner'),
        ),
        help_text='Choose Customer to explore gyms or Gym Owner to manage a listing.',
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'role', 'password1', 'password2')

    def clean_role(self):
        role = self.cleaned_data.get('role')
        if role not in {User.Role.CUSTOMER, User.Role.OWNER}:
            raise forms.ValidationError('This role cannot be selected during public signup.')
        return role

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = self.cleaned_data['role']
        user.is_staff = False
        user.is_superuser = False
        if commit:
            user.save()
        return user


class MyGymLoginView(LoginView):
    template_name = 'accounts/login.html'

    def form_valid(self, form):
        response = super().form_valid(form)
        try:
            from apps.bookings.views import _refresh_due_membership_qrs_for_user
            refreshed = _refresh_due_membership_qrs_for_user(self.request.user)
            if refreshed:
                messages.info(self.request, f'{refreshed} Access Pass QR code(s) refreshed.')
        except Exception:
            pass
        return response


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            send_welcome_email(user, request=request)
            log_event(level='INFO', category='AUTH', event='user_registered', message=f'{user.username} registered as {user.role}', actor=user, request=request, related_model='User', related_id=user.id)
            login(request, user)
            messages.success(request, 'Welcome to myGym!')
            return redirect(request.GET.get('next') or 'gym_list')
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})
