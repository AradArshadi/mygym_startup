# myGym v0.9.3.6 — Owner Analytics & Favorite Gym Foundation

This refinement keeps the project inside the v0.9.3 UI/UX tuning line while adding the first real owner analytics foundation.

## Added

- Owner portfolio analytics page: `/dashboard/owner/analytics/`
- Per-gym analytics page: `/dashboard/owner/gyms/<id>/analytics/`
- QR-based peak arrival time chart using real `GymCheckIn` records.
- Weekday traffic bars for gym attendance patterns.
- Membership growth metrics from `GymSubscription` records.
- Estimated income streams, currently based on subscriptions and confirmed bookings, with a scalable service structure for future income sources such as products, trainer sessions, marketplace sales, and Stripe payments.
- Booking conversion metrics: requests, confirmed, pending, rejected, cancelled, and confirmation rate.
- Portfolio comparison for owners with multiple gyms.
- Favorite gym toggle on gym detail and gym cards.
- Tests for owner analytics and favorite gym behavior.

## Improved

- Owner dashboard now links directly to portfolio analytics and per-gym analytics.
- Analytics UI is responsive for desktop and mobile.
- Charts use myGym's orange design language with subtle animation.

## Database

No new migration is required. Favorite gyms already existed in the data model; this release adds the missing UX/actions.

## Test commands

```bash
python manage.py test apps.dashboard
python manage.py test apps.reviews
python manage.py test apps.bookings
python manage.py test apps.fitness
python manage.py check
```

## Suggested commit

```bash
git add .
git commit -m "feat: add owner analytics and favorite gyms foundation"
git push origin main
```

Do not create a tag yet if the UI/UX is still being tested.
