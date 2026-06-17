from django import forms
from apps.accounts.models import User
from .models import Gym, GymImage, MembershipPlan, TrainerProfile


class GymForm(forms.ModelForm):
    class Meta:
        model = Gym
        fields = [
            'name', 'slug', 'description', 'city', 'address', 'email', 'phone',
            'website', 'latitude', 'longitude', 'starting_price', 'facilities'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
            'facilities': forms.CheckboxSelectMultiple,
        }
        help_texts = {
            'slug': 'URL-friendly name, for example: iron-temple-bamberg',
            'latitude': 'Optional. Needed for map view.',
            'longitude': 'Optional. Needed for map view.',
        }


class MembershipPlanForm(forms.ModelForm):
    class Meta:
        model = MembershipPlan
        fields = ['title', 'description', 'price', 'duration_days', 'is_trial']
        widgets = {'description': forms.Textarea(attrs={'rows': 3})}


class GymImageForm(forms.ModelForm):
    class Meta:
        model = GymImage
        fields = ['image', 'alt_text', 'is_cover']


class TrainerProfileForm(forms.ModelForm):
    class Meta:
        model = TrainerProfile
        fields = ['user', 'bio', 'specialties', 'hourly_rate', 'is_available']
        widgets = {'bio': forms.Textarea(attrs={'rows': 4})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['user'].queryset = User.objects.filter(role=User.Role.TRAINER).order_by('username')
        self.fields['user'].help_text = 'Create/register a trainer account first, then attach it to this gym.'
