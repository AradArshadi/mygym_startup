from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from apps.emails.services import (
    send_booking_created_to_owner,
    send_booking_status_to_customer,
    send_membership_access_pass_to_customer,
    send_session_qr_to_customer,
)
from apps.gyms.models import Gym, MembershipPlan
from apps.systemlogs.services import log_event

from .models import Booking, GymCheckIn, GymSubscription, Session
from .qr_utils import build_qr_data_uri


def _is_owner_or_admin(user, gym):
    return gym.owner_id == user.id or user.is_staff or user.is_superuser or getattr(user, 'role', '') == 'ADMIN'


def _absolute_url(request, name, *args, **kwargs):
    path = reverse(name, args=args, kwargs=kwargs)
    try:
        return request.build_absolute_uri(path)
    except Exception:
        site_url = getattr(settings, 'SITE_URL', '').rstrip('/')
        return f'{site_url}{path}' if site_url else path


def _session_checkin_url(request, session):
    return _absolute_url(request, 'session_check_in', session.qr_token)


def _membership_checkin_url(request, subscription):
    return _absolute_url(request, 'membership_check_in', subscription.current_qr_token)


def _attach_session_qr(request, session):
    url = _session_checkin_url(request, session)
    session.qr_url = url
    session.qr_data_uri = build_qr_data_uri(url)
    return session


def _attach_membership_qr(request, subscription):
    url = _membership_checkin_url(request, subscription)
    subscription.qr_url = url
    subscription.qr_data_uri = build_qr_data_uri(url)
    return subscription


def _refresh_due_membership_qrs_for_user(user):
    if not user.is_authenticated:
        return 0
    refreshed = 0
    for subscription in GymSubscription.objects.filter(customer=user, status=GymSubscription.Status.ACTIVE):
        subscription.mark_expired_if_needed()
        if subscription.status == GymSubscription.Status.ACTIVE and subscription.needs_qr_refresh:
            subscription.refresh_qr_if_needed()
            refreshed += 1
    return refreshed


def _create_operational_records_for_confirmed_booking(booking, *, actor=None, request=None):
    """Create one-time Session and optional GymSubscription after owner confirms a booking."""
    session, session_created = Session.objects.get_or_create(
        booking=booking,
        defaults={
            'customer': booking.customer,
            'gym': booking.gym,
            'start_time': booking.booking_datetime,
            'end_time': booking.booking_datetime + timedelta(hours=1),
        },
    )

    subscription = None
    subscription_created = False
    if booking.plan and not booking.plan.is_trial:
        start_date = timezone.localdate(booking.booking_datetime)
        end_date = start_date + timedelta(days=max(booking.plan.duration_days, 1))
        subscription, subscription_created = GymSubscription.objects.get_or_create(
            source_booking=booking,
            defaults={
                'customer': booking.customer,
                'gym': booking.gym,
                'plan': booking.plan,
                'status': GymSubscription.Status.ACTIVE,
                'start_date': start_date,
                'end_date': end_date,
            },
        )
        subscription.refresh_qr_if_needed(force=True)

    if session_created:
        log_event(level='INFO', category='SESSION', event='session_created', message=f'Session created for booking {booking.id}', actor=actor, request=request, related_model='Session', related_id=session.id)
    if subscription_created and subscription:
        log_event(level='INFO', category='SUBSCRIPTION', event='subscription_created', message=f'Access pass created for booking {booking.id}', actor=actor, request=request, related_model='GymSubscription', related_id=subscription.id)

    return session, subscription


