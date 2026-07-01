import random
from decimal import Decimal
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.bookings.models import Booking, GymCheckIn, GymSubscription
from apps.gyms.models import Gym, MembershipPlan
from apps.reviews.models import Favorite

try:
    from apps.fitness.models import WorkoutLog
except Exception:  # pragma: no cover - optional app safety
    WorkoutLog = None


class Command(BaseCommand):
    help = 'Append realistic demo analytics data for bookings, subscriptions, QR check-ins, favorites, and workouts.'

    def add_arguments(self, parser):
        parser.add_argument('--owner', default='', help='Limit generated data to one owner username.')
        parser.add_argument('--customers', type=int, default=25, help='Number of demo customers to ensure.')
        parser.add_argument('--days', type=int, default=120, help='How far back to spread demo activity.')
        parser.add_argument('--subscriptions-per-gym', type=int, default=24)
        parser.add_argument('--bookings-per-gym', type=int, default=45)
        parser.add_argument('--checkins-per-gym', type=int, default=220)
        parser.add_argument('--favorites-per-gym', type=int, default=12)
        parser.add_argument('--workouts-per-customer', type=int, default=18)
        parser.add_argument('--password', default='DemoPass123')
        parser.add_argument('--dry-run', action='store_true', help='Show what would be generated without creating records.')
        parser.add_argument('--reset-demo', action='store_true', help='Remove previous demo analytics records before creating smoother demo data.')
        parser.add_argument('--seed', type=int, default=9309)

    def handle(self, *args, **options):
        self.options = options
        self.now = timezone.now()
        self.today = timezone.localdate()
        random.seed(options['seed'])

        gyms = self.get_target_gyms(options['owner'])
        customers = self.get_or_create_demo_customers(options['customers'], options['password'])

        self.stdout.write(f'Demo analytics seed: gyms={len(gyms)} customers={len(customers)} days={options["days"]} dry_run={options["dry_run"]}')
        if options['dry_run']:
            self.stdout.write(self.style.WARNING('Dry run only. No database records will be created.'))
            return

        if options['reset_demo']:
            self.reset_demo_data()

        totals = {'subscriptions': 0, 'bookings': 0, 'checkins': 0, 'favorites': 0, 'workouts': 0}
        with transaction.atomic():
            for gym in gyms:
                plan = self.get_or_create_plan(gym)
                subs = self.create_subscriptions(gym, customers, plan)
                bookings = self.create_bookings(gym, customers, plan)
                checkins = self.create_checkins(gym)
                favorites = self.create_favorites(gym, customers)
                totals['subscriptions'] += subs
                totals['bookings'] += bookings
                totals['checkins'] += checkins
                totals['favorites'] += favorites
                self.stdout.write(f'{gym.name}: +{subs} subscriptions, +{bookings} bookings, +{checkins} check-ins, +{favorites} favorites')
            totals['workouts'] = self.create_workouts(customers)

        self.stdout.write(self.style.SUCCESS('DONE'))
        for key, value in totals.items():
            self.stdout.write(f'{key.title()}: {value}')
        self.stdout.write('Refresh /dashboard/owner/#owner-analytics and /fitness/.')

    @staticmethod
    def model_fields(model):
        return {field.name for field in model._meta.fields}

    def random_past_datetime(self):
        """Generate natural-looking demo traffic.

        The previous generator could create cartoonish single-hour spikes. This
        version still has realistic after-work peaks, but spreads visits across
        morning, lunch, and evening windows with weekday/weekend variation.
        """
        max_days = max(1, self.options['days'])
        # Slightly favor recent activity without making old ranges empty.
        if random.random() < 0.58:
            days = int(random.triangular(0, max_days - 1, 12))
        else:
            days = random.randint(0, max_days - 1)
        candidate_day = self.now - timedelta(days=days)
        weekday = timezone.localtime(candidate_day).weekday()
        if weekday >= 5:
            population = [8, 9, 10, 11, 12, 15, 16, 17, 18, 19]
            weights =    [3, 5, 7, 7, 4, 4, 6, 7, 5, 3]
        else:
            population = [6, 7, 8, 9, 12, 16, 17, 18, 19, 20, 21]
            weights =    [3, 4, 5, 3, 2, 4, 7, 9, 10, 7, 3]
        hour = random.choices(population=population, weights=weights, k=1)[0]
        minute = random.choice([0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55])
        return candidate_day.replace(hour=hour, minute=minute, second=random.randint(0, 59), microsecond=0)

    def reset_demo_data(self):
        """Remove only records created by this demo analytics tool.

        This keeps real users/gyms intact and lets testers rebuild smoother demo
        charts after experimenting with older fake data.
        """
        demo_users = get_user_model().objects.filter(username__startswith='demo_customer_analytics_')
        demo_user_ids = list(demo_users.values_list('id', flat=True))
        checkins_deleted = GymCheckIn.objects.filter(notes__icontains='Demo QR check-in').delete()[0]
        workouts_deleted = 0
        if WorkoutLog is not None:
            workouts_deleted = WorkoutLog.objects.filter(source='demo_seed').delete()[0]
        favorites_deleted = Favorite.objects.filter(user_id__in=demo_user_ids).delete()[0]
        subscriptions_deleted = GymSubscription.objects.filter(customer_id__in=demo_user_ids).delete()[0]
        bookings_deleted = Booking.objects.filter(customer_id__in=demo_user_ids, customer_note__icontains='Demo analytics booking').delete()[0]
        self.stdout.write(self.style.WARNING(
            f'Reset demo analytics data: check-ins={checkins_deleted}, workouts={workouts_deleted}, '
            f'favorites={favorites_deleted}, subscriptions={subscriptions_deleted}, bookings={bookings_deleted}'
        ))

    def get_target_gyms(self, owner_username):
        gyms = Gym.objects.filter(owner__isnull=False).select_related('owner')
        if owner_username:
            gyms = gyms.filter(owner__username=owner_username)
        gyms = list(gyms)
        if not gyms:
            raise CommandError('No owner gyms found. Create/seed gyms first or check --owner username.')
        return gyms

    def get_or_create_demo_customers(self, count, password):
        User = get_user_model()
        customers = []
        for i in range(1, count + 1):
            user, created = User.objects.get_or_create(
                username=f'demo_customer_analytics_{i}',
                defaults={
                    'email': f'demo.customer.analytics.{i}@example.com',
                    'role': getattr(User.Role, 'CUSTOMER', 'CUSTOMER'),
                    'is_active': True,
                },
            )
            if created:
                user.set_password(password)
                user.save()
            customers.append(user)
        return customers

    def get_or_create_plan(self, gym):
        plan = MembershipPlan.objects.filter(gym=gym).order_by('price').first()
        if plan:
            return plan
        return MembershipPlan.objects.create(
            gym=gym,
            title='Demo Monthly Access',
            description='Demo monthly membership plan for analytics testing.',
            price=Decimal('49.00'),
            duration_days=30,
            is_trial=False,
        )

    def create_booking(self, gym, customer, plan, status=None, dt=None):
        status = status or getattr(Booking.Status, 'CONFIRMED', 'CONFIRMED')
        dt = dt or self.random_past_datetime()
        for offset in range(8):
            candidate_dt = dt + timedelta(seconds=offset)
            booking, created = Booking.objects.get_or_create(
                customer=customer,
                gym=gym,
                booking_datetime=candidate_dt,
                defaults={
                    'plan': plan,
                    'status': status,
                    'payment_status': 'PAID',
                    'customer_note': 'Demo analytics booking',
                },
            )
            if created:
                Booking.objects.filter(pk=booking.pk).update(created_at=candidate_dt)
                booking.created_at = candidate_dt
                return booking
        return booking

    def create_subscriptions(self, gym, customers, plan):
        active_status = getattr(GymSubscription.Status, 'ACTIVE', 'ACTIVE')
        expired_status = getattr(GymSubscription.Status, 'EXPIRED', 'EXPIRED')
        created_count = 0
        for _ in range(self.options['subscriptions_per_gym']):
            customer = random.choice(customers)
            dt = self.random_past_datetime()
            booking = self.create_booking(gym, customer, plan, status=getattr(Booking.Status, 'CONFIRMED', 'CONFIRMED'), dt=dt)
            duration = int(getattr(plan, 'duration_days', 30) or 30)
            if random.random() < 0.78:
                status = active_status
                end_date = self.today + timedelta(days=random.randint(5, duration + 20))
            else:
                status = expired_status
                end_date = self.today - timedelta(days=random.randint(1, 40))
            _, created = GymSubscription.objects.get_or_create(
                source_booking=booking,
                defaults={
                    'customer': customer,
                    'gym': gym,
                    'plan': plan,
                    'status': status,
                    'start_date': dt.date(),
                    'end_date': end_date,
                },
            )
            created_count += int(created)
        return created_count

    def create_bookings(self, gym, customers, plan):
        statuses = [
            getattr(Booking.Status, 'CONFIRMED', 'CONFIRMED'),
            getattr(Booking.Status, 'CONFIRMED', 'CONFIRMED'),
            getattr(Booking.Status, 'CONFIRMED', 'CONFIRMED'),
            getattr(Booking.Status, 'PENDING', 'PENDING'),
            getattr(Booking.Status, 'REJECTED', 'REJECTED'),
            getattr(Booking.Status, 'CANCELLED', 'CANCELLED'),
        ]
        count = 0
        for _ in range(self.options['bookings_per_gym']):
            self.create_booking(gym, random.choice(customers), plan, status=random.choice(statuses))
            count += 1
        return count

    def create_checkins(self, gym):
        subscriptions = list(GymSubscription.objects.filter(gym=gym))
        if not subscriptions:
            return 0
        fields = self.model_fields(GymCheckIn)
        checkin_type_value = 'MEMBERSHIP'
        if hasattr(GymCheckIn, 'Type'):
            checkin_type_value = getattr(GymCheckIn.Type, 'MEMBERSHIP', 'MEMBERSHIP')
        count = 0
        for _ in range(self.options['checkins_per_gym']):
            sub = random.choice(subscriptions)
            dt = self.random_past_datetime()
            kwargs = {}
            if 'customer' in fields:
                kwargs['customer'] = sub.customer
            if 'user' in fields:
                kwargs['user'] = sub.customer
            if 'gym' in fields:
                kwargs['gym'] = gym
            if 'subscription' in fields:
                kwargs['subscription'] = sub
            if 'checked_in_at' in fields:
                kwargs['checked_in_at'] = dt
            if 'notes' in fields:
                kwargs['notes'] = 'Demo QR check-in for traffic analytics'
            if 'type' in fields:
                kwargs['type'] = checkin_type_value
            elif 'checkin_type' in fields:
                kwargs['checkin_type'] = checkin_type_value
            elif 'check_in_type' in fields:
                kwargs['check_in_type'] = checkin_type_value
            elif 'source' in fields:
                kwargs['source'] = 'MEMBERSHIP'
            GymCheckIn.objects.create(**kwargs)
            count += 1
        return count

    def create_favorites(self, gym, customers):
        count = 0
        for customer in random.sample(customers, min(self.options['favorites_per_gym'], len(customers))):
            _, created = Favorite.objects.get_or_create(user=customer, gym=gym)
            count += int(created)
        return count

    def create_workouts(self, customers):
        if WorkoutLog is None:
            return 0
        fields = self.model_fields(WorkoutLog)
        count = 0
        workout_types = ['Strength', 'Upper Body', 'Lower Body', 'Cardio', 'Hypertrophy', 'Recovery']
        for customer in customers[:15]:
            for _ in range(self.options['workouts_per_customer']):
                dt = self.random_past_datetime()
                kwargs = {}
                if 'user' in fields:
                    kwargs['user'] = customer
                if 'title' in fields:
                    kwargs['title'] = random.choice(['Gym Session', 'Strength Workout', 'Cardio Day', 'Push Day', 'Pull Day', 'Leg Day'])
                if 'workout_type' in fields:
                    kwargs['workout_type'] = random.choice(workout_types)
                if 'duration_minutes' in fields:
                    kwargs['duration_minutes'] = random.choice([35, 45, 50, 60, 75, 90])
                if 'notes' in fields:
                    kwargs['notes'] = 'Demo workout log for activity map testing.'
                if 'logged_at' in fields:
                    kwargs['logged_at'] = dt
                if 'source' in fields:
                    kwargs['source'] = 'demo_seed'
                WorkoutLog.objects.create(**kwargs)
                count += 1
        return count
