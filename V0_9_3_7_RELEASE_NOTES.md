# myGym v0.9.3.7 — Owner Analytics MySQL Safety Hotfix

This hotfix fixes a production error on `/dashboard/owner/analytics/`:

```text
AttributeError: 'NoneType' object has no attribute 'strftime'
```

## Fixed

- Owner analytics no longer depends on database-side `TruncDate`, `TruncMonth`, `ExtractHour`, or `ExtractWeekDay` for chart buckets.
- Peak-time charts now aggregate QR check-in times in Python after safely converting datetimes to the project timezone.
- Weekday traffic charts now aggregate in Python and remain safe if MySQL timezone tables are missing on the host.
- Growth trend labels now skip invalid/null timestamps instead of crashing.
- This makes owner analytics safer on PythonAnywhere/MySQL deployments.

## Migration

No database migration required.

## Test commands

```bash
python manage.py test apps.dashboard
python manage.py test apps.bookings
python manage.py test apps.fitness
python manage.py check
```
