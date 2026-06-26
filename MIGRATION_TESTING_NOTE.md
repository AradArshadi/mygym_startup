# Migration/testing note

If `python manage.py test apps.bookings` fails with:

```text
django.db.utils.OperationalError: (1050, "Table 'gyms_importbatch' already exists")
```

it means Django is trying to apply migrations into a MySQL schema that already contains tables.
This is usually caused by a leftover/interrupted MySQL test database or a migration history mismatch.

This hotfix makes normal Django tests use an isolated in-memory SQLite database by default:

```bash
python manage.py test apps.bookings
```

Your real development/production database can still be MySQL. The switch only happens while running
Django's test command.

To intentionally test against MySQL, set:

```env
USE_SQLITE_FOR_TESTS=False
TEST_DB_NAME=test_mygym
```

Then make sure the MySQL test schema is clean before running tests:

```sql
DROP DATABASE IF EXISTS test_mygym;
CREATE DATABASE test_mygym CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
GRANT ALL PRIVILEGES ON test_mygym.* TO 'your_db_user'@'localhost';
FLUSH PRIVILEGES;
```
