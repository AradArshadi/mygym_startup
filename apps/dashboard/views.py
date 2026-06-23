from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Prefetch, Q
from django.shortcuts import render
from django.utils import timezone
from apps.gyms.models import Gym
from apps.bookings.models import Booking, GymCheckIn, GymSubscription, Session
from apps.reviews.models import Favorite, Review


def _refresh_due_membership_qrs_for_user(user):
    refreshed = 0
    for subscription in GymSubscription.objects.filter(customer=user, status=GymSubscription.Status.ACTIVE):
        subscription.mark_expired_if_needed()
        if subscription.status == GymSubscription.Status.ACTIVE and subscription.needs_qr_refresh:
            subscription.refresh_qr_if_needed()
            refreshed += 1
    return refreshed


@login_required
def owner_dashboard(request):
    recent_booking_qs = Booking.objects.select_related('customer', 'trainer', 'plan').order_by('-created_at')
    gyms = Gym.objects.filter(owner=request.user).prefetch_related(
        Prefetch('bookings', queryset=recent_booking_qs, to_attr='recent_bookings')
    ).annotate(
        total_views=Count('views', distinct=True),
        total_bookings=Count('bookings', distinct=True),
        pending_bookings=Count('bookings', filter=Q(bookings__status=Booking.Status.PENDING), distinct=True),
        avg_rating=Avg('reviews__rating'),
        total_favorites=Count('favorited_by', distinct=True),
    )
    total_pending = Booking.objects.filter(gym__owner=request.user, status=Booking.Status.PENDING).count()
    total_confirmed = Booking.objects.filter(gym__owner=request.user, status=Booking.Status.CONFIRMED).count()
    today = timezone.localdate()
    todays_sessions = Session.objects.filter(gym__owner=request.user, start_time__date=today).select_related('customer', 'gym').order_by('start_time')[:10]
    todays_checkins = GymCheckIn.objects.filter(gym__owner=request.user, checked_in_at__date=today).select_related('customer', 'gym').order_by('-checked_in_at')[:10]
    active_memberships = GymSubscription.objects.filter(gym__owner=request.user, status=GymSubscription.Status.ACTIVE, end_date__gte=today).count()
    return render(request, 'dashboard/owner_dashboard.html', {
        'gyms': gyms,
        'total_pending': total_pending,
        'total_confirmed': total_confirmed,
        'todays_sessions': todays_sessions,
        'todays_checkins': todays_checkins,
        'active_memberships': active_memberships,
    })


@login_required
def customer_dashboard(request):
    _refresh_due_membership_qrs_for_user(request.user)
    bookings = Booking.objects.filter(customer=request.user).select_related('gym', 'trainer', 'plan')[:10]
    favorites = Favorite.objects.filter(user=request.user).select_related('gym')[:10]
    reviews = Review.objects.filter(user=request.user).select_related('gym')[:10]
    active_subscriptions = GymSubscription.objects.filter(customer=request.user, status=GymSubscription.Status.ACTIVE, end_date__gte=timezone.localdate()).select_related('gym', 'plan')[:3]
    upcoming_sessions = Session.objects.filter(customer=request.user, status=Session.Status.UPCOMING, start_time__gte=timezone.now()).select_related('gym')[:3]
    stats = {
        'bookings': Booking.objects.filter(customer=request.user).count(),
        'favorites': Favorite.objects.filter(user=request.user).count(),
        'reviews': Review.objects.filter(user=request.user).count(),
        'pending_bookings': Booking.objects.filter(customer=request.user, status=Booking.Status.PENDING).count(),
        'upcoming_sessions': Session.objects.filter(customer=request.user, status=Session.Status.UPCOMING, start_time__gte=timezone.now()).count(),
        'active_memberships': GymSubscription.objects.filter(customer=request.user, status=GymSubscription.Status.ACTIVE, end_date__gte=timezone.localdate()).count(),
    }
    return render(request, 'dashboard/customer_dashboard.html', {
        'bookings': bookings,
        'favorites': favorites,
        'reviews': reviews,
        'active_subscriptions': active_subscriptions,
        'upcoming_sessions': upcoming_sessions,
        'stats': stats,
    })
