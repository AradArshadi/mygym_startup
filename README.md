
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
