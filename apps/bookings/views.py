from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.utils.dateparse import parse_datetime
from apps.gyms.models import Gym
from .models import Booking
from apps.emails.services import send_booking_created_to_owner, send_booking_status_to_customer
from apps.systemlogs.services import log_event


@login_required
def create_booking(request, gym_id):
    gym = get_object_or_404(Gym, id=gym_id, status=Gym.Status.APPROVED)
    if request.method == 'POST':
        booking_datetime = parse_datetime(request.POST.get('booking_datetime', ''))
        note = request.POST.get('customer_note', '')
        if not booking_datetime:
            messages.error(request, 'Please choose a valid date and time.')
            return redirect('gym_detail', slug=gym.slug)

        booking, created = Booking.objects.get_or_create(
            customer=request.user,
            gym=gym,
            booking_datetime=booking_datetime,
            defaults={'customer_note': note},
        )
        if not created:
            messages.warning(request, 'You already have a booking request for this gym at this time.')
            return redirect('gym_detail', slug=gym.slug)

        send_booking_created_to_owner(booking, actor=request.user, request=request)
        log_event(level='INFO', category='BOOKING', event='booking_created', message=f'Booking request for {gym.name}', actor=request.user, request=request, related_model='Booking', related_id=booking.id)

        try:
            from apps.notifications.models import Notification
            Notification.objects.create(
                recipient=gym.owner,
                sender=request.user,
                kind=Notification.Kind.BOOKING,
                title=f'New booking request for {gym.name}',
                message=f'{request.user.username} requested a visit at {booking.booking_datetime}.',
                url='/dashboard/owner/',
            )
            Notification.objects.create(
                recipient=request.user,
                sender=gym.owner,
                kind=Notification.Kind.BOOKING,
                title='Booking request sent',
                message=f'Your booking request for {gym.name} is now pending.',
                url='/dashboard/customer/',
            )
        except Exception:
            pass

        messages.success(request, 'Booking request sent!')
    return redirect('gym_detail', slug=gym.slug)


@login_required
def update_booking_status(request, booking_id, status):
    """Allow a gym owner to accept or reject booking requests for their own gyms."""
    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('owner_dashboard')

    booking = get_object_or_404(
        Booking.objects.select_related('gym', 'customer'),
        id=booking_id,
        gym__owner=request.user,
    )

    allowed_statuses = {
        'confirm': Booking.Status.CONFIRMED,
        'reject': Booking.Status.REJECTED,
        'cancel': Booking.Status.CANCELLED,
    }

    new_status = allowed_statuses.get(status)
    if not new_status:
        messages.error(request, 'Invalid booking action.')
        return redirect('owner_dashboard')

    old_status = booking.status
    booking.status = new_status
    booking.save(update_fields=['status'])

    action_text = {
        Booking.Status.CONFIRMED: 'confirmed',
        Booking.Status.REJECTED: 'rejected',
        Booking.Status.CANCELLED: 'cancelled',
    }[new_status]

    try:
        from apps.notifications.models import Notification
        Notification.objects.create(
            recipient=booking.customer,
            sender=request.user,
            kind=Notification.Kind.BOOKING,
            title=f'Booking {action_text}',
            message=f'Your booking request for {booking.gym.name} was {action_text}.',
            url='/dashboard/customer/',
        )
    except Exception:
        pass

    send_booking_status_to_customer(booking, action_text, actor=request.user, request=request)
    log_event(level='INFO', category='BOOKING', event='booking_status_updated', message=f'Booking {booking.id} moved from {old_status} to {new_status}', actor=request.user, request=request, related_model='Booking', related_id=booking.id, metadata={'old_status': old_status, 'new_status': new_status})

    messages.success(request, f'Booking moved from {old_status} to {new_status}.')
    return redirect('owner_dashboard')


@login_required
def cancel_own_booking(request, booking_id):
    """Allow customers to cancel their own pending/confirmed bookings."""
    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('customer_dashboard')

    booking = get_object_or_404(
        Booking.objects.select_related('gym'),
        id=booking_id,
        customer=request.user,
    )

    if booking.status in [Booking.Status.CANCELLED, Booking.Status.REJECTED]:
        messages.warning(request, 'This booking is already closed.')
        return redirect('customer_dashboard')

    booking.status = Booking.Status.CANCELLED
    booking.save(update_fields=['status'])

    try:
        from apps.notifications.models import Notification
        Notification.objects.create(
            recipient=booking.gym.owner,
            sender=request.user,
            kind=Notification.Kind.BOOKING,
            title='Booking cancelled by customer',
            message=f'{request.user.username} cancelled a booking for {booking.gym.name}.',
            url='/dashboard/owner/',
        )
    except Exception:
        pass

    log_event(level='INFO', category='BOOKING', event='booking_cancelled_by_customer', message=f'Customer cancelled booking {booking.id}', actor=request.user, request=request, related_model='Booking', related_id=booking.id)
    messages.success(request, 'Booking cancelled.')
    return redirect('customer_dashboard')
