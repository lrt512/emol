# Development Guide

Welcome to eMoL (electronic Ministry of Lists)! This guide will help you get started with development and understand the project structure.

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
   - 👤 **Admin**: http://localhost:8000/admin (superuser: `admin` / `admin`)

## Initial Data
See also the Google doc here: https://docs.google.com/document/d/1OxtfClGNAlUrNU9n_-nHQv7xctCttW2iRf1dfTpFqrw/edit?tab=t.0

You'll need to seed some data before you can use the system once it is bootstrapped
- Go to the app running locally - http://localhost:8000
- Click the Sign In button, it should sign you in as "admin@emol.ca"
- Click the gear icon that appears to go to the admin panel

### Privacy Policy
You need to define a privacy policy so that the email flows work. 
- Click `+Add` beside `Privacy policies`
- Add some text. It can be anything at all in development
- Save it

### Disciplines
You need at least one Discipline
- Click `+Add` beside `Disciplines`
- Enter a name like Fencing, Armoured Combat, whatever
- Click Save

### Authorizations
Your Discipline needs authorizations
- Click `+Add` beside `Authorizations`
- Enter an authorization name
- Select a discipline from the dropdown box
- Click Save

### Marshals
You don't _have_ to define marshal types for development, but if you do the idea is similar to Authorizations

### User Permissions
The built in test user is a superuser, so you don't need to assign any User Permissions for development

### Managing Combatants
Now you can go back to the home page at http://localhost:8000 and click the crossed swords icon to get to the combatant management interface. 
See https://docs.google.com/document/d/1Z9rKMqbi-IJS9clKqhzlunVEEHrzbnlpyw1T4kRCYlE/edit?tab=t.0 for a guide on managing combatants

*Note:* emails will _not_ be sent from the running development environment. Instead, open another terminal window and run `make django-logs` to see the log output from the application. The emails that would be sent will appear there.


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

## 🏗️ Project Architecture

### Overview
eMoL is a Django-based application for managing combat authorizations and marshal lists for the Society for Creative Anachronism (SCA).

### Core Components

#### Django Apps
- **`cards/`** - Main application for authorization card management
  - Models: `Combatant`, `Card`, `Authorization`, `Discipline`, `Marshal`, `Waiver`
  - Views: Card requests, self-serve updates, admin interfaces
  - API: REST endpoints for data access
- **`sso_user/`** - Single Sign-On user management
- **`current_user/`** - Current user context middleware
- **`global_throttle/`** - Rate limiting middleware

#### Key Models
- **`Combatant`** - Core entity representing a person with authorizations
- **`Card`** - Authorization cards with expiration logic
- **`Authorization`** - Specific combat authorizations
- **`Discipline`** - Types of combat (e.g., Heavy, Rapier)
- **`Region`** - Geographic regions (provinces/states)
- **`UpdateCode`** - Secure codes for self-serve updates

#### Technology Stack
- **Backend**: Django 4.2, Django REST Framework
- **Database**: MySQL
- **Frontend**: Bootstrap, jQuery
- **Containerization**: Docker, Docker Compose
- **Dependency Management**: Poetry
- **Code Quality**: Black, isort, flake8, mypy, pylint

## 🔧 Development Environment

### Container Services
- **App Container**: Django + Gunicorn + Nginx
- **Database**: MySQL with persistent volumes
- **LocalStack**: AWS SSM emulation for development

### Environment Variables
- `EMOL_DEV=1` - Development mode
- `DJANGO_SETTINGS_MODULE=emol.settings.dev` - Development settings
- AWS credentials for LocalStack integration

### Volume Mounts
- Code is live-mounted: `/opt/emol` → `./`
- Static files: `/opt/emol/static`
- Logs: `/var/log/emol` and `/var/log/nginx`

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

## 🧪 Testing

### Running Tests
```bash
make test                  # Run all tests
make test cards.tests.test_self_serve_update  # Run specific test file
make test cards.tests.test_self_serve_update.SelfServeUpdateSerializerTestCase  # Run specific test class
```

### Test Structure
- **Unit Tests**: `emol/cards/tests/`
- **Model Tests**: `emol/cards/tests/test_models/`
- **View Tests**: `emol/cards/tests/test_views_home.py`
- **Integration Tests**: `emol/cards/tests/test_self_serve_update.py`

