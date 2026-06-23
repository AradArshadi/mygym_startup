# myGym — Django Marketplace & Operations Platform

**myGym** is a modular Django web application that demonstrates how to build a multi-role marketplace platform with customer dashboards, business/operator dashboards, booking workflows, membership access, QR-based check-ins, admin controls, notifications, email services, logging, and SQL-backed data models.

The project started as a gym marketplace, but it has evolved into a broader example of a service-commerce and operations platform. The same architecture can be adapted to e-commerce, network marketing, affiliate systems, subscription platforms, wallet/ledger systems, and member-management products.

---

## Why this project matters

This project is not a simple CRUD demo. It shows end-to-end ownership of a real business workflow:

```text
Customer discovers a venue
→ customer sends a booking request
→ owner approves or rejects it
→ system creates a confirmed session
→ customer receives QR access
→ owner validates entry/check-in
→ dashboards and logs update
→ admin can monitor and control the platform
```

That workflow demonstrates the same backend thinking needed for commercial platforms where users, orders, referrals, commissions, subscriptions, wallets, reporting, and administrative tools must work together cleanly.

---

## Relevant to e-commerce / MLM / affiliate-style platforms

Although this project is built around gyms and wellness venues, several parts are directly transferable to a network-marketing or e-commerce system:

| Requirement in target platform | Similar foundation in myGym |
|---|---|
| Online store / order management | Booking request and approval lifecycle, plan selection, status tracking |
| Member dashboard | Customer dashboard with bookings, sessions, memberships, notifications |
| Seller/operator dashboard | Owner dashboard for gyms, requests, sessions, and check-ins |
| Admin management tools | Custom Control Deck for users, gyms, bookings, reviews, and logs |
| Subscription management | GymSubscription model with active/expired/cancelled states |
| Access / entitlement validation | QR-based Digital Access Pass with 24-hour refresh |
| Reporting | Analytics app, owner dashboard metrics, check-in history |
| Financial system foundation | Booking payment fields, plan pricing, subscription records, status tracking |
| Auditability | SystemLog app, email logs, request/error logging middleware |
| Maintainability | Separated Django apps, services, templates, and migrations |

For an MLM/e-commerce platform, the next natural modules would be:

- product catalog and cart
- order and invoice models
- referral/sponsor tree
- commission ledger
- wallet and payout records
- bonus calculation engine
- member rank/level system
- admin payout approval workflow
- Celery tasks for asynchronous commission calculations

---

## Core features

### Multi-role account system

- Customer users
- Owner/business users
- Admin/control users
- Role-based access control
- Protected dashboards and management pages

### Gym / business marketplace

- Venue listing and detail pages
- Search and filtering UI
- Facility tags
- Membership plans
- Trainer profiles
- Photo/gallery foundation
- Imported/demo business data support

### Booking workflow

- Customer booking request form
- Owner approve/reject flow
- Booking statuses: pending, confirmed, cancelled, rejected
- Customer notes
- Plan selection
- Email and in-app notification events

### Sessions system

- Confirmed bookings create operational sessions
- Customer can view upcoming, previous, and cancelled sessions
- One-time QR code for session check-in
- QR becomes used after successful check-in
- Session status tracking

### Digital Access Pass / membership QR

- Membership access pass for subscribed users
- QR token refreshes every 24 hours
- QR remains available until subscription expiry/cancellation
- Owner/staff can validate membership QR codes
- Check-in records are stored for attendance history

### Owner dashboard

- Business overview
- Booking request management
- Session/check-in visibility
- Gym management tools
- Customer information for relevant bookings

### Customer dashboard

- Bookings overview
- Sessions page
- Memberships / access pass page
- Notifications
- QR display for sessions and membership passes

### Control Deck

A custom administrative control panel at `/control/` for platform operators.

Includes:

- platform overview metrics
- user management
- role changes
- gym approval/rejection
- booking status controls
- review moderation
- system logs
- links to Django Admin for technical database administration

### Email system

Centralized email service layer under `apps/emails/`.

Supported events include:

- welcome emails
- booking request email to owner
- booking status update email to customer
- gym approval/rejection email
- review notification email
- session QR email
- membership access pass email

### Notifications

- In-app notifications for customers and owners
- Booking and review notifications
- Dashboard notification visibility

### Logging and observability

- `apps/systemlogs` app
- database-backed system logs
- request/error logging middleware
- file logs for application and email activity
- Control Deck log viewer

---

