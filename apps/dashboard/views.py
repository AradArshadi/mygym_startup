from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Prefetch, Q
from django.shortcuts import render
from apps.gyms.models import Gym
from apps.bookings.models import Booking
from apps.reviews.models import Favorite, Review


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
    return render(request, 'dashboard/owner_dashboard.html', {
        'gyms': gyms,
        'total_pending': total_pending,
        'total_confirmed': total_confirmed,
    })


@login_required
def customer_dashboard(request):
    bookings = Booking.objects.filter(customer=request.user).select_related('gym', 'trainer', 'plan')[:10]
    favorites = Favorite.objects.filter(user=request.user).select_related('gym')[:10]
    reviews = Review.objects.filter(user=request.user).select_related('gym')[:10]
    stats = {
        'bookings': Booking.objects.filter(customer=request.user).count(),
        'favorites': Favorite.objects.filter(user=request.user).count(),
        'reviews': Review.objects.filter(user=request.user).count(),
        'pending_bookings': Booking.objects.filter(customer=request.user, status=Booking.Status.PENDING).count(),
    }
    return render(request, 'dashboard/customer_dashboard.html', {
        'bookings': bookings,
        'favorites': favorites,
        'reviews': reviews,
        'stats': stats,
    })
