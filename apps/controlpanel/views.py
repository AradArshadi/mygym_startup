from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Avg, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.analytics.models import GymView
from apps.bookings.models import Booking
from apps.gyms.models import Gym
from apps.notifications.models import Notification
from apps.reviews.models import Review
from apps.emails.services import send_gym_status_to_owner, send_booking_status_to_customer
from apps.systemlogs.services import log_event

User = get_user_model()


def admin_required(view_func):
    @login_required
    def wrapper(request, *args, **kwargs):
        if not (request.user.is_superuser or request.user.is_staff or request.user.role == User.Role.ADMIN):
            raise PermissionDenied('Only platform admins can access the Control Deck.')
        return view_func(request, *args, **kwargs)
    return wrapper


def can_promote_admin(user):
    # Only the real Django superuser can create another platform admin.
    return user.is_authenticated and user.is_superuser


def _base_metrics():
    today = timezone.now().date()
    return {
        'total_users': User.objects.count(),
        'total_customers': User.objects.filter(role=User.Role.CUSTOMER).count(),
        'total_owners': User.objects.filter(role=User.Role.OWNER).count(),
        'total_trainers': User.objects.filter(role=User.Role.TRAINER).count(),
        'total_gyms': Gym.objects.count(),
        'pending_gyms': Gym.objects.filter(status=Gym.Status.PENDING).count(),
        'approved_gyms': Gym.objects.filter(status=Gym.Status.APPROVED).count(),
        'total_bookings': Booking.objects.count(),
        'pending_bookings': Booking.objects.filter(status=Booking.Status.PENDING).count(),
        'confirmed_bookings': Booking.objects.filter(status=Booking.Status.CONFIRMED).count(),
        'total_reviews': Review.objects.count(),
        'hidden_reviews': Review.objects.filter(is_visible=False).count(),
        'total_views': GymView.objects.count(),
        'today_signups': User.objects.filter(date_joined__date=today).count(),
        'today_bookings': Booking.objects.filter(created_at__date=today).count(),
        'today_views': GymView.objects.filter(created_at__date=today).count(),
    }


@admin_required
def control_overview(request):
    metrics = _base_metrics()
    recent_users = User.objects.order_by('-date_joined')[:8]
    recent_bookings = Booking.objects.select_related('customer', 'gym', 'trainer__user').order_by('-created_at')[:8]
    pending_gyms = Gym.objects.select_related('owner').filter(status=Gym.Status.PENDING).order_by('-created_at')[:8]
    top_gyms = Gym.objects.annotate(
        view_count=Count('views', distinct=True),
        booking_count=Count('bookings', distinct=True),
        avg_rating=Avg('reviews__rating', filter=Q(reviews__is_visible=True)),
    ).order_by('-view_count')[:8]
    return render(request, 'controlpanel/overview.html', {
        'metrics': metrics,
        'recent_users': recent_users,
        'recent_bookings': recent_bookings,
        'pending_gyms': pending_gyms,
        'top_gyms': top_gyms,
    })


@admin_required
def control_users(request):
    role = request.GET.get('role', '')
    q = request.GET.get('q', '')
    users = User.objects.order_by('-date_joined')
    if role:
        users = users.filter(role=role)
    if q:
        users = users.filter(Q(username__icontains=q) | Q(email__icontains=q) | Q(first_name__icontains=q) | Q(last_name__icontains=q))
    return render(request, 'controlpanel/users.html', {'users': users[:200], 'roles': User.Role.choices, 'active_role': role, 'q': q})


