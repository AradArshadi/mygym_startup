from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from PIL import Image
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

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if not image:
            return image

        max_mb = getattr(settings, 'MAX_GYM_IMAGE_UPLOAD_MB', 5)
        max_bytes = max_mb * 1024 * 1024
        if image.size and image.size > max_bytes:
            raise ValidationError(f'Image is too large. Maximum allowed size is {max_mb} MB.')

        name = image.name or ''
        ext = name.rsplit('.', 1)[-1].lower() if '.' in name else ''
        allowed_exts = set(getattr(settings, 'ALLOWED_GYM_IMAGE_EXTENSIONS', ['jpg', 'jpeg', 'png', 'webp']))
        if ext not in allowed_exts:
            raise ValidationError('Unsupported image type. Please upload JPG, PNG, or WEBP.')

        try:
            image.seek(0)
            with Image.open(image) as img:
                img.verify()
            image.seek(0)
        except Exception:
            raise ValidationError('Uploaded file is not a valid image.')

        return image


class TrainerProfileForm(forms.ModelForm):
    class Meta:
        model = TrainerProfile
        fields = ['user', 'bio', 'specialties', 'hourly_rate', 'is_available']
        widgets = {'bio': forms.Textarea(attrs={'rows': 4})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['user'].queryset = User.objects.filter(role=User.Role.TRAINER).order_by('username')
        self.fields['user'].help_text = 'Create/register a trainer account first, then attach it to this gym.'
