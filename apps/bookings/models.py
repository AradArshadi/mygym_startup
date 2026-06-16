from django.conf import settings
from django.db import models


class Booking(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        CONFIRMED = 'CONFIRMED', 'Confirmed'
        CANCELLED = 'CANCELLED', 'Cancelled'
        REJECTED = 'REJECTED', 'Rejected'

    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookings')
    gym = models.ForeignKey('gyms.Gym', on_delete=models.CASCADE, related_name='bookings')
    trainer = models.ForeignKey('gyms.TrainerProfile', on_delete=models.SET_NULL, null=True, blank=True, related_name='bookings')
    plan = models.ForeignKey('gyms.MembershipPlan', on_delete=models.SET_NULL, null=True, blank=True, related_name='bookings')
    booking_datetime = models.DateTimeField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    customer_note = models.TextField(blank=True)
    payment_status = models.CharField(max_length=30, default='NOT_REQUIRED')
    payment_provider = models.CharField(max_length=40, blank=True)
    payment_reference = models.CharField(max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(fields=['customer', 'gym', 'booking_datetime'], name='unique_customer_gym_booking_time')
        ]

    def __str__(self):
        return f'{self.customer} -> {self.gym} at {self.booking_datetime}'