@require_POST
@admin_required
def toggle_user_active(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if user == request.user:
        messages.warning(request, 'You cannot deactivate your own admin account from the Control Deck.')
        return redirect('control_users')
    user.is_active = not user.is_active
    user.save(update_fields=['is_active'])
    log_event(level='WARNING', category='ADMIN', event='user_active_toggled', message=f'{user.username} active={user.is_active}', actor=request.user, request=request, related_model='User', related_id=user.id)
    messages.success(request, f'{user.username} is now {"active" if user.is_active else "inactive"}.')
    return redirect('control_users')


@require_POST
@admin_required
def change_user_role(request, user_id):
    user = get_object_or_404(User, id=user_id)
    new_role = request.POST.get('role')
    valid_roles = {choice[0] for choice in User.Role.choices}
    if new_role not in valid_roles:
        messages.error(request, 'Invalid role selected.')
        return redirect('control_users')
    if new_role == User.Role.ADMIN and not can_promote_admin(request.user):
        messages.error(request, 'Only a Django superuser can promote another user to ADMIN.')
        return redirect('control_users')
    if user == request.user and new_role != User.Role.ADMIN and not request.user.is_superuser:
        messages.error(request, 'You cannot remove your own admin role from here.')
        return redirect('control_users')

    user.role = new_role
    if new_role == User.Role.ADMIN:
        user.is_staff = True
    elif not user.is_superuser:
        user.is_staff = False
    user.save(update_fields=['role', 'is_staff'])
    log_event(level='WARNING', category='ADMIN', event='user_role_changed', message=f'{user.username} role changed to {new_role}', actor=request.user, request=request, related_model='User', related_id=user.id, metadata={'new_role': new_role})
    messages.success(request, f'{user.username} role changed to {new_role}.')
    return redirect('control_users')


@admin_required
def control_gyms(request):
    status = request.GET.get('status', '')
    q = request.GET.get('q', '')
    gyms = Gym.objects.select_related('owner').annotate(
        view_count=Count('views', distinct=True),
        booking_count=Count('bookings', distinct=True),
        avg_rating=Avg('reviews__rating', filter=Q(reviews__is_visible=True)),
    ).order_by('-created_at')
    if status:
        gyms = gyms.filter(status=status)
    if q:
        gyms = gyms.filter(Q(name__icontains=q) | Q(city__icontains=q) | Q(owner__username__icontains=q))
    return render(request, 'controlpanel/gyms.html', {'gyms': gyms[:200], 'statuses': Gym.Status.choices, 'active_status': status, 'q': q})


@require_POST
@admin_required
def approve_gym(request, gym_id):
    gym = get_object_or_404(Gym, id=gym_id)
    gym.status = Gym.Status.APPROVED
    gym.save(update_fields=['status', 'updated_at'])
    Notification.objects.create(recipient=gym.owner, sender=request.user, kind=Notification.Kind.GYM, title='Gym approved', message=f'{gym.name} has been approved and is now public.', url=gym.get_absolute_url())
    send_gym_status_to_owner(gym, 'approved', actor=request.user, request=request)
    log_event(level='INFO', category='GYM', event='gym_approved', message=f'{gym.name} approved', actor=request.user, request=request, related_model='Gym', related_id=gym.id)
    messages.success(request, f'{gym.name} approved.')
    return redirect(request.POST.get('next') or 'control_gyms')


@require_POST
@admin_required
def reject_gym(request, gym_id):
    gym = get_object_or_404(Gym, id=gym_id)
    gym.status = Gym.Status.REJECTED
    gym.save(update_fields=['status', 'updated_at'])
    Notification.objects.create(recipient=gym.owner, sender=request.user, kind=Notification.Kind.GYM, title='Gym rejected', message=f'{gym.name} needs changes before approval.', url='')
    send_gym_status_to_owner(gym, 'rejected', actor=request.user, request=request)
    log_event(level='WARNING', category='GYM', event='gym_rejected', message=f'{gym.name} rejected', actor=request.user, request=request, related_model='Gym', related_id=gym.id)
    messages.warning(request, f'{gym.name} rejected.')
    return redirect(request.POST.get('next') or 'control_gyms')


@admin_required
def control_bookings(request):
    status = request.GET.get('status', '')
    q = request.GET.get('q', '')
    bookings = Booking.objects.select_related('customer', 'gym', 'gym__owner', 'trainer__user').order_by('-created_at')
    if status:
        bookings = bookings.filter(status=status)
    if q:
        bookings = bookings.filter(Q(customer__username__icontains=q) | Q(customer__email__icontains=q) | Q(gym__name__icontains=q) | Q(gym__owner__username__icontains=q))
    return render(request, 'controlpanel/bookings.html', {'bookings': bookings[:250], 'statuses': Booking.Status.choices, 'active_status': status, 'q': q})


@require_POST
@admin_required
def update_booking_status(request, booking_id, action):
    booking = get_object_or_404(Booking.objects.select_related('customer', 'gym'), id=booking_id)
    mapping = {
        'confirm': Booking.Status.CONFIRMED,
        'reject': Booking.Status.REJECTED,
        'cancel': Booking.Status.CANCELLED,
        'pending': Booking.Status.PENDING,
    }
    if action not in mapping:
        messages.error(request, 'Invalid booking action.')
        return redirect('control_bookings')
    booking.status = mapping[action]
    booking.save(update_fields=['status'])
    Notification.objects.create(recipient=booking.customer, sender=request.user, kind=Notification.Kind.BOOKING, title=f'Booking {booking.status.lower()}', message=f'Your booking at {booking.gym.name} is now {booking.status.lower()}.', url='/dashboard/customer/')
    send_booking_status_to_customer(booking, booking.status.lower(), actor=request.user, request=request)
    log_event(level='INFO', category='BOOKING', event='booking_status_updated_by_admin', message=f'Admin changed booking {booking.id} to {booking.status}', actor=request.user, request=request, related_model='Booking', related_id=booking.id, metadata={'status': booking.status})
    messages.success(request, f'Booking updated to {booking.status}.')
    return redirect(request.POST.get('next') or 'control_bookings')


@admin_required
def control_reviews(request):
    visible = request.GET.get('visible', '')
    q = request.GET.get('q', '')
    reviews = Review.objects.select_related('user', 'gym').order_by('-created_at')
    if visible == 'yes':
        reviews = reviews.filter(is_visible=True)
    elif visible == 'no':
        reviews = reviews.filter(is_visible=False)
    if q:
        reviews = reviews.filter(Q(user__username__icontains=q) | Q(gym__name__icontains=q) | Q(comment__icontains=q))
    return render(request, 'controlpanel/reviews.html', {'reviews': reviews[:250], 'visible': visible, 'q': q})


@require_POST
@admin_required
def toggle_review_visibility(request, review_id):
    review = get_object_or_404(Review.objects.select_related('user', 'gym'), id=review_id)
    review.is_visible = not review.is_visible
    review.save(update_fields=['is_visible'])
    log_event(level='WARNING', category='REVIEW', event='review_visibility_toggled', message=f'Review {review.id} visibility={review.is_visible}', actor=request.user, request=request, related_model='Review', related_id=review.id)
    messages.success(request, f'Review for {review.gym.name} is now {"visible" if review.is_visible else "hidden"}.')
    return redirect(request.POST.get('next') or 'control_reviews')

@admin_required
def control_logs(request):
    from apps.systemlogs.models import SystemLog
    level = request.GET.get('level', '')
    category = request.GET.get('category', '')
    q = request.GET.get('q', '')
    logs = SystemLog.objects.select_related('actor').order_by('-created_at')
    if level:
        logs = logs.filter(level=level)
    if category:
        logs = logs.filter(category=category)
    if q:
        logs = logs.filter(Q(event__icontains=q) | Q(message__icontains=q) | Q(actor__username__icontains=q) | Q(actor__email__icontains=q) | Q(related_model__icontains=q) | Q(related_id__icontains=q))
    return render(request, 'controlpanel/logs.html', {
        'logs': logs[:300],
        'levels': SystemLog.Level.choices,
        'categories': SystemLog.Category.choices,
        'active_level': level,
        'active_category': category,
        'q': q,
    })
