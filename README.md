
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
