import random
from decimal import Decimal
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.gyms.models import Gym, MembershipPlan
from apps.bookings.models import Booking, GymSubscription, GymCheckIn
from apps.reviews.models import Favorite

try:
    from apps.fitness.models import WorkoutLog
except Exception:
    WorkoutLog = None


# Optional:
# Set this to one owner username if you only want data for that owner.
# Example: OWNER_USERNAME = "owner_demo"
OWNER_USERNAME = None

CUSTOMER_COUNT = 25
DAYS_BACK = 120
SUBSCRIPTIONS_PER_GYM = 24
BOOKINGS_PER_GYM = 45
CHECKINS_PER_GYM = 220
FAVORITES_PER_GYM = 12
WORKOUTS_PER_CUSTOMER = 18

User = get_user_model()
now = timezone.now()
today = timezone.localdate()

random.seed(9306)


def random_past_datetime(days_back=DAYS_BACK):
    days = random.randint(0, days_back - 1)

    # More realistic gym traffic: morning + evening peaks
    hour = random.choices(
        population=[6, 7, 8, 9, 12, 16, 17, 18, 19, 20, 21],
        weights=[3, 5, 7, 5, 2, 4, 8, 12, 12, 9, 4],
        k=1,
    )[0]

    minute = random.choice([0, 10, 15, 20, 30, 40, 45, 50])
    return (now - timedelta(days=days)).replace(
        hour=hour,
        minute=minute,
        second=random.randint(0, 59),
        microsecond=0,
    )


def create_demo_customers():
    customers = []
    for i in range(1, CUSTOMER_COUNT + 1):
        username = f"demo_customer_analytics_{i}"
        email = f"demo.customer.analytics.{i}@example.com"

        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "email": email,
                "role": getattr(User.Role, "CUSTOMER", "CUSTOMER"),
                "is_active": True,
            },
        )

        if created:
            user.set_password("DemoPass123")
            user.save()

        customers.append(user)

    return customers


def get_target_gyms():
    gyms = Gym.objects.filter(owner__isnull=False).select_related("owner")

    if OWNER_USERNAME:
        gyms = gyms.filter(owner__username=OWNER_USERNAME)

    gyms = list(gyms)

    if not gyms:
        raise SystemExit(
            "No owner gyms found. Create/seed gyms first, or set OWNER_USERNAME correctly."
        )

    return gyms


def get_or_create_plan(gym):
    plan = MembershipPlan.objects.filter(gym=gym).order_by("price").first()

    if not plan:
        plan = MembershipPlan.objects.create(
            gym=gym,
            title="Demo Monthly Access",
            description="Demo monthly membership plan for analytics testing.",
            price=Decimal("49.00"),
            duration_days=30,
            is_trial=False,
        )

    return plan


def create_booking(gym, customer, plan, status=None, dt=None):
    if status is None:
        status = getattr(Booking.Status, "CONFIRMED", "CONFIRMED")

    if dt is None:
        dt = random_past_datetime()

    # Avoid unique constraint collisions by slightly shifting if needed
    for offset in range(5):
        candidate_dt = dt + timedelta(seconds=offset)
        booking, created = Booking.objects.get_or_create(
            customer=customer,
            gym=gym,
            booking_datetime=candidate_dt,
            defaults={
                "plan": plan,
                "status": status,
                "payment_status": "PAID",
                "customer_note": "Demo analytics booking",
            },
        )
        if created:
            # created_at is auto_now_add, so update it after creation for realistic history
            Booking.objects.filter(pk=booking.pk).update(created_at=candidate_dt)
            booking.created_at = candidate_dt
            return booking

    return booking


def create_subscriptions(gym, customers, plan):
    active_status = getattr(GymSubscription.Status, "ACTIVE", "ACTIVE")
    expired_status = getattr(GymSubscription.Status, "EXPIRED", "EXPIRED")

    created_count = 0

    for _ in range(SUBSCRIPTIONS_PER_GYM):
        customer = random.choice(customers)
        dt = random_past_datetime()
        booking = create_booking(
            gym,
            customer,
            plan,
            status=getattr(Booking.Status, "CONFIRMED", "CONFIRMED"),
            dt=dt,
        )

        start_date = dt.date()
        duration = int(getattr(plan, "duration_days", 30) or 30)

        # Most memberships active, some expired for realistic analytics
        if random.random() < 0.78:
            status = active_status
            end_date = today + timedelta(days=random.randint(5, duration + 20))
        else:
            status = expired_status
            end_date = today - timedelta(days=random.randint(1, 40))

        _, created = GymSubscription.objects.get_or_create(
            source_booking=booking,
            defaults={
                "customer": customer,
                "gym": gym,
                "plan": plan,
                "status": status,
                "start_date": start_date,
                "end_date": end_date,
            },
        )

        if created:
            created_count += 1

    return created_count