## Technical stack

- Python
- Django 5
- Django Templates
- Bootstrap 5
- HTML / CSS / JavaScript
- SQL database support through Django ORM
- MySQL currently supported via `mysqlclient`
- SQLite supported for local lightweight development
- PostgreSQL can be supported through Django ORM with standard database configuration
- Git
- Pillow
- qrcode
- python-decouple

---

## Project structure

```text
mygym_startup/
├── apps/
│   ├── accounts/        # custom user roles and authentication views
│   ├── gyms/            # venue, plans, trainers, facilities, imports
│   ├── bookings/        # bookings, sessions, memberships, QR access, check-ins
│   ├── reviews/         # customer reviews and rating logic
│   ├── dashboard/       # customer and owner dashboards
│   ├── controlpanel/    # custom admin/operator control deck
│   ├── analytics/       # platform and business metrics
│   ├── notifications/   # in-app notification system
│   ├── emails/          # centralized email service layer
│   └── systemlogs/      # logging, observability, diagnostics
├── core/                # Django settings, URLs, WSGI/ASGI
├── templates/           # Django templates
├── static/              # CSS and static assets
├── manage.py
├── requirements.txt
└── README.md
```

---

## Database and configuration

Configuration is environment-based.

Example `.env`:

```env
DEBUG=True
SECRET_KEY=your-secret-key

DB_ENGINE=mysql
DB_NAME=mygym_local
DB_USER=root
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=3306

EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
DEFAULT_FROM_EMAIL=myGym <noreply@example.com>
SITE_URL=http://127.0.0.1:8000
```

For SQLite local development:

```env
DB_ENGINE=sqlite
DB_NAME=db.sqlite3
```

---

## Installation

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows PowerShell

pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/
```

---

## Useful commands

```bash
python manage.py check
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Email diagnostics:

```bash
python manage.py show_email_config
python manage.py test_email your-email@example.com
```

Demo data commands may exist depending on the branch/version:

```bash
python manage.py seed_demo
python manage.py seed_demo_users
python manage.py seed_demo_reviews
```

---

## Current version

```text
v0.9.2.9 — Sessions + Digital Access Pass
```

Main additions in this version:

- one-time QR codes for confirmed sessions
- membership QR access passes
- 24-hour QR refresh for active memberships
- customer sessions page
- customer memberships/access pass page
- owner QR validation and check-in flow
- attendance history model
- QR emails
- MySQL-safe migration for new access tables

---

## Architecture notes

The project is intentionally split into small Django apps so that each business capability is isolated:

- `accounts` handles identity and roles
- `gyms` handles supply-side business profiles
- `bookings` handles transactions, sessions, memberships, and access validation
- `dashboard` handles user-facing reporting
- `controlpanel` handles platform operations
- `emails` centralizes communication
- `systemlogs` supports diagnostics and production debugging

This structure makes the code easier to transfer to another backend team and easier to extend into new domains such as e-commerce, affiliate marketing, referral systems, wallets, or commission engines.

---

## What I would build next for an MLM / e-commerce version

If this architecture were adapted into a network-marketing and e-commerce platform, I would add the following modules:

### Commerce

- Product
- ProductVariant
- Cart
- Order
- OrderItem
- Invoice
- PaymentTransaction
- Shipment/Fulfillment status

### Referral and network structure

- Sponsor relationship
- Referral tree
- Placement tree
- Member rank/level
- Team volume tracking
- Direct and indirect referral reporting

### Commission engine

- CommissionRule
- CommissionRun
- CommissionLedger
- BonusLedger
- WalletTransaction
- PayoutRequest
- PayoutApproval

### Background processing

- Celery tasks for commission calculations
- Redis broker/cache
- scheduled payout runs
- async email/report generation

### PWA readiness

- service worker
- web app manifest
- offline-safe dashboard shell
- mobile-first member dashboard

---

## Project value

This project demonstrates that I can take ownership of a Django platform from architecture to implementation:

- design relational data models
- separate business logic across maintainable apps
- build multi-role dashboards
- implement approval workflows
- integrate email and notifications
- work with SQL migrations
- handle MySQL migration issues
- build admin/operator tools beyond default Django Admin
- document the system for transfer and future development

It is a practical foundation for service-commerce, subscription, marketplace, and member-management systems.

---

## Author

**Arad Arshadi**  
Bachelor's Degree — University of Tabriz  
Django / Python Developer  
GitHub: https://github.com/AradArshadi
