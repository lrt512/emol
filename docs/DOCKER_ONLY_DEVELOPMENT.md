# Development Environment

All development runs in Docker containers. No local Python, Poetry, or dependencies required.

## Prerequisites

- Docker and Docker Compose v2+
- Git
- Make

## Quick Start

```bash
# Clone and bootstrap (one-time)
git clone <repo>
cd emol
make bootstrap

# Daily development
make up          # Start containers
make logs        # View logs
make shell       # Open container shell
make down        # Stop containers
```

## How It Works

- **Code is live-mounted** — edit locally, changes appear immediately in container
- **Database persists** — MySQL data survives `make down`
- **No rebuild needed** for code changes

## Common Commands

| Command | Purpose |
|---------|---------|
| `make up` | Start containers |
| `make down` | Stop containers |
| `make logs` | Tail application logs |
| `make shell` | Bash shell in container |
| `make test` | Run tests |
| `make format` | Format code (black, isort) |
| `make lint` | Lint code (flake8) |
| `make types` | Type check (mypy) |
| `make migrate` | Run migrations |
| `make db` | MySQL shell |

## When to Rebuild

Only rebuild (`make rebuild`) for:
- Dependency changes (poetry.lock)
- Dockerfile.dev changes
- System package changes

Code changes don't need rebuild.

## Container Architecture

```
┌─────────────────────────────────────────────┐
│  app (emol-app-1)                           │
│  - Python 3.13 + Poetry                     │
│  - Django + Gunicorn + Nginx                │
│  - Your code mounted at /opt/emol           │
└─────────────────────────────────────────────┘
         │
         ├── db (MySQL)
         │
         └── localstack (SSM parameters)
```

## Troubleshooting

**Container won't start?**
```bash
make bootstrap  # Complete rebuild
```

**Database issues?**
```bash
make db  # Check MySQL directly
```

**Check container status?**
```bash
docker compose ps
```
