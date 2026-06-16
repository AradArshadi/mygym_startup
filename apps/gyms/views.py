from django.db.models import Avg, Q
from django.utils import timezone
from django.shortcuts import get_object_or_404, render
from apps.analytics.models import GymView, SearchLog
from .models import Gym


def gym_list(request):
    gyms = Gym.objects.filter(status=Gym.Status.APPROVED).prefetch_related('facilities').annotate(avg_rating=Avg('reviews__rating'))
    query = request.GET.get('q', '').strip()
    city = request.GET.get('city', '').strip()
    max_price = request.GET.get('max_price', '').strip()

    if query:
        gyms = gyms.filter(Q(name__icontains=query) | Q(description__icontains=query) | Q(facilities__name__icontains=query)).distinct()
    if city:
        gyms = gyms.filter(city__icontains=city)
    if max_price:
        gyms = gyms.filter(starting_price__lte=max_price)

    if query or city:
        SearchLog.objects.create(user=request.user if request.user.is_authenticated else None, query=query, city=city)

    view_mode = request.GET.get('view', 'cards')
    if view_mode not in ['cards', 'table', 'map']:
        view_mode = 'cards'
    return render(request, 'gyms/gym_list.html', {
        'gyms': gyms,
        'query': query,
        'city': city,
        'max_price': max_price,
        'view_mode': view_mode,
    })


def gym_detail(request, slug):
    gym = get_object_or_404(Gym.objects.prefetch_related('facilities', 'plans', 'trainers'), slug=slug, status=Gym.Status.APPROVED)
    if not request.session.session_key:
        request.session.create()
    # Count one profile view per gym/session/day. Refreshing the page should not spam analytics.
    already_counted_today = GymView.objects.filter(
        gym=gym,
        session_key=request.session.session_key or '',
        created_at__date=timezone.localdate(),
    ).exists()
    if not already_counted_today:
        GymView.objects.create(
            gym=gym,
            user=request.user if request.user.is_authenticated else None,
            session_key=request.session.session_key or '',
            ip_address=request.META.get('REMOTE_ADDR'),
        )
    return render(request, 'gyms/gym_detail.html', {'gym': gym})