def create_bookings(gym, customers, plan):
    created_count = 0

    statuses = [
        getattr(Booking.Status, "CONFIRMED", "CONFIRMED"),
        getattr(Booking.Status, "CONFIRMED", "CONFIRMED"),
        getattr(Booking.Status, "CONFIRMED", "CONFIRMED"),
        getattr(Booking.Status, "PENDING", "PENDING"),
        getattr(Booking.Status, "REJECTED", "REJECTED"),
        getattr(Booking.Status, "CANCELLED", "CANCELLED"),
    ]

    for _ in range(BOOKINGS_PER_GYM):
        customer = random.choice(customers)
        status = random.choice(statuses)
        booking = create_booking(gym, customer, plan, status=status)
        if booking:
            created_count += 1

    return created_count


def create_checkins(gym):
    membership_type = getattr(getattr(GymCheckIn, "Type", object), "MEMBERSHIP", "MEMBERSHIP")
    subscriptions = list(GymSubscription.objects.filter(gym=gym))

    if not subscriptions:
        return 0

    created_count = 0

    for _ in range(CHECKINS_PER_GYM):
        sub = random.choice(subscriptions)
        dt = random_past_datetime()

        GymCheckIn.objects.create(
            customer=sub.customer,
            gym=gym,
            subscription=sub,
            type=membership_type,
            checked_in_at=dt,
            notes="Demo QR check-in for traffic analytics",
        )
        created_count += 1

    return created_count


def create_favorites(gym, customers):
    created_count = 0
    sample_size = min(FAVORITES_PER_GYM, len(customers))

    for customer in random.sample(customers, sample_size):
        _, created = Favorite.objects.get_or_create(user=customer, gym=gym)
        if created:
            created_count += 1

    return created_count


def create_workouts(customers):
    if WorkoutLog is None:
        return 0

    created_count = 0
    workout_types = ["Strength", "Upper Body", "Lower Body", "Cardio", "Hypertrophy", "Recovery"]

    for customer in customers[:15]:
        for _ in range(WORKOUTS_PER_CUSTOMER):
            dt = random_past_datetime()
            WorkoutLog.objects.create(
                user=customer,
                title=random.choice(
                    ["Gym Session", "Strength Workout", "Cardio Day", "Push Day", "Pull Day", "Leg Day"]
                ),
                workout_type=random.choice(workout_types),
                duration_minutes=random.choice([35, 45, 50, 60, 75, 90]),
                notes="Demo workout log for activity map testing.",
                logged_at=dt,
                source="demo_seed",
            )
            created_count += 1

    return created_count


customers = create_demo_customers()
gyms = get_target_gyms()

print(f"Demo customers ready: {len(customers)}")
print(f"Target gyms: {len(gyms)}")

total_subs = 0
total_bookings = 0
total_checkins = 0
total_favorites = 0

for gym in gyms:
    plan = get_or_create_plan(gym)

    subs = create_subscriptions(gym, customers, plan)
    bookings = create_bookings(gym, customers, plan)
    checkins = create_checkins(gym)
    favorites = create_favorites(gym, customers)

    total_subs += subs
    total_bookings += bookings
    total_checkins += checkins
    total_favorites += favorites

    print(
        f"{gym.name}: +{subs} subscriptions, +{bookings} bookings, "
        f"+{checkins} check-ins, +{favorites} favorites"
    )

workouts = create_workouts(customers)

print("")
print("DONE")
print(f"Subscriptions created: {total_subs}")
print(f"Bookings touched/created: {total_bookings}")
print(f"Check-ins created: {total_checkins}")
print(f"Favorites created: {total_favorites}")
print(f"Workout logs created: {workouts}")
print("")
print("Refresh:")
print("  /dashboard/owner/analytics/")
print("  /fitness/")
