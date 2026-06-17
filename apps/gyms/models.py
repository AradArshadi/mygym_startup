from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Facility(models.Model):
    name = models.CharField(max_length=80, unique=True)
    icon = models.CharField(max_length=40, blank=True)

    class Meta:
        verbose_name_plural = 'Facilities'

    def __str__(self):
        return self.name


class Gym(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending approval'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='owned_gyms')
    name = models.CharField(max_length=160)
    slug = models.SlugField(max_length=180, unique=True)
    description = models.TextField()
    city = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=40, blank=True)
    website = models.URLField(blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    facilities = models.ManyToManyField(Facility, blank=True, related_name='gyms')
    starting_price = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)])
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return f'/gyms/{self.slug}/'

    @property
    def cover_image(self):
        cover = self.images.filter(is_cover=True).first()
        if cover:
            return cover
        return self.images.first()

    @property
    def gallery_images(self):
        return self.images.filter(is_cover=False)


class GymImage(models.Model):
    gym = models.ForeignKey(Gym, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='gyms/')
    alt_text = models.CharField(max_length=160, blank=True)
    is_cover = models.BooleanField(default=False)


class MembershipPlan(models.Model):
    gym = models.ForeignKey(Gym, on_delete=models.CASCADE, related_name='plans')
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)])
    duration_days = models.PositiveIntegerField()
    is_trial = models.BooleanField(default=False)

    class Meta:
        ordering = ['price']

    def __str__(self):
        return f'{self.gym.name} - {self.title}'


class TrainerProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='trainer_profile')
    gym = models.ForeignKey(Gym, on_delete=models.CASCADE, related_name='trainers')
    bio = models.TextField()
    specialties = models.CharField(max_length=255, help_text='Comma-separated: Strength, Boxing, Yoga')
    hourly_rate = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)], null=True, blank=True)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.username
