# myGym

**The Operating System for Sports & Wellness**

myGym is a Django-based marketplace platform that helps users discover, review, book, and manage fitness and wellness venues.

The project started as a gym marketplace and is being designed to evolve into a broader ecosystem covering:

* Gyms
* Trainers
* Tennis Coaches
* Wellness Centers
* Sports Facilities
* Nutrition Services
* Recovery Services
* AI Coaching
* Smart Gym Infrastructure

---

## Vision

Our long-term goal is to build the central platform for discovering, booking, training, recovering, and staying motivated.

myGym is not simply a gym finder.

It aims to become:

> The Operating System for Sports & Wellness.

---

# Current Status

Version: **v0.9.2.8.1**

Current Phase:

**Marketplace Foundation**

The platform already supports:

* Gym discovery
* User accounts
* Owner accounts
* Reviews & ratings
* Bookings
* Notifications
* Analytics
* Import pipelines
* Control Deck administration
* Gym photos
* Search & filtering

---

# Features

## User Features

* Register and login
* Browse gyms
* Search gyms
* Filter gyms
* View gym details
* Submit reviews
* Submit booking requests
* Receive notifications

## Gym Owner Features

* Manage owned gyms
* Receive booking requests
* Receive review notifications
* View owner dashboard

## Admin Features

* Control Deck administration panel
* User management
* Gym moderation
* Review moderation
* Booking oversight
* Import management
* Platform analytics
* System logs

---

# Import Pipeline

Real gym data can be imported using Geoapify.

Features:

* Import batching
* Duplicate protection
* Source tracking
* Safe deletion
* Review workflow

Management commands:

```bash
python manage.py import_gyms_geoapify --city "Tabriz" --country "Iran" --radius-km 25 --limit 15
python manage.py list_import_batches
python manage.py wipe_import_batch 1
```

---

# Tech Stack

## Backend

* Django 5.x
* Python 3.x

## Frontend

* Bootstrap 5
* Custom CSS
* Leaflet Maps
* OpenStreetMap

## Database

Current:

* SQLite

In Progress:

* MySQL Migration

Future:

* PostgreSQL Production Deployment

## Deployment

* PythonAnywhere
* Cloudflare (planned)

---

# Project Structure

```text
apps/
├── accounts
├── gyms
├── bookings
├── reviews
├── notifications
├── analytics
├── dashboard
├── emails
├── controlpanel
└── systemlogs
```

---

# Installation

```bash
git clone https://github.com/AradArshadi/mygym.git

cd mygym

python -m venv .venv

source .venv/bin/activate

pip install -r requirements.txt

python manage.py migrate

python manage.py runserver
```

---

# Environment Variables

Example:

```env
SECRET_KEY=your-secret-key

DEBUG=True

DATABASE_ENGINE=sqlite

EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

---

# Useful Commands

Import gyms:

```bash
python manage.py import_gyms_geoapify --city "Tabriz" --country "Iran"
```

Generate placeholder photos:

```bash
python manage.py generate_gym_placeholder_photos --replace
```

Seed demo users:

```bash
python manage.py seed_demo_users --customers 15 --owners 3
```

Seed reviews:

```bash
python manage.py seed_demo_reviews --reviews 40
```

Clean demo data:

```bash
python manage.py wipe_demo_data --yes
```

---

# Roadmap

## Marketplace Foundation

* Gym discovery
* Reviews
* Bookings
* Notifications
* Analytics

## Upcoming

* Gym claim workflow
* Advanced owner dashboard
* MySQL migration
* Cloud deployment
* Production hardening

## Future Vision

* AI coaching
* Wellness marketplace
* Smart gym integrations
* Wearables
* Nutrition services
* Gamification

---

# Versioning

The project intentionally remains below v1.0.

Rules:

* Major feature: 0.9.2.8 → 0.9.2.9
* Minor update: 0.9.2.8 → 0.9.2.8.1
* v1.0.0 only when production-ready

---

# Founder

**Arad Arshadi**

GitHub:
https://github.com/AradArshadi

LinkedIn:
https://linkedin.com/in/arad-arshadi
