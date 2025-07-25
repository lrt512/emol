#!/bin/bash

GREEN='\033[1;32m'
RESET='\033[0m'

EMOL_DIR=/opt/emol

# create is_dev based on existence of EMOL_DEV envvar
if [[ -z "${EMOL_DEV}" ]]; then
    is_dev=false
    SOURCE_DIR=$(dirname "$(pwd)")
else
    is_dev=true
    SOURCE_DIR="/opt/emol"
    echo -e "\n"
    echo -e "${GREEN}Dev environment${RESET}"
    echo -e "\n"
fi

# Add near the top
DRY_RUN=false

# Add to the argument parsing
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --status)
            check_status
            exit 0
            ;;
        --help)
            show_help
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

setup_logging() {
    LOGFILE="/var/log/emol_bootstrap.log"
    exec 1> >(tee -a "$LOGFILE")
    exec 2> >(tee -a "$LOGFILE" >&2)
    echo -e "\n=== Bootstrap started at $(date) ===" >> "$LOGFILE"
}

system_dependencies() {
    echo -e "\nInstalling/updating system dependencies..."
    apt-get update
    apt-get install -y \
        awscli nginx certbot \
        git python3-venv python3-pip \
        python3-certbot-nginx

    apt-get install -y --no-install-recommends \
        build-essential pkg-config  \
        python3-dev \
        libmysqlclient-dev

    # Update pip and poetry
    pip install -U pip setuptools wheel poetry
}

check_dependencies() {
    echo -e "Checking dependencies..."
    
    # Source asdf if available
    if [ -f "${ASDF_DIR}/asdf.sh" ]; then
        source ${ASDF_DIR}/asdf.sh
    fi
    
    # Check Python version
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')

    # Convert version strings to comparable numbers
    version_to_number() {
        echo "$1" | awk -F. '{ printf("%d%03d\n", $1, $2) }'
    }

    MIN_VERSION="3.8"
    CURRENT_VERSION_NUM=$(version_to_number "$PYTHON_VERSION")
    MIN_VERSION_NUM=$(version_to_number "$MIN_VERSION")

    if [ "$CURRENT_VERSION_NUM" -ge "$MIN_VERSION_NUM" ]; then
        echo -e "${GREEN}Python version check passed: found $PYTHON_VERSION${RESET}"
    else
        echo -e "${RED}Python 3.8 or higher required, found $PYTHON_VERSION${RESET}"
        exit 1
    fi

    # Check for required system packages
    REQUIRED_PACKAGES="nginx certbot python3-venv python3-pip python3-dev libmysqlclient-dev"
    for pkg in $REQUIRED_PACKAGES; do
        if ! dpkg -l | grep -q "^ii  $pkg "; then
            echo -e "\033[1;31mRequired package '$pkg' not found - installing dependencies${RESET}"
            system_dependencies
            return
        fi
    done
    
    # Check for required commands
    REQUIRED_COMMANDS="poetry nginx aws git"
    for cmd in $REQUIRED_COMMANDS; do
        if ! command -v $cmd &> /dev/null; then
            echo -e "\033[1;31mRequired command '$cmd' not found - installing dependencies${RESET}"
            system_dependencies
            return
        fi
    done
    
    echo -e "${GREEN}All dependencies satisfied${RESET}"
}

check_disk_space() {
    # Check if we have at least 1GB free
    FREE_SPACE=$(df -m /opt | awk 'NR==2 {print $4}')
    if [ "$FREE_SPACE" -lt 1024 ]; then
        echo -e "\033[1;31mInsufficient disk space (less than 1GB free) - aborting${RESET}"
        exit 1
    fi
}

backup_existing() {
    if [ -d "$EMOL_DIR" ]; then
        check_disk_space
        echo -e "Creating backup of existing installation..."
        BACKUP_DIR="/opt/emol_backup_$(date +%Y%m%d_%H%M%S)"
        cp -R "$EMOL_DIR" "$BACKUP_DIR"
        echo -e "${GREEN}Backup created at ${BACKUP_DIR}${RESET}"
    fi
}

rollback() {
    if [ -d "$BACKUP_DIR" ]; then
        echo -e "Rolling back to previous version..."
        rm -rf "$EMOL_DIR"
        mv "$BACKUP_DIR" "$EMOL_DIR"
        echo -e "${GREEN}Rollback complete${RESET}"
    fi
}

install_emol() {
    if [ "$is_dev" = true ]; then
        return
    fi

    if [ "$DRY_RUN" = true ]; then
        echo "[DRY RUN] Would install EMOL to $INSTALL_DIR"
        return
    fi

    INSTALL_DIR="/opt/emol"
    
    # Backup existing installation
    backup_existing

    # Create fresh install directory
    rm -rf "$INSTALL_DIR"
    mkdir -p "$INSTALL_DIR"

    # Define an array of files and directories to be copied
    FILES_TO_COPY=(
        "LICENSE"
        "README.md"
        "emol/"
        "poetry.lock"
        "poetry.toml"
        "pyproject.toml"
    )

    # Copy files with error checking
    for item in "${FILES_TO_COPY[@]}"; do
        if ! cp -R "$SOURCE_DIR/$item" "$INSTALL_DIR"; then
            echo -e "\033[1;31mError copying $item - rolling back${RESET}"
            rollback
            exit 1
        fi
    done
}


