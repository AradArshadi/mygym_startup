# myGym v0.9.3.9 — Security, Safety & Demo Stability

## Added

- Control Deck Safety Center at `/control/security/`.
- Control Deck Demo Tools at `/control/demo-tools/`.
- `seed_demo_analytics` management command for append-only realistic test data.
- Backup and recovery documentation.
- Security and safety documentation.
- Upload validation for gym images.
- Demo tools environment switch: `DEMO_TOOLS_ENABLED`.

## Improved

- Dark/light mode consistency for gym cards, filters, tables and white Bootstrap leftovers.
- Permission-denied attempts to the Control Deck are now logged.
- Admins can run demo data generation without shell access on test/demo environments.

## Notes

- No database migration required.
- Keep `DEMO_TOOLS_ENABLED=False` for real production.
- Run `python manage.py check --deploy` before production deployment.
