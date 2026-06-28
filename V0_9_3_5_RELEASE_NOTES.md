# myGym v0.9.3.5 — Owner Dashboard UX Hotfix

This patch improves the owner dashboard without changing the database schema.

## Fixed

- Owner metric cards are now clickable jump links instead of dead numbers.
- Pending booking requests now appear in a command-center section near the top, so owners do not need to scroll through every gym card to act.
- Added confirmed bookings and active access-pass/member sections near the top.
- Reworked owner dashboard cards/panels for cleaner alignment, premium typography, and better dark/light theme consistency.
- Reworked gym portfolio stats into clickable mini-stat cards.
- Added dashboard regression tests for actionable stat cards and top-level pending request visibility.

## No migration required

This release changes views, templates, CSS, and tests only.

Run:

```bash
python manage.py test apps.dashboard
python manage.py test apps.bookings
python manage.py test apps.fitness
python manage.py check
```