cleanup_build() {
    echo -e "\n"
    echo -e "Removing build dependencies..."
    apt-get purge --auto-remove -y build-essential
    apt-get clean
    rm -rf /var/lib/apt/lists/*
}

environment_specific_setup() {
    if [ "$is_dev" = true ]; then
        echo "Setting up development environment..."
        
        # Set up AWS SSM parameters for development
        aws ssm put-parameter --name "/emol/django_settings_module" --value "emol.settings.dev" --type "SecureString" --endpoint-url "http://localstack:4566" --overwrite
        aws ssm put-parameter --name "/emol/oauth_client_id" --value "mock-client-id" --type "SecureString" --endpoint-url "http://localstack:4566" --overwrite
        aws ssm put-parameter --name "/emol/oauth_client_secret" --value "mock-client-secret" --type "SecureString" --endpoint-url "http://localstack:4566" --overwrite
        aws ssm put-parameter --name "/emol/db_host" --value "db" --type "SecureString" --endpoint-url "http://localstack:4566" --overwrite
        aws ssm put-parameter --name "/emol/db_name" --value "emol" --type "SecureString" --endpoint-url "http://localstack:4566" --overwrite
        aws ssm put-parameter --name "/emol/db_user" --value "emol_db_user" --type "SecureString" --endpoint-url "http://localstack:4566" --overwrite
        aws ssm put-parameter --name "/emol/db_password" --value "emol_db_password" --type "SecureString" --endpoint-url "http://localstack:4566" --overwrite
        
        # Grant test database permissions for Django tests
        echo "Setting up test database permissions..."
    else
        # In the real world, www-data needs to own the files    
        chown -R www-data:www-data /opt/emol
    fi
}

emol_dependencies() {
    pushd /opt/emol
    poetry config virtualenvs.in-project true
    poetry install --only main
    chown -R www-data:www-data .venv
    popd
}

run_db_operations() {
    echo -e "\nRunning database operations..."
    pushd /opt/emol
    # Change directory to emol to find manage.py
    cd emol

    echo "Apply migrations"
    if ! poetry run python manage.py migrate; then
        echo -e "\033[1;31mDatabase migrations failed - rolling back${RESET}"
        popd
        rollback
        exit 1
    fi
    
    echo "Collect static files"
    if ! poetry run python manage.py collectstatic --noinput; then
        echo -e "\033[1;31mStatic file collection failed - rolling back${RESET}"
        popd
        rollback
        exit 1
    fi
    
    echo "Create cache table"
    if ! poetry run python manage.py createcachetable; then
        echo -e "\033[1;31mCache table creation failed - rolling back${RESET}"
        popd
        rollback
        exit 1
    fi
    
    echo "Ensure superuser exists"
    if ! poetry run python manage.py ensure_superuser; then
        echo -e "\033[1;31mSuperuser creation failed - rolling back${RESET}"
        popd
        rollback
        exit 1
    fi
    
    popd
}

check_version() {
    if [ "$is_dev" = true ]; then
        return
    fi

    echo -e "Checking version..."
    
    # Get current version if it exists
    CURRENT_VERSION=""
    if [ -f "$EMOL_DIR/VERSION" ]; then
        CURRENT_VERSION=$(cat "$EMOL_DIR/VERSION")
    fi
    
    # Get new version
    NEW_VERSION=$(cat "$SOURCE_DIR/VERSION")
    
    if [ "$CURRENT_VERSION" = "$NEW_VERSION" ]; then
        echo -e "${GREEN}Already at version $NEW_VERSION - no update needed${RESET}"
        exit 0
    fi
    
    echo -e "Updating from version $CURRENT_VERSION to $NEW_VERSION"
}

check_status() {
    echo -e "\nChecking system status..."
    
    # Check services
    echo "Services:"
    systemctl is-active --quiet nginx && echo "  nginx: ✓" || echo "  nginx: ✗"
    systemctl is-active --quiet emol && echo "  emol: ✓" || echo "  emol: ✗"
    
    # Check disk space
    echo -e "\nDisk space:"
    df -h /opt | awk 'NR==2 {printf "  Available: %s\n", $4}'
    
    # Check current version
    echo -e "\nVersion:"
    if [ -f "$EMOL_DIR/VERSION" ]; then
        echo "  $(cat $EMOL_DIR/VERSION)"
    else
        echo "  Unknown"
    fi
}

show_help() {
    cat << EOF
EMOL Bootstrap Script

Usage: $0 [options]

Options:
    --dry-run       Show what would be done without making changes
    --status        Show system status and exit
    --help          Show this help message and exit

Examples:
    $0                     # Normal installation/update
    $0 --dry-run          # Show what would be done
    $0 --status           # Check system status
EOF
    exit 0
}

progress() {
    echo -e "\n${GREEN}[$1/${TOTAL_STEPS}] $2${RESET}"
}

setup_logging

# Always check and potentially update dependencies
TOTAL_STEPS=7
CURRENT_STEP=0

progress $((++CURRENT_STEP)) "Checking dependencies"
check_dependencies

progress $((++CURRENT_STEP)) "Installing EMOL"
install_emol
emol_dependencies
environment_specific_setup
run_db_operations
echo -e "\n"
echo -e "${GREEN}Bootstrap complete${RESET}"

# Service configuration functions
configure_nginx() {
    echo -e "\nConfiguring nginx..."
    
    # Ensure nginx pid directory exists and has correct permissions
    mkdir -p /run/nginx
    chown -R www-data:www-data /run/nginx
    
    # Configure main nginx.conf
    cat > /etc/nginx/nginx.conf << 'EOF'
user www-data;
worker_processes auto;
pid /run/nginx/nginx.pid;
include /etc/nginx/modules-enabled/*.conf;

events {
    worker_connections 768;
}

http {
    sendfile on;
    tcp_nopush on;
    types_hash_max_size 2048;
    
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;

    access_log /var/log/nginx/access.log combined buffer=512k flush=1m;
    error_log /var/log/nginx/error.log warn;

    gzip on;

    include /etc/nginx/conf.d/*.conf;
    include /etc/nginx/sites-enabled/*;
}
EOF

    # Set up environment variables for templates
    export NGINX_LOG_PATH="/var/log/nginx"
    export STATIC_ROOT="/opt/emol/static"
    export SOCKET_PATH="/opt/emol/emol.sock"
    
    local template_file
    if [ "$is_dev" = true ]; then
        template_file="/opt/emol/setup_files/configs/nginx.dev.conf"
    else
        template_file="/opt/emol/setup_files/configs/nginx.prod.conf"
    fi

    # Process template and ensure sites-enabled directory exists
    mkdir -p /etc/nginx/sites-enabled
    envsubst < "$template_file" > /etc/nginx/sites-enabled/emol.conf
    
    # Also set up proxy params
    cp /opt/emol/setup_files/configs/proxy_params /etc/nginx/proxy_params

    # Ensure log directory exists with proper permissions
    mkdir -p /var/log/nginx
    chown -R www-data:www-data /var/log/nginx

    # Test configuration
    if ! nginx -t; then
        echo -e "\033[1;31mNginx configuration test failed${RESET}"
        exit 1
    fi
}

configure_gunicorn() {
    echo -e "\nConfiguring gunicorn..."
    cat > /etc/init.d/emol << 'EOF'
#!/bin/sh
### BEGIN INIT INFO
# Provides:          gunicorn
# Required-Start:    $all
# Required-Stop:     $all
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: Start Gunicorn at boot
# Description:       Enable Gunicorn service.
### END INIT INFO

ROOT=/opt/emol/emol
PID=/var/run/emol.pid

case "$1" in
  start)
    echo "Starting eMoL"
    cd $ROOT
    poetry run gunicorn \
        --pid $PID \
        --workers 3 \
        --bind unix:/opt/emol/emol.sock \
        --access-logfile /var/log/emol/gunicorn.log \
        --error-logfile /var/log/emol/gunicorn.error.log \
        --daemon \
        emol.wsgi:application
    ;;
  stop)
    echo "Stopping Gunicorn"
    if [ -f $PID ]; then
        kill -9 $(cat $PID)
        rm -f $PID
    fi
    ;;
  status)
    if [ -f $PID ]; then
      echo "emol (gunicorn) is running with pid: $(cat $PID)"
    else
      echo "emol (gunicorn) is not running"
    fi
    ;;
  restart)
    $0 stop
    $0 start
    ;;
  *)
    echo "Usage: /etc/init.d/emol {start|stop|restart}"
    exit 1
    ;;
esac

exit 0
EOF

    chmod +x /etc/init.d/emol
}

configure_logrotate() {
    echo -e "\nConfiguring log rotation..."
    
    # Only set up logrotate in production (not in development containers)
    if [ "$is_dev" = true ]; then
        echo "Skipping logrotate configuration in development environment"
        return
    fi
    
    # Install logrotate configuration for eMoL logs
    cp /opt/emol/setup_files/configs/emol-logrotate /etc/logrotate.d/emol
    chmod 644 /etc/logrotate.d/emol
    
    echo "Log rotation configured for 7-day retention"
}

setup_services() {
    echo -e "\nSetting up services..."
    configure_gunicorn
    configure_nginx
    configure_logrotate
}

# In the main sequence
progress $((++CURRENT_STEP)) "Setting up services"
setup_services

configure_settings() {
    echo -e "\nConfiguring settings..."
    
    # Ensure we're using dev.py in development
    if [ "$is_dev" = true ]; then
        echo "Using development settings (dev.py)"
        export DJANGO_SETTINGS_MODULE=emol.settings.dev
    fi
}

# Add to the main sequence
progress $((++CURRENT_STEP)) "Configuring settings"
configure_settings
