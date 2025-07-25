# eMoL (electronic Ministry of Lists)

A Django-based application for managing medieval combat authorizations and marshal lists.

## 🚀 Quick Start for New Developers

### Prerequisites
- **Docker** and **Docker Compose** v2+
- **Git**
- **Make** (included on most Unix systems)

### First-Time Setup (5 minutes)

1. **Clone and navigate:**
   ```bash
   git clone <repository-url>
   cd emol
   ```

2. **Bootstrap your environment:**
   ```bash
   make bootstrap
   ```
   This single command:
   - Builds containers from scratch
   - Starts all services with health checks
   - Runs database migrations
   - Creates cache tables
   - Generates a superuser account
   - Imports initial data
   - Sets up production-parity environment

3. **Access the application:**
   - 🌐 **Web App**: http://localhost:8000

## 📋 Daily Development Workflow

### Essential Commands

| Command | Purpose | When to Use |
|---------|---------|-------------|
| `make up` | Start existing services | Daily startup |
| `make down` | Stop all services | End of day |
| `make test` | Run tests | Before commits |
| `make shell` | Container shell access | Code inspection |
| `make restart-app` | Quick app restart | Config changes |

### Development vs Structural Changes

**Daily Code Changes** (live-mounted, no rebuild needed):
- Python code changes
- Template modifications  
- Static file updates
- Configuration tweaks

**Structural Changes** (require rebuild):
```bash
make rebuild  # For dependency or Dockerfile changes
```

**Fresh Start** (nuclear option):
```bash
make bootstrap  # Complete environment rebuild
```

## 📊 Real-Time Log Monitoring

### Log Commands (Use in Second Terminal)

| Command | Shows | Best For |
|---------|-------|----------|
| `make django-logs` | Django app logs | General debugging |
| `make access-logs` | HTTP requests | API testing |
| `make error-logs` | Error messages | Troubleshooting |
| `make all-logs` | Everything combined | Comprehensive monitoring |
| `make nginx-logs` | Web server logs | Proxy issues |

### Example Development Session
```bash
# Terminal 1: Development
make up                    # Start services
make test                  # Run tests
# ... make code changes ...
make restart-app           # Apply changes

# Terminal 2: Live monitoring  
make django-logs           # Watch application activity
```

## 🏗️ Architecture & Services

### Container Services
- **App Container**: Django + Gunicorn + Nginx
- **Database**: MySQL with persistent volumes
- **LocalStack**: AWS SSM emulation for dev

### Health Checks & Dependencies
- Automatic service dependency management
- Health check validation before startup
- `--wait` flag ensures reliable initialization

### Production Parity
- Same service configuration as production
- Identical logging structure
- Matching security headers and middleware

## 🔧 Advanced Development

### Database Operations
```bash
make db              # Connect to app database  
make db-root         # Connect as root
make migrate         # Run migrations
```

### Code Quality
```bash
make test            # Run test suite
make lint            # Code linting
make format          # Auto-format code
make check           # All quality checks
```

### Container Management
```bash
make logs            # Container system logs
make status          # Service status check
make prune           # Clean unused images
```

## 🐛 Troubleshooting

### Common Issues

**Import/Module Errors After `make test`:**
```bash
make bootstrap  # Rebuild environment
```

**Services Won't Start:**
```bash
make down
make bootstrap  # Fresh rebuild
```

**Database Connection Issues:**
```bash
make status          # Check service health
make db              # Test database connectivity
```

**Can't Access Website:**
- Check `make status` shows both nginx and gunicorn running
- Verify http://localhost:8000 in browser
- Check `make access-logs` for request activity

### Getting Help
```bash
make help           # Show all available commands
make <target>       # Run specific command
```

## 🔐 Authentication (Development)

### Mock OAuth Setup
- **Email**: Any registered user email
- **Password**: Anything (ignored in dev mode)
- **Admin Access**: `admin@emol.com`

The development environment uses MockOAuthClient that simulates Google OAuth without requiring real credentials.

## 🌐 Production Deployment

### Google OAuth Configuration
1. **Google Developers Console**: https://console.developers.google.com/
2. **Create OAuth credentials**:
   - Application type: Web application
   - Authorized redirect URIs:
     - `https://your-domain.com/auth/callback`
     - `https://your-domain.com/auth/admin/oauth/`

### AWS SSM Parameter Store
Store these production parameters:
```
/emol/django_settings_module  # emol.settings.prod
/emol/oauth_client_id         # From Google OAuth setup
/emol/oauth_client_secret     # From Google OAuth setup  
/emol/db_host                 # MySQL server host
/emol/db_name                 # Database name
/emol/db_user                 # Database username
/emol/db_password             # Database password
```

### Production Database
1. **Create MySQL database** and user
2. **Set database permissions** for application user
3. **Update SSM parameters** with credentials

### Application Deployment
```bash
# On production server
git clone <repository-url>
cd emol/setup_files
chmod +x *.sh
./bootstrap.sh  # Production setup
```

## 🎯 Development Features

### Live Development
- **Code changes**: Immediately reflected (no restart needed)
- **Template changes**: Live updates
- **Static files**: Auto-collected
- **Volume mounting**: Preserves data between restarts

### Comprehensive Logging
- **File-based**: Persistent logs in `/var/log/emol/`
- **Real-time**: Live log streaming with Make targets
- **Structured**: Separate access, error, and application logs
- **Development-friendly**: Enhanced console output

### Testing & Quality
- **Automated testing**: `make test` with container startup
- **Code quality**: Linting, formatting, type checking
- **Health checks**: Service dependency validation

## 📚 Project Structure

```
emol/
├── emol/                   # Django application
│   ├── cards/              # Main app (authorizations, cards)
│   ├── sso_user/           # Authentication system
│   ├── global_throttle/    # Rate limiting middleware
│   └── settings/           # Environment-specific settings
├── setup_files/           # Deployment and configuration
├── docker-compose.yml     # Development services
├── Dockerfile             # Application container
├── Makefile              # Development workflow
└── README.md             # This file
```

## 🤝 Contributing

### Development Guidelines
1. **Start with `make bootstrap`** for fresh environment
2. **Use `make test`** before committing
3. **Monitor with `make django-logs`** during development
4. **Follow code quality** with `make check`

### Git Workflow
```bash
git checkout -b feature/my-feature
# ... make changes ...
make test                  # Ensure tests pass
git commit -m "feat: my feature"
git push origin feature/my-feature
```

---

**Happy coding! 🎉**

For questions or issues, check `make help` or consult the troubleshooting section above.