# myGym v0.9.3 — Fitness Home Rebase

This release begins the product shift from a gym booking marketplace into a fitness lifestyle platform.

## Added

- New `apps.fitness` Django app.
- Customer Fitness Home at `/fitness/`.
- Mobile-first bottom navigation for customer experience: Home, Discover, +, Chat, Profile.
- Workout logging foundation with `WorkoutLog`.
- Weekly workout goal foundation with `WorkoutGoal`.
- Weekly consistency/streak service.
- Training activity grid inspired by modern fitness apps.
- Profile hub for sessions, access passes, saved gyms, reviews, and workout stats.
- Discover placeholder for future social feed/posts/videos/challenges.
- Chat placeholder for future DMs.
- Role-aware login redirect: customers go to Fitness Home, owners to Owner Dashboard, admins to Control Deck.
- Fitness app tests.

## Preserved

- Existing booking flow.
- Existing QR session/access pass system.
- Existing owner dashboard and admin Control Deck functionality.
- Existing gym marketplace/discovery pages.
- Existing infrastructure hotfix from v0.9.2.10.1.

## Not included yet

- Full social feed backend.
- Friends list.
- Real DM backend.
- Marketplace products/cart/payments.
- Advanced workout set tracking.
- Muscle recovery maps.

## Recommended commands

```bash
python manage.py migrate
python manage.py test apps.bookings
python manage.py test apps.fitness
python manage.py check
```

## Suggested tag

```bash
git tag -a v0.9.3 -m "myGym v0.9.3 — Fitness Home Rebase"
git push origin main --tags
```
