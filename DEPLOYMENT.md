# EMOL Deployment Guide

EMOL (Electronic Minister of Lists) is designed to be easily deployable for any SCA kingdom. This guide explains how to set up and maintain your own instance.

## Initial Setup

### Prerequisites
- Ubuntu/Debian server
- Python 3.8 or higher
- Git
- AWS account for parameter storage

### First-Time Installation

1. Clone the repository:

```bash
cd /tmp
git clone https://github.com/lrt512/emol.git
cd emol
```

2. Run the bootstrap script:
```bash
./setup_files/bootstrap.sh
```

The script will:
- Install all required system dependencies
- Set up Python environment
- Configure nginx and services
- Create database tables
- Set up initial superuser

### Configuration

1. Set up AWS SSM parameters:
```bash
aws ssm put-parameter --name "/emol/django_settings_module" --value "emol.settings.prod" --type "SecureString"
aws ssm put-parameter --name "/emol/oauth_client_id" --value "your-oauth-id" --type "SecureString"
aws ssm put-parameter --name "/emol/oauth_client_secret" --value "your-oauth-secret" --type "SecureString"
aws ssm put-parameter --name "/emol/db_host" --value "your-db-host" --type "SecureString"
aws ssm put-parameter --name "/emol/db_name" --value "your-db-name" --type "SecureString"
aws ssm put-parameter --name "/emol/db_user" --value "your-db-user" --type "SecureString"
aws ssm put-parameter --name "/emol/db_password" --value "your-db-password" --type "SecureString"
```

2. Update nginx configuration:
Edit `/etc/nginx/sites-enabled/nginx.conf` and update `server_name` to match your domain.

## Maintenance

### Checking System Status
```bash
/opt/emol/setup_files/bootstrap.sh --status
```

This shows:
- Service status (nginx, emol)
- Available disk space
- Current version

### Updates

Check for updates:
```bash
/opt/emol/setup_files/deploy.sh --check
```

Deploy latest version:
```bash
/opt/emol/setup_files/deploy.sh
```

The update process:
- Checks current vs latest version
- Creates backup of existing installation
- Updates code and dependencies
- Runs database migrations
- Restarts services
- Rolls back automatically if anything fails

### Troubleshooting

1. View logs:
```bash
tail -f /var/log/emol_bootstrap.log  # Installation/update logs
tail -f /var/log/emol/error.log      # Application logs
```

2. Check service status:
```bash
systemctl status emol
systemctl status nginx
```

3. Force specific version:
```bash
/opt/emol/setup_files/deploy.sh --force v0.1.0
```

### Testing

The system includes features to help with testing:
- Throttling whitelist for development IPs
- Debug headers for rate limiting
- Testing decorator for higher throttle limits

## Security Considerations

1. SSL/TLS:
   - The system is configured to use HTTPS by default
   - Certbot is installed for Let's Encrypt certificates
   - HTTP traffic is automatically redirected to HTTPS

2. Rate Limiting:
   - Anonymous users are rate-limited
   - Authenticated users have unlimited access
   - IP whitelist available for trusted sources

3. Database:
   - Credentials stored in AWS SSM
   - Regular backups recommended
   - Migrations run automatically during updates

## Customization

EMOL is designed to be kingdom-agnostic. Main customization points:

1. OAuth Settings:
   - Update client ID/secret in AWS SSM
   - Configure callback URLs

2. Domain Configuration:
   - Update nginx.conf with your domain
   - Configure SSL certificates

3. Rate Limiting:
   - Adjust in settings.py:
     ```python
     GLOBAL_THROTTLE_LIMIT = 20  # Requests per window
     GLOBAL_THROTTLE_WINDOW = 3600  # Window in seconds
     GLOBAL_THROTTLE_WHITELIST = ['127.0.0.1', 'localhost', '::1']
     ```

4. Email Templates:
   - Customize templates in templates/email/
   - Update kingdom-specific text and branding

## Support

For issues or questions:
- Open an issue on GitHub
- Contact the maintainers
- Check the logs for detailed error information

## License

This project is licensed under the terms of the LICENSE file included in the repository.