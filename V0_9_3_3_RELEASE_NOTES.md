# myGym v0.9.3.3 — Interactive Activity Map UX Hotfix

This hotfix polishes the v0.9.3 Fitness Home activity calendar.

## Fixed

- Made the Training Activity map interactive on desktop and mobile.
- Users can click or tap any activity square to see the workout count for that exact day.
- Added keyboard support for Enter/Space on activity cells.
- Removed the helper text: `GitHub-style calendar · today is highlighted`.
- Fixed short-range month label collision such as `MayJun` by skipping tiny leading partial-month labels and enforcing spacing between labels.
- Added selected-cell styling and an activity detail panel.
- Added regression tests for interactive cells and non-overlapping month labels.

## Database

No migration required.

## Verification

```bash
python manage.py test apps.fitness
python manage.py test apps.bookings
python manage.py check
```
