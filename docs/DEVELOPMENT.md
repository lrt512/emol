# Development Guide

eMoL development runs entirely in Docker containers.

## Quick Start

### Prerequisites
- Docker and Docker Compose v2+
- Git
- Make

### Setup (5 minutes)

```bash
git clone <repository-url>
cd emol
make bootstrap
```

Access at http://localhost:8000 (admin: `admin` / `admin`)

## Initial Data

After bootstrap, seed some data via the admin panel (http://localhost:8000/admin):

1. **Privacy Policy** — Required for email flows. Add any text.
2. **Discipline** — At least one (e.g., Fencing, Armoured Combat)
3. **Authorizations** — Link to a discipline

See the [setup guide](https://docs.google.com/document/d/1OxtfClGNAlUrNU9n_-nHQv7xctCttW2iRf1dfTpFqrw/edit) for details.

## Daily Workflow

| Command | Purpose |
|---------|---------|
| `make up` | Start containers |
| `make down` | Stop containers |
| `make logs` | Tail app logs |
| `make shell` | Container bash shell |
| `make test` | Run tests |
| `make migrate` | Run migrations |

**Code changes are live-mounted** — no rebuild needed for Python/template changes.

Only use `make rebuild` for dependency or Dockerfile changes.

## Code Quality

```bash
make format    # black + isort
make lint      # flake8
make types     # mypy
make check     # all of the above
```

## Database

```bash
make db        # MySQL shell
make db-root   # MySQL as root
make db-dump   # Backup to file
make db-restore # Restore from backup
```

## Project Structure

### Django Apps
- **`cards/`** — Authorization card management (Combatant, Card, Authorization, Discipline, Marshal, Waiver)
- **`sso_user/`** — Single Sign-On
- **`current_user/`** — User context middleware
- **`global_throttle/`** — Rate limiting

### Container Services
- **app** — Django + Gunicorn + Nginx (Python 3.13)
- **db** — MySQL
- **localstack** — AWS SSM emulation

### Key Models
- **Combatant** — Person with authorizations
- **Card** — Authorization card with expiration
- **Authorization** — Specific combat permission
- **Discipline** — Combat type (Heavy, Rapier, etc.)
- **Region** — Geographic region

## Testing

```bash
make test                                    # All tests
make shell
poetry run python manage.py test cards.tests.test_models  # Specific module
```

## Troubleshooting

**Container won't start?**
```bash
make bootstrap  # Complete rebuild
```

**Database issues?**
```bash
make db         # Check MySQL directly
make migrate    # Run pending migrations
```

**Import errors?**
```bash
make rebuild    # Rebuild with fresh dependencies
```