### Test Best Practices
- Use `django.test.TestCase` for database tests
- Mock external services with `unittest.mock`
- Test both valid and invalid scenarios
- Include edge cases and error conditions

## 🔍 Code Quality

### Code Quality Commands
```bash
make check                # Run all checks (format, types, lint, test)
make format               # Format code with black and isort
make check-format         # Check formatting without changing
make check-types          # Run mypy type checking
make check-lint           # Run flake8 linting
make pylint               # Run pylint (more strict)
```

### Code Style Guidelines
- **Python**: PEP 8, Black formatting, type hints
- **Django**: Follow Django coding style guide
- **Comments**: Minimal, focus on "why" not "what"
- **Names**: Descriptive, reveal purpose and usage

### Pre-commit Checklist
- [ ] Code passes `make check`
- [ ] Tests pass: `make test`
- [ ] No new linting errors
- [ ] Type hints are complete
- [ ] Documentation updated if needed

## 🗄️ Database Operations

### Database Commands
```bash
make db                   # Connect to MySQL as application user
make db-root              # Connect as root
make db-dump              # Create database backup
make db-restore <file>    # Restore from backup
make migrate              # Run Django migrations
```

### Migration Best Practices
- Always test migrations on development data
- Use `RunPython` for complex data migrations
- Include rollback logic when possible
- Test both forward and backward migrations

## 🚀 Deployment

### Development vs Production
- **Development**: Docker containers, LocalStack for AWS services
- **Production**: AWS Lightsail container, real AWS services
- **Settings**: `emol.settings.dev` vs `emol.settings.prod`

### Deployment Commands
```bash
make setup                # Quick production-parity setup
make bootstrap-script     # Run production bootstrap script
make bootstrap-test       # Test deployment scripts locally
```

## 🐛 Debugging

### Common Issues

#### Container Won't Start
```bash
make down                 # Stop all containers
make bootstrap            # Complete rebuild
```

#### Import Errors
```bash
make shell                # Check container environment
poetry install            # Install dependencies
```

#### Database Issues
```bash
make db                   # Check database connection
make migrate              # Run pending migrations
```

#### Permission Issues
- Check file permissions in mounted volumes
- Verify Docker user permissions
- Check SELinux/AppArmor settings

### Debug Tools
- **Django Debug Toolbar**: Available in development
- **Logs**: Use `make all-logs` for comprehensive monitoring
- **Shell**: `make shell` for interactive debugging
- **Database**: `make db` for direct database access

## 📚 Key Concepts

### SCA Terminology
- **Combatant**: Person with combat authorizations
- **Authorization**: Permission for specific combat type
- **Marshal**: Official who oversees combat activities
- **Discipline**: Type of combat (Heavy, Rapier, etc.)
- **Kingdom**: Regional SCA organization

### Django Patterns Used
- **MVT Pattern**: Models, Views, Templates
- **Class-Based Views**: For complex view logic
- **Model Serializers**: For API and form handling
- **Signals**: For post-save actions
- **Custom Model Fields**: For encrypted data
- **Middleware**: For user context and throttling

### Security Features
- **Encrypted Fields**: Sensitive data encrypted at rest
- **Permission System**: Granular access control
- **Rate Limiting**: Global throttle middleware
- **CSRF Protection**: Built-in Django protection
- **Input Validation**: Comprehensive form validation

## 🤝 Contributing

### Development Workflow
1. Create feature branch from `main`
2. Make changes with tests
3. Run `make check` to ensure quality
4. Submit pull request with clear description
5. Address review feedback

### Code Review Checklist
- [ ] Tests pass and cover new functionality
- [ ] Code follows project style guidelines
- [ ] No security vulnerabilities introduced
- [ ] Documentation updated if needed
- [ ] Migration files included for model changes

### Getting Help
- Check existing issues and documentation
- Review test files for usage examples
- Use `make shell` to explore the environment
- Check logs for error details

## 📖 Additional Resources

- **Django Documentation**: https://docs.djangoproject.com/
- **Django REST Framework**: https://www.django-rest-framework.org/
- **Poetry Documentation**: https://python-poetry.org/docs/
- **Docker Documentation**: https://docs.docker.com/

---

**Happy coding!** 🎉
