# Development Guide

eMoL development runs entirely in Docker containers.

## Quick Start

### Prerequisites
- Docker and Docker Compose v2+
- Git
- Make

> **Need help setting up?** See our [Developer Setup Guide](DEVELOPER_SETUP.md) for Windows, Mac, and Linux instructions.

### Setup (5 minutes)

```bash
git clone <repository-url>
cd emol
make bootstrap
```

This will:
1. Build the development container (`Dockerfile.dev`)
2. Start the services (App, MySQL, Localstack)
3. Apply database migrations
4. **Seed initial development data** (Disciplines, Authorizations, Marshals, Privacy Policy)
5. Create a superuser (`admin` / `admin`)

Access the site at http://localhost:8000

## Initial Data

The `make bootstrap` command automatically populates the database with essential data for development:

*   **Privacy Policy**: A default policy required for email flows.
*   **Disciplines**:
    *   Armoured Combat
    *   Fencing
    *   Archery
    *   Thrown Weapons
*   **Authorizations**: Standard authorizations for each discipline.
*   **Marshals**: Default marshal types for each discipline.

You can reset this data at any time by re-running `make bootstrap` (warning: this resets the entire database).

## Daily Workflow

| Command | Purpose |
|---------|---------|
| `make up` | Start containers in background |
| `make down` | Stop containers |
| `make logs` | Follow application logs |
| `make shell` | Open a bash shell inside the container |
| `make test` | Run the test suite |
| `make migrate` | Run pending database migrations |
| `make makemigrations` | Create new migrations based on model changes |

**Code changes are live-mounted** — you do not need to rebuild the container for Python or template changes. The development server will auto-reload.

Only use `make rebuild` if you change `pyproject.toml` (dependencies) or `Dockerfile.dev`.

## Code Quality

Run these commands to ensure your code meets project standards:

```bash
make format    # Runs black and isort to format code
make lint      # Runs flake8 to check for style issues
make types     # Runs mypy for static type checking
make check     # Runs all of the above
```

## Database Management

Direct database access is available via these helper commands:

```bash
make db         # Opens a MySQL shell for the 'emol' user
make db-root    # Opens a MySQL shell for the 'root' user
make db-dump    # Dumps the current database to a file
make db-restore # Restores the database from a dump file
```

## Configuration

The development environment mirrors the production configuration structure. You can optionally create a local `config/` directory in the project root with:

*   **`config/emol_production.py`** (optional): Django settings overrides. This mirrors production's `/opt/emol_config/emol_production.py`.
*   **`config/emol_credentials.json`** (optional): AWS credentials for local testing. This mirrors production's `/opt/emol_config/emol_credentials.json`.

These files are automatically mounted into the container if they exist. The `config/` directory is git-ignored to protect any secrets you may place there.

## Project Structure

### Django Apps
- **`cards/`** — Core domain logic: Authorization card management, Combatants, Cards, Authorizations, Disciplines, Marshals, Waivers.
- **`sso_user/`** — Authentication and Single Sign-On (Google OAuth).
- **`current_user/`** — Middleware to manage user context.
- **`global_throttle/`** — Rate limiting middleware.

### Container Services
- **app** — Django + Gunicorn + Nginx (Python 3.13)
- **db** — MySQL 8.0
- **localstack** — AWS SSM emulation for local secrets management

### Key Models
- **Combatant**: A person who participates in combat activities.
- **Card**: Represents a physical authorization card with an expiration date.
- **Authorization**: A specific permission (e.g., "Sword and Shield") linked to a Discipline.
- **Discipline**: A major category of combat (e.g., "Armoured Combat").
- **Region**: Geographic grouping for combatants.

## Testing

Tests run inside the container to ensure environment parity.

```bash
make test                                    # Run all tests
make shell
poetry run python manage.py test cards.tests.test_models  # Run specific tests
```

## Troubleshooting

**Container won't start?**
```bash
make bootstrap  # Nuclear option: rebuilds containers and resets database
```

**Database connection issues?**
Ensure the `db` service is healthy.
```bash
docker compose ps
make db         # Try connecting manually
```

**New dependencies not found?**
If you added a package to `pyproject.toml`:
```bash
make rebuild    # Rebuilds image with new dependencies
```
