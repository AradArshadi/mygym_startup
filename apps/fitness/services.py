from datetime import timedelta

from django.db.models import Count, Sum
from django.utils import timezone

from .models import WorkoutGoal, WorkoutLog


def week_start_for(date_value=None):
    """Return Monday for the week containing date_value in the current timezone."""
    date_value = date_value or timezone.localdate()
    return date_value - timedelta(days=date_value.weekday())


def get_or_create_goal(user):
    goal, _ = WorkoutGoal.objects.get_or_create(user=user, defaults={'weekly_target': 3})
    return goal


def workouts_for_week(user, start_date=None):
    start_date = start_date or week_start_for()
    end_date = start_date + timedelta(days=7)
    return WorkoutLog.objects.filter(
        user=user,
        logged_at__date__gte=start_date,
        logged_at__date__lt=end_date,
    )


def weekly_workout_count(user, start_date=None):
    return workouts_for_week(user, start_date=start_date).count()


def weekly_active_days(user, start_date=None):
    start_date = start_date or week_start_for()
    end_date = start_date + timedelta(days=7)
    days = set()
    qs = WorkoutLog.objects.filter(user=user, logged_at__date__gte=start_date, logged_at__date__lt=end_date)
    for workout in qs.only('logged_at'):
        days.add(timezone.localtime(workout.logged_at).date())
    return len(days)


def current_weekly_streak(user, target=None, reference_date=None, max_weeks=52):
    """Count consecutive weeks where the user met their target.

    We use weekly consistency instead of a daily streak because fitness recovery matters.
    If the current week is not complete yet, it counts only if the user has already met
    the goal this week; otherwise the streak starts from the previous week.
    """
    target = target or get_or_create_goal(user).weekly_target
    current_start = week_start_for(reference_date)
    streak = 0

    for offset in range(max_weeks):
        week_start = current_start - timedelta(days=7 * offset)
        count = weekly_workout_count(user, week_start)
        if count >= target:
            streak += 1
        else:
            if offset == 0:
                # The current week can still be in progress; keep looking at completed previous weeks.
                continue
            break
    return streak


def training_activity_grid(user, weeks=7):
    """Return a GitHub/Duolingo-style activity grid for dashboard display."""
    today = timezone.localdate()
    start = today - timedelta(days=(weeks * 7) - 1)
    counts = {}
    qs = (
        WorkoutLog.objects
        .filter(user=user, logged_at__date__gte=start, logged_at__date__lte=today)
        .values('logged_at__date')
        .annotate(total=Count('id'))
    )
    for row in qs:
        counts[row['logged_at__date']] = row['total']

    days = []
    for index in range(weeks * 7):
        day = start + timedelta(days=index)
        count = counts.get(day, 0)
        if count == 0:
            intensity = 0
        elif count == 1:
            intensity = 1
        elif count == 2:
            intensity = 2
        else:
            intensity = 3
        days.append({
            'date': day,
            'count': count,
            'intensity': intensity,
            'is_today': day == today,
        })
    return days


def fitness_summary(user):
    goal = get_or_create_goal(user)
    week_start = week_start_for()
    week_count = weekly_workout_count(user, week_start)
    active_days = weekly_active_days(user, week_start)
    total_workouts = WorkoutLog.objects.filter(user=user).count()
    total_minutes = WorkoutLog.objects.filter(user=user).aggregate(total=Sum('duration_minutes'))['total'] or 0
    streak = current_weekly_streak(user, goal.weekly_target)
    progress_percent = min(100, round((week_count / goal.weekly_target) * 100)) if goal.weekly_target else 0

    return {
        'goal': goal,
        'week_start': week_start,
        'week_count': week_count,
        'active_days': active_days,
        'total_workouts': total_workouts,
        'total_minutes': total_minutes,
        'streak': streak,
        'progress_percent': progress_percent,
        'activity_grid': training_activity_grid(user),
    }
