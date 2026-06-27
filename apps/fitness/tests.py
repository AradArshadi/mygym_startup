from datetime import datetime, time, timedelta

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from .models import WorkoutGoal, WorkoutLog
from .services import current_weekly_streak, fitness_summary, week_start_for, weekly_workout_count


class FitnessHomeTests(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.customer = self.User.objects.create_user(
            username='fitness_customer',
            email='customer@example.com',
            password='pass12345',
            role='CUSTOMER',
        )
        self.owner = self.User.objects.create_user(
            username='fitness_owner',
            email='owner@example.com',
            password='pass12345',
            role='OWNER',
        )

    def test_goal_is_created_with_default_weekly_target(self):
        self.client.force_login(self.customer)
        response = self.client.get(reverse('fitness_home'))
        self.assertEqual(response.status_code, 200)
        goal = WorkoutGoal.objects.get(user=self.customer)
        self.assertEqual(goal.weekly_target, 3)

    def test_log_workout_creates_entry(self):
        self.client.force_login(self.customer)
        response = self.client.post(reverse('log_workout'), {
            'title': 'Upper A',
            'workout_type': 'Strength',
            'duration_minutes': 62,
            'notes': 'Good session.',
        })
        self.assertRedirects(response, reverse('fitness_home'))
        workout = WorkoutLog.objects.get(user=self.customer)
        self.assertEqual(workout.title, 'Upper A')
        self.assertEqual(workout.duration_minutes, 62)

    def test_weekly_count_and_summary(self):
        now = timezone.now()
        WorkoutLog.objects.create(user=self.customer, title='Push', logged_at=now, duration_minutes=45)
        WorkoutLog.objects.create(user=self.customer, title='Pull', logged_at=now - timedelta(days=1), duration_minutes=50)
        self.assertEqual(weekly_workout_count(self.customer), 2)
        summary = fitness_summary(self.customer)
        self.assertEqual(summary['week_count'], 2)
        self.assertEqual(summary['total_workouts'], 2)
        self.assertEqual(summary['total_minutes'], 95)

    def test_weekly_streak_counts_completed_weeks(self):
        goal = WorkoutGoal.objects.create(user=self.customer, weekly_target=3)
        current_week = week_start_for()
        previous_week = current_week - timedelta(days=7)
        for day in [0, 1, 2]:
            WorkoutLog.objects.create(user=self.customer, title=f'Current {day}', logged_at=timezone.make_aware(datetime.combine(current_week + timedelta(days=day), time.min)))
            WorkoutLog.objects.create(user=self.customer, title=f'Previous {day}', logged_at=timezone.make_aware(datetime.combine(previous_week + timedelta(days=day), time.min)))
        self.assertEqual(current_weekly_streak(self.customer, target=goal.weekly_target), 2)

    def test_owner_is_redirected_from_customer_fitness_home(self):
        self.client.force_login(self.owner)
        response = self.client.get(reverse('fitness_home'))
        self.assertRedirects(response, reverse('owner_dashboard'))

    def test_mobile_nav_urls_are_available(self):
        self.client.force_login(self.customer)
        for name in ['fitness_home', 'discover', 'log_workout', 'chat_home', 'profile_hub']:
            response = self.client.get(reverse(name))
            self.assertIn(response.status_code, [200, 302])