@login_required
def create_booking(request, gym_id):
    gym = get_object_or_404(Gym, id=gym_id, status=Gym.Status.APPROVED)
    if request.method == 'POST':
        booking_datetime = parse_datetime(request.POST.get('booking_datetime', ''))
        note = request.POST.get('customer_note', '')
        plan = None
        plan_id = request.POST.get('plan')
        if plan_id:
            plan = get_object_or_404(MembershipPlan, id=plan_id, gym=gym)

        if not booking_datetime:
            messages.error(request, 'Please choose a valid date and time.')
            return redirect('gym_detail', slug=gym.slug)

        booking, created = Booking.objects.get_or_create(
            customer=request.user,
            gym=gym,
            booking_datetime=booking_datetime,
            defaults={'customer_note': note, 'plan': plan},
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
        Booking.objects.select_related('gym', 'customer', 'plan'),
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

    with transaction.atomic():
        old_status = booking.status
        booking.status = new_status
        booking.save(update_fields=['status'])

        session = None
        subscription = None
        if new_status == Booking.Status.CONFIRMED:
            session, subscription = _create_operational_records_for_confirmed_booking(booking, actor=request.user, request=request)
        elif new_status == Booking.Status.CANCELLED:
            if hasattr(booking, 'session') and booking.session.status != Session.Status.CANCELLED:
                booking.session.cancel('Cancelled by gym owner.')
            if hasattr(booking, 'subscription') and booking.subscription.status == GymSubscription.Status.ACTIVE:
                booking.subscription.status = GymSubscription.Status.CANCELLED
                booking.subscription.save(update_fields=['status', 'updated_at'])

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
            url='/bookings/sessions/',
        )
    except Exception:
        pass

    send_booking_status_to_customer(booking, action_text, actor=request.user, request=request)
    if new_status == Booking.Status.CONFIRMED and session:
        _attach_session_qr(request, session)
        send_session_qr_to_customer(session, session.qr_url, session.qr_data_uri, actor=request.user, request=request)
        if subscription:
            _attach_membership_qr(request, subscription)
            send_membership_access_pass_to_customer(subscription, subscription.qr_url, subscription.qr_data_uri, actor=request.user, request=request)

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

    if hasattr(booking, 'session') and booking.session.status != Session.Status.CANCELLED:
        booking.session.cancel('Cancelled by customer.')
    if hasattr(booking, 'subscription') and booking.subscription.status == GymSubscription.Status.ACTIVE:
        booking.subscription.status = GymSubscription.Status.CANCELLED
        booking.subscription.save(update_fields=['status', 'updated_at'])

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


@login_required
def my_sessions(request):
    _refresh_due_membership_qrs_for_user(request.user)
    sessions = Session.objects.filter(customer=request.user).select_related('gym', 'booking', 'booking__plan')
    now = timezone.now()
    upcoming = sessions.filter(status=Session.Status.UPCOMING, start_time__gte=now).order_by('start_time')
    previous = sessions.exclude(status__in=[Session.Status.UPCOMING, Session.Status.CANCELLED]).order_by('-start_time')
    cancelled = sessions.filter(status=Session.Status.CANCELLED).order_by('-start_time')

    # For demo friendliness, future sessions include QR data directly in the list.
    for session in upcoming:
        _attach_session_qr(request, session)

    return render(request, 'bookings/my_sessions.html', {
        'upcoming_sessions': upcoming,
        'previous_sessions': previous,
        'cancelled_sessions': cancelled,
    })


@login_required
def session_detail(request, session_id):
    session = get_object_or_404(Session.objects.select_related('gym', 'booking', 'booking__plan'), id=session_id, customer=request.user)
    _attach_session_qr(request, session)
    return render(request, 'bookings/session_detail.html', {'session': session})


@login_required
def cancel_session(request, session_id):
    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('my_sessions')
    session = get_object_or_404(Session.objects.select_related('booking', 'gym'), id=session_id, customer=request.user)
    if session.status != Session.Status.UPCOMING:
        messages.warning(request, 'Only upcoming sessions can be cancelled.')
        return redirect('my_sessions')

    session.cancel('Cancelled by customer from My Sessions.')
    session.booking.status = Booking.Status.CANCELLED
    session.booking.save(update_fields=['status'])

    try:
        from apps.notifications.models import Notification
        Notification.objects.create(
            recipient=session.gym.owner,
            sender=request.user,
            kind=Notification.Kind.BOOKING,
            title='Session cancelled by customer',
            message=f'{request.user.username} cancelled a session for {session.gym.name}.',
            url='/dashboard/owner/',
        )
    except Exception:
        pass

    log_event(level='INFO', category='SESSION', event='session_cancelled_by_customer', message=f'Session {session.id} cancelled by customer', actor=request.user, request=request, related_model='Session', related_id=session.id)
    messages.success(request, 'Session cancelled.')
    return redirect('my_sessions')


