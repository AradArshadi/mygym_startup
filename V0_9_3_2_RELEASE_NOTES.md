# myGym v0.9.3.2 — Activity Map & Mobile Navigation Debug Hotfix

This hotfix corrects the first Fitness Home activity calendar implementation and improves mobile navigation reliability.

## Fixed

- Replaced the large tile activity panel with a true GitHub-style contribution calendar.
- Activity map now flows Monday-to-Sunday per week, left-to-right by week.
- Calendar now uses myGym orange intensity levels instead of white blocks.
- Calendar headline now counts workouts inside the selected range, not all-time workouts.
- Footer summary now shows active days in the selected range, not current-week active days.
- 30 / 90 / 120 / 360 day selectors still work.
- Today remains highlighted.
- Mobile bottom navigation z-index and safe-area positioning improved.
- Mobile top hamburger menu is restored as a fallback so navigation never disappears completely.

## Added

- `python manage.py debug_workout_activity <username> --days 30`

This command prints timezone, selected range, workout counts, active days, and the latest workout logs with IN_RANGE / OUT_OF_RANGE markers.

## Tests

Additional regression tests cover:

- selected-range activity counts
- GitHub-style calendar rendering
- mobile nav fallback availability

## No database migration required

This release does not add or change database models.
