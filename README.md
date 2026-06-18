
## v3 additions

- Gym detail pages now include a Photos section, Reviews section, plans, trainers, and booking form.
- Customers can submit one review per gym.
- Owners receive in-app notifications for bookings and reviews.
- Customers receive in-app notification after sending a booking request.
- Owner dashboard shows customer names, emails, requested booking time, status, and notes per gym.
- New notifications module: `/notifications/`.

After updating, run:

```bash
python manage.py makemigrations notifications reviews bookings gyms dashboard analytics accounts
python manage.py migrate
python manage.py runserver
```

## v0.8 UI/UX Bootstrap Refresh

- Added Bootstrap 5 CDN integration.
- Redesigned navbar, landing/explore page, gym cards, table view, map container, gym detail page, customer dashboard, owner dashboard, and auth pages.
- Kept backend logic unchanged; no migration required for this UI-only upgrade.

Run:

```bash
python manage.py check
python manage.py runserver
```


---

Powered by Arad Arshadi  
GitHub: https://github.com/AradArshadi

## v0.9 Control Deck

The project now includes a custom admin/operator dashboard at `/control/`.

Access is limited to superusers, staff users, or users with role `ADMIN`.

Control Deck features:
- Platform overview metrics
- User management and role changes
- Gym approval/rejection workflow
- Booking status controls
- Review moderation
- Links back to Django Admin for low-level database administration

Django Admin remains available at `/admin/` as the technical back office.

## v0.9.1 Email System

This version adds a centralized email service layer under `apps/emails/`.

Email events currently supported:
- Customer/owner/trainer welcome email after registration
- Booking request email to gym owner / gym contact email
- Booking status email to customer when accepted, rejected, cancelled, or updated by Control Deck
- Gym approval/rejection email to owner
- New review email to gym owner

### Local development

By default emails are printed to the terminal:

```env
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

### SMTP deployment

For SMTP, set:

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@example.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=myGym <your-email@example.com>
SITE_URL=https://yourusername.pythonanywhere.com
```

### Test email

```bash
python manage.py test_email your-email@example.com
```

No database migration is required for v0.9.1.

## v0.9.2 Logging & Observability

This version adds a production debugging layer so silent failures are easier to detect.

Added:
- `apps/systemlogs` app
- `SystemLog` database model
- `/control/logs/` Control Deck page
- File logs in `logs/mygym.log` and `logs/emails.log`
- Email diagnostics for every send attempt, success, skip, and failure
- Request/error logging middleware
- `show_email_config` command for sanitized email configuration checks

After updating, run:

```bash
python manage.py migrate
python manage.py check
python manage.py show_email_config
python manage.py test_email your-email@example.com
```

Important deployment notes:
- The `logs/` directory is intentionally ignored by Git.
- Email credentials must stay inside `.env` and must never be committed.
- Use `/control/logs/` to inspect email failures and admin/business events.

Useful commands:

```bash
tail -n 80 logs/emails.log
tail -n 80 logs/mygym.log
```

## v0.9.2.2 — Real Gym Import Pipeline

This version replaces fake seed data with a safer import workflow for real public data.

### What changed

- Added `ImportBatch` model to group imported data.
- Added import tracking fields on `Gym`:
  - `is_imported`
  - `is_claimed`
  - `source`
  - `external_id`
  - `import_batch`
  - `imported_at`
- Added OpenStreetMap/Overpass import command.
- Added safe wipe commands so imported data can be removed without touching owner-created gyms.

### Run migrations

```bash
python manage.py makemigrations gyms
python manage.py migrate
```

### Import gyms from OpenStreetMap

```bash
python manage.py import_gyms_osm --city "Tabriz" --country "Iran"
```

Import as approved immediately:

```bash
python manage.py import_gyms_osm --city "Tabriz" --country "Iran" --approve
```

Dry run:

```bash
python manage.py import_gyms_osm --city "Tabriz" --country "Iran" --dry-run
```

Limit records:

```bash
python manage.py import_gyms_osm --city "Tabriz" --country "Iran" --limit 25
```

### List import batches

```bash
python manage.py list_import_batches
```

### Wipe one import batch

```bash
python manage.py wipe_import_batch 1
```

If some imported gyms have bookings/reviews/favorites, they are protected by default. To delete them anyway:

```bash
python manage.py wipe_import_batch 1 --force
```

### Wipe imported gyms by city

```bash
python manage.py wipe_imported_gyms --city "Tabriz"
```

This never deletes owner-created gyms or claimed gyms.

## v0.9.2.4 security/import hotfix notes

### Emergency rollback for accidentally approved imports

If a Geoapify batch was imported as approved, move it back to review/pending:

```bash
python manage.py mark_import_batch_pending 3
```

### Safer Geoapify importing

`--approve` is now ignored unless it is deliberately combined with `--allow-auto-approve`.
Default imported gyms stay `PENDING` for Control Deck review.

```bash
python manage.py import_gyms_geoapify --city "Tabriz" --country "Iran" --radius-km 25 --limit 100
```

Unsafe demo-only auto approval:

```bash
python manage.py import_gyms_geoapify --city "Tabriz" --country "Iran" --radius-km 25 --approve --allow-auto-approve
```

### Public signup role security

The public register page now only allows:

- Customer
- Gym Owner

Admin accounts cannot be created from public signup. Admin promotion is handled from the Control Deck, and promotion to `ADMIN` is restricted to Django superusers.

### Test data reset trigger

Delete imported, unclaimed test gyms safely:

```bash
python manage.py wipe_test_data --source geoapify --city Tabriz --yes --delete-empty-batches
```

Full demo/test cleanup, still protecting superusers and claimed gyms:

```bash
python manage.py wipe_test_data --yes --include-demo-users --delete-empty-batches
```

### Gym photos

Owner-uploaded gym photos are already supported through gym management. Geoapify Places does not reliably provide gym photos, so imported gyms still use the current placeholder unless photos are uploaded later by an owner/admin.