@login_required
def my_memberships(request):
    _refresh_due_membership_qrs_for_user(request.user)
    subscriptions = GymSubscription.objects.filter(customer=request.user).select_related('gym', 'plan')
    active = []
    expired_or_closed = []
    for subscription in subscriptions:
        subscription.mark_expired_if_needed()
        if subscription.status == GymSubscription.Status.ACTIVE:
            _attach_membership_qr(request, subscription)
            active.append(subscription)
        else:
            expired_or_closed.append(subscription)
    return render(request, 'bookings/my_memberships.html', {
        'active_subscriptions': active,
        'closed_subscriptions': expired_or_closed,
    })


@login_required
def refresh_membership_qr(request, subscription_id):
    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('my_memberships')
    subscription = get_object_or_404(GymSubscription, id=subscription_id, customer=request.user)
    if not subscription.is_active:
        messages.warning(request, 'This access pass is not active.')
        return redirect('my_memberships')
    subscription.refresh_qr_if_needed(force=True)
    messages.success(request, 'Access Pass QR refreshed.')
    return redirect('my_memberships')


@login_required
def session_check_in(request, token):
    session = get_object_or_404(Session.objects.select_related('customer', 'gym', 'booking'), qr_token=token)
    valid = session.is_one_time_qr_available
    if not _is_owner_or_admin(request.user, session.gym):
        valid = False
        reason = 'Only this gym owner or platform admin can validate this QR code.'
    elif not session.is_one_time_qr_available:
        reason = 'This one-time session QR is cancelled, already used, or no longer available.'
    else:
        reason = ''

    if request.method == 'POST':
        if not valid:
            messages.error(request, reason or 'Invalid session QR code.')
            return redirect('owner_dashboard')
        checkin = session.mark_checked_in()
        log_event(level='INFO', category='CHECKIN', event='session_checkin_confirmed', message=f'Session {session.id} checked in', actor=request.user, request=request, related_model='GymCheckIn', related_id=checkin.id)
        messages.success(request, f'{session.customer.username} checked in successfully for {session.gym.name}.')
        return redirect('owner_dashboard')

    return render(request, 'bookings/check_in_validate.html', {
        'mode': 'SESSION',
        'valid': valid,
        'reason': reason,
        'session': session,
        'subscription': None,
    })


@login_required
def membership_check_in(request, token):
    subscription = get_object_or_404(GymSubscription.objects.select_related('customer', 'gym', 'plan'), current_qr_token=token)
    subscription.mark_expired_if_needed()

    valid = subscription.is_active and subscription.qr_is_fresh
    if not _is_owner_or_admin(request.user, subscription.gym):
        valid = False
        reason = 'Only this gym owner or platform admin can validate this Access Pass.'
    elif not subscription.is_active:
        reason = 'This membership is not active or has expired.'
    elif not subscription.qr_is_fresh:
        reason = 'This Access Pass QR is older than 24 hours. The customer must open their account to refresh it.'
    else:
        reason = ''

    if request.method == 'POST':
        if not valid:
            messages.error(request, reason or 'Invalid Access Pass QR.')
            return redirect('owner_dashboard')
        checkin = GymCheckIn.objects.create(
            customer=subscription.customer,
            gym=subscription.gym,
            subscription=subscription,
            checkin_type=GymCheckIn.CheckInType.MEMBERSHIP,
        )
        log_event(level='INFO', category='CHECKIN', event='membership_checkin_confirmed', message=f'Subscription {subscription.id} checked in', actor=request.user, request=request, related_model='GymCheckIn', related_id=checkin.id)
        messages.success(request, f'{subscription.customer.username} entry confirmed for {subscription.gym.name}.')
        return redirect('owner_dashboard')

    return render(request, 'bookings/check_in_validate.html', {
        'mode': 'MEMBERSHIP',
        'valid': valid,
        'reason': reason,
        'session': None,
        'subscription': subscription,
    })
