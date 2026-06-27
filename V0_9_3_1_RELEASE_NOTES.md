# myGym v0.9.3.1 — Mobile UX & Activity Calendar Hotfix

This release fixes the first UX issues found after the `v0.9.3 — Fitness Home Rebase` build.

## Fixed

- Added a mobile-accessible logout flow inside the Profile hub.
- Added a global dark/light mode toggle with localStorage persistence.
- Improved the Fitness Home activity calendar:
  - Orange intensity scale to match the myGym design language.
  - Top-left calendar flow from oldest day to today.
  - Range selector for 30, 90, 120, and 360 days.
  - Clear legend and today highlight.

## Technical notes

- `fitness_summary()` now accepts an `activity_days` parameter.
- Activity range values are normalized to safe options: 30, 90, 120, 360.
- Added tests for activity range rendering and mobile logout/theme access.
- No database migration is required for this hotfix.

## Recommended test commands

```bash
python manage.py test apps.bookings
python manage.py test apps.fitness
python manage.py check
```
