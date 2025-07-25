FROM ubuntu:22.04

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    TZ=America/Toronto \
    POETRY_VERSION=1.8.5 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    ASDF_DIR=/opt/asdf \
    ASDF_DATA_DIR=/opt/asdf

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip python3-venv \
    nginx \
    awscli \
    certbot \
    python3-certbot-nginx \
    git \
    build-essential \
    pkg-config \
    python3-dev \
    libmysqlclient-dev \
    curl \
    systemd \
    unzip \
    gettext-base \
    && rm -rf /var/lib/apt/lists/*

# Copy .tool-versions first to read Python version
COPY .tool-versions /opt/emol/

# Install asdf
RUN git clone https://github.com/asdf-vm/asdf.git ${ASDF_DIR} --branch v0.13.1 && \
    echo '. ${ASDF_DIR}/asdf.sh' >> ~/.bashrc && \
    echo '. ${ASDF_DIR}/completions/asdf.bash' >> ~/.bashrc

# Source asdf in current shell
SHELL ["/bin/bash", "-c"]
RUN source ${ASDF_DIR}/asdf.sh && \
    # Add Python plugin
    asdf plugin add python && \
    # Read and install Python version from .tool-versions
    PYTHON_VERSION=$(grep "^python" /opt/emol/.tool-versions | cut -d' ' -f2) && \
    asdf install python ${PYTHON_VERSION} && \
    asdf global python ${PYTHON_VERSION}

# Install poetry
RUN source ${ASDF_DIR}/asdf.sh && \
    curl -sSL https://install.python-poetry.org | python3 - && \
    ln -s /opt/poetry/bin/poetry /usr/local/bin/poetry

# Create directory structure
RUN mkdir -p /opt/emol/emol

# Copy setup files first
COPY setup_files /opt/emol/setup_files
RUN chmod +x /opt/emol/setup_files/*.sh

# Setup AWS credentials for local development
RUN mkdir -p ~/.aws && \
    echo "[default]\n\
    aws_access_key_id = test\n\
    aws_secret_access_key = test\n\
    region = ca-central-1\n\
    output = json" > ~/.aws/credentials && \
    echo "[default]\n\
    region = ca-central-1\n\
    output = json" > ~/.aws/config

# Copy application code
COPY . /opt/emol/
WORKDIR /opt/emol/emol

# Configure nginx
RUN rm -f /etc/nginx/sites-enabled/default

# Create required directories with proper permissions
RUN mkdir -p /var/log/emol && \
    chown -R www-data:www-data /var/log/emol && \
    mkdir -p /var/run/emol && \
    chown -R www-data:www-data /var/run/emol && \
    mkdir -p /etc/nginx/sites-enabled && \
    mkdir -p /etc/init.d

# Install Python dependencies
RUN cd /opt/emol && \
    poetry install --only main && \
    chown -R www-data:www-data /opt/emol

EXPOSE 80

# Use a custom entrypoint script
COPY setup_files/docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

ENTRYPOINT ["/docker-entrypoint.sh"]
